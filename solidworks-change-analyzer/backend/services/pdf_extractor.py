"""
PDF Extraction Service for SolidWorks Change Impact Analyzer.

Dual-track extraction:
  Track 1: pdfplumber — extracts raw text and tables (fast, reliable)
  Track 2: Groq Vision (Llama 4 Scout) — reads PDF pages as images,
           understands dimensions, annotations, and context

Both tracks merge into a unified extraction result.
"""

import os
import io
import json
import base64
import pdfplumber
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# Track 1: pdfplumber text + table extraction
# ──────────────────────────────────────────────

def extract_with_pdfplumber(pdf_path: str) -> dict:
    """
    Extract raw text and tables from a PDF using pdfplumber.
    Returns structured data with text content and table data per page.
    """
    result = {
        "file": os.path.basename(pdf_path),
        "pages": [],
        "total_pages": 0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["total_pages"] = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            page_data = {
                "page_number": i + 1,
                "text": page.extract_text() or "",
                "tables": [],
            }

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                if table:
                    # Clean up table data
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [
                            cell.strip() if cell else ""
                            for cell in row
                        ]
                        cleaned_table.append(cleaned_row)
                    page_data["tables"].append(cleaned_table)

            result["pages"].append(page_data)

    return result


# ──────────────────────────────────────────────
# Track 2: Groq Vision extraction
# ──────────────────────────────────────────────

EXTRACTION_PROMPT = """You are an expert engineering drawing analyzer. Analyze this engineering drawing page and extract ALL information in the following JSON format.

IMPORTANT: Return ONLY valid JSON, no other text.

{
  "dimensions": [
    {
      "label": "descriptive name of the dimension (e.g., Rim Diameter, Bolt Hole Diameter)",
      "value": "the numeric value as a string (e.g., 16.00)",
      "unit": "the unit (e.g., inches, mm)",
      "context": "where on the page this appears (e.g., specification table, dimension line, note)"
    }
  ],
  "tables": [
    {
      "title": "table name or purpose",
      "headers": ["column1", "column2"],
      "rows": [["val1", "val2"]]
    }
  ],
  "notes": ["any text notes that contain numeric values or specifications"],
  "title_block": {
    "part_name": "",
    "part_number": "",
    "revision": "",
    "material": "",
    "drawn_by": "",
    "date": ""
  },
  "revision_history": [
    {
      "rev": "A",
      "description": "",
      "date": "",
      "approved_by": ""
    }
  ]
}

Extract EVERY dimension, EVERY table value, EVERY note. Be thorough — missing a value could cause manufacturing errors. Pay special attention to:
- Diameter values (often shown as "Ø" or "DIA")
- Length and width measurements
- Values in specification tables
- Part numbers and descriptions that contain size references (like "16 inch" or "16x8")
- Tolerance values
"""


def pdf_page_to_base64(pdf_path: str, page_num: int, dpi: int = 200) -> str:
    """
    Convert a specific PDF page to a base64-encoded JPEG image.
    Uses pdfplumber's page.to_image() to avoid poppler dependency.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        # Render page to image using pdfplumber's built-in renderer
        img = page.to_image(resolution=dpi)

        # Convert PIL image to JPEG bytes
        buffered = io.BytesIO()
        img.original.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def extract_with_vision(pdf_path: str) -> dict:
    """
    Send each page of a PDF as an image to Groq Llama 4 Scout Vision
    and extract structured engineering data.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    client = Groq(api_key=api_key)
    model = "meta-llama/llama-4-scout-17b-16e-instruct"

    result = {
        "file": os.path.basename(pdf_path),
        "pages": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    for page_num in range(total_pages):
        print(f"  [Vision] Processing page {page_num + 1}/{total_pages}...")

        # Convert page to image
        base64_image = pdf_page_to_base64(pdf_path, page_num)

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": EXTRACTION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.1,  # Low temperature for accurate extraction
                max_completion_tokens=4096,
                top_p=1,
                stream=False,
            )

            response_text = completion.choices[0].message.content

            # Parse JSON from response (handle possible markdown code blocks)
            json_text = response_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            page_data = json.loads(json_text.strip())
            page_data["page_number"] = page_num + 1
            result["pages"].append(page_data)

        except json.JSONDecodeError as e:
            print(f"  [Warning] Could not parse JSON for page {page_num + 1}: {e}")
            print(f"  Raw response: {response_text[:300]}...")
            result["pages"].append({
                "page_number": page_num + 1,
                "error": f"JSON parse error: {str(e)}",
                "raw_response": response_text[:500],
            })
        except Exception as e:
            print(f"  [Error] Vision extraction failed for page {page_num + 1}: {e}")
            result["pages"].append({
                "page_number": page_num + 1,
                "error": str(e),
            })

    return result


# ──────────────────────────────────────────────
# Merged extraction
# ──────────────────────────────────────────────

def extract_all(pdf_path: str) -> dict:
    """
    Run both extraction tracks and merge results.
    """
    print(f"\nExtracting from: {os.path.basename(pdf_path)}")
    print("-" * 50)

    # Track 1: pdfplumber
    print("[Track 1] pdfplumber text extraction...")
    text_data = extract_with_pdfplumber(pdf_path)
    print(f"  Found {len(text_data['pages'])} pages with text/tables")

    # Track 2: Vision
    print("[Track 2] Groq Vision extraction...")
    vision_data = extract_with_vision(pdf_path)
    print(f"  Processed {len(vision_data['pages'])} pages with AI")

    # Merge results
    merged = {
        "file": os.path.basename(pdf_path),
        "file_path": pdf_path,
        "total_pages": text_data["total_pages"],
        "extraction": {
            "pdfplumber": text_data,
            "vision": vision_data,
        },
    }

    return merged


# ──────────────────────────────────────────────
# CLI for testing
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # Default: process all test PDFs
        test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
        if not os.path.exists(test_dir):
            print("No test_data directory found. Run generate_test_data.py first.")
            sys.exit(1)

        pdf_files = [
            os.path.join(test_dir, f)
            for f in os.listdir(test_dir)
            if f.endswith(".pdf")
        ]
    else:
        pdf_files = [sys.argv[1]]

    # Output directory for extraction results
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extracted")
    os.makedirs(output_dir, exist_ok=True)

    all_results = []

    for pdf_path in pdf_files:
        result = extract_all(pdf_path)
        all_results.append(result)

        # Save individual result
        out_file = os.path.join(
            output_dir,
            os.path.basename(pdf_path).replace(".pdf", "_extracted.json"),
        )
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {out_file}")

    # Save combined results
    combined_file = os.path.join(output_dir, "all_extractions.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] All extractions saved to: {combined_file}")
