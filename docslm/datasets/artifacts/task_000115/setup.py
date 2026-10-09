# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 271], ["South", 299], ["East", 381], ["West", 711]]:
    ws.append(r)

wb.save("task_000115_wb.xlsx")
print("ok")
