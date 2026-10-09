# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 778], ["South", 641], ["East", 634], ["West", 846]]:
    ws.append(r)

wb.save("task_000355_wb.xlsx")
print("ok")
