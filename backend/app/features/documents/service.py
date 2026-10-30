from fastapi import HTTPException
from sqlmodel import Session, select

from app.features.documents import storage
from app.features.documents.model import Document
from app.features.jobs import service as jobs_service


def add_document(
    session: Session, company_id: int, job_id: int, filename: str, content_type: str, data: bytes
) -> Document:
    job = jobs_service.get_job(session, company_id, job_id)
    document = Document(
        company_id=company_id,
        job_id=job.id,
        filename=filename,
        stored_name=storage.save_file(filename, data),
        content_type=content_type,
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
