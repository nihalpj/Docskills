# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 765], ["South", 395], ["East", 420], ["West", 769]]:
    ws.append(r)

wb.save("task_000445_wb.xlsx")
print("ok")
