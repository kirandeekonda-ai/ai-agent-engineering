"""
FastAPI Backend for SolidWorks Change Impact Analyzer POC.

Endpoints:
  POST /upload              - Upload PDF files for extraction
  GET  /documents           - List all processed documents
  POST /change-request      - Submit a change request and get visual impact analysis
  GET  /annotated/{file}    - Get annotated page image for a specific file
  GET  /health              - Health check
"""

import os
import sys
import json
import shutil

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add parent to path for service imports
sys.path.insert(0, os.path.dirname(__file__))
from services.pdf_extractor import extract_all
from services.pdf_annotator import render_annotated_page, annotate_all_pages
from services.change_matcher import find_matches, generate_impact_report

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = FastAPI(
    title="SolidWorks Change Impact Analyzer",
    description="AI-powered tool to detect design change impact across engineering documents",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
EXTRACTED_DIR = os.path.join(BASE_DIR, "extracted")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEST_DATA_DIR = os.path.join(BASE_DIR, "test_data")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)

# Mount frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def _find_pdf(filename: str) -> str:
    """Find a PDF file in upload or test_data directories."""
    for directory in [UPLOAD_DIR, TEST_DATA_DIR]:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
    return None


@app.get("/")
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SolidWorks Change Impact Analyzer API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    """Upload and process PDF files."""
    results = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({"file": file.filename, "error": "Not a PDF file"})
            continue

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            extraction = extract_all(file_path)
            out_file = os.path.join(
                EXTRACTED_DIR,
                file.filename.replace(".pdf", "_extracted.json"),
            )
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(extraction, f, indent=2, ensure_ascii=False)

            vision_pages = extraction.get("extraction", {}).get("vision", {}).get("pages", [])
            dim_count = sum(len(p.get("dimensions", [])) for p in vision_pages)
            table_count = sum(len(p.get("tables", [])) for p in vision_pages)

            results.append({
                "file": file.filename,
                "status": "success",
                "pages": extraction["total_pages"],
                "dimensions_found": dim_count,
                "tables_found": table_count,
            })
        except Exception as e:
            results.append({"file": file.filename, "error": str(e)})

    return {"uploaded": len(results), "results": results}


@app.get("/documents")
async def list_documents():
    """List all processed documents."""
    documents = []
    for filename in sorted(os.listdir(EXTRACTED_DIR)):
        if not filename.endswith("_extracted.json"):
            continue

        filepath = os.path.join(EXTRACTED_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        vision_pages = data.get("extraction", {}).get("vision", {}).get("pages", [])
        dim_count = sum(len(p.get("dimensions", [])) for p in vision_pages)
        table_count = sum(len(p.get("tables", [])) for p in vision_pages)
        note_count = sum(len(p.get("notes", [])) for p in vision_pages)

        title_block = {}
        if vision_pages:
            title_block = vision_pages[0].get("title_block", {})

        documents.append({
            "file": data.get("file", filename),
            "total_pages": data.get("total_pages", 0),
            "dimensions_found": dim_count,
            "tables_found": table_count,
            "notes_found": note_count,
            "title_block": title_block,
        })

    return {"total_documents": len(documents), "documents": documents}


@app.post("/change-request")
async def submit_change_request(
    parameter_name: str = Form(...),
    old_value: str = Form(...),
    new_value: str = Form(...),
):
    """
    Submit a design change and get visual impact analysis with annotated PDF pages.
    """
    # Load all extracted documents
    all_extractions = []
    for filename in sorted(os.listdir(EXTRACTED_DIR)):
        if not filename.endswith("_extracted.json"):
            continue
        filepath = os.path.join(EXTRACTED_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            all_extractions.append(json.load(f))

    if not all_extractions:
        raise HTTPException(status_code=400, detail="No documents processed yet.")

    # Get text-based matches for the report summary
    all_matches = []
    for ext in all_extractions:
        matches = find_matches(ext, old_value, parameter_name)
        all_matches.append(matches)

    report = generate_impact_report(all_matches, old_value, new_value, parameter_name)

    # Generate annotated images for each affected file
    annotated_files = []
    for ext in all_extractions:
        pdf_filename = ext.get("file", "")
        pdf_path = _find_pdf(pdf_filename)

        if not pdf_path:
            annotated_files.append({
                "file": pdf_filename,
                "error": "PDF file not found for annotation",
                "pages": [],
            })
            continue

        try:
            pages = annotate_all_pages(pdf_path, old_value, parameter_name)
            # Compute related counts from annotated pages
            related = sum(p.get("related_count", 0) for p in pages)
            annotated_files.append({
                "file": pdf_filename,
                "pages": pages,
                "related_count": related,
            })
        except Exception as e:
            annotated_files.append({
                "file": pdf_filename,
                "error": str(e),
                "pages": [],
            })

    # Combine report with annotated images
    report["annotated_files"] = annotated_files

    return report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
