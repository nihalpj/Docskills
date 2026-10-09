# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 802], ["South", 552], ["East", 243], ["West", 221]]:
    ws.append(r)

wb.save("task_000867_wb.xlsx")
print("ok")
