"""
Change Matcher Service for SolidWorks Change Impact Analyzer.

Takes a change request (e.g., "Rim Diameter: 16 -> 17") and finds
all occurrences of the old value across extracted PDF data.
"""

import os
import json
import re


def find_matches(extraction_data: dict, old_value: str, parameter_name: str = "") -> dict:
    """
    Search through extracted PDF data for all occurrences of a value.

    Args:
        extraction_data: The merged extraction result from pdf_extractor
        old_value: The value to search for (e.g., "16")
        parameter_name: Optional parameter name for context matching (e.g., "Rim Diameter")

    Returns:
        Dict with all found matches, locations, and confidence scores
    """
    file_name = extraction_data.get("file", "unknown")
    matches = []

    # ── Search pdfplumber text data ──
    plumber_data = extraction_data.get("extraction", {}).get("pdfplumber", {})
    for page in plumber_data.get("pages", []):
        page_num = page.get("page_number", 0)
        text = page.get("text", "")

        # Find all occurrences in raw text
        for line_num, line in enumerate(text.split("\n"), 1):
            if old_value in line:
                # Determine context and confidence
                confidence, context = _analyze_match_context(
                    line, old_value, parameter_name
                )
                matches.append({
                    "source": "text",
                    "page": page_num,
                    "line": line_num,
                    "content": line.strip(),
                    "context": context,
                    "confidence": confidence,
                })

        # Find in tables
        for table_idx, table in enumerate(page.get("tables", [])):
            for row_idx, row in enumerate(table):
                for col_idx, cell in enumerate(row):
                    if old_value in str(cell):
                        confidence, context = _analyze_match_context(
                            cell, old_value, parameter_name,
                            table_header=table[0] if table else None,
                            col_idx=col_idx
                        )
                        matches.append({
                            "source": "table",
                            "page": page_num,
                            "table_index": table_idx,
                            "row": row_idx,
                            "column": col_idx,
                            "cell_content": cell.strip(),
                            "context": context,
                            "confidence": confidence,
                        })

    # ── Search Vision extraction data ──
    vision_data = extraction_data.get("extraction", {}).get("vision", {})
    for page in vision_data.get("pages", []):
        if "error" in page:
            continue

        page_num = page.get("page_number", 0)

        # Search dimensions
        for dim in page.get("dimensions", []):
            dim_value = str(dim.get("value", ""))
            dim_label = str(dim.get("label", ""))

            if old_value in dim_value:
                # Higher confidence if parameter name matches
                confidence = 0.9
                if parameter_name and parameter_name.lower() in dim_label.lower():
                    confidence = 0.98

                matches.append({
                    "source": "vision_dimension",
                    "page": page_num,
                    "label": dim_label,
                    "value": dim_value,
                    "unit": dim.get("unit", ""),
                    "context": dim.get("context", ""),
                    "confidence": confidence,
                })

        # Search tables from vision
        for table in page.get("tables", []):
            title = table.get("title", "")
            for row_idx, row in enumerate(table.get("rows", [])):
                for col_idx, cell in enumerate(row):
                    if old_value in str(cell):
                        confidence = 0.85
                        if parameter_name.lower() in str(cell).lower():
                            confidence = 0.95
                        matches.append({
                            "source": "vision_table",
                            "page": page_num,
                            "table_title": title,
                            "row": row_idx,
                            "column": col_idx,
                            "cell_content": str(cell),
                            "context": f"Table: {title}",
                            "confidence": confidence,
                        })

        # Search notes
        for note in page.get("notes", []):
            if old_value in str(note):
                confidence = 0.80
                if parameter_name.lower() in str(note).lower():
                    confidence = 0.92
                matches.append({
                    "source": "vision_note",
                    "page": page_num,
                    "content": str(note),
                    "context": "Drawing note",
                    "confidence": confidence,
                })

        # Search title block
        title_block = page.get("title_block", {})
        for key, value in title_block.items():
            if old_value in str(value):
                matches.append({
                    "source": "vision_title_block",
                    "page": page_num,
                    "field": key,
                    "content": str(value),
                    "context": f"Title block: {key}",
                    "confidence": 0.90,
                })

        # Search revision history
        for rev in page.get("revision_history", []):
            desc = str(rev.get("description", ""))
            if old_value in desc:
                matches.append({
                    "source": "vision_revision",
                    "page": page_num,
                    "revision": rev.get("rev", ""),
                    "content": desc,
                    "context": "Revision history",
                    "confidence": 0.85,
                })

    # Deduplicate matches (same content on same page from different sources)
    deduplicated = _deduplicate_matches(matches)

    return {
        "file": file_name,
        "search_value": old_value,
        "parameter_name": parameter_name,
        "total_matches": len(deduplicated),
        "matches": deduplicated,
    }


def _analyze_match_context(text: str, value: str, parameter_name: str,
                           table_header=None, col_idx=None) -> tuple:
    """
    Analyze the context of a match to determine confidence level.
    Returns (confidence_score, context_description).
    """
    text_lower = text.lower()
    confidence = 0.70  # Base confidence

    # Check if parameter name appears nearby
    if parameter_name and parameter_name.lower() in text_lower:
        confidence = 0.95
        return confidence, f"Direct match: '{parameter_name}' found in context"

    # Check for common dimension keywords
    dim_keywords = ["diameter", "dia", "width", "length", "height", "size",
                    "radius", "bore", "offset", "pcd", "inch", "mm"]
    for kw in dim_keywords:
        if kw in text_lower:
            confidence = max(confidence, 0.85)
            return confidence, f"Dimension context: '{kw}' keyword found"

    # Check table headers for context
    if table_header and col_idx is not None:
        try:
            header = str(table_header[col_idx]).lower()
            if any(kw in header for kw in ["value", "nominal", "spec", "size", "dim"]):
                confidence = 0.88
                return confidence, f"Table column: {table_header[col_idx]}"
        except (IndexError, TypeError):
            pass

    # Check if it's part of a part number (like TR-16-001)
    if re.search(rf'[A-Z]+-{re.escape(value)}-', text):
        confidence = 0.75
        return confidence, "Part number reference"

    # Check if the value appears in a descriptive context
    size_patterns = [
        rf'{value}\s*(?:inch|in|mm|cm)',
        rf'{value}\s*[xX]\s*\d+',  # like "16 x 8"
        rf'[Oo]\s*{value}',  # diameter symbol
    ]
    for pattern in size_patterns:
        if re.search(pattern, text):
            confidence = 0.90
            return confidence, "Size/dimension pattern"

    return confidence, "Value found in text"


def _deduplicate_matches(matches: list) -> list:
    """
    Remove duplicate matches (same value found by both pdfplumber and vision).
    Keep the one with higher confidence.
    """
    seen = {}
    for match in matches:
        # Create a key based on page and content
        key = (
            match.get("page", 0),
            match.get("content", match.get("cell_content", match.get("value", ""))),
        )
        if key not in seen or match["confidence"] > seen[key]["confidence"]:
            seen[key] = match

    return sorted(seen.values(), key=lambda x: -x["confidence"])


def generate_impact_report(all_file_matches: list, old_value: str,
                           new_value: str, parameter_name: str) -> dict:
    """
    Generate a full impact analysis report across all files.
    """
    total_matches = sum(fm["total_matches"] for fm in all_file_matches)
    affected_files = [fm for fm in all_file_matches if fm["total_matches"] > 0]

    report = {
        "change_request": {
            "parameter": parameter_name,
            "old_value": old_value,
            "new_value": new_value,
        },
        "summary": {
            "total_files_scanned": len(all_file_matches),
            "total_files_affected": len(affected_files),
            "total_occurrences": total_matches,
            "high_confidence_matches": sum(
                1 for fm in all_file_matches
                for m in fm.get("matches", [])
                if m["confidence"] >= 0.90
            ),
            "needs_review": sum(
                1 for fm in all_file_matches
                for m in fm.get("matches", [])
                if m["confidence"] < 0.85
            ),
        },
        "affected_files": affected_files,
    }

    return report


# ──────────────────────────────────────────────
# CLI for testing
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    extracted_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extracted")
    combined_file = os.path.join(extracted_dir, "all_extractions.json")

    if not os.path.exists(combined_file):
        print("No extraction data found. Run pdf_extractor.py first.")
        sys.exit(1)

    with open(combined_file, "r", encoding="utf-8") as f:
        all_extractions = json.load(f)

    # Default test: search for "16" (rim diameter)
    old_value = sys.argv[1] if len(sys.argv) > 1 else "16"
    new_value = sys.argv[2] if len(sys.argv) > 2 else "17"
    param_name = sys.argv[3] if len(sys.argv) > 3 else "Rim Diameter"

    print(f"\nChange Request: {param_name} = {old_value} -> {new_value}")
    print("=" * 60)

    all_matches = []
    for extraction in all_extractions:
        matches = find_matches(extraction, old_value, param_name)
        all_matches.append(matches)

        if matches["total_matches"] > 0:
            print(f"\n{matches['file']}: {matches['total_matches']} matches found")
            for m in matches["matches"]:
                conf_bar = "#" * int(m["confidence"] * 10)
                print(f"  [{conf_bar:<10}] {m['confidence']:.0%} | {m.get('context', 'N/A')}")
                content = m.get("content", m.get("cell_content", m.get("value", "")))
                print(f"    Content: {content[:80]}")

    # Generate report
    report = generate_impact_report(all_matches, old_value, new_value, param_name)

    print(f"\n{'=' * 60}")
    print(f"IMPACT SUMMARY")
    print(f"  Files scanned:  {report['summary']['total_files_scanned']}")
    print(f"  Files affected: {report['summary']['total_files_affected']}")
    print(f"  Total matches:  {report['summary']['total_occurrences']}")
    print(f"  High confidence: {report['summary']['high_confidence_matches']}")
    print(f"  Needs review:   {report['summary']['needs_review']}")

    # Save report
    report_file = os.path.join(extracted_dir, "impact_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Report saved to: {report_file}")
