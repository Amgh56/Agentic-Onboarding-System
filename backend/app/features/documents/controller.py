from fastapi import APIRouter, Depends, Response, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.documents import service, storage
from app.features.documents.schema import DocumentRead

router = APIRouter(tags=["documents"])


@router.post("/jobs/{job_id}/documents", response_model=DocumentRead, status_code=201)
def upload_document(
    job_id: int,
    file: UploadFile,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.add_document(
        session, user.company_id, job_id, file.filename or "document", file.content_type or "", file.file.read()
    )


@router.get("/jobs/{job_id}/documents", response_model=list[DocumentRead])
def list_documents(
    job_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.list_documents(session, user.company_id, job_id)


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    document = service.get_document(session, user.company_id, document_id)
    return FileResponse(storage.file_path(document.stored_name), filename=document.filename)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    service.delete_document(session, user.company_id, document_id)
    return Response(status_code=204)
