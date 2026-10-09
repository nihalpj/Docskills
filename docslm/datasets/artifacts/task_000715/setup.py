# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 567], ["South", 132], ["East", 121], ["West", 803]]:
    ws.append(r)

wb.save("task_000715_wb.xlsx")
print("ok")
