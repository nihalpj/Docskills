# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 541], ["South", 171], ["East", 620], ["West", 784]]:
    ws.append(r)

wb.save("task_000296_wb.xlsx")
print("ok")
