# setup: pdf with an embedded image
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image

img = PILImage.new("RGB", (200, 120), (31, 78, 121))
img.save("task_000824_chart.png")
doc = SimpleDocTemplate("task_000824_img.pdf", pagesize=A4)
doc.build([Image("task_000824_chart.png", width=80 * mm, height=48 * mm)])
print("ok")
