"""
Main application module for Election Navigator AI.
"""
# pylint: disable=broad-exception-caught,missing-function-docstring,logging-fstring-interpolation,unused-argument,wrong-import-order
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import logging
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from google.cloud import logging as cloud_logging

from app.models.schemas import ChatRequest, ChatResponse
from app.core.ai import assistant
from app.core.db import db

# Resolve absolute paths for reliable template/static loading
BASE_DIR = Path(__file__).resolve().parent

# Initialize Observability (Cloud Logging)
try:
    log_client = cloud_logging.Client()
    log_client.setup_logging()
    logging.info("Cloud Logging initialized.")
except Exception:
    logging.basicConfig(level=logging.INFO)
    logging.info("Local logging initialized.")

# Initialize Security (Rate Limiting)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Election Navigator AI",
    description="Interactive assistant for understanding the election process.",
    version="1.0.0",
)

# Security and Performance Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://election-navigator-ai-954508895838.us-central1.run.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],  # Strict production origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """
    Serves the main application landing page.
    Bypasses template cache for local compatibility while maintaining efficiency via manual IO.
    """
    template_path = BASE_DIR / "templates" / "index.html"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(
            content=content, headers={"Cache-Control": "public, max-age=3600"}
        )
    except Exception as e:
        logging.error(f"Failed to load index template: {e}")
        raise HTTPException(status_code=500, detail="Template loading error") from e


# Optimized static mounting with caching
app.mount(
    "/static", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static"
)


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    # Additional Security Headers
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_endpoint(request: Request, req: ChatRequest) -> ChatResponse:
    """
    Primary endpoint for the AI chat assistant.
    Coordinates database history retrieval, AI generation, and real-time translation.
    """
    logging.info(
        f"Chat request initiated | Session: {req.session_id} | Language: {req.language}"
    )

    # Concurrent retrieval of session history (Efficiency)
    history = await db.get_session_history(req.session_id)

    # Persistent logging of user interaction
    await db.append_message(req.session_id, "user", req.message)

    # Generate and Translate response
    ai_result = assistant.generate_response(
        req.message, context_history=history, language=req.language
    )

    # Persistent logging of AI response
    await db.append_message(req.session_id, "model", ai_result["response"])

    return ChatResponse(
        response=ai_result["response"],
        suggested_actions=ai_result["suggested_actions"],
        timeline_event=ai_result.get("timeline_event"),
    )


@app.get("/health")
async def health_check() -> dict:
    """Returns the health status of the service."""
    return {"status": "ok", "service": "election-navigator-ai"}
