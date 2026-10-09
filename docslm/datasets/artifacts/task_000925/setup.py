# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 337], ["South", 784], ["East", 179], ["West", 136]]:
    ws.append(r)

wb.save("task_000925_wb.xlsx")
print("ok")
