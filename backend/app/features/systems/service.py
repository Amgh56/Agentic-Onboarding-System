from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.candidates import service as candidates_service
from app.features.systems import fake
from app.features.systems.model import Account, CompanySystem, SystemGroup, Ticket
from app.features.systems.schema import SystemContents, SystemRead

# Every company starts with these. They are data, so a company can differ from this list.
DEFAULT_SYSTEMS = [
    ("work_email", "Work email", "البريد الوظيفي", "mailbox", "The employee's company mailbox. Always created first.", []),
    ("erp", "ERP", "نظام ERP", "account", "Finance, purchasing and operations.", [
        ("accountant", "Books, invoices and payments"),
        ("procurement", "Purchase orders and suppliers"),
        ("operations", "Stock and logistics"),
    ]),
    ("github", "GitHub", "جيت هاب", "invite", "Source code. The candidate is invited to the organisation.", [
        ("backend-team", "Backend repositories"),
        ("frontend-team", "Frontend repositories"),
    ]),
    ("slack", "Slack", "سلاك", "invite", "Team chat. The candidate is invited to channels.", [
        ("#general", "Company announcements"),
        ("#engineering", "Engineering team"),
        ("#sales", "Sales team"),
    ]),
    ("teams", "Microsoft Teams", "مايكروسوفت تيمز", "account", "Meetings and department channels.", [
        ("finance", "Finance department"),
        ("people", "HR department"),
        ("operations", "Operations department"),
    ]),
    ("it_desk", "IT desk", "مكتب الدعم التقني", "tickets", "Requests for equipment and access.", []),
]


def seed_defaults(session: Session, company_id: int, company_name: str) -> str:
    """Add the default systems. Returns the company's domain, e.g. barq.example."""
    for key, name, name_ar, kind, description, groups in DEFAULT_SYSTEMS:
        config = {"domain": fake.company_domain(company_name, company_id)} if kind == "mailbox" else {}
        session.add(
            CompanySystem(
                company_id=company_id, key=key, name=name, name_ar=name_ar,
                kind=kind, description=description, config=config,
            )
        )
        for group_name, group_description in groups:
            session.add(
                SystemGroup(
                    company_id=company_id, system_key=key, name=group_name, description=group_description
                )
            )
    session.commit()
    return fake.company_domain(company_name, company_id)


def get_system(session: Session, company_id: int, key: str) -> CompanySystem:
    query = select(CompanySystem).where(CompanySystem.company_id == company_id, CompanySystem.key == key)
    system = session.exec(query).first()
    if not system:
        raise HTTPException(404, f"Unknown system: {key}")
    return system


def list_groups(session: Session, company_id: int, key: str) -> list[SystemGroup]:
    query = select(SystemGroup).where(SystemGroup.company_id == company_id, SystemGroup.system_key == key)
    return session.exec(query.order_by(SystemGroup.id)).all()


def list_systems(session: Session, company_id: int) -> list[SystemRead]:
    systems = session.exec(
        select(CompanySystem).where(CompanySystem.company_id == company_id).order_by(CompanySystem.id)
    ).all()
    return [
        SystemRead(**system.model_dump(), groups=list_groups(session, company_id, system.key))
        for system in systems
    ]


def _find_account(session: Session, candidate_id: int, key: str) -> Account | None:
    query = select(Account).where(Account.candidate_id == candidate_id, Account.system_key == key)
    return session.exec(query).first()


def create_account(
    session: Session, company_id: int, candidate_id: int, key: str, groups: list[str]
) -> Account:
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    system = get_system(session, company_id, key)

    existing = _find_account(session, candidate_id, key)
    if existing:
        return existing

    if system.kind == "tickets":
        raise HTTPException(400, f"{system.name} takes tickets, not accounts")
    catalog = {group.name for group in list_groups(session, company_id, key)}
    for group in groups:
        if group not in catalog:
            raise HTTPException(400, f"{system.name} has no group called {group}")

    if system.kind == "mailbox":
        taken = {a.address for a in session.exec(select(Account).where(Account.company_id == company_id, Account.system_key == key))}
        address = fake.work_email_address(candidate.full_name_en, system.config["domain"], taken)
    else:
        work_email = _find_account(session, candidate_id, "work_email")
        if not work_email:
            raise HTTPException(400, "Create the work email first")
        address = work_email.address

    account = Account(
        company_id=company_id,
        candidate_id=candidate_id,
        system_key=key,
        display_name=candidate.full_name_en,
        address=address,
        groups=groups,
        status="invited" if system.kind == "invite" else "created",
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def create_ticket(session: Session, company_id: int, candidate_id: int, item: str) -> Ticket:
    candidate = candidates_service.get_candidate(session, company_id, candidate_id)
    query = select(CompanySystem).where(CompanySystem.company_id == company_id, CompanySystem.kind == "tickets")
    desk = session.exec(query).first()
    if not desk:
        raise HTTPException(404, "This company has no ticket system")

    query = select(Ticket).where(Ticket.candidate_id == candidate_id, Ticket.item == item)
    existing = session.exec(query).first()
    if existing:
        return existing

    ticket = Ticket(
        company_id=company_id, candidate_id=candidate_id, system_key=desk.key,
        requester=candidate.full_name_en, item=item,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def list_contents(session: Session, company_id: int) -> list[SystemContents]:
    accounts = session.exec(select(Account).where(Account.company_id == company_id).order_by(Account.id)).all()
    tickets = session.exec(select(Ticket).where(Ticket.company_id == company_id).order_by(Ticket.id)).all()
    systems = session.exec(
        select(CompanySystem).where(CompanySystem.company_id == company_id).order_by(CompanySystem.id)
    ).all()
    return [
        SystemContents(
            key=system.key, name=system.name, name_ar=system.name_ar, kind=system.kind,
            accounts=[a for a in accounts if a.system_key == system.key],
            tickets=[t for t in tickets if t.system_key == system.key],
        )
        for system in systems
    ]


def list_candidate_accounts(session: Session, company_id: int, candidate_id: int) -> list[Account]:
    query = select(Account).where(Account.company_id == company_id, Account.candidate_id == candidate_id)
    return session.exec(query.order_by(Account.id)).all()


def list_candidate_tickets(session: Session, company_id: int, candidate_id: int) -> list[Ticket]:
    query = select(Ticket).where(Ticket.company_id == company_id, Ticket.candidate_id == candidate_id)
    return session.exec(query.order_by(Ticket.id)).all()
