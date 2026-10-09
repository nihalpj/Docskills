# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 486], ["South", 457], ["East", 623], ["West", 692]]:
    ws.append(r)

wb.save("task_000625_wb.xlsx")
print("ok")
