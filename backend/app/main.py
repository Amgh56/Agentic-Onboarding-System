from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.database import engine
from app.features.agent.controller import router as agent_router
from app.features.approvals.controller import router as approvals_router
from app.features.auth.controller import router as auth_router
from app.features.candidates.controller import router as candidates_router
from app.features.companies.controller import router as companies_router
from app.features.departments.controller import router as departments_router
from app.features.documents.controller import router as documents_router
from app.features.jobs.controller import router as jobs_router
from app.features.notifications.controller import router as notifications_router
from app.features.plans.controller import router as plans_router
from app.features.portal.controller import router as portal_router
from app.features.systems.controller import candidate_router as systems_candidate_router
from app.features.systems.controller import router as systems_router


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
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(documents_router)
app.include_router(departments_router)
app.include_router(systems_router)
app.include_router(systems_candidate_router)
app.include_router(plans_router)
app.include_router(notifications_router)
app.include_router(approvals_router)
app.include_router(agent_router)
app.include_router(portal_router)
