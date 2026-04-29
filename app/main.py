from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.logger import get_session_logger

get_session_logger()  # Initialize session log file on startup

app = FastAPI(
    title="RAG Agent Evaluation Service",
    description="Guidelines-based evaluation service for multiple runs of a single RAG Agent using DeepEval + Cortex LLM.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
