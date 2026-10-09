# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 323], ["South", 611], ["East", 428], ["West", 116]]:
    ws.append(r)

wb.save("task_000265_wb.xlsx")
print("ok")
