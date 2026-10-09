# DocSLM pdf report — reportlab (business-report)
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

PRIMARY = HexColor(0x7B3B00)
FONT = "Helvetica"

styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=20, leading=26,
                            textColor=PRIMARY, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=15, leading=20,
                         textColor=PRIMARY, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=10.5, leading=15, spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName=FONT, fontSize=9.5, leading=13,
                           textColor=HexColor(0x666666)),
}

doc = SimpleDocTemplate("task_000607_doc.pdf", pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm)
story = [Paragraph("Monthly Business Analysis Report", styles["title"]),
         Paragraph("Helios Energy · 2026-09", styles["meta"]),
         Spacer(1, 6), PageBreak()]
story.append(Paragraph("Next-Step Plan", styles["h1"]))
story.append(Paragraph("Revenue concentration in the main product line increased and retention improved. Cost pressure and regional competition remain the principal risks to monitor. We recommend expanding channel investment and rebalancing resourcing to sustain growth.", styles["body"]))
tbl = Table([["Item", "Revenue (k)", "YoY"], ["Nimbus Storage", "597", "-0.061"], ["Sales", "279", "0.01"], ["Marketing", "403", "0.433"], ["People Ops", "784", "0.387"]], repeatRows=1)
tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor(0xCCCCCC)),
    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(0xFFFFFF)),
    ("FONTNAME", (0, 0), (-1, -1), FONT),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
]))
story.append(tbl)
story.append(Paragraph("Key Project Updates", styles["h1"]))
story.append(Paragraph("Revenue concentration in the main product line increased and retention improved.. The business delivered steady growth this quarter, with core KPIs on target.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.. Revenue concentration in the main product line increased and retention improved.", styles["body"]))
story.append(Paragraph("Summary and Recommendations", styles["h1"]))
story.append(Paragraph("Cross-team efficiency rose and delivery lead times shortened versus last quarter.. The business delivered steady growth this quarter, with core KPIs on target.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.", styles["body"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("Executive Overview", styles["h1"]))
story.append(Paragraph("Cross-team efficiency rose and delivery lead times shortened versus last quarter.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Revenue concentration in the main product line increased and retention improved.", styles["body"]))
story.append(Paragraph("We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Revenue concentration in the main product line increased and retention improved.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("Risks and Challenges", styles["h1"]))
story.append(Paragraph("We recommend expanding channel investment and rebalancing resourcing to sustain growth.. The business delivered steady growth this quarter, with core KPIs on target.. Revenue concentration in the main product line increased and retention improved.", styles["body"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target.. Revenue concentration in the main product line increased and retention improved.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.", styles["body"]))
doc.build(story)
print(json.dumps({"exit": 0, "artifact": "task_000607_doc.pdf"}))
