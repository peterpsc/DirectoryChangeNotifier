from pathlib import Path
import csv

import Persistence

data = [
    [r"g:\My Drive\East Kingdom Exchequer\MA Branches\Carolingia\2025\Quarterly Reports\4Q\2025 Q4 EK-Quarterly-Report_Carolingia updated by Kex.xlsm",
     r"g:\My Drive\East Kingdom Exchequer\MA Branches\Carolingia\2026\Quarterly Reports",
     r"g:\My Drive\East Kingdom Exchequer\MA Branches\Carolingia\2025\Quarterly Reports\4Q\2025 Q4 EK-Quarterly-Report_Carolingia updated by Kex.xlsm",
     r"g:\My Drive\East Kingdom Exchequer\MA Branches\Carolingia\2026\Quarterly Reports", "2026 Q1 Carolingia"],
    [r"C:\Docs\2.pdf", r"C:\Docs\2.txt", "S4", "S5", "S6"],
    [r"C:\Docs\3.pdf", r"C:\Docs\3.txt", "S7", "S8", "S9"],
]


def create_complex_csv(dest_path):
    formatted_rows = []
    for row in data:
        formatted_row = []
        for i, val in enumerate(row):
            if i < 2:
                title = "Open"
                file_path = val
                hyperlink = Persistence.create_hyperlink(file_path, title)
                formatted_row.append(hyperlink)
            else:
                formatted_row.append(val)
        formatted_rows.append(formatted_row)
    Persistence.save_list(formatted_rows, dest_path)

if __name__ == '__main__':
    create_complex_csv(".\experiment.csv")
