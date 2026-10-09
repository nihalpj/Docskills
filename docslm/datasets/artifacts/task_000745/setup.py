# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 873], ["South", 666], ["East", 772], ["West", 708]]:
    ws.append(r)

wb.save("task_000745_wb.xlsx")
print("ok")
