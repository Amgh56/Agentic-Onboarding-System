"""The agent's tools. The model chooses them; this code runs them.

company_id and the candidate come from the run, never from the model.
Every tool is safe to call twice, and every call is logged with its reason.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.core.events import log_event
from app.core.security import create_upload_token
from app.features.agent import verifier
from app.features.agent.model import ActionLog
from app.features.approvals import service as approvals_service
from app.features.candidates import service as candidates_service
from app.features.departments import service as departments_service
from app.features.documents import service as documents_service
from app.features.jobs import service as jobs_service
from app.features.notifications import service as notifications_service
from app.features.notifications.email_templates import render
from app.features.plans import service as plans_service
from app.features.systems import service as systems_service

CANDIDATE = {"type": "integer", "description": "The candidate this run is about."}
REASON = {"type": "string", "description": "One sentence: why you are doing this. HR reads it."}


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {**properties, "reason": REASON},
                "required": [*required, "reason"],
            },
        },
    }


SCHEMAS = [
    _schema(
        "request_documents",
        "Ask the candidate for documents, by email. channel email: they reply with attachments. "
        "channel upload_link: the email has a personal link to upload them. The job's files are attached.",
        {
            "candidate_id": CANDIDATE,
            "documents": {"type": "array", "items": {"type": "string"}, "description": "Document names, e.g. National ID."},
            "channel": {"type": "string", "enum": ["email", "upload_link"], "description": "Use what the procedure says. Default email."},
            "due_in_days": {"type": "integer", "description": "Days the candidate has. Default 3, or what the procedure says."},
        },
        ["candidate_id", "documents"],
    ),
    _schema(
        "request_missing_documents",
        "Email the candidate one message listing every requested document that is still missing or was "
        "rejected, with the reason. Use it after checking a reply, and with reminder=true when a deadline passed.",
        {"candidate_id": CANDIDATE, "reminder": {"type": "boolean", "description": "True when a deadline has passed."}},
        ["candidate_id"],
    ),
    _schema(
        "read_inbox",
        "Read the candidate's new replies. Attachments become documents you can validate.",
        {"candidate_id": CANDIDATE},
        ["candidate_id"],
    ),
    _schema(
        "validate_document",
        "Check one received document: right type, name matches, not expired, readable.",
        {"candidate_id": CANDIDATE, "document_id": {"type": "integer"}},
        ["candidate_id", "document_id"],
    ),
    _schema(
        "send_email",
        "Email the candidate (candidate_id) or a department (department_id). Give exactly one of them.",
        {
            "candidate_id": CANDIDATE,
            "department_id": {"type": "integer", "description": "From the department directory."},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        ["subject", "body"],
    ),
    _schema(
        "create_account",
        "Create an account in one of the company's systems. Create work_email first; the others use it.",
        {
            "candidate_id": CANDIDATE,
            "system": {"type": "string", "description": "A system key from the catalog."},
            "groups": {"type": "array", "items": {"type": "string"}, "description": "Groups from that system's catalog."},
        },
        ["candidate_id", "system", "groups"],
    ),
    _schema(
        "create_ticket",
        "Open an IT desk ticket for equipment or access, e.g. Laptop.",
        {"candidate_id": CANDIDATE, "item": {"type": "string"}},
        ["candidate_id", "item"],
    ),
    _schema(
        "escalate",
        "Hand a problem to HR when you cannot or should not decide it yourself.",
        {"candidate_id": CANDIDATE},
        ["candidate_id"],
    ),
    _schema(
        "request_approval",
        "Ask HR to approve an action before you do it.",
        {"candidate_id": CANDIDATE, "action": {"type": "string", "description": "The action you want to take."}},
        ["candidate_id", "action"],
    ),
    _schema(
        "complete_steps",
        "Record plan steps as done, or skipped when a step does not apply to this candidate. "
        "Call it whenever you finish steps.",
        {
            "candidate_id": CANDIDATE,
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "string", "description": "e.g. step-2"},
                        "outcome": {"type": "string", "enum": ["done", "skipped"]},
                    },
                    "required": ["step_id", "outcome"],
                },
            },
        },
        ["candidate_id", "steps"],
    ),
    _schema(
        "mark_completed",
        "Mark onboarding as finished. Every plan step must be done or skipped, and every department in the "
        "directory must have been emailed about this new hire or be listed in skipped_departments with a reason.",
        {
            "candidate_id": CANDIDATE,
            "skipped_departments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "reason": {"type": "string"}},
                    "required": ["name", "reason"],
                },
                "description": "Departments that do not need to know about this new hire, and why.",
            },
        },
        ["candidate_id"],
    ),
]

RISKY = {"create_account", "send_email"}


def request_documents(session: Session, company_id: int, candidate, args: dict) -> dict:
    channel = args.get("channel", "email")
    if channel not in ("email", "upload_link"):
        raise HTTPException(400, "channel must be email or upload_link")
    documents = [str(d) for d in args["documents"]]
    documents += [d for d in documents_service.documents_to_return(session, company_id, candidate.job_id) if d not in documents]
    if not documents:
        raise HTTPException(400, "List at least one document")

    reference = candidates_service.reference_code(candidate.id)
    values = {
        "name_en": candidate.full_name_en,
        "name_ar": candidate.full_name_ar,
        "documents": "\n".join(f"- {d}" for d in documents),
        "reference": reference,
    }
    if channel == "upload_link":
        values["link"] = f"{settings.app_base_url}/portal/upload/{create_upload_token(candidate.id, company_id)}"
        body = render("request_documents_link", **values)
    else:
        body = render("request_documents", **values)

    subject = f"Documents needed for your onboarding: {', '.join(documents)} [{reference}]"
    email, sent = notifications_service.send_to_candidate(
        session, company_id, candidate.id, subject, body, args["reason"],
        kind="documents_request", documents=documents,
        files=documents_service.job_files(session, company_id, candidate.job_id),
    )
    if sent:
        due_days = int(args.get("due_in_days") or 3)
        candidates_service.set_documents_due(session, company_id, candidate.id, datetime.now(timezone.utc) + timedelta(days=due_days))
        if candidate.status == "draft":
            candidates_service.set_status(session, company_id, candidate.id, "invited")
    return {"status": "sent" if sent else "already_sent", "channel": channel, "to": email.to_address, "subject": subject}


def request_missing_documents(session: Session, company_id: int, candidate, args: dict) -> dict:
    requested = notifications_service.latest_requested_documents(session, company_id, candidate.id)
    missing = documents_service.still_missing(session, company_id, candidate.id, requested)
    if not requested or not missing:
        raise HTTPException(400, "Nothing is missing: every requested document is valid")

    reference = candidates_service.reference_code(candidate.id)
    rejected = documents_service.rejected_documents(session, company_id, candidate.id)
    problems = "\n".join(f"- {d.filename}: {d.result.get('reason', '')}" for d in rejected)
    link = notifications_service.latest_upload_link(session, company_id, candidate.id)
    body = render(
        "missing_documents",
        name_en=candidate.full_name_en,
        name_ar=candidate.full_name_ar,
        documents="\n".join(f"- {d}" for d in missing),
        problems_en=f"\nThese files could not be accepted:\n{problems}\n" if problems else "",
        problems_ar=f"\nلم نتمكن من قبول هذه الملفات:\n{problems}\n" if problems else "",
        how_en=f"Upload them here: {link}" if link else "Please reply to this email with them attached.",
        how_ar=f"ارفعها من هنا: {link}" if link else "يرجى الرد على هذا البريد مع إرفاقها.",
        reference=reference,
    )
    prefix = "Reminder: " if args.get("reminder") else ""
    subject = f"{prefix}Still needed for your onboarding: {', '.join(missing)} [{reference}]"
    email, sent = notifications_service.send_to_candidate(session, company_id, candidate.id, subject, body, args["reason"])
    return {"status": "sent" if sent else "already_sent", "missing": missing}


def read_inbox(session: Session, company_id: int, candidate, args: dict) -> dict:
    notifications_service.sync_inbox(session, company_id)
    messages = []
    for message in notifications_service.take_unread(session, company_id, candidate.id):
        documents = [
            documents_service.add_candidate_document(
                session, company_id, candidate.id, message.id,
                attachment["filename"], attachment["stored_name"], attachment["content_type"],
            )
            for attachment in message.attachments
        ]
        messages.append({
            "email": f"<untrusted_email>\nFrom: {message.from_address}\nSubject: {message.subject}\n\n{message.body}\n</untrusted_email>",
            "documents": [{"document_id": d.id, "filename": d.filename} for d in documents],
        })
    if messages and candidate.status in ("draft", "invited"):
        candidates_service.set_status(session, company_id, candidate.id, "in_progress")
    return {"messages": messages}


def validate_document(session: Session, company_id: int, candidate, args: dict) -> dict:
    document_id = int(args["document_id"])
    requested = notifications_service.latest_requested_documents(session, company_id, candidate.id)
    result = documents_service.validate(session, company_id, candidate.id, document_id, requested)
    if verifier.ENABLED and not result.get("verified"):
        result = verifier.verify_document(session, company_id, candidate, document_id, requested, result)
    missing = documents_service.still_missing(session, company_id, candidate.id, requested)
    return {"document_id": document_id, **result, "still_missing": missing}


def send_email(session: Session, company_id: int, candidate, args: dict) -> dict:
    to_candidate = args.get("candidate_id") is not None
    to_department = args.get("department_id") is not None
    if to_candidate == to_department:
        raise HTTPException(400, "Give exactly one of candidate_id or department_id")

    subject, body, reason = str(args["subject"]), str(args["body"]), args["reason"]
    if to_department:
        email, sent = notifications_service.send_to_department(
            session, company_id, int(args["department_id"]), subject, body, reason, candidate_id=candidate.id
        )
    else:
        email, sent = notifications_service.send_to_candidate(session, company_id, candidate.id, subject, body, reason)
    return {"status": "sent" if sent else "already_sent", "to": email.to_address}


def create_account(session: Session, company_id: int, candidate, args: dict) -> dict:
    # Enforced here, not in the prompt: no account of any kind until every required document is accepted.
    requested = notifications_service.latest_requested_documents(session, company_id, candidate.id)
    if not requested and documents_service.list_documents(session, company_id, candidate.job_id):
        raise HTTPException(400, "The documents have not been requested yet. Request them and wait until they are accepted.")
    missing = documents_service.still_missing(session, company_id, candidate.id, requested)
    if missing:
        raise HTTPException(400, f"No accounts until every required document is accepted. Still missing or not valid: {', '.join(missing)}.")

    groups = [str(g) for g in args.get("groups", [])]
    account = systems_service.create_account(session, company_id, candidate.id, str(args["system"]), groups)
    return {"system": account.system_key, "address": account.address, "groups": account.groups, "status": account.status}


def create_ticket(session: Session, company_id: int, candidate, args: dict) -> dict:
    ticket = systems_service.create_ticket(session, company_id, candidate.id, str(args["item"]))
    return {"ticket_id": ticket.id, "item": ticket.item, "status": ticket.status}


def escalate(session: Session, company_id: int, candidate, args: dict) -> dict:
    approval = approvals_service.create_approval(session, company_id, candidate.id, "escalation", "", args["reason"])
    return {"approval_id": approval.id, "status": approval.status}


def request_approval(session: Session, company_id: int, candidate, args: dict) -> dict:
    approval = approvals_service.create_approval(
        session, company_id, candidate.id, "approval", str(args["action"]), args["reason"]
    )
    return {"approval_id": approval.id, "status": approval.status}


def complete_steps(session: Session, company_id: int, candidate, args: dict) -> dict:
    plan = plans_service.get_approved_plan(session, company_id, candidate.job_id)
    step_ids = [step["id"] for step in plan.steps]
    outcomes = {}
    for item in args["steps"]:
        step_id, outcome = str(item["step_id"]), str(item.get("outcome", "done"))
        if step_id not in step_ids:
            raise HTTPException(400, f"Unknown step {step_id}. The plan's steps are: {', '.join(step_ids)}")
        if outcome not in ("done", "skipped"):
            raise HTTPException(400, "outcome must be done or skipped")
        outcomes[step_id] = {"outcome": outcome, "reason": args["reason"]}

    finished = set(candidate.step_status) | set(outcomes)
    for number, step_id in enumerate(step_ids, start=1):
        if step_id in outcomes:
            earlier = [i for i in step_ids[: number - 1] if i not in finished]
            if earlier:
                raise HTTPException(400, f"Steps go in number order. Finish {', '.join(earlier)} before {step_id}.")

    if verifier.ENABLED:
        for number, step in enumerate(plan.steps, start=1):
            if step["id"] in outcomes:
                review = verifier.review_step(session, company_id, candidate, number, step, outcomes[step["id"]]["outcome"], args["reason"])
                if not review["approved"]:
                    raise HTTPException(400, f"The verifier says step {number} is not finished: {review['reason']}")

    candidate = candidates_service.set_step_outcomes(session, company_id, candidate.id, outcomes)
    remaining = [step["title"] for step in plan.steps if step["id"] not in candidate.step_status]
    return {"done": len(plan.steps) - len(remaining), "total": len(plan.steps), "remaining": remaining}


def mark_completed(session: Session, company_id: int, candidate, args: dict) -> dict:
    plan = plans_service.find_approved_plan(session, company_id, candidate.job_id)
    unfinished = [step["title"] for step in (plan.steps if plan else []) if step["id"] not in candidate.step_status]
    if unfinished:
        raise HTTPException(400, f"Finish or skip these plan steps first, with complete_steps: {', '.join(unfinished)}")

    skipped = {str(d["name"]).strip().lower(): str(d.get("reason", "")).strip() for d in args.get("skipped_departments") or []}
    if not all(skipped.values()):
        raise HTTPException(400, "Give a reason for every skipped department")
    told = notifications_service.departments_told(session, company_id, candidate.id)
    it_ticket = bool(systems_service.list_candidate_tickets(session, company_id, candidate.id))  # a ticket to the IT desk tells IT
    untold = [
        d.name for d in departments_service.list_departments(session, company_id)
        if d.id not in told and d.name.lower() not in skipped and not (it_ticket and d.name == "IT")
    ]
    if untold:
        raise HTTPException(
            400,
            f"These departments were not told about this new hire: {', '.join(untold)}. Email the ones that "
            "should know, and list the others in skipped_departments with a reason.",
        )

    candidates_service.set_status(session, company_id, candidate.id, "completed")
    return {"status": "completed"}


TOOLS = {
    "request_documents": (request_documents, "Requested documents"),
    "request_missing_documents": (request_missing_documents, "Asked for missing documents"),
    "read_inbox": (read_inbox, "Read the inbox"),
    "validate_document": (validate_document, "Checked a document"),
    "send_email": (send_email, "Sent an email"),
    "create_account": (create_account, "Created an account"),
    "create_ticket": (create_ticket, "Opened an IT ticket"),
    "escalate": (escalate, "Escalated to HR"),
    "request_approval": (request_approval, "Asked HR for approval"),
    "complete_steps": (complete_steps, "Updated the plan steps"),
    "mark_completed": (mark_completed, "Marked onboarding as completed"),
}


def describe(session: Session, company_id: int, name: str, args: dict) -> str:
    """A short sentence HR can read, e.g. "Create a github account (groups: backend-team)"."""
    if name == "create_account":
        groups = ", ".join(str(g) for g in args.get("groups") or []) or "no groups"
        return f"Create a {args.get('system')} account ({groups})"
    if name == "send_email":
        recipient = "the candidate"
        if args.get("department_id") is not None:
            try:
                recipient = departments_service.get_department(session, company_id, int(args["department_id"])).name
            except (HTTPException, ValueError):
                recipient = f"department {args['department_id']}"
        return f"Email {recipient}: {args.get('subject', '')}"
    return name


def _gate(session: Session, company_id: int, candidate, name: str, args: dict) -> dict | None:
    """Checks a risky action before it runs. Returns a result to stop it, or None to let it run."""
    mode = jobs_service.get_job(session, company_id, candidate.job_id).start_mode
    action = describe(session, company_id, name, args)

    if mode == "ask_first":
        decided = approvals_service.find_decided(session, company_id, candidate.id, action)
        if decided and decided.status == "approved":
            return None
        if decided:
            return {"error": f"HR declined this: {decided.decision_note or 'no reason given'}. Do not try it again."}
        approval = approvals_service.create_approval(
            session, company_id, candidate.id, "approval", action, str(args.get("reason", "")),
            payload={"tool": name, "args": args},
        )
        return {"status": "waiting_for_hr", "approval_id": approval.id, "message": "HR must approve this first. Stop and wait."}

    if verifier.ENABLED:
        review = verifier.review_action(session, company_id, candidate, name, args)
        if not review["approved"]:
            return {"error": f"The verifier did not approve this: {review['reason']}"}
    return None


def _call(tool, session: Session, company_id: int, candidate, args: dict) -> dict:
    try:
        return tool(session, company_id, candidate, args)
    except HTTPException as error:
        return {"error": error.detail}
    except (KeyError, TypeError, ValueError) as error:
        return {"error": f"Bad arguments: {error}"}


def execute(session: Session, company_id: int, candidate, name: str, args, approved_by_hr: bool = False) -> dict:
    """Run one tool call. Problems come back as {"error": ...} so the agent can react to them.

    Risky actions first go through the start mode (ask HR, or notify HR) and the verifier.
    approved_by_hr runs an action HR already approved, without asking again."""
    args = args if isinstance(args, dict) else {}
    tool, title = TOOLS.get(name, (None, name))

    if tool is None:
        result = {"error": f"Unknown tool: {name}"}
    elif args.get("candidate_id") not in (None, candidate.id):
        result = {"error": f"This run is about candidate {candidate.id} only"}
    else:
        stopped = _gate(session, company_id, candidate, name, args) if name in RISKY and not approved_by_hr else None
        result = stopped or _call(tool, session, company_id, candidate, args)
        if stopped and stopped.get("status") == "waiting_for_hr":
            title = f"Asked HR to approve: {describe(session, company_id, name, args)}"
        elif name in RISKY and not stopped and not approved_by_hr and "error" not in result:
            if jobs_service.get_job(session, company_id, candidate.job_id).start_mode == "notify":
                approvals_service.create_notice(
                    session, company_id, candidate.id, describe(session, company_id, name, args), str(args.get("reason", ""))
                )

    reason = str(args.get("reason", ""))
    session.add(ActionLog(company_id=company_id, candidate_id=candidate.id, tool=name, input=args, output=result, reason=reason))
    log_event(session, company_id, candidate.id, "agent", title if "error" not in result else f"{title} (failed)", reason)
    session.commit()
    return result
