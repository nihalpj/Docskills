import json
from openpyxl import Workbook
wb = Workbook(); ws = wb.active; ws.title = "Data"
ws.append(['Item', 'Revenue', 'Cost', 'Margin'])
for r in [["row1", 110, 65], ["row2", 120, 70], ["row3", 130, 75], ["row4", 140, 80]]:
    ws.append(r)
wb.save("task_000922_src.xlsx")
print('ok')
