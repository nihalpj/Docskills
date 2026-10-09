# setup: AcroForm feedback pdf
from reportlab.pdfgen import canvas as cvs

c = cvs.Canvas("task_000585_form.pdf", pagesize=(612, 792))
c.setFont("Helvetica", 12)
c.drawString(72, 750, "Meridian Health Feedback Form")
c.acroForm.textfield(name="fullname", x=72, y=700, width=300, height=20,
                     borderColor=None, fillColor=None, relative=False)
c.acroForm.textfield(name="email", x=72, y=650, width=300, height=20,
                     borderColor=None, fillColor=None, relative=False)
c.save()
print("ok")
