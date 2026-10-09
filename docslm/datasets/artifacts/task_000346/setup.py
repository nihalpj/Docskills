# setup: source report pdf (2 pages)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak

style = ParagraphStyle("b", fontName="Helvetica", fontSize=11, leading=15)
doc = SimpleDocTemplate("task_000346_src.pdf", pagesize=A4)
grid = TableStyle([("GRID", (0, 0), (-1, -1), 0.5, grey)])
story = [Paragraph("Key Project Updates", style), Paragraph("Revenue by item:", style),
         Table([["Item", "Revenue"], ["Orbit CRM", "120"], ["Pulse Dashboard", "240"]],
               style=grid),
         PageBreak(), Paragraph("Second page content for Key Project Updates.", style)]
doc.build(story)
print("ok")
