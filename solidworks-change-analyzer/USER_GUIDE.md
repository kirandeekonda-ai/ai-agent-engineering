# SolidWorks Change Impact Analyzer — User Guide

> AI-powered tool that scans engineering PDFs to find exactly where a design change needs to be applied, filtering out false positives like part numbers and dates.

---

## Prerequisites

1. **Python 3.10+** with these packages installed:
   ```
   pip install pdfplumber fastapi uvicorn groq Pillow python-dotenv
   ```

2. **Groq API Key** — create a `.env` file in the project root:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
   Get a free key at [console.groq.com](https://console.groq.com)

---

## Quick Start

```bash
cd "C:\Users\Kiran\AI Practice\solidworks-change-analyzer"
python -c "import uvicorn; uvicorn.run('backend.main:app', host='0.0.0.0', port=8000)"
```

Open **http://localhost:8000** in your browser.

---

## Step-by-Step Usage

### Step 1 — Upload Engineering Drawings

- **Drag & drop** PDF files onto the upload area, or click **"browse"**
- The AI extracts dimensions, tables, notes, and title blocks from each page
- Processed documents appear under **"Processed Documents"** with stats

> 5 test PDFs are already pre-loaded (BOM, QC Sheet, Supplier Spec, Part Drawing, Assembly Drawing)

### Step 2 — Submit a Design Change

Fill in the three fields:

| Field | What to enter | Example |
|---|---|---|
| **Parameter Name** | The specific parameter being changed | `Rim Diameter` |
| **Current Value** | The old value to search for | `16` |
| **New Value** | What it's changing to | `17` |

Click **"Analyze Impact"** and wait ~30-60 seconds while the AI scans all documents.

### Step 3 — Read the Impact Report

The report has four parts:

**Summary Cards**
- Files Scanned / Files Affected
- **Need Updating** — locations confirmed by AI as relevant to your parameter
- **Review / Skip** — part numbers, dates, and other unrelated matches

**AI Classification Legend**
| Color | Meaning | Example |
|---|---|---|
| 🟢 Green | **Needs Update** — refers to the parameter | `Rim Diameter: 16 inches` |
| 🟡 Yellow | **Review** — possibly related, verify manually | `16 INCH CONFIG` |
| ⚫ Gray | **Unrelated** — part number, date, or code | `TR-16-001`, `BOM-WA-16-001` |

**File Tabs** — click each tab to view that document's results

**Side-by-Side Viewer**
- **Left panel**: Annotated PDF with color-coded bounding boxes
- **Right panel**: Match list sorted by relevance with AI reasoning

### Step 4 — Navigate the Viewer

| Action | How |
|---|---|
| Zoom in/out | `+` / `−` buttons or `Ctrl + Scroll Wheel` |
| Reset zoom | Click `Fit` |
| Highlight a match | Hover over it in the match list |
| Switch files | Click file tabs at the top |
| Toggle theme | Click ☀️/🌙 icon in the header |

---

## What This Tool Tells the PLM Team

> *"If you change Rim Diameter from 16 to 17, here are the **exact locations** across all documents where '16' actually refers to the rim diameter and needs updating. Part numbers like TR-16-001 and dates are already filtered out."*

**Before this tool:** Manual Ctrl+F across dozens of PDFs, every "16" looks the same.  
**After this tool:** AI highlights only the relevant matches, with reasons for each classification.

---

## Architecture Overview

```
Frontend (HTML/CSS/JS)          Backend (FastAPI)
┌─────────────────────┐        ┌──────────────────────────────┐
│ Upload PDFs          │──POST──│ /upload                      │
│ Submit Change        │──POST──│ /change-request              │
│ View Annotated PDFs  │◄───────│   ├─ pdf_extractor (AI+plumber)│
│ Theme Toggle         │        │   ├─ change_matcher           │
└─────────────────────┘        │   └─ pdf_annotator (AI classify)│
                               └──────────────────────────────┘
```

- **pdf_extractor** — Dual extraction using pdfplumber + Groq Vision (Llama 4 Scout)
- **change_matcher** — Finds value occurrences with confidence scoring
- **pdf_annotator** — Smart classification using Groq LLM with `>>>marker<<<` technique

---

## Project Structure

```
solidworks-change-analyzer/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── services/
│   │   ├── pdf_extractor.py       # AI-powered PDF extraction
│   │   ├── change_matcher.py      # Value matching + confidence
│   │   └── pdf_annotator.py       # Smart annotation with AI classification
│   ├── extracted/                 # JSON extraction results
│   └── annotated/                 # Test annotation outputs
├── frontend/
│   ├── index.html                 # Dashboard UI
│   ├── style.css                  # Dual-theme styles (light/dark)
│   └── app.js                     # UI logic + theme toggle
├── test_data/                     # Sample engineering PDFs
├── .env                           # GROQ_API_KEY
└── USER_GUIDE.md                  # This file
```
