import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from utils.db import db_manager
from api.documents import router as documents_router
from api.chat import router as chat_router
from api.notes import router as notes_router
from api.quiz import router as quiz_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("study_hub.main")

app = FastAPI(
    title="Study Hub API",
    description="A simplified RAG-like microservice for documents QA, notes, and quiz generation.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log database status at startup
@app.on_event("startup")
async def startup_event():
    logger.info(f"Study Hub application starting up...")
    logger.info(f"Database active mode: {db_manager.mode.upper()}")
    
    # Check Gemini config status
    if settings.GEMINI_API_KEY:
        logger.info("Gemini API key is configured.")
    else:
        logger.warning("Gemini API key is MISSING!")

# Mount API Routers
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(notes_router)
app.include_router(quiz_router)

@app.get("/health")
async def health_check():
    gemini_status = "configured" if settings.GEMINI_API_KEY else "missing"
    return {
        "status": "ok",
        "mongodb": db_manager.mode,
        "gemini": gemini_status
    }
