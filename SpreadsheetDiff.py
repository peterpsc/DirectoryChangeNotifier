import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment
import os
import tkinter as tk
from tkinter import filedialog
import subprocess


# Row fill colors
FILL_CHANGED = PatternFill(fill_type='solid', fgColor='FFFBE6')
FILL_ADDED   = PatternFill(fill_type='solid', fgColor='E8F9ED')
FILL_REMOVED = PatternFill(fill_type='solid', fgColor='FDECEA')
FILLS = {'changed': FILL_CHANGED, 'added': FILL_ADDED, 'removed': FILL_REMOVED}

FONT_HEADER   = Font(bold=True)
FONT_LINK_A   = Font(color='1155CC', underline='single')
FONT_LINK_B   = Font(color='1155CC', underline='single')
FONT_MISSING  = Font(color='721C24', bold=True)


def prompt_file(label):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    print(f"Opening file browser for {label}...")
    path = filedialog.askopenfilename(
        title=f"Select {label}",
        filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")]
    )
    root.destroy()
    if not path:
        print("  No file selected — exiting.")
        raise SystemExit(1)
    print(f"  {label}: {path}")
    return path


def compare_sheets(ws_a, ws_b):
    """Compare two sheets cell by cell. Returns list of diffs with Excel addresses."""
    def sheet_to_dict(ws):
        data = {}
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    data[(cell.row, cell.column)] = cell.value
        return data

    data_a = sheet_to_dict(ws_a)
    data_b = sheet_to_dict(ws_b)

    diffs = []
    for (row, col) in sorted(set(data_a) | set(data_b)):
        val_a = data_a.get((row, col))
        val_b = data_b.get((row, col))
        if val_a != val_b:
            addr = f"{get_column_letter(col)}{row}"
            if val_a is not None and val_b is not None:
                diff_type = 'changed'
            elif val_a is not None:
                diff_type = 'removed'
            else:
                diff_type = 'added'
            diffs.append({'addr': addr, 'val_a': val_a, 'val_b': val_b, 'type': diff_type})

    return diffs


def cell_link(path, sheet_name, addr):
    """Build an Excel hyperlink URL to a specific cell in a local workbook."""
    abs_path = os.path.abspath(path).replace('\\', '/')
    return f"file:///{abs_path}#'{sheet_name}'!{addr}"


def write_xlsx(file_a, file_b, sheets_only_in_a, sheets_only_in_b, sheet_results, out_path):
    name_a = os.path.basename(file_a)
    name_b = os.path.basename(file_b)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet

    # --- Summary sheet ---
    ws_sum = wb.create_sheet("Summary")
    ws_sum.column_dimensions['A'].width = 20
    ws_sum.column_dimensions['B'].width = 60

    ws_sum.append(["File A", file_a])
    ws_sum.append(["File B", file_b])
    ws_sum.append([])

    if sheets_only_in_a or sheets_only_in_b:
        ws_sum.append(["Missing Sheets", ""])
        ws_sum.cell(ws_sum.max_row, 1).font = FONT_HEADER
        for s in sheets_only_in_a:
            ws_sum.append([s, f"Only in {name_a}"])
            ws_sum.cell(ws_sum.max_row, 1).font = FONT_MISSING
        for s in sheets_only_in_b:
            ws_sum.append([s, f"Only in {name_b}"])
            ws_sum.cell(ws_sum.max_row, 1).font = FONT_MISSING
        ws_sum.append([])

    ws_sum.append(["Sheet", "Differences"])
    ws_sum.cell(ws_sum.max_row, 1).font = FONT_HEADER
    ws_sum.cell(ws_sum.max_row, 2).font = FONT_HEADER
    for sheet_name, diffs in sheet_results.items():
        ws_sum.append([sheet_name, len(diffs)])

    # --- Per-sheet diff sheets ---
    for sheet_name, diffs in sheet_results.items():
        # Sheet names max 31 chars; truncate if needed
        tab_name = sheet_name[:31]
        ws = wb.create_sheet(tab_name)

        ws.column_dimensions['A'].width = 10   # Cell in A
        ws.column_dimensions['B'].width = 10   # Cell in B
        ws.column_dimensions['C'].width = 30   # Value in A
        ws.column_dimensions['D'].width = 30   # Value in B
        ws.column_dimensions['E'].width = 12   # Type

        # Header row
        ws.append(["Cell in A", "Cell in B", name_a, name_b, "Type"])
        for col in range(1, 6):
            ws.cell(1, col).font = FONT_HEADER

        for d in diffs:
            addr  = d['addr']
            val_a = d['val_a'] if d['val_a'] is not None else ''
            val_b = d['val_b'] if d['val_b'] is not None else ''
            dtype = d['type']
            row_num = ws.max_row + 1

            ws.append([addr, addr, val_a, val_b, dtype.capitalize()])

            fill = FILLS[dtype]
            for col in range(1, 6):
                ws.cell(row_num, col).fill = fill

            # Hyperlink col A → cell in file A (for changed/removed)
            if dtype in ('changed', 'removed'):
                c = ws.cell(row_num, 1)
                c.hyperlink = cell_link(file_a, sheet_name, addr)
                c.font = FONT_LINK_A
            else:
                ws.cell(row_num, 1).value = ''

            # Hyperlink col B → cell in file B (for changed/added)
            if dtype in ('changed', 'added'):
                c = ws.cell(row_num, 2)
                c.hyperlink = cell_link(file_b, sheet_name, addr)
                c.font = FONT_LINK_B
            else:
                ws.cell(row_num, 2).value = ''

    wb.save(out_path)


def main():
    print("Spreadsheet Diff Tool")
    print("---------------------")
    file_a = prompt_file("File A")
    file_b = prompt_file("File B")

    print("\nLoading workbooks...")
    wb_a = openpyxl.load_workbook(file_a, data_only=True)
    wb_b = openpyxl.load_workbook(file_b, data_only=True)

    sheets_a = set(wb_a.sheetnames)
    sheets_b = set(wb_b.sheetnames)
    sheets_only_in_a = [s for s in wb_a.sheetnames if s not in sheets_b]
    sheets_only_in_b = [s for s in wb_b.sheetnames if s not in sheets_a]
    common_sheets    = [s for s in wb_a.sheetnames if s in sheets_b]

    print(f"  Sheets in common : {len(common_sheets)}")
    if sheets_only_in_a:
        print(f"  Only in File A   : {sheets_only_in_a}")
    if sheets_only_in_b:
        print(f"  Only in File B   : {sheets_only_in_b}")

    sheet_results = {}
    for sheet in common_sheets:
        diffs = compare_sheets(wb_a[sheet], wb_b[sheet])
        if diffs:
            print(f"  Differences found: {sheet} ({len(diffs)})")
            sheet_results[sheet] = diffs
        else:
            print(f"  No differences   : {sheet} (skipped)")

    out_dir  = os.path.dirname(os.path.abspath(file_a))
    out_path = os.path.join(out_dir, "spreadsheet_diff.xlsx")
    write_xlsx(file_a, file_b, sheets_only_in_a, sheets_only_in_b, sheet_results, out_path)

    print(f"\nReport saved to: {out_path}")
    os.startfile(out_path)


if __name__ == '__main__':
    main()
