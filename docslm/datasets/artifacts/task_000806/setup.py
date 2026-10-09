# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 543], ["South", 384], ["East", 850], ["West", 338]]:
    ws.append(r)

wb.save("task_000806_wb.xlsx")
print("ok")
