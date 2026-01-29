import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
# from src.document_ingestion.data_ingestion import (
#     DocHandler,
#     DocumentComparator,
#     ChatIngestor,
# )
# from src.document_analyzer.data_analysis import DocumentAnalyzer
# from src.document_compare.document_comparator import DocumentComparatorLLM
# from src.document_chat.retrieval import ConversationalRAG
# from utils.document_ops import FastAPIFileAdapter,read_pdf_via_handler
from logger import GLOBAL_LOGGER as log


FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")  # <--- keep consistent with save_local()

app = FastAPI(title="Document Portal API", version="0.1")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    log.info("Serving UI homepage.")
    resp = templates.TemplateResponse("index.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.get("/health")
def health() -> Dict[str, str]:
    log.info("Health check passed.")
    return {"status": "ok", "service": "document-portal"}


@app.get("/analyze")
async def chat_build_index():
    try:
        pass
    except Exception as e:
        log.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=str(e))
