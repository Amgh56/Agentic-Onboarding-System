"""The evaluation cases. Each one states what must happen (and what must not) BEFORE the agent runs.

Four are for development. The fifth, in a second company with a different procedure, is held out:
it only runs with --final so it cannot be tuned against.

The three "demo" cases (Yousef, Abdulaziz, Omar) are a separate group: they play the demo applicants through
scripts/send_reply.py and only run when named, e.g. --cases demo_yousef demo_abdulaziz demo_omar.
"""

from dataclasses import dataclass, field
from typing import Callable

from eval.world import World
from scripts import seed_demo


@dataclass
class Check:
    label: str
    test: Callable[[World], bool]
    forbidden: bool = False  # for a forbidden check, test() is True when the agent did the wrong thing


@dataclass
class Case:
    name: str
    split: str  # "dev" or "held_out"
    company: dict
    job: dict
    candidate: dict
    checks: list[Check]
    script: list = field(default_factory=list)  # [("reply", round) | ("checkpoint", None) | ("hr", note)], played in order
    reply: dict | None = None  # what the candidate sends back: {"via": "inbox" | "link", "filename", "text"}
    deadline_checks: list[int] = field(default_factory=list)  # days after Start, e.g. [4, 8]
    expects_escalation: bool = False


def national_id(name: str, expiry: str) -> str:
    return f"""KINGDOM OF SAUDI ARABIA - NATIONAL ID CARD
Name: {name}
ID number: 1098765432
Date of birth: 1992-03-14
Expiry date: {expiry}"""


def iqama(name: str, expiry: str) -> str:
    return f"""KINGDOM OF SAUDI ARABIA - RESIDENCY PERMIT (IQAMA)
Name: {name}
Iqama number: 2345678901
Expiry date: {expiry}"""


BARQ = {
    "name": "Barq Logistics",
    "procedure": """Ask each new hire for their national ID. It must be valid, not expired, and the name must match.
Only after the ID is valid, create their work email, then the other accounts for their role:
- Business roles (accountants, finance, procurement, operations) get an ERP account.
- Developers get a GitHub invite and a laptop request through the IT desk.
Tell Payroll that the person is joining (name and job title only, no equipment details).
Only developers involve the IT department, because they need a laptop.
Finish with a welcome email to the candidate that lists the new work email and accounts.""",
}

GULF = {
    "name": "Gulf Pharma",
    "procedure": """Ask each new hire for their Iqama (residency permit). Do not ask for a national ID.
They must upload it through their personal upload link, not as an email attachment.
When the Iqama is valid, create their work email, then the accounts for their role:
- Pharmacists get a Teams account in the operations group.
For any other role, do not guess. Escalate to HR and wait.""",
}

ACCOUNTANT = {"title": "Accountant", "description": "Keeps the books and pays suppliers."}
DEVELOPER = {"title": "Backend Developer", "description": "Builds and runs our Python APIs."}

FAISAL = {"name_en": "Faisal Al-Otaibi", "name_ar": "فيصل العتيبي", "email": "faisal@personal.example", "role": "Accountant"}
OMAR = {"name_en": "Omar Abdullah", "name_ar": "عمر عبدالله", "email": "omar@personal.example", "role": "Backend developer"}
SARA = {"name_en": "Sara Mohammed", "name_ar": "سارة محمد", "email": "sara@personal.example", "role": "Accountant"}
AHMED = {"name_en": "Ahmed Hassan", "name_ar": "أحمد حسن", "email": "ahmed@personal.example", "role": "Chief Wizard"}


def welcome_lists_the_work_email(w: World) -> bool:
    address = w.account_address("work_email")
    return bool(address) and any(address in e["body"] for e in w.emails_to_candidate())


CASES = [
    Case(
        name="business_valid",
        split="dev",
        company=BARQ,
        job=ACCOUNTANT,
        candidate=FAISAL,
        reply={"via": "inbox", "filename": "national_id.txt", "text": national_id("Faisal Al-Otaibi", "2031-05-01")},
        checks=[
            Check("work email created", lambda w: w.has_account("work_email")),
            Check("ERP account created", lambda w: w.has_account("erp")),
            Check("welcome email lists the new work email", welcome_lists_the_work_email),
            Check("payroll was told", lambda w: bool(w.emails_to("Payroll"))),
            Check("onboarding completed", lambda w: w.candidate_status == "completed"),
            Check("GitHub account for a business role", lambda w: w.has_account("github"), forbidden=True),
            Check("IT ticket for a business role", lambda w: bool(w.tickets), forbidden=True),
            Check("IT department was emailed", lambda w: bool(w.emails_to("IT")), forbidden=True),
        ],
    ),
    Case(
        name="developer_valid",
        split="dev",
        company=BARQ,
        job=DEVELOPER,
        candidate=OMAR,
        reply={"via": "inbox", "filename": "national_id.txt", "text": national_id("Omar Abdullah", "2031-05-01")},
        checks=[
            Check("work email created", lambda w: w.has_account("work_email")),
            Check("GitHub invite sent", lambda w: (w.account("github") or {}).get("status") == "invited"),
            Check("laptop ticket opened", lambda w: any("laptop" in t.lower() for t in w.tickets)),
            Check("IT department was emailed", lambda w: bool(w.emails_to("IT"))),
            Check("welcome email lists the new work email", welcome_lists_the_work_email),
            Check("onboarding completed", lambda w: w.candidate_status == "completed"),
            Check("ERP account for a developer", lambda w: w.has_account("erp"), forbidden=True),
            Check(
                "equipment details sent to payroll",
                lambda w: any("laptop" in e["body"].lower() for e in w.emails_to("Payroll")),
                forbidden=True,
            ),
        ],
    ),
    Case(
        name="expired_document",
        split="dev",
        company=BARQ,
        job=ACCOUNTANT,
        candidate=SARA,
        reply={"via": "inbox", "filename": "national_id.txt", "text": national_id("Sara Mohammed", "2021-03-01")},
        checks=[
            Check("document rejected", lambda w: "rejected" in w.documents),
            Check(
                "candidate told it is expired",
                lambda w: any("expir" in (e["subject"] + e["body"]).lower() for e in w.emails_to_candidate()[1:]),
            ),
            Check("any account created", lambda w: bool(w.accounts), forbidden=True),
            Check("onboarding completed", lambda w: w.candidate_status == "completed", forbidden=True),
            Check("IT ticket opened", lambda w: bool(w.tickets), forbidden=True),
        ],
    ),
    Case(
        name="missing_past_deadline",
        split="dev",
        company=BARQ,
        job=DEVELOPER,
        candidate=OMAR,
        deadline_checks=[4, 8],
        expects_escalation=True,
        checks=[
            Check("reminder sent to the candidate", lambda w: len(w.emails_to_candidate()) >= 2),
            Check("escalated to HR", lambda w: w.escalated),
            Check("any account created", lambda w: bool(w.accounts), forbidden=True),
            Check("onboarding completed", lambda w: w.candidate_status == "completed", forbidden=True),
        ],
    ),
    Case(
        name="unknown_role_second_company",
        split="held_out",
        company=GULF,
        job={"title": "Wizard", "description": "A role this company has no rules for."},
        candidate=AHMED,
        reply={"via": "link", "filename": "iqama.txt", "text": iqama("Ahmed Hassan", "2030-09-15")},
        expects_escalation=True,
        checks=[
            Check(
                "asked for the Iqama, as this company's procedure says",
                lambda w: any("iqama" in (e["subject"] + e["body"]).lower() for e in w.emails_to_candidate()),
            ),
            Check(
                "used the upload link, as this company's procedure says",
                lambda w: any("/portal/upload/" in e["body"] for e in w.emails_to_candidate()),
            ),
            Check("escalated the unknown role to HR", lambda w: w.escalated),
            Check(
                "guessed accounts for an unknown role",
                lambda w: any(w.has_account(s) for s in ("erp", "github", "slack", "teams")),
                forbidden=True,
            ),
        ],
    ),
]

# ---------- the three demo cases: the real procedure, the real blank documents, and the applicants' signed PDFs

DEMO = {"name": "Demo Co", "procedure": seed_demo.PROCEDURE, "documents": seed_demo.DOCUMENTS}
DEMO_JOB = {"title": "Nov 2026 cohort", "description": ""}


def demo_applicant(first_name: str) -> dict:
    found = next(a for a in seed_demo.APPLICANTS if a["full_name_en"].startswith(first_name))
    return {"name_en": found["full_name_en"], "name_ar": found["full_name_ar"], "email": found["email"], "role": found["role"]}


def mentions(w: World, *words: str) -> bool:
    return any(all(word in e["body"].lower() for word in words) for e in w.emails_to_candidate()[1:])


def laptop(kind: str):
    return lambda w: any(kind in t.lower() and "laptop" in t.lower() for t in w.tickets)


def all_steps_done(w: World) -> bool:
    return w.steps_total > 0 and w.steps_done == w.steps_total


def role_accounts(*systems: str) -> list[Check]:
    return [Check(f"{system} account created", lambda w, s=system: w.has_account(s)) for system in systems]


ROLE_SYSTEMS = ("erp", "github", "slack", "teams")

DEMO_CASES = [
    Case(
        name="demo_yousef",
        split="demo",
        company=DEMO,
        job=DEMO_JOB,
        candidate=demo_applicant("Yousef"),
        script=[("reply", None)],
        checks=[
            Check("all steps done", all_steps_done),
            Check("onboarding completed", lambda w: w.candidate_status == "completed"),
            *role_accounts("work_email", "slack", "teams"),
            Check("GitHub invite sent", lambda w: w.has_account("github")),
            Check("developer laptop requested", laptop("developer")),
            Check("ERP account for a developer", lambda w: w.has_account("erp"), forbidden=True),
            Check("standard laptop for a developer", laptop("standard"), forbidden=True),
            Check("Finance was told", lambda w: bool(w.emails_to("Finance")), forbidden=True),
        ],
    ),
    Case(
        name="demo_abdulaziz",
        split="demo",
        company=DEMO,
        job=DEMO_JOB,
        candidate=demo_applicant("Abdulaziz"),
        script=[("reply", None), ("checkpoint", None), ("hr", "treat him as a business role")],
        expects_escalation=True,
        checks=[
            Check("documents accepted", lambda w: w.checkpoint.documents.count("valid") >= 3),
            Check("work email created", lambda w: w.checkpoint.has_account("work_email")),
            Check("escalated to HR", lambda w: w.checkpoint.escalated),
            Check(
                "a role account before HR answered",
                lambda w: any(w.checkpoint.has_account(s) for s in ROLE_SYSTEMS),
                forbidden=True,
            ),
            *role_accounts("erp", "slack", "teams"),
            Check("standard laptop requested", laptop("standard")),
            Check("onboarding completed", lambda w: w.candidate_status == "completed"),
            Check("GitHub account for a business role", lambda w: w.has_account("github"), forbidden=True),
        ],
    ),
    Case(
        name="demo_omar",
        split="demo",
        company=DEMO,
        job=DEMO_JOB,
        candidate=demo_applicant("Omar"),
        script=[("reply", 1), ("checkpoint", None), ("reply", 2)],
        checks=[
            Check("exactly one chase email", lambda w: len(w.checkpoint.emails_to_candidate()) == 2),
            Check("it says the policy is missing", lambda w: mentions(w.checkpoint, "policy")),
            Check("it says the NDA is unsigned", lambda w: mentions(w.checkpoint, "sign") and (mentions(w.checkpoint, "nda") or mentions(w.checkpoint, "non-disclosure"))),
            Check("it says the contract is in a different name", lambda w: mentions(w.checkpoint, "contract", "name")),
            Check("an account before the documents were fixed", lambda w: bool(w.checkpoint.accounts), forbidden=True),
            *role_accounts("erp", "slack", "teams"),
            Check("standard laptop requested", laptop("standard")),
            Check("onboarding completed", lambda w: w.candidate_status == "completed"),
            Check("GitHub account for a business role", lambda w: w.has_account("github"), forbidden=True),
        ],
    ),
]

ALL = CASES + DEMO_CASES
