from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import HealthStatus
from app.routers.chat import router as chat_router

app = FastAPI(
    title="Cadre AI Chatbot API",
    description=(
        "Backend for the Cadre AI support chatbot. Answers questions from a "
        "curated knowledge file and escalates to a human when it doesn't "
        "know something -- see POST /api/chat."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get(
    "/api/health",
    summary="Health check",
    description="Used to verify the deployment is up and reachable.",
)
def health_check() -> HealthStatus:
    return HealthStatus(status="ok")
