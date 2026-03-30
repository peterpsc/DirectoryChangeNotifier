import openpyxl
from openpyxl.utils import get_column_letter
import os
import tkinter as tk
from tkinter import filedialog
import webbrowser


def prompt_file(label):
    root = tk.Tk()
    root.withdraw()  # hide the blank Tk window
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


def esc(val):
    if val is None:
        return '<em class="empty">empty</em>'
    s = str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return s


def generate_html(file_a, file_b, sheets_only_in_a, sheets_only_in_b, sheet_results):
    name_a = os.path.basename(file_a)
    name_b = os.path.basename(file_b)

    p = []
    p.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Spreadsheet Diff: {esc(name_a)} vs {esc(name_b)}</title>
<style>
  body {{ font-family: sans-serif; font-size: 14px; margin: 24px; color: #222; }}
  h1   {{ font-size: 1.4em; margin-bottom: 4px; }}
  h2   {{ font-size: 1.1em; margin-top: 2em; border-bottom: 2px solid #ccc; padding-bottom: 4px; }}
  .summary {{ background:#f5f5f5; border:1px solid #ddd; padding:10px 16px;
              border-radius:4px; margin-top:10px; line-height:1.7; }}
  table {{ border-collapse:collapse; width:100%; margin-top:10px; }}
  th  {{ background:#f0f0f0; text-align:left; padding:6px 10px; border:1px solid #ccc; white-space:nowrap; }}
  td  {{ padding:5px 10px; border:1px solid #ddd; vertical-align:top; }}
  tr.changed  {{ background:#fffbe6; }}
  tr.added    {{ background:#e8f9ed; }}
  tr.removed  {{ background:#fdecea; }}
  .badge {{ display:inline-block; padding:2px 7px; border-radius:3px;
            font-size:0.82em; font-weight:bold; }}
  .b-changed  {{ background:#fff3cd; color:#7d5a00; }}
  .b-added    {{ background:#d4edda; color:#155724; }}
  .b-removed  {{ background:#f8d7da; color:#721c24; }}
  .missing  {{ color:#721c24; }}
  .empty    {{ color:#aaa; }}
  ul {{ margin-top:6px; }}
</style>
</head>
<body>
<h1>Spreadsheet Diff Report</h1>
<div class="summary">
  <strong>File A:</strong> {esc(name_a)}<br>
  <strong>File B:</strong> {esc(name_b)}
</div>
""")

    # Missing sheets
    if sheets_only_in_a or sheets_only_in_b:
        p.append('<h2>Missing Sheets</h2><ul>')
        for s in sheets_only_in_a:
            p.append(f'<li class="missing">Sheet <strong>{esc(s)}</strong> exists only in <strong>{esc(name_a)}</strong></li>')
        for s in sheets_only_in_b:
            p.append(f'<li class="missing">Sheet <strong>{esc(s)}</strong> exists only in <strong>{esc(name_b)}</strong></li>')
        p.append('</ul>')

    # Per-sheet sections
    for sheet_name, diffs in sheet_results.items():
        count_label = f'{len(diffs)} difference{"s" if len(diffs) != 1 else ""}'
        p.append(f'<h2>Sheet: {esc(sheet_name)} &nbsp;<span style="font-weight:normal;font-size:0.9em;color:#666">({count_label})</span></h2>')

        p.append(f"""<table>
<thead><tr>
  <th>Cell</th>
  <th>{esc(name_a)}</th>
  <th>{esc(name_b)}</th>
  <th>Type</th>
</tr></thead>
<tbody>""")

        for d in diffs:
            css = d['type']
            badge_css = f'b-{d["type"]}'
            label = d['type'].capitalize()
            p.append(f"""<tr class="{css}">
  <td>{esc(d['addr'])}</td>
  <td>{esc(d['val_a'])}</td>
  <td>{esc(d['val_b'])}</td>
  <td><span class="badge {badge_css}">{label}</span></td>
</tr>""")

        p.append('</tbody></table>')

    p.append('</body></html>')
    return '\n'.join(p)


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

    html = generate_html(file_a, file_b, sheets_only_in_a, sheets_only_in_b, sheet_results)

    out_dir  = os.path.dirname(os.path.abspath(file_a))
    out_path = os.path.join(out_dir, "spreadsheet_diff.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nReport saved to: {out_path}")
    webbrowser.open(out_path)


if __name__ == '__main__':
    main()
