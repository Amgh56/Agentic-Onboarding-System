from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.database import engine
from app.features.auth.controller import router as auth_router
from app.features.candidates.controller import router as candidates_router
from app.features.companies.controller import router as companies_router
from app.features.documents.controller import router as documents_router
from app.features.jobs.controller import router as jobs_router
from app.features.templates.controller import router as templates_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Onboarding", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(templates_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(documents_router)
