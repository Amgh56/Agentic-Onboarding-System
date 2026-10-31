from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.candidates import service as candidates_service
from app.features.documents import storage, validation
from app.features.documents.model import CandidateDocument, Document
from app.features.jobs import service as jobs_service


def add_document(
    session: Session, company_id: int, job_id: int, filename: str, content_type: str, data: bytes,
    instructions: str = "",
) -> Document:
    job = jobs_service.get_job(session, company_id, job_id)
    document = Document(
        company_id=company_id,
        job_id=job.id,
        filename=filename,
        stored_name=storage.save_file(filename, data),
        content_type=content_type,
        instructions=instructions.strip(),
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def list_documents(session: Session, company_id: int, job_id: int) -> list[Document]:
    jobs_service.get_job(session, company_id, job_id)
    query = select(Document).where(Document.company_id == company_id, Document.job_id == job_id)
    return session.exec(query.order_by(Document.id)).all()


def get_document(session: Session, company_id: int, document_id: int) -> Document:
    document = session.get(Document, document_id)
    if not document or document.company_id != company_id:
        raise HTTPException(404, "Document not found")
    return document


def delete_document(session: Session, company_id: int, document_id: int) -> None:
    document = get_document(session, company_id, document_id)
    storage.delete_file(document.stored_name)
    session.delete(document)
    session.commit()


def save_upload(filename: str, data: bytes) -> str:
    return storage.save_file(filename, data)


def add_candidate_document(
    session: Session, company_id: int, candidate_id: int, message_id: int,
    filename: str, stored_name: str, content_type: str,
) -> CandidateDocument:
    query = select(CandidateDocument).where(
        CandidateDocument.company_id == company_id, CandidateDocument.stored_name == stored_name
    )
    existing = session.exec(query).first()
    if existing:
        return existing

    document = CandidateDocument(
        company_id=company_id, candidate_id=candidate_id, message_id=message_id,
        filename=filename, stored_name=stored_name, content_type=content_type,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def list_candidate_documents(session: Session, company_id: int, candidate_id: int) -> list[CandidateDocument]:
    query = select(CandidateDocument).where(
        CandidateDocument.company_id == company_id, CandidateDocument.candidate_id == candidate_id
    )
    return session.exec(query.order_by(CandidateDocument.id)).all()


def validate(
    session: Session, company_id: int, candidate_id: int, document_id: int, requested: list[str]
) -> dict:
    """Check a received document once. Later calls return the stored result."""
    document = _candidate_document(session, company_id, candidate_id, document_id)
    if document.status == "received":
        result = _read(session, company_id, document, requested, second=False)
        return save_result(session, company_id, document.id, "valid" if result["valid"] else "rejected", result)
    return {"status": document.status, **document.result}


def recheck(session: Session, company_id: int, candidate_id: int, document_id: int, requested: list[str]) -> dict:
    """Read the document again, even if it was checked before."""
    document = _candidate_document(session, company_id, candidate_id, document_id)
    result = _read(session, company_id, document, requested, second=False)
    return save_result(session, company_id, document.id, "valid" if result["valid"] else "rejected", result)


def second_opinion(session: Session, company_id: int, candidate_id: int, document_id: int, requested: list[str]) -> dict:
    """The verifier's independent reading. Not stored on its own."""
    document = _candidate_document(session, company_id, candidate_id, document_id)
    return _read(session, company_id, document, requested, second=True)


def save_result(session: Session, company_id: int, document_id: int, status: str, result: dict) -> dict:
    document = get_candidate_document(session, company_id, document_id)
    document.status = status
    document.result = {**document.result, **{k: v for k, v in result.items() if k != "status"}}
    session.add(document)
    session.commit()
    session.refresh(document)
    return {"status": document.status, **document.result}


def get_candidate_document(session: Session, company_id: int, document_id: int) -> CandidateDocument:
    document = session.get(CandidateDocument, document_id)
    if not document or document.company_id != company_id:
        raise HTTPException(404, "Document not found")
    return document


def _candidate_document(session: Session, company_id: int, candidate_id: int, document_id: int) -> CandidateDocument:
    document = get_candidate_document(session, company_id, document_id)
    if document.candidate_id != candidate_id:
        raise HTTPException(404, "Document not found")
    return document


def _read(session: Session, company_id: int, document: CandidateDocument, requested: list[str], second: bool) -> dict:
    candidate = candidates_service.get_candidate(session, company_id, document.candidate_id)
    job = jobs_service.get_job(session, company_id, candidate.job_id)
    data = storage.file_path(document.stored_name).read_bytes()
    return validation.check(
        candidate.full_name_en, candidate.full_name_ar, requested, document.filename, document.content_type, data, second,
        procedure=job.procedure,
    )


def still_missing(session: Session, company_id: int, candidate_id: int, requested: list[str]) -> list[str]:
    """Requested documents that no valid document covers yet.

    A document covers a request when either name contains the other, so a "National ID" covers
    a request for "National ID or Iqama"."""
    received = [
        str(d.result.get("matches") or "").strip().lower()
        for d in list_candidate_documents(session, company_id, candidate_id)
        if d.status == "valid"
    ]
    return [
        name for name in requested
        if not any(match and (match in name.lower() or name.strip().lower() in match) for match in received)
    ]


def job_files(session: Session, company_id: int, job_id: int) -> list[tuple[str, bytes]]:
    """The job's documents as (filename, bytes), to attach to an email."""
    return [(d.filename, storage.file_path(d.stored_name).read_bytes()) for d in list_documents(session, company_id, job_id)]


def set_instructions(session: Session, company_id: int, document_id: int, instructions: str) -> Document:
    document = get_document(session, company_id, document_id)
    document.instructions = instructions.strip()
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def documents_to_return(session: Session, company_id: int, job_id: int) -> list[str]:
    """The job's files the candidate must complete and send back, e.g. "contract.pdf (Sign each page)"."""
    return [f"{d.filename} ({d.instructions})" for d in list_documents(session, company_id, job_id) if d.instructions]


def rejected_documents(session: Session, company_id: int, candidate_id: int) -> list[CandidateDocument]:
    return [d for d in list_candidate_documents(session, company_id, candidate_id) if d.status == "rejected"]
