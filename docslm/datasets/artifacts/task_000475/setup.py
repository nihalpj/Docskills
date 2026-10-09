# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 443], ["South", 824], ["East", 778], ["West", 563]]:
    ws.append(r)

wb.save("task_000475_wb.xlsx")
print("ok")
