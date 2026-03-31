"""
Creates DirectoryChangeNotifier.html — a TiddlyWiki for this project.
Based on the same pattern as webdriver/create_wordlebot_wiki.py.
"""

import json
import os
import shutil
from datetime import datetime

# ---------------------------------------------------------------------------
# Minimal TiddlyFile (inlined to avoid depending on webdriver/pyutils)
# ---------------------------------------------------------------------------

STORE_OPEN = '<script class="tiddlywiki-tiddler-store" type="application/json">'
STORE_CLOSE = '</script>'

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "Resources")
EMPTY_HTML = os.path.join(RESOURCES_DIR, "Empty Project.html")
OUTPUT_HTML = os.path.join(RESOURCES_DIR, "DirectoryChangeNotifier.html")


def _now():
    return datetime.now().strftime("%Y%m%d%H%M%S") + "000"


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    start = html.index(STORE_OPEN) + len(STORE_OPEN)
    end = html.index(STORE_CLOSE, start)
    tiddlers = json.loads(html[start:end])
    return html, tiddlers, start, end


def _save(html, tiddlers, start, end, path):
    new_json = json.dumps(tiddlers, ensure_ascii=False).replace('</', '<\\/')
    html = html[:start] + new_json + html[end:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def add_or_update(tiddlers, title, text, tags=None):
    now = _now()
    for t in tiddlers:
        if t.get("title") == title:
            t["text"] = text
            t["modified"] = now
            if tags is not None:
                t["tags"] = tags
            return
    entry = {"title": title, "text": text, "created": now, "modified": now}
    if tags:
        entry["tags"] = tags
    tiddlers.append(entry)


# ---------------------------------------------------------------------------
# Wiki content
# ---------------------------------------------------------------------------

HOME = """\
Welcome to the DirectoryChangeNotifier wiki.

This project monitors directories (primarily Google Drive) for file additions, removals,
and modifications, then sends automated notifications via Gmail and/or Facebook
(Messenger, Pages, Groups).

It is tailored for the Society for Creative Anachronism (SCA) organisation's file-tracking needs.

[[Running the Application]] | [[Configuration]] | [[Architecture]] | [[Modules]] | [[SpreadsheetDiff]]
"""

RUNNING = """\
!! Running the Application

```
python DirChangeNotifier.py
```

No CLI arguments — all configuration is file-based in `Private/`.

!! Individual Module Self-Tests

Each module has an `if __name__ == '__main__':` block:

```
python Persistence.py
python DataFrame.py
python Gmail.py
python Facebook.py
```
"""

CONFIGURATION = """\
!! Required Files in Private/

The `Private/` directory is git-ignored and must be created manually.

| File | Purpose |
|---|---|
| `CredentialsNotifier.txt` | Line 1: Gmail address, Line 2: app password |
| `NotificationNames.lst` | List of profile names to run, one per line |

!! Per-Profile Files

For each profile name (e.g. `GoogleDrive`):

| File | Purpose |
|---|---|
| `GoogleDrive_Path_Options.txt` | Paths to monitor; append `/S` for recursive |
| `GoogleDrive_Ignore_Paths.txt` | Path substrings to skip |
| `GoogleDrive_Ignore_Files_Containing.txt` | Filename patterns to skip |
| `GoogleDrive_Notification_List.txt` | Recipients (see below) |
| `GoogleDrive_Title.txt` | Email subject prefix |
| `GoogleDrive_Signature.txt` | Optional email signature |

!! Notification List Format

```
email@example.com
FB:PageName
FBM:PersonName
FBG:GroupName
```

!! State Snapshots

Saved to `Private/{ProfileName}_DirTreeToday.txt`.
Line 1 = timestamp, remaining lines = file paths.
"""

ARCHITECTURE = """\
!! Core Flow

# DirChangeNotifier loads profiles and scans the filesystem
# Compares current file list against saved snapshot
# Triggers notifications for any additions, removals, or modifications
# Saves new snapshot for next run

!! Change Detection

Snapshot-based: current file list vs `_DirTreeToday.txt`.

* Files only in current → Added
* Files only in previous → Removed
* Same path with newer mtime → Modified

No database — entirely file-based state.

!! Notification Routing

```
DirChangeNotifier → Gmail → SMTP (email)
                          → Facebook → FB wall post
                                     → Messenger DM
                                     → Group post
```

!! Environment Detection

`HostFlavor.get_host_flavor()` switches between `TEST` (local dev) and `DEPLOYED` (production).
Check `HostFlavor.py` when paths or behaviour seem environment-dependent.
"""

MODULES = """\
!! Module Overview

| Module | Purpose |
|---|---|
| `DirChangeNotifier.py` | Entry point: loads profiles, scans filesystem, compares snapshot, triggers notifications |
| `Gmail.py` | Routes notifications: splits recipients into email vs Facebook, sends via SMTP |
| `Facebook.py` | Selenium browser automation for FB wall posts, Messenger DMs, and group posts |
| `Persistence.py` | All file I/O: config files, snapshots, path utilities, clipboard |
| `PrintHelper.py` | Styled console output with colours and indentation |
| `Substitutions.py` | Template variable substitution, signatures, date formatting |
| `DataFrame.py` | Pandas DataFrame wrapper for CSV operations |
| `HostFlavor.py` | Detects TEST vs DEPLOYED environment and resolves paths |
| `GroupFields.py` | SCA group metadata and field lookups |
| `Converter.py` | Converts Q4 Excel Exchequer reports to Q1 format for the new year |

!! Resources Directory

* `Substitutions.csv`, `Signatures.csv`, `Group_Substitutions.csv` — template data
* `SCA Regions.csv`, `States.csv` — SCA organisational reference data
* `Converter the Red Test.lst` / `Converter the Red Deployed.lst` — Converter config per environment

!! Key Dependencies

* `selenium` — Facebook browser automation
* `pandas` — CSV/DataFrame operations
* `pyperclip` — clipboard utilities
* `openpyxl` — Excel file handling (SpreadsheetDiff)
* Standard: `smtplib`, `os`, `re`, `csv`, `datetime`
"""

SPREADSHEETDIFF = """\
!! SpreadsheetDiff

Compares two Excel workbooks and produces an `.xlsx` diff report.

!! Running

```
python SpreadsheetDiff.py
```

Or double-click `SpreadsheetDiff.bat`.

!! How It Works

# File browser dialogs prompt for File A and File B
# All sheets present in both workbooks are compared cell by cell
# Sheets with no differences are skipped
# An `.xlsx` report is saved next to File A and opened automatically in Excel

!! Output Format

One sheet per workbook sheet that has differences.

| Column | Content |
|---|---|
| Cell in A | Clickable hyperlink → opens File A at that cell |
| Cell in B | Clickable hyperlink → opens File B at that cell |
| File A | Value in File A |
| File B | Value in File B |
| Type | Changed / Added / Removed |

Rows are colour-coded: yellow = Changed, green = Added, red = Removed.

A Summary sheet lists both file paths, any missing sheets, and diff counts per sheet.
"""

# ---------------------------------------------------------------------------
# Build the wiki
# ---------------------------------------------------------------------------

shutil.copy(EMPTY_HTML, OUTPUT_HTML)
html, tiddlers, start, end = _load(OUTPUT_HTML)

add_or_update(tiddlers, "$:/SiteTitle", "DirectoryChangeNotifier")
add_or_update(tiddlers, "$:/DefaultTiddlers", "[[DirectoryChangeNotifier]]")

add_or_update(tiddlers, "DirectoryChangeNotifier", HOME)
add_or_update(tiddlers, "Running the Application", RUNNING)
add_or_update(tiddlers, "Configuration", CONFIGURATION)
add_or_update(tiddlers, "Architecture", ARCHITECTURE)
add_or_update(tiddlers, "Modules", MODULES)
add_or_update(tiddlers, "SpreadsheetDiff", SPREADSHEETDIFF)

_save(html, tiddlers, start, end, OUTPUT_HTML)

print(f"Wiki written to: {OUTPUT_HTML}")
