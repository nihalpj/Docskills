# DocSLM pdf report — reportlab (certificate)
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

PRIMARY = HexColor(0x5B2C6F)
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

doc = SimpleDocTemplate("task_000547_doc.pdf", pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm)
story = [Paragraph("Certificate of Achievement", styles["title"]),
         Paragraph("Cobalt Financial · 2026-09", styles["meta"]),
         Spacer(1, 6), PageBreak()]
story.append(Paragraph("Next-Step Plan", styles["h1"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target. Cost pressure and regional competition remain the principal risks to monitor. We recommend expanding channel investment and rebalancing resourcing to sustain growth.", styles["body"]))
tbl = Table([["Item", "Revenue (k)", "YoY"], ["Sales", "424", "0.01"], ["Vertex Payroll", "861", "0.262"], ["Nimbus Storage", "834", "0.133"], ["Vertex Payroll", "499", "0.223"]], repeatRows=1)
tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor(0xCCCCCC)),
    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(0xFFFFFF)),
    ("FONTNAME", (0, 0), (-1, -1), FONT),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
]))
story.append(tbl)
story.append(Paragraph("Executive Overview", styles["h1"]))
story.append(Paragraph("Cost pressure and regional competition remain the principal risks to monitor.. The business delivered steady growth this quarter, with core KPIs on target.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.. Cost pressure and regional competition remain the principal risks to monitor.", styles["body"]))
story.append(Paragraph("Risks and Challenges", styles["h1"]))
story.append(Paragraph("We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.. Revenue concentration in the main product line increased and retention improved.", styles["body"]))
story.append(Paragraph("Cross-team efficiency rose and delivery lead times shortened versus last quarter.. Revenue concentration in the main product line increased and retention improved.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.", styles["body"]))
story.append(Paragraph("Key Project Updates", styles["h1"]))
story.append(Paragraph("The business delivered steady growth this quarter, with core KPIs on target.. Cost pressure and regional competition remain the principal risks to monitor.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("Cost pressure and regional competition remain the principal risks to monitor.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.. The business delivered steady growth this quarter, with core KPIs on target.", styles["body"]))
story.append(Paragraph("Performance Analysis", styles["h1"]))
story.append(Paragraph("Cost pressure and regional competition remain the principal risks to monitor.. We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.", styles["body"]))
story.append(Paragraph("We recommend expanding channel investment and rebalancing resourcing to sustain growth.. Cross-team efficiency rose and delivery lead times shortened versus last quarter.. Cost pressure and regional competition remain the principal risks to monitor.", styles["body"]))
doc.build(story)
print(json.dumps({"exit": 0, "artifact": "task_000547_doc.pdf"}))
