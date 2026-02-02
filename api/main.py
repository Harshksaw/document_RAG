import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.document_ingestion.data_ingestion import (
    DocHandler,
    DocumentComparator,
    ChatIngestor,
)
from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_compare.document_comparator import DocumentComparatorLLM
from src.document_chat.retrieval import ConversationalRAG
from utils.document_ops import FastAPIFileAdapter, read_pdf_via_handler
from utils.token_counter import get_token_counter
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

# ---------- ANALYZE ----------
@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Any:
    try:
        log.info(f"Received file for analysis: {file.filename}")
        dh = DocHandler()
        saved_path = dh.save_pdf(FastAPIFileAdapter(file))
        text = read_pdf_via_handler(dh, saved_path)
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze_document(text)
        log.info("Document analysis complete.", token_usage=result.get("token_usage"))
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Error during document analysis")
        raise HTTPException(status_code=500, detail="Document analysis service encountered an error. Please check logs or try again.")

# ---------- COMPARE ----------
@app.post("/compare")
async def compare_documents(reference: UploadFile = File(...), actual: UploadFile = File(...)) -> Any:
    try:
        log.info(f"Comparing files: {reference.filename} vs {actual.filename}")
        dc = DocumentComparator()
        ref_path, act_path = dc.save_uploaded_files(
            FastAPIFileAdapter(reference), FastAPIFileAdapter(actual)
        )
        _ = ref_path, act_path
        combined_text = dc.combine_documents()
        comp = DocumentComparatorLLM()
        df, token_usage = comp.compare_documents(combined_text)
        log.info("Document comparison completed.", token_usage=token_usage)
        return {
            "rows": df.to_dict(orient="records"),
            "session_id": dc.session_id,
            "token_usage": token_usage
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Comparison failed")
        raise HTTPException(status_code=500, detail="Document comparison service encountered an error.")

# ---------- CHAT: INDEX ----------
@app.post("/chat/index")
async def chat_build_index(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    k: int = Form(5),
) -> Any:
    try:
        log.info(f"Indexing chat session. Session ID: {session_id}, Files: {[f.filename for f in files]}")
        wrapped = [FastAPIFileAdapter(f) for f in files]
        # this is my main class for storing a data into VDB
        # created a object of ChatIngestor
        ci = ChatIngestor(
            temp_base=UPLOAD_BASE,
            faiss_base=FAISS_BASE,
            use_session_dirs=use_session_dirs,
            session_id=session_id or None,
        )
        # NOTE: ensure your ChatIngestor saves with index_name="index" or FAISS_INDEX_NAME
        # e.g., if it calls FAISS.save_local(dir, index_name=FAISS_INDEX_NAME)
        ci.built_retriver(  # if your method name is actually build_retriever, fix it there as well
            wrapped, chunk_size=chunk_size, chunk_overlap=chunk_overlap, k=k
        )
        log.info(f"Index created successfully for session: {ci.session_id}")
        return {"session_id": ci.session_id, "k": k, "use_session_dirs": use_session_dirs}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Chat index building failed")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

# ---------- CHAT: QUERY ----------
@app.post("/chat/query")
async def chat_query(
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    k: int = Form(5),
) -> Any:
    try:
        log.info(f"Received chat query: '{question}' | session: {session_id}")
        if use_session_dirs and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dirs=True")

        index_dir = os.path.join(FAISS_BASE, session_id) if use_session_dirs else FAISS_BASE  # type: ignore
        if not os.path.isdir(index_dir):
            raise HTTPException(status_code=404, detail=f"FAISS index not found at: {index_dir}")

        rag = ConversationalRAG(session_id=session_id)
        rag.load_retriever_from_faiss(index_dir, k=k, index_name=FAISS_INDEX_NAME)  # build retriever + chain
        result = rag.invoke(question, chat_history=[])
        log.info("Chat query handled successfully.", token_usage=result.get("token_usage"))

        return {
            "answer": result["answer"],
            "session_id": session_id,
            "k": k,
            "engine": "LCEL-RAG",
            "token_usage": result.get("token_usage", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Chat query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

# ---------- TOKEN USAGE ----------
@app.get("/tokens/usage")
def get_token_usage() -> Dict[str, Any]:
    """Get token usage statistics for all operation types."""
    try:
        counter = get_token_counter()
        return {
            "by_type": counter.get_all_usage(),
            "total": counter.get_total_usage()
        }
    except Exception as e:
        log.exception("Failed to get token usage")
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {e}")


@app.get("/tokens/usage/{operation_type}")
def get_token_usage_by_type(operation_type: str) -> Dict[str, Any]:
    """Get token usage for a specific operation type (chat, analyze, compare)."""
    try:
        counter = get_token_counter()
        return counter.get_usage_by_type(operation_type)
    except Exception as e:
        log.exception(f"Failed to get token usage for {operation_type}")
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {e}")


@app.get("/tokens/session/{session_id}")
def get_session_token_usage(session_id: str) -> Dict[str, Any]:
    """Get token usage for a specific session."""
    try:
        counter = get_token_counter()
        return {
            "session_id": session_id,
            "usage": counter.get_session_usage(session_id)
        }
    except Exception as e:
        log.exception(f"Failed to get token usage for session {session_id}")
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {e}")


@app.post("/tokens/reset")
def reset_token_counter() -> Dict[str, str]:
    """Reset all token counters."""
    try:
        counter = get_token_counter()
        counter.reset()
        log.info("Token counters reset")
        return {"status": "ok", "message": "Token counters reset successfully"}
    except Exception as e:
        log.exception("Failed to reset token counters")
        raise HTTPException(status_code=500, detail=f"Failed to reset counters: {e}")


# command for executing the fast api
# uvicorn api.main:app --port 6000 --reload
# uvicorn api.main:app --host 0.0.0.0 --port 6000 --reload