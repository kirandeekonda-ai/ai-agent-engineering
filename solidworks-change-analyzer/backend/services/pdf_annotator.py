"""
PDF Annotator v3 — Context-Aware Smart Matching.

Instead of highlighting every "16", uses AI (Groq) to determine
which occurrences actually relate to the parameter being changed.

Flow:
  1. pdfplumber finds ALL positions of the value on the page (coordinates)
  2. Each match + surrounding text is batched into ONE Groq API call
  3. Groq classifies each as: "related", "maybe", or "unrelated"
  4. Only related/maybe matches are drawn as bounding boxes
  5. Color coding: green = related, yellow = maybe, dim gray = unrelated
"""

import os
import io
import re
import json
import base64
import pdfplumber
from PIL import Image, ImageDraw
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))


# ──────────────────────────────────────────────
# 1. Find value positions using pdfplumber chars
# ──────────────────────────────────────────────

def find_value_positions(pdf_path: str, search_value: str, page_num: int = 0) -> list:
    """Find all occurrences of a value on a PDF page with exact coordinates."""
    matches = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            return matches

        page = pdf.pages[page_num]
        chars = page.chars
        if not chars:
            return matches

        lines = _group_chars_into_lines(chars)

        for line in lines:
            line_text = "".join(c["text"] for c in line["chars"])
            start = 0
            while True:
                idx = line_text.find(search_value, start)
                if idx == -1:
                    break

                matched_chars = line["chars"][idx:idx + len(search_value)]
                if matched_chars:
                    x0 = min(c["x0"] for c in matched_chars)
                    y0 = min(c["top"] for c in matched_chars)
                    x1 = max(c["x1"] for c in matched_chars)
                    y1 = max(c["bottom"] for c in matched_chars)

                    # Context: grab surrounding text with MARKERS around the exact target
                    # This prevents the LLM from confusing nearby occurrences
                    ctx_start = max(0, idx - 50)
                    ctx_end = min(len(line_text), idx + len(search_value) + 50)
                    # Build context with >>>VALUE<<< markers around THIS occurrence
                    before = line_text[ctx_start:idx]
                    after = line_text[idx + len(search_value):ctx_end]
                    marked_context = f"{before}>>>{search_value}<<<{after}".strip()

                    matches.append({
                        "idx": len(matches),
                        "text": search_value,
                        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "context": marked_context,
                        "display_context": line_text[ctx_start:ctx_end].strip(),
                        "full_line": line_text.strip(),
                    })

                start = idx + 1

    return matches


def _group_chars_into_lines(chars: list, tolerance: float = 3.0) -> list:
    if not chars:
        return []
    sorted_chars = sorted(chars, key=lambda c: (round(c["top"] / tolerance), c["x0"]))
    lines = []
    current_line = {"chars": [sorted_chars[0]], "top": sorted_chars[0]["top"]}

    for char in sorted_chars[1:]:
        if abs(char["top"] - current_line["top"]) <= tolerance:
            current_line["chars"].append(char)
        else:
            current_line["chars"].sort(key=lambda c: c["x0"])
            lines.append(current_line)
            current_line = {"chars": [char], "top": char["top"]}

    current_line["chars"].sort(key=lambda c: c["x0"])
    lines.append(current_line)
    return lines


# ──────────────────────────────────────────────
# 2. AI-powered context classification
# ──────────────────────────────────────────────

def classify_matches_with_ai(
    matches: list,
    parameter_name: str,
    old_value: str,
    filename: str,
) -> list:
    """
    Send all found matches to Groq in ONE call and ask it to classify each.
    Returns the matches list with added 'relevance' and 'reason' fields.
    """
    if not matches:
        return matches

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback: use heuristic classification
        return _heuristic_classify(matches, parameter_name, old_value)

    client = Groq(api_key=api_key)

    # Build the batch prompt
    match_descriptions = []
    for m in matches:
        match_descriptions.append(
            f"  Match #{m['idx']}: \"{m['context']}\""
        )
    matches_text = "\n".join(match_descriptions)

    prompt = f"""You are analyzing an engineering drawing PDF named "{filename}".

A design change is being made: the parameter "{parameter_name}" is changing from "{old_value}" to a new value.

I found {len(matches)} occurrences of "{old_value}" in the document. In each match below, the SPECIFIC occurrence to classify is wrapped in >>>markers<<<. There may be other instances of "{old_value}" in the same line — IGNORE those. Only classify the one inside >>><<<.

MATCHES FOUND:
{matches_text}

For each match, respond with a JSON array where each object has:
- "idx": the match number
- "relevance": one of "related" (this >>>{old_value}<<< refers to {parameter_name}), "maybe" (possibly related), or "unrelated" (NOT about {parameter_name})
- "reason": brief explanation (max 10 words)

CLASSIFICATION RULES — apply these to the >>>marked<<< occurrence ONLY:
- If the >>>{old_value}<<< is INSIDE a part number code like "TR->>>{old_value}<<<-001" or "WA->>>{old_value}<<<-001" → "unrelated" (it's an identifier, not a dimension)
- If the >>>{old_value}<<< is followed by dimension words ("inch", "mm", "diameter") → "related"
- If the >>>{old_value}<<< describes the parameter like "{parameter_name} >>>{old_value}<<<" → "related"
- If the >>>{old_value}<<< is in a revision note about the parameter change → "related"
- If the >>>{old_value}<<< is a configuration name like ">>>{old_value}<<< INCH" → "related"
- If the >>>{old_value}<<< is inside a date → "unrelated"
- If the >>>{old_value}<<< is a quantity or count → "unrelated"

Respond ONLY with the JSON array, no other text."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_completion_tokens=2000,
        )

        response_text = completion.choices[0].message.content.strip()

        # Parse JSON from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            classifications = json.loads(json_match.group())
        else:
            classifications = json.loads(response_text)

        # Merge classifications back into matches
        class_map = {c["idx"]: c for c in classifications}
        for m in matches:
            c = class_map.get(m["idx"], {})
            m["relevance"] = c.get("relevance", "maybe")
            m["reason"] = c.get("reason", "Could not classify")

    except Exception as e:
        print(f"  [AI Classification] Error: {e}, falling back to heuristic")
        return _heuristic_classify(matches, parameter_name, old_value)

    return matches


def _heuristic_classify(matches: list, parameter_name: str, old_value: str) -> list:
    """Fallback classification using pattern matching."""
    param_lower = parameter_name.lower()
    param_words = param_lower.split()

    for m in matches:
        ctx = m["full_line"].lower()
        before_val = m["full_line"][:m["full_line"].find(old_value)]
        after_val = m["full_line"][m["full_line"].find(old_value) + len(old_value):]

        # Check if it's in a part number pattern (letters-digits-letters)
        if re.search(r'[A-Z]+-' + re.escape(old_value) + r'-', m["full_line"]):
            m["relevance"] = "unrelated"
            m["reason"] = "Part of a part number"
            continue

        # Check if parameter name is nearby
        if any(w in ctx for w in param_words):
            m["relevance"] = "related"
            m["reason"] = f"Contains '{parameter_name}'"
            continue

        # Dimension keywords
        dim_kw = ["diameter", "dia", "inch", "width", "size", "rim"]
        if any(kw in ctx for kw in dim_kw):
            m["relevance"] = "related"
            m["reason"] = "Dimension context"
            continue

        # Configuration reference
        if "config" in ctx or "assembly" in ctx:
            m["relevance"] = "maybe"
            m["reason"] = "Configuration reference"
            continue

        # Date pattern
        if re.search(r'\d{4}-\d{2}-' + re.escape(old_value), m["full_line"]):
            m["relevance"] = "unrelated"
            m["reason"] = "Part of a date"
            continue

        m["relevance"] = "maybe"
        m["reason"] = "Needs manual review"

    return matches


# ──────────────────────────────────────────────
# 3. Render annotated image with smart colors
# ──────────────────────────────────────────────

# Green = related (needs updating), Yellow = maybe, Gray dimmed = unrelated
RELEVANCE_COLORS = {
    "related":   {"fill": (34, 197, 94, 50),   "border": (34, 197, 94),    "label": "Related"},
    "maybe":     {"fill": (245, 158, 11, 50),  "border": (245, 158, 11),   "label": "Review"},
    "unrelated": {"fill": (107, 114, 128, 25), "border": (107, 114, 128),  "label": "Unrelated"},
}


def render_annotated_page(
    pdf_path: str,
    search_value: str,
    parameter_name: str,
    page_num: int = 0,
    dpi: int = 200,
) -> dict:
    """
    Render a PDF page with smart, context-aware bounding boxes.
    Green = definitely needs updating, Yellow = review, Gray = unrelated.
    """
    filename = os.path.basename(pdf_path)

    # Step 1: Find all positions
    matches = find_value_positions(pdf_path, search_value, page_num)

    if not matches:
        # Still render the page image even if no matches
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            page_img = page.to_image(resolution=dpi)
            img = page_img.original.copy()
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=90)
            return {
                "image_base64": base64.b64encode(buffered.getvalue()).decode("utf-8"),
                "matches": [],
                "page_width": img.width,
                "page_height": img.height,
                "total_matches": 0,
                "related_count": 0,
                "maybe_count": 0,
                "unrelated_count": 0,
            }

    # Step 2: Classify with AI
    matches = classify_matches_with_ai(matches, parameter_name, search_value, filename)

    # Step 3: Render page
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        page_img = page.to_image(resolution=dpi)
        img = page_img.original.copy()
        scale = dpi / 72.0

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    img_rgba = img.convert("RGBA")
    draw = ImageDraw.Draw(img_rgba)

    for match in matches:
        x0 = match["x0"] * scale
        y0 = match["y0"] * scale
        x1 = match["x1"] * scale
        y1 = match["y1"] * scale

        pad = 4 * scale / 2
        x0 -= pad
        y0 -= pad
        x1 += pad
        y1 += pad

        relevance = match.get("relevance", "maybe")
        colors = RELEVANCE_COLORS.get(relevance, RELEVANCE_COLORS["maybe"])

        # Draw
        draw_overlay.rectangle([x0, y0, x1, y1], fill=colors["fill"])
        border_width = 3 if relevance == "related" else 2 if relevance == "maybe" else 1
        draw.rectangle([x0, y0, x1, y1], outline=colors["border"], width=border_width)

        # Store pixel coords for frontend
        match["x0_px"] = round(x0)
        match["y0_px"] = round(y0)
        match["x1_px"] = round(x1)
        match["y1_px"] = round(y1)

    # Composite
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    img_final = img_rgba.convert("RGB")

    buffered = io.BytesIO()
    img_final.save(buffered, format="JPEG", quality=90)
    image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    related = [m for m in matches if m.get("relevance") == "related"]
    maybe = [m for m in matches if m.get("relevance") == "maybe"]
    unrelated = [m for m in matches if m.get("relevance") == "unrelated"]

    return {
        "image_base64": image_base64,
        "matches": matches,
        "page_width": img_final.width,
        "page_height": img_final.height,
        "total_matches": len(matches),
        "related_count": len(related),
        "maybe_count": len(maybe),
        "unrelated_count": len(unrelated),
    }


def annotate_all_pages(
    pdf_path: str, search_value: str, parameter_name: str, dpi: int = 200
) -> list:
    """Annotate all pages of a PDF with smart context-aware matching."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    for page_num in range(total_pages):
        result = render_annotated_page(
            pdf_path, search_value, parameter_name, page_num, dpi
        )
        result["page_number"] = page_num + 1
        results.append(result)

    return results


# ──────────────────────────────────────────────
# CLI test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        test_dir, "TyreRim_PartDrawing.pdf"
    )
    search_value = sys.argv[2] if len(sys.argv) > 2 else "16"
    param_name = sys.argv[3] if len(sys.argv) > 3 else "Rim Diameter"

    print(f"Smart Annotating: {pdf_path}")
    print(f"Parameter: '{param_name}', Value: '{search_value}'")

    result = render_annotated_page(pdf_path, search_value, param_name)

    print(f"\nTotal occurrences: {result['total_matches']}")
    print(f"  Related:   {result['related_count']}")
    print(f"  Maybe:     {result['maybe_count']}")
    print(f"  Unrelated: {result['unrelated_count']}")
    print()
    for m in result["matches"]:
        icon = {"related": "[YES]", "maybe": "[???]", "unrelated": "[ - ]"}.get(
            m.get("relevance", ""), "[???]"
        )
        print(f"  {icon} {m.get('relevance','?'):10s} | {m.get('reason','')[:30]:30s} | {m['context'][:50]}")

    # Save image
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "annotated")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "test_smart_annotated.jpg")
    with open(out_file, "wb") as f:
        f.write(base64.b64decode(result["image_base64"]))
    print(f"\n[OK] Saved: {out_file}")
