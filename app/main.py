import os
from fastapi import FastAPI, Request, HTTPException, Depends
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
    version="1.0.0"
)

# Security and Performance Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Stability Hotfix for Python 3.14: Bypass broken Jinja2 cache by reading manually
    template_path = BASE_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    logging.info(f"Chat request received for session: {req.session_id}")
    
    # Retrieve history
    history = db.get_session_history(req.session_id)
    
    # Log User Message
    db.append_message(req.session_id, "user", req.message)
    
    # Generate Response
    ai_result = assistant.generate_response(req.message, context_history=history, language=req.language)
    
    # Log AI Message
    db.append_message(req.session_id, "model", ai_result["response"])
    
    return ChatResponse(
        response=ai_result["response"],
        suggested_actions=ai_result["suggested_actions"],
        timeline_event=ai_result.get("timeline_event")
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "election-navigator-ai"}
