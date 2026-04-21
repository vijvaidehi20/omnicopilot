"""
OmniCopilot — FastAPI entry point.
"""
import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from auth.router import router as auth_router
from auth.google_oauth import router as google_auth_router
from routes.chat import router as chat_router


from services.reminder_service import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup and manage background jobs."""
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="OmniCopilot API",
    description="Phase 1 — Auth, Chat, Gemini, and Tool System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(google_auth_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "OmniCopilot API is running", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
