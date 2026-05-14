from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import shutil
import os
import json

from .ingest import DocumentIngester
from .rag import RAGEngine
from .inference import SLMEngine
from .use_case_handler import UseCaseHandler
from .utils import get_logger, timer

logger = get_logger("api")

app = FastAPI(title="Generic Self-Hosted Support SLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
rag_engine = RAGEngine()
ingester = DocumentIngester()
use_case_handler = UseCaseHandler()
# Lazy load SLM to avoid startup delay if just checking API, 
# but requirement says "Model downloaded once on startup". 
# So we initialize it on startup.
slm_engine = None

@app.on_event("startup")
async def startup_event():
    global slm_engine
    # Initialize SLM (will download if needed)
    slm_engine = SLMEngine()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    use_case: Optional[str] = None  # Detected use case
    confidence: Optional[float] = None  # Use case detection confidence
    metadata: Optional[List[Dict[str, Any]]] = None  # For JSON metadata from CSV

@app.get("/health")
def health_check():
    return {"status": "ok", "components": {"rag": "ready", "slm": "ready" if slm_engine else "loading"}}

@app.post("/v1/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    total_chunks = 0
    processed_files = []
    
    with timer("Document Upload & Indexing"):
        for file in files:
            logger.info(f"Processing {file.filename}...")
            
            # Check if it's a CSV file
            if file.filename.lower().endswith('.csv'):
                # Handle CSV with structured JSON metadata
                csv_records = await ingester.extract_csv_with_metadata(file)
                if csv_records:
                    chunks = ingester.chunk_csv_records(csv_records)
                    rag_engine.add_documents(chunks)
                    total_chunks += len(chunks)
                    processed_files.append(file.filename)
                    logger.info(f"Processed CSV: {file.filename} with {len(chunks)} loan records")
                else:
                    logger.warning(f"No records extracted from CSV {file.filename}")
            else:
                # Handle regular documents (PDF, DOCX, TXT, MD)
                text = await ingester.extract_text(file)
                if text:
                    chunks = ingester.chunk_text(text, source=file.filename)
                    rag_engine.add_documents(chunks)
                    total_chunks += len(chunks)
                    processed_files.append(file.filename)
                else:
                    logger.warning(f"No text extracted from {file.filename}")

    return {
        "status": "success",
        "files_processed": processed_files,
        "chunks_indexed": total_chunks
    }

@app.post("/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    with timer(f"Query: {request.question}"):
        # Detect use case
        use_case, confidence = use_case_handler.detect_use_case(request.question)
        logger.info(f"Use case: {use_case} (confidence: {confidence:.2f})")
        
        # Retrieve (k=4 for better context)
        retrieved_docs = rag_engine.search(request.question, k=4)
        
        if not retrieved_docs:
            return {
                "answer": "I don't know based on the provided documents.",
                "sources": [],
                "use_case": use_case,
                "confidence": confidence,
                "metadata": None
            }
        
        # Collect sources and metadata
        sources = list(set([d['source'] for d in retrieved_docs]))
        json_metadata_list = [d['json_metadata'] for d in retrieved_docs if 'json_metadata' in d]
        
        # Create optimized context based on use case
        context_text = use_case_handler.create_optimized_context(
            retrieved_docs, 
            use_case, 
            max_chars=800
        )
        
        # Get use case specific prompt
        system_prompt = use_case_handler.get_use_case_prompt(use_case, request.question)
        
        # Generate answer with use case context
        answer = slm_engine.generate_answer(context_text, request.question, system_prompt=system_prompt)
        
        # Format metadata based on use case
        if json_metadata_list:
            json_metadata_list = use_case_handler.format_response_metadata(
                use_case, 
                json_metadata_list
            )
        
        return {
            "answer": answer,
            "sources": sources,
            "use_case": use_case,
            "confidence": confidence,
            "metadata": json_metadata_list if json_metadata_list else None
        }

@app.post("/v1/reset")
def reset_index():
    rag_engine.reset()
    return {"status": "success", "message": "Index reset"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
