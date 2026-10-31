from fastapi import APIRouter, Depends, Form, Response, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.features.auth.service import get_current_user
from app.features.documents import service, storage
from app.features.candidates import service as candidates_service
from app.features.documents.schema import CandidateDocumentRead, DocumentInstructions, DocumentRead

router = APIRouter(tags=["documents"])


@router.post("/jobs/{job_id}/documents", response_model=DocumentRead, status_code=201)
def upload_document(
    job_id: int,
    file: UploadFile,
    instructions: str = Form(""),
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return service.add_document(
        session, user.company_id, job_id, file.filename or "document", file.content_type or "", file.file.read(), instructions
    )


@router.put("/documents/{document_id}", response_model=DocumentRead)
def set_instructions(
    document_id: int, data: DocumentInstructions, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    return service.set_instructions(session, user.company_id, document_id, data.instructions)


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


@router.get("/candidates/{candidate_id}/documents", response_model=list[CandidateDocumentRead])
def list_candidate_documents(
    candidate_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    candidates_service.get_candidate(session, user.company_id, candidate_id)
    return [
        {**d.model_dump(), "reason": str(d.result.get("reason", ""))}
        for d in service.list_candidate_documents(session, user.company_id, candidate_id)
    ]


@router.get("/candidate-documents/{document_id}/download")
def download_candidate_document(
    document_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)
):
    document = service.get_candidate_document(session, user.company_id, document_id)
    return FileResponse(storage.file_path(document.stored_name), filename=document.filename)
