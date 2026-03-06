"""
Generate realistic engineering drawing PDFs for SolidWorks Change Analyzer POC.

Creates 5 PDFs simulating SolidWorks engineering drawing output:
1. TyreRim_PartDrawing.pdf - Part detail drawing with dimensions
2. WheelAssembly_Drawing.pdf - Assembly drawing with BOM reference
3. BOM_WheelAssembly.pdf - Bill of Materials spreadsheet
4. QualityInspection_Sheet.pdf - QC inspection checklist
5. SupplierSpec_TyreRim.pdf - Supplier specification document
"""

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# Common drawing elements
# ──────────────────────────────────────────────

def draw_title_block(c, width, height, part_name, part_number, rev, sheet, material="Aluminum Alloy 6061-T6"):
    """Draw a standard engineering drawing title block at bottom-right."""
    tb_w = 180 * mm
    tb_h = 45 * mm
    tb_x = width - tb_w - 10 * mm
    tb_y = 10 * mm

    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.rect(tb_x, tb_y, tb_w, tb_h)

    # Internal lines
    c.setLineWidth(0.5)
    mid_x = tb_x + tb_w / 2
    c.line(mid_x, tb_y, mid_x, tb_y + tb_h)
    for i in range(1, 4):
        y = tb_y + i * (tb_h / 4)
        c.line(tb_x, y, tb_x + tb_w, y)

    c.setFont("Helvetica", 6)
    c.drawString(tb_x + 3, tb_y + tb_h - 8, "PART NAME")
    c.drawString(mid_x + 3, tb_y + tb_h - 8, "DRAWN BY")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 * 3 - 8, "PART NUMBER")
    c.drawString(mid_x + 3, tb_y + tb_h / 4 * 3 - 8, "DATE")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 * 2 - 8, "MATERIAL")
    c.drawString(mid_x + 3, tb_y + tb_h / 4 * 2 - 8, "SCALE")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 - 8, "REV")
    c.drawString(mid_x + 3, tb_y + tb_h / 4 - 8, "SHEET")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(tb_x + 3, tb_y + tb_h - 18, part_name)
    c.drawString(mid_x + 3, tb_y + tb_h - 18, "K. DEEKONDA")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 * 3 - 18, part_number)
    c.drawString(mid_x + 3, tb_y + tb_h / 4 * 3 - 18, "2026-03-05")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 * 2 - 18, material)
    c.drawString(mid_x + 3, tb_y + tb_h / 4 * 2 - 18, "1:2")
    c.drawString(tb_x + 3, tb_y + tb_h / 4 - 18, rev)
    c.drawString(mid_x + 3, tb_y + tb_h / 4 - 18, sheet)

    # Company name
    c.setFont("Helvetica-Bold", 11)
    c.drawString(tb_x + 5, tb_y + tb_h + 5, "ACME AUTOMOTIVE COMPONENTS PVT. LTD.")


def draw_revision_table(c, x, y, revisions):
    """Draw a revision history table."""
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x, y + 5, "REVISION HISTORY")

    col_widths = [15 * mm, 60 * mm, 25 * mm, 25 * mm]
    row_h = 6 * mm
    headers = ["REV", "DESCRIPTION", "DATE", "APPROVED"]

    c.setLineWidth(0.5)
    # Header row
    cx = x
    for i, (hdr, w) in enumerate(zip(headers, col_widths)):
        c.rect(cx, y - row_h, w, row_h)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(cx + 2, y - row_h + 2, hdr)
        cx += w

    # Data rows
    for ri, rev in enumerate(revisions):
        cy = y - (ri + 2) * row_h
        cx = x
        c.setFont("Helvetica", 6)
        for vi, (val, w) in enumerate(zip(rev, col_widths)):
            c.rect(cx, cy, w, row_h)
            c.drawString(cx + 2, cy + 2, str(val))
            cx += w


def draw_border(c, width, height):
    """Draw standard drawing border with margin."""
    margin = 10 * mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    c.setLineWidth(0.5)
    c.rect(margin + 2, margin + 2, width - 2 * margin - 4, height - 2 * margin - 4)


def draw_dimension_line(c, x1, y1, x2, y2, text, offset=15, vertical=False):
    """Draw a dimension line with arrows and text."""
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.4)
    c.setFont("Helvetica", 8)

    if vertical:
        # Vertical dimension
        dx = x1 + offset
        c.line(x1, y1, dx + 5, y1)  # extension line 1
        c.line(x2, y2, dx + 5, y2)  # extension line 2
        c.line(dx, y1, dx, y2)  # dimension line

        # Arrows
        c.line(dx - 2, y1 + 5, dx, y1)
        c.line(dx + 2, y1 + 5, dx, y1)
        c.line(dx - 2, y2 - 5, dx, y2)
        c.line(dx + 2, y2 - 5, dx, y2)

        # Text
        c.saveState()
        c.translate(dx - 3, (y1 + y2) / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, text)
        c.restoreState()
    else:
        # Horizontal dimension
        dy = y1 + offset
        c.line(x1, y1, x1, dy + 5)  # extension line 1
        c.line(x2, y2, x2, dy + 5)  # extension line 2
        c.line(x1, dy, x2, dy)  # dimension line

        # Arrows
        c.line(x1 + 5, dy - 2, x1, dy)
        c.line(x1 + 5, dy + 2, x1, dy)
        c.line(x2 - 5, dy - 2, x2, dy)
        c.line(x2 - 5, dy + 2, x2, dy)

        # Text
        c.drawCentredString((x1 + x2) / 2, dy + 3, text)


# ──────────────────────────────────────────────
# PDF 1: Tyre Rim Part Drawing
# ──────────────────────────────────────────────

def create_tyre_rim_part_drawing():
    filepath = os.path.join(OUTPUT_DIR, "TyreRim_PartDrawing.pdf")
    width, height = landscape(A3)
    c = canvas.Canvas(filepath, pagesize=landscape(A3))

    draw_border(c, width, height)

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 30 * mm, "TYRE RIM - DETAIL DRAWING")

    # ── Front View (circle representing rim cross-section) ──
    cx_front = 200 * mm
    cy_front = 200 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx_front, cy_front + 110 * mm, "FRONT VIEW")

    # Outer rim circle
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.0)
    c.circle(cx_front, cy_front, 95 * mm)  # Outer diameter

    # Inner hub circle
    c.circle(cx_front, cy_front, 40 * mm)

    # Bolt holes (5 holes)
    import math
    for i in range(5):
        angle = math.radians(i * 72 + 90)
        hx = cx_front + 60 * mm * math.cos(angle)
        hy = cy_front + 60 * mm * math.sin(angle)
        c.circle(hx, hy, 7 * mm)

    # Center hole
    c.circle(cx_front, cy_front, 15 * mm)

    # Spokes (5 spokes)
    c.setLineWidth(0.5)
    for i in range(5):
        angle = math.radians(i * 72 + 54)
        sx = cx_front + 42 * mm * math.cos(angle)
        sy = cy_front + 42 * mm * math.sin(angle)
        ex = cx_front + 90 * mm * math.cos(angle)
        ey = cy_front + 90 * mm * math.sin(angle)
        c.line(sx, sy, ex, ey)

    # Dimensions on front view
    # Outer diameter
    draw_dimension_line(c,
                        cx_front - 95 * mm, cy_front,
                        cx_front + 95 * mm, cy_front,
                        "Ø406.4 (16.00 in)", offset=115 * mm)

    # Bolt circle diameter
    draw_dimension_line(c,
                        cx_front - 60 * mm, cy_front - 70 * mm,
                        cx_front + 60 * mm, cy_front - 70 * mm,
                        "PCD 120.00 (BOLT CIRCLE)", offset=-20 * mm)

    # Center bore
    c.setFont("Helvetica", 7)
    c.drawString(cx_front + 17 * mm, cy_front + 2, "Ø67.1 (CENTER BORE)")

    # Bolt hole callout
    c.drawString(cx_front + 70 * mm, cy_front + 75 * mm, "5X Ø14.0 BOLT HOLES")
    c.drawString(cx_front + 70 * mm, cy_front + 68 * mm, "EQUALLY SPACED ON PCD 120")

    # ── Side/Section View ──
    sv_x = 500 * mm
    sv_y = 200 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(sv_x, sv_y + 80 * mm, "SECTION VIEW A-A")

    # Side profile of rim (simplified trapezoid shape)
    c.setLineWidth(1.0)
    rim_profile = [
        (sv_x - 50 * mm, sv_y - 60 * mm),
        (sv_x - 40 * mm, sv_y + 60 * mm),
        (sv_x + 40 * mm, sv_y + 60 * mm),
        (sv_x + 50 * mm, sv_y - 60 * mm),
    ]
    c.lines([(rim_profile[i][0], rim_profile[i][1],
              rim_profile[(i + 1) % 4][0], rim_profile[(i + 1) % 4][1])
             for i in range(4)])

    # Inner lip
    c.setLineWidth(0.5)
    c.line(sv_x - 35 * mm, sv_y + 60 * mm, sv_x - 35 * mm, sv_y + 50 * mm)
    c.line(sv_x + 35 * mm, sv_y + 60 * mm, sv_x + 35 * mm, sv_y + 50 * mm)

    # Hub mounting surface
    c.line(sv_x - 30 * mm, sv_y - 60 * mm, sv_x - 30 * mm, sv_y - 45 * mm)
    c.line(sv_x + 30 * mm, sv_y - 60 * mm, sv_x + 30 * mm, sv_y - 45 * mm)
    c.line(sv_x - 30 * mm, sv_y - 45 * mm, sv_x + 30 * mm, sv_y - 45 * mm)

    # Dimensions on section view
    # Width
    draw_dimension_line(c,
                        sv_x - 50 * mm, sv_y - 60 * mm,
                        sv_x + 50 * mm, sv_y - 60 * mm,
                        "203.2 (8.00 in) RIM WIDTH", offset=-25 * mm)

    # Height/depth
    draw_dimension_line(c,
                        sv_x + 50 * mm, sv_y - 60 * mm,
                        sv_x + 40 * mm, sv_y + 60 * mm,
                        "120.0 RIM DEPTH", offset=25 * mm, vertical=True)

    # Lip thickness
    c.setFont("Helvetica", 7)
    c.drawString(sv_x - 65 * mm, sv_y + 55 * mm, "FLANGE: 3.5 mm")
    c.drawString(sv_x - 65 * mm, sv_y - 55 * mm, "OFFSET: 45.0 mm (ET45)")

    # ── Specifications Table ──
    spec_x = 15 * mm
    spec_y = 100 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(spec_x + 5, spec_y + 5, "SPECIFICATIONS")

    specs = [
        ["PARAMETER", "VALUE", "TOLERANCE"],
        ["Rim Diameter", "16.00 inches (406.4 mm)", "± 0.05 mm"],
        ["Rim Width", "8.00 inches (203.2 mm)", "± 0.05 mm"],
        ["Bolt Pattern", "5 x 120 mm PCD", "-"],
        ["Center Bore", "Ø67.1 mm", "+0.00 / -0.02 mm"],
        ["Bolt Hole Dia", "Ø14.0 mm", "± 0.02 mm"],
        ["Offset (ET)", "45.0 mm", "± 0.5 mm"],
        ["Weight (Target)", "9.5 kg", "± 0.3 kg"],
        ["Material", "Aluminum 6061-T6", "-"],
        ["Surface Finish", "Ra 1.6 μm (machined)", "-"],
        ["Number of Spokes", "5", "-"],
    ]

    t = Table(specs, colWidths=[50 * mm, 55 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t.wrapOn(c, 150 * mm, 200 * mm)
    t.drawOn(c, spec_x, spec_y - len(specs) * 5.5 * mm)

    # Notes
    c.setFont("Helvetica-Bold", 8)
    c.drawString(15 * mm, 35 * mm, "NOTES:")
    c.setFont("Helvetica", 7)
    c.drawString(15 * mm, 28 * mm, "1. ALL DIMENSIONS IN MM UNLESS OTHERWISE STATED")
    c.drawString(15 * mm, 22 * mm, "2. RIM DIAMETER 16 INCHES - VERIFY AGAINST 3D MODEL REF: MDL-TR-001")
    c.drawString(15 * mm, 16 * mm, "3. BREAK ALL SHARP EDGES 0.5 mm MAX")
    c.drawString(15 * mm, 10 * mm, "4. SURFACE TREATMENT: ANODIZE PER MIL-A-8625 TYPE III")

    # Revision table
    revisions = [
        ["A", "INITIAL RELEASE", "2025-01-15", "JK"],
        ["B", "UPDATED RIM DIA TO 16.00 IN", "2025-03-22", "JK"],
        ["C", "ADDED BOLT HOLE TOLERANCES", "2025-06-10", "RD"],
        ["D", "CHANGED SPOKE COUNT FROM 6 TO 5", "2025-09-01", "JK"],
        ["E", "UPDATED SURFACE FINISH SPEC", "2026-01-20", "RD"],
    ]
    draw_revision_table(c, width - 140 * mm, height - 25 * mm, revisions)

    # Title block
    draw_title_block(c, width, height, "TYRE RIM 16 INCH", "TR-16-001", "E", "1 OF 1")

    c.save()
    print(f"[OK] Created: {filepath}")


# ──────────────────────────────────────────────
# PDF 2: Wheel Assembly Drawing
# ──────────────────────────────────────────────

def create_wheel_assembly_drawing():
    filepath = os.path.join(OUTPUT_DIR, "WheelAssembly_Drawing.pdf")
    width, height = landscape(A3)
    c = canvas.Canvas(filepath, pagesize=landscape(A3))

    draw_border(c, width, height)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 30 * mm, "WHEEL ASSEMBLY - GENERAL ARRANGEMENT")

    # ── Assembly side view ──
    cx = 250 * mm
    cy = 200 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, cy + 100 * mm, "SIDE VIEW")

    # Tyre cross-section (outer)
    c.setLineWidth(1.5)
    c.circle(cx, cy, 100 * mm)  # Tyre outer

    # Rim (inner circle)
    c.setLineWidth(1.0)
    c.circle(cx, cy, 60 * mm)  # Rim outer edge area

    # Hub
    c.circle(cx, cy, 25 * mm)

    # Center
    c.circle(cx, cy, 8 * mm)

    # Balloon callouts
    callouts = [
        (cx + 75 * mm, cy + 75 * mm, "1", "TYRE 225/50R16"),
        (cx + 50 * mm, cy - 70 * mm, "2", "RIM 16 x 8J"),
        (cx - 80 * mm, cy + 50 * mm, "3", "HUB ASSEMBLY"),
        (cx - 70 * mm, cy - 50 * mm, "4", "LUG NUT M14x1.5 (x5)"),
        (cx + 85 * mm, cy - 30 * mm, "5", "VALVE STEM"),
    ]

    for bx, by, num, label in callouts:
        c.setLineWidth(0.5)
        c.circle(bx, by, 5 * mm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(bx, by - 2, num)
        c.setFont("Helvetica", 7)
        c.drawString(bx + 8 * mm, by - 2, label)

        # Leader line
        c.setLineWidth(0.3)
        c.setDash(1, 2)
        c.line(bx, by, cx + (bx - cx) * 0.4, cy + (by - cy) * 0.4)
        c.setDash()

    # Overall diameter dimension
    draw_dimension_line(c,
                        cx - 100 * mm, cy,
                        cx + 100 * mm, cy,
                        "Ø632.0 OVERALL (TYRE + RIM)", offset=115 * mm)

    # Rim diameter callout
    draw_dimension_line(c,
                        cx - 60 * mm, cy - 80 * mm,
                        cx + 60 * mm, cy - 80 * mm,
                        "RIM Ø406.4 (16.00 in)", offset=-20 * mm)

    # ── BOM Table ──
    bom_x = 480 * mm
    bom_y = 340 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(bom_x, bom_y + 5, "ASSEMBLY BILL OF MATERIALS")

    bom_data = [
        ["ITEM", "PART NUMBER", "DESCRIPTION", "QTY", "MATERIAL"],
        ["1", "TR-225-50R16", "TYRE 225/50R16", "1", "RUBBER COMPOUND"],
        ["2", "TR-16-001", "ALLOY RIM 16 x 8J", "1", "AL 6061-T6"],
        ["3", "HA-005", "HUB ASSEMBLY", "1", "STEEL AISI 4140"],
        ["4", "LN-M14-15", "LUG NUT M14x1.5", "5", "STEEL GR 10.9"],
        ["5", "VS-STD-01", "VALVE STEM (TUBELESS)", "1", "BRASS / RUBBER"],
    ]

    t = Table(bom_data, colWidths=[12 * mm, 30 * mm, 40 * mm, 12 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t.wrapOn(c, 200 * mm, 200 * mm)
    t.drawOn(c, bom_x, bom_y - len(bom_data) * 5.5 * mm)

    # Assembly specifications
    c.setFont("Helvetica-Bold", 9)
    c.drawString(480 * mm, 250 * mm, "ASSEMBLY SPECIFICATIONS")
    c.setFont("Helvetica", 7)
    specs_text = [
        "Overall Diameter (with tyre): 632.0 mm",
        "Rim Diameter: 16.00 inches (406.4 mm)",
        "Rim Width: 8.00 inches (203.2 mm)",
        "Tyre Section Width: 225 mm",
        "Tyre Aspect Ratio: 50%",
        "Tyre Type: Radial (R)",
        "Load Rating: 680 kg per wheel",
        "Lug Torque: 120 Nm",
        "Bolt Pattern: 5 x 120 PCD",
        "Assembly Weight: 21.5 kg (rim 9.5 kg + tyre 12.0 kg)",
    ]
    for i, spec in enumerate(specs_text):
        c.drawString(480 * mm, 243 * mm - i * 5.5 * mm, spec)

    # Notes
    c.setFont("Helvetica-Bold", 8)
    c.drawString(15 * mm, 50 * mm, "ASSEMBLY NOTES:")
    c.setFont("Helvetica", 7)
    c.drawString(15 * mm, 43 * mm, "1. TYRE TO BE MOUNTED ON 16 INCH RIM WITH BEAD SEALER")
    c.drawString(15 * mm, 37 * mm, "2. INFLATE TO 32 PSI (2.2 BAR) COLD PRESSURE")
    c.drawString(15 * mm, 31 * mm, "3. TORQUE LUG NUTS TO 120 Nm IN STAR PATTERN")
    c.drawString(15 * mm, 25 * mm, "4. VERIFY RIM RUNOUT < 0.5 mm TIR AFTER ASSEMBLY")
    c.drawString(15 * mm, 19 * mm, "5. WHEEL ASSEMBLY FOR 16 INCH RIM CONFIGURATION ONLY")

    # Revision table
    revisions = [
        ["A", "INITIAL ASSEMBLY DRAWING", "2025-02-01", "JK"],
        ["B", "UPDATED RIM SIZE TO 16 INCH", "2025-04-15", "RD"],
        ["C", "ADDED LUG TORQUE SPEC", "2025-08-20", "JK"],
    ]
    draw_revision_table(c, width - 140 * mm, height - 25 * mm, revisions)

    draw_title_block(c, width, height, "WHEEL ASSEMBLY 16 IN", "WA-16-001", "C", "1 OF 1",
                     material="MULTI (SEE BOM)")

    c.save()
    print(f"[OK] Created: {filepath}")


# ──────────────────────────────────────────────
# PDF 3: Bill of Materials
# ──────────────────────────────────────────────

def create_bom():
    filepath = os.path.join(OUTPUT_DIR, "BOM_WheelAssembly.pdf")
    width, height = landscape(A3)
    c = canvas.Canvas(filepath, pagesize=landscape(A3))

    draw_border(c, width, height)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 30 * mm, "BILL OF MATERIALS - WHEEL ASSEMBLY (16 INCH CONFIGURATION)")

    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, height - 40 * mm, "Project: ACME Sedan MY2026  |  Assembly: WA-16-001  |  Configuration: 16 INCH RIM")

    # Main BOM table
    bom_x = 20 * mm
    bom_y = height - 55 * mm

    bom_data = [
        ["ITEM", "PART NUMBER", "DESCRIPTION", "REVISION", "QTY", "UNIT", "MATERIAL", "WEIGHT (kg)", "SUPPLIER", "UNIT COST (₹)", "STATUS"],
        ["1", "TR-16-001", "ALLOY RIM 16 x 8J", "E", "4", "EA", "AL 6061-T6", "9.5", "ALCOA INDIA", "4,500.00", "RELEASED"],
        ["2", "TR-225-50R16", "TYRE 225/50R16 97W", "B", "4", "EA", "RUBBER COMP", "12.0", "MRF LTD", "6,200.00", "RELEASED"],
        ["3", "HA-005", "HUB ASSEMBLY (FOR 16\" RIM)", "C", "4", "EA", "AISI 4140", "3.2", "BHARAT FORGE", "2,800.00", "RELEASED"],
        ["4", "LN-M14-15", "LUG NUT M14x1.5 GR10.9", "A", "20", "EA", "STEEL 10.9", "0.045", "SUNDRAM FAST", "45.00", "RELEASED"],
        ["5", "VS-STD-01", "VALVE STEM (TUBELESS)", "A", "4", "EA", "BRASS/RUBBER", "0.015", "SCHRADER", "120.00", "RELEASED"],
        ["6", "WB-16-01", "WHEEL BALANCE WEIGHT KIT", "A", "4", "SET", "ZINC ALLOY", "0.060", "WEGMANN AUTO", "85.00", "RELEASED"],
        ["7", "TP-16-SEN", "TPMS SENSOR (16\" RIM)", "B", "4", "EA", "ELECTRONIC", "0.035", "CONTINENTAL", "950.00", "RELEASED"],
        ["8", "CC-16-ABS", "CENTER CAP (16\" RIM)", "A", "4", "EA", "ABS PLASTIC", "0.025", "ACME MOLDING", "150.00", "PENDING"],
        ["9", "WS-M14-FL", "WHEEL STUD M14 FLANGED", "A", "20", "EA", "STEEL 12.9", "0.085", "KAMAX", "65.00", "RELEASED"],
        ["10", "RP-16-KIT", "REPAIR KIT (16\" TYRE)", "A", "1", "SET", "MIXED", "0.500", "SLIME AUTO", "350.00", "RELEASED"],
    ]

    col_widths = [12*mm, 25*mm, 42*mm, 15*mm, 10*mm, 12*mm, 25*mm, 20*mm, 28*mm, 22*mm, 18*mm]

    t = Table(bom_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.15, 0.15)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
    ]))
    t.wrapOn(c, width - 40 * mm, 200 * mm)
    t.drawOn(c, bom_x, bom_y - len(bom_data) * 5.5 * mm)

    # Summary
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, 120 * mm, "ASSEMBLY SUMMARY")

    summary = [
        ["PARAMETER", "VALUE"],
        ["Total Assembly Weight (per wheel)", "24.8 kg"],
        ["Total Assembly Weight (4 wheels)", "99.2 kg"],
        ["Rim Configuration", "16 x 8J"],
        ["Rim Diameter", "16 inches"],
        ["Total Unique Parts", "10"],
        ["Total Part Count (4 wheels)", "65 items"],
        ["Estimated Cost per Wheel", "₹15,265.00"],
        ["Estimated Cost (4 wheels)", "₹61,060.00"],
    ]

    t2 = Table(summary, colWidths=[55 * mm, 45 * mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t2.wrapOn(c, 200 * mm, 200 * mm)
    t2.drawOn(c, 20 * mm, 120 * mm - len(summary) * 5.5 * mm)

    # Notes
    c.setFont("Helvetica-Bold", 8)
    c.drawString(250 * mm, 120 * mm, "BOM NOTES:")
    c.setFont("Helvetica", 7)
    c.drawString(250 * mm, 113 * mm, "1. ALL QUANTITIES ARE PER VEHICLE (4 WHEEL POSITIONS)")
    c.drawString(250 * mm, 107 * mm, "2. THIS BOM IS FOR 16 INCH RIM CONFIGURATION ONLY")
    c.drawString(250 * mm, 101 * mm, "3. TPMS SENSOR CALIBRATED FOR 16\" RIM DIAMETER")
    c.drawString(250 * mm, 95 * mm, "4. CENTER CAP DESIGN SPECIFIC TO 16 INCH RIM MODEL")
    c.drawString(250 * mm, 89 * mm, "5. PRICES AS OF Q1 2026, SUBJECT TO REVISION")

    # Revision table
    revisions = [
        ["A", "INITIAL BOM RELEASE", "2025-02-10", "JK"],
        ["B", "UPDATED FOR 16\" RIM CONFIG", "2025-05-01", "RD"],
        ["C", "ADDED TPMS SENSOR FOR 16\" RIM", "2025-11-15", "JK"],
        ["D", "ADDED CENTER CAP & REPAIR KIT", "2026-02-01", "RD"],
    ]
    draw_revision_table(c, width - 140 * mm, height - 25 * mm, revisions)

    draw_title_block(c, width, height, "BOM - WHEEL ASSY 16 IN", "BOM-WA-16-001", "D", "1 OF 1",
                     material="MULTI (SEE TABLE)")

    c.save()
    print(f"[OK] Created: {filepath}")


# ──────────────────────────────────────────────
# PDF 4: Quality Inspection Sheet
# ──────────────────────────────────────────────

def create_quality_inspection():
    filepath = os.path.join(OUTPUT_DIR, "QualityInspection_Sheet.pdf")
    width, height = landscape(A3)
    c = canvas.Canvas(filepath, pagesize=landscape(A3))

    draw_border(c, width, height)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 30 * mm, "INCOMING QUALITY INSPECTION REPORT")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 38 * mm, "PART: ALLOY RIM 16 x 8J  |  PART NO: TR-16-001  |  SUPPLIER: ALCOA INDIA")

    # Inspection checklist
    insp_y = height - 55 * mm

    insp_data = [
        ["#", "INSPECTION PARAMETER", "SPECIFICATION", "NOMINAL", "TOLERANCE", "MIN", "MAX", "MEASURED", "RESULT", "INSTRUMENT"],
        ["1", "Rim Diameter", "As per DWG TR-16-001", "406.4 mm\n(16.00 in)", "± 0.05 mm", "406.35", "406.45", "", "☐ PASS\n☐ FAIL", "CMM"],
        ["2", "Rim Width", "As per DWG TR-16-001", "203.2 mm\n(8.00 in)", "± 0.05 mm", "203.15", "203.25", "", "☐ PASS\n☐ FAIL", "CMM"],
        ["3", "PCD (Bolt Circle)", "As per DWG TR-16-001", "120.00 mm", "± 0.03 mm", "119.97", "120.03", "", "☐ PASS\n☐ FAIL", "CMM"],
        ["4", "Center Bore Dia", "As per DWG TR-16-001", "67.10 mm", "+0.00/-0.02", "67.08", "67.10", "", "☐ PASS\n☐ FAIL", "BORE GAUGE"],
        ["5", "Bolt Hole Dia (x5)", "As per DWG TR-16-001", "14.00 mm", "± 0.02 mm", "13.98", "14.02", "", "☐ PASS\n☐ FAIL", "PIN GAUGE"],
        ["6", "Offset (ET)", "As per DWG TR-16-001", "45.0 mm", "± 0.5 mm", "44.5", "45.5", "", "☐ PASS\n☐ FAIL", "CMM"],
        ["7", "Radial Runout", "ISO 1101", "0.00 mm", "MAX 0.3 mm", "0.00", "0.30", "", "☐ PASS\n☐ FAIL", "DIAL GAUGE"],
        ["8", "Lateral Runout", "ISO 1101", "0.00 mm", "MAX 0.25 mm", "0.00", "0.25", "", "☐ PASS\n☐ FAIL", "DIAL GAUGE"],
        ["9", "Weight", "As per BOM", "9.50 kg", "± 0.3 kg", "9.20", "9.80", "", "☐ PASS\n☐ FAIL", "SCALE"],
        ["10", "Surface Finish", "MIL-A-8625", "Ra 1.6 μm", "MAX Ra 2.0", "-", "2.0", "", "☐ PASS\n☐ FAIL", "PROFILOMETER"],
        ["11", "Visual Inspection", "No cracks, porosity,\nor casting defects", "ZERO\nDEFECTS", "-", "-", "-", "", "☐ PASS\n☐ FAIL", "VISUAL"],
        ["12", "Hardness Test", "ASTM E18", "95 HRB", "± 5 HRB", "90", "100", "", "☐ PASS\n☐ FAIL", "HARDNESS\nTESTER"],
    ]

    col_widths = [8*mm, 32*mm, 32*mm, 22*mm, 20*mm, 14*mm, 14*mm, 18*mm, 16*mm, 22*mm]

    t = Table(insp_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.15, 0.15)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
    ]))
    t.wrapOn(c, width - 40 * mm, 300 * mm)
    t.drawOn(c, 15 * mm, insp_y - len(insp_data) * 8 * mm)

    # Sign-off section
    sign_y = 65 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(15 * mm, sign_y, "INSPECTION SIGN-OFF")

    c.setFont("Helvetica", 7)
    c.drawString(15 * mm, sign_y - 12, "Inspector Name: ____________________    Signature: ____________________    Date: ____/____/______")
    c.drawString(15 * mm, sign_y - 24, "QC Manager:     ____________________    Signature: ____________________    Date: ____/____/______")
    c.drawString(15 * mm, sign_y - 36, "Lot Size: ________    Sample Size: ________    AQL: 1.0    Sampling Plan: ISO 2859-1 Level II")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(15 * mm, sign_y - 52, "NOTES:")
    c.setFont("Helvetica", 7)
    c.drawString(15 * mm, sign_y - 60, "1. THIS INSPECTION SHEET IS FOR 16 INCH RIM (PART NO: TR-16-001) ONLY")
    c.drawString(15 * mm, sign_y - 68, "2. ALL DIMENSIONS REFERENCE DRAWING TR-16-001 REV E")
    c.drawString(15 * mm, sign_y - 76, "3. REJECT ENTIRE LOT IF ANY CRITICAL DIMENSION (ITEMS 1-6) FAILS")

    revisions = [
        ["A", "INITIAL QC SHEET FOR 16\" RIM", "2025-03-01", "QM"],
        ["B", "ADDED HARDNESS TEST FOR 16\" RIM", "2025-07-15", "QM"],
        ["C", "UPDATED TOLERANCES PER ECO-2025-089", "2026-01-10", "QM"],
    ]
    draw_revision_table(c, width - 140 * mm, height - 25 * mm, revisions)

    draw_title_block(c, width, height, "QC INSP - RIM 16 INCH", "QC-TR-16-001", "C", "1 OF 1",
                     material="N/A (INSPECTION DOC)")

    c.save()
    print(f"[OK] Created: {filepath}")


# ──────────────────────────────────────────────
# PDF 5: Supplier Specification
# ──────────────────────────────────────────────

def create_supplier_spec():
    filepath = os.path.join(OUTPUT_DIR, "SupplierSpec_TyreRim.pdf")
    width, height = landscape(A3)
    c = canvas.Canvas(filepath, pagesize=landscape(A3))

    draw_border(c, width, height)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 30 * mm, "SUPPLIER SPECIFICATION - ALLOY RIM 16 INCH")

    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, height - 42 * mm,
                 "SUPPLIER: ALCOA INDIA PVT LTD  |  PURCHASE ORDER REF: PO-2026-TR16-0045  |  DELIVERY: CIF PUNE")

    # Section 1: General specs
    y = height - 60 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y, "1. PRODUCT SPECIFICATION")

    spec_data = [
        ["PARAMETER", "REQUIREMENT", "REFERENCE"],
        ["Product", "Alloy Wheel Rim", "As per 3D Model MDL-TR-001"],
        ["Rim Diameter", "16.00 inches (406.4 mm)", "Drawing TR-16-001 Rev E"],
        ["Rim Width", "8.00 inches (203.2 mm)", "Drawing TR-16-001 Rev E"],
        ["Rim Type", "J-Type Flange", "JWL Standard"],
        ["Bolt Pattern", "5 x 120 mm PCD", "Drawing TR-16-001 Rev E"],
        ["Center Bore", "67.1 mm (Hub-Centric)", "Drawing TR-16-001 Rev E"],
        ["Offset", "ET45 (45.0 mm)", "Drawing TR-16-001 Rev E"],
        ["Number of Spokes", "5", "Drawing TR-16-001 Rev E"],
        ["Weight (per rim)", "9.5 kg (max 9.8 kg)", "BOM-WA-16-001"],
    ]

    t = Table(spec_data, colWidths=[40 * mm, 50 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t.wrapOn(c, 200 * mm, 200 * mm)
    t.drawOn(c, 15 * mm, y - len(spec_data) * 5.5 * mm - 5)

    # Section 2: Material specs
    y2 = y - len(spec_data) * 5.5 * mm - 25 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y2, "2. MATERIAL SPECIFICATION")

    mat_data = [
        ["PROPERTY", "REQUIREMENT", "TEST METHOD"],
        ["Alloy Grade", "6061-T6", "ASTM B221"],
        ["Tensile Strength", "≥ 310 MPa", "ASTM E8"],
        ["Yield Strength", "≥ 276 MPa", "ASTM E8"],
        ["Elongation", "≥ 12%", "ASTM E8"],
        ["Hardness", "95 ± 5 HRB", "ASTM E18"],
        ["Density", "2.70 g/cm³", "ASTM B311"],
    ]

    t2 = Table(mat_data, colWidths=[40 * mm, 40 * mm, 40 * mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t2.wrapOn(c, 200 * mm, 200 * mm)
    t2.drawOn(c, 15 * mm, y2 - len(mat_data) * 5.5 * mm - 5)

    # Section 3: Packaging for 16" rim
    y3 = y2 - len(mat_data) * 5.5 * mm - 25 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y3, "3. PACKAGING & SHIPPING (FOR 16 INCH RIM)")

    c.setFont("Helvetica", 7)
    pkg_lines = [
        "3.1  Each 16\" rim to be individually wrapped in VCI paper",
        "3.2  Carton box size: 450 x 450 x 250 mm (sized for 16\" rim)",
        "3.3  Maximum stacking: 4 cartons high",
        "3.4  Pallet configuration: 16 rims per pallet (4x4 arrangement)",
        "3.5  Each carton labeled with: Part No TR-16-001, Lot No, Date of Mfg",
        "3.6  Include material test certificate per lot",
    ]
    for i, line in enumerate(pkg_lines):
        c.drawString(15 * mm, y3 - 10 - i * 5.5 * mm, line)

    # Right side - delivery schedule
    c.setFont("Helvetica-Bold", 10)
    c.drawString(330 * mm, height - 60 * mm, "4. DELIVERY SCHEDULE (16\" RIM)")

    del_data = [
        ["MONTH", "QTY (UNITS)", "PART NUMBER", "DESTINATION"],
        ["APR 2026", "2,000", "TR-16-001", "ACME PUNE PLANT"],
        ["MAY 2026", "2,500", "TR-16-001", "ACME PUNE PLANT"],
        ["JUN 2026", "3,000", "TR-16-001", "ACME PUNE PLANT"],
        ["JUL 2026", "3,000", "TR-16-001", "ACME PUNE PLANT"],
        ["AUG 2026", "2,500", "TR-16-001", "ACME PUNE PLANT"],
        ["SEP 2026", "2,000", "TR-16-001", "ACME PUNE PLANT"],
    ]

    t3 = Table(del_data, colWidths=[25 * mm, 22 * mm, 25 * mm, 35 * mm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t3.wrapOn(c, 200 * mm, 200 * mm)
    t3.drawOn(c, 330 * mm, height - 65 * mm - len(del_data) * 5.5 * mm)

    # Pricing
    c.setFont("Helvetica-Bold", 10)
    c.drawString(330 * mm, height - 130 * mm, "5. PRICING (16\" RIM)")

    price_data = [
        ["DESCRIPTION", "UNIT PRICE (₹)", "ANNUAL QTY", "ANNUAL VALUE (₹)"],
        ["Alloy Rim 16x8J (TR-16-001)", "4,500.00", "15,000", "6,75,00,000"],
        ["Tooling (one-time)", "12,00,000", "1", "12,00,000"],
        ["Packaging (per unit)", "85.00", "15,000", "12,75,000"],
    ]

    t4 = Table(price_data, colWidths=[45 * mm, 25 * mm, 22 * mm, 30 * mm])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t4.wrapOn(c, 200 * mm, 200 * mm)
    t4.drawOn(c, 330 * mm, height - 135 * mm - len(price_data) * 5.5 * mm)

    # Notes
    c.setFont("Helvetica-Bold", 8)
    c.drawString(330 * mm, 80 * mm, "SUPPLIER NOTES:")
    c.setFont("Helvetica", 7)
    c.drawString(330 * mm, 73 * mm, "1. THIS SPECIFICATION IS FOR 16 INCH RIM ONLY")
    c.drawString(330 * mm, 67 * mm, "2. SUPPLIER TO MAINTAIN 16\" RIM TOOLING IN GOOD CONDITION")
    c.drawString(330 * mm, 61 * mm, "3. ANY DEVIATION FROM 16\" SPEC REQUIRES WRITTEN APPROVAL")
    c.drawString(330 * mm, 55 * mm, "4. PPAP SUBMISSION REQUIRED BEFORE FIRST DELIVERY")
    c.drawString(330 * mm, 49 * mm, "5. REFER TO DRAWING TR-16-001 REV E FOR ALL DIMENSIONS")

    revisions = [
        ["A", "INITIAL SUPPLIER SPEC FOR 16\" RIM", "2025-03-15", "PURCH"],
        ["B", "UPDATED PRICING FOR 16\" RIM", "2025-09-01", "PURCH"],
        ["C", "ADDED DELIVERY SCHEDULE 2026", "2026-01-15", "PURCH"],
    ]
    draw_revision_table(c, width - 140 * mm, height - 25 * mm, revisions)

    draw_title_block(c, width, height, "SUPPLIER SPEC RIM 16\"", "SS-TR-16-001", "C", "1 OF 1",
                     material="AL 6061-T6 (REF)")

    c.save()
    print(f"[OK] Created: {filepath}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating test engineering drawing PDFs...")
    print(f"Output directory: {OUTPUT_DIR}\n")

    create_tyre_rim_part_drawing()
    create_wheel_assembly_drawing()
    create_bom()
    create_quality_inspection()
    create_supplier_spec()

    print(f"\n[OK] All 5 PDFs generated in: {OUTPUT_DIR}")
    print("\nTest scenario: Change 'Rim Diameter' from 16 inches to 17 inches")
    print("The AI should find '16' references across ALL 5 documents.")
