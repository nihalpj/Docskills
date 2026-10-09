# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 784], ["South", 777], ["East", 144], ["West", 300]]:
    ws.append(r)

wb.save("task_000356_wb.xlsx")
print("ok")
