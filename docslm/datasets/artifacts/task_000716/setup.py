# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 277], ["South", 171], ["East", 457], ["West", 106]]:
    ws.append(r)

wb.save("task_000716_wb.xlsx")
print("ok")
