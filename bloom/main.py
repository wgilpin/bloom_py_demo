"""FastAPI application entry point for Bloom GCSE Mathematics Tutor.

This module initializes the FastAPI app, configures middleware, and loads
environment variables for LLM providers and application settings.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from bloom.database import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bloom")

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# Environment Variable Loading
# ============================================================================

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, google, xai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Model selection (provider-specific)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Application settings
DATABASE_PATH = os.getenv("DATABASE_PATH", "bloom.db")
COMPLETION_THRESHOLD = int(os.getenv("COMPLETION_THRESHOLD", "3"))  # Correct answers for subtopic completion

# Validate API key for selected provider
def validate_api_keys():
    """Ensure the API key for the selected provider is set."""
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable required when LLM_PROVIDER=openai")
    elif LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable required when LLM_PROVIDER=anthropic")
    elif LLM_PROVIDER == "google" and not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable required when LLM_PROVIDER=google")
    elif LLM_PROVIDER == "xai" and not XAI_API_KEY:
        raise ValueError("XAI_API_KEY environment variable required when LLM_PROVIDER=xai")


# ============================================================================
# Lifespan Event Handler
# ============================================================================

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting Bloom GCSE Mathematics Tutor...")
    
    # Validate API keys
    try:
        validate_api_keys()
        logger.info("✓ Using LLM provider: %s (model: %s)", LLM_PROVIDER, LLM_MODEL)
    except ValueError as e:
        logger.warning("⚠️  %s", e)
        logger.warning("   Set the appropriate API key environment variable before using the app.")
    
    # Initialize database
    init_database(DATABASE_PATH)
    logger.info("✓ Database initialized: %s", DATABASE_PATH)
    logger.info("✓ Completion threshold: %s correct answers", COMPLETION_THRESHOLD)
    logger.info("✓ Ready to serve requests at http://localhost:8000")
    logger.info("   Note: Run 'uv run python -m bloom.load_syllabus' to load sample data if needed")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Bloom...")


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Bloom GCSE Mathematics Tutor",
    description="AI-powered tutoring system for UK GCSE mathematics",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow all origins for local demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS, JS, images)
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Templates configuration (Jinja2)
templates_path = Path(__file__).parent / "templates"
templates_path.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint - returns API status."""
    return {
        "status": "healthy",
        "app": "Bloom GCSE Mathematics Tutor",
        "version": "0.1.0",
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL,
    }


# ============================================================================
# Route Registration (imported after app creation to avoid circular imports)
# ============================================================================

from bloom.routes import student

app.include_router(student.router)

# Admin routes will be added in Phase 4
# from bloom.routes import admin
# app.include_router(admin.router)

