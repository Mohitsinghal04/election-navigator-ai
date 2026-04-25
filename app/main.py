import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.models.schemas import ChatRequest, ChatResponse
from app.core.ai import assistant
from app.core.db import db

app = FastAPI(
    title="Election Navigator AI",
    description="Interactive assistant for understanding the election process.",
    version="1.0.0"
)

# Security and Performance Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # Retrieve history
    history = db.get_session_history(req.session_id)
    
    # In a real Vertex AI integration we'd convert history to the proper Content format.
    # For now, we pass the query.
    
    # Log User Message
    db.append_message(req.session_id, "user", req.message)
    
    # Generate Response
    ai_result = assistant.generate_response(req.message, context_history=history, language=req.language)
    
    # Log AI Message
    db.append_message(req.session_id, "model", ai_result["response"])
    
    return ChatResponse(
        response=ai_result["response"],
        suggested_actions=ai_result["suggested_actions"]
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "election-navigator-ai"}
