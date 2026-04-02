"""
Creates DirectoryChangeNotifier.html — a TiddlyWiki for this project.
Based on the same pattern as webdriver/create_wordlebot_wiki.py and
formatted to match the Adafruit wiki conventions.

Run:  python create_wiki.py
Output: Resources/DirectoryChangeNotifier.html
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


def _ts(offset_seconds=0):
    """Unique timestamp for a todolist item, optionally offset by seconds."""
    from datetime import timedelta
    dt = datetime.now() + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y%m%d%H%M%S") + "000"


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


def add_or_update(tiddlers, title, text, tags=None, tiddler_type=None):
    now = _now()
    for t in tiddlers:
        if t.get("title") == title:
            t["text"] = text
            t["modified"] = now
            if tags is not None:
                t["tags"] = tags
            if tiddler_type is not None:
                t["type"] = tiddler_type
            return
    entry = {"title": title, "text": text, "created": now, "modified": now}
    if tags:
        entry["tags"] = tags
    if tiddler_type:
        entry["type"] = tiddler_type
    tiddlers.append(entry)


def add_json_tiddler(tiddlers, title, data):
    """Add a todolist JSON data tiddler. Only adds if not already present."""
    for t in tiddlers:
        if t.get("title") == title:
            return  # don't overwrite — user may have edited via UI
    now = _now()
    entry = {
        "title": title,
        "text": json.dumps(data, indent=4),
        "type": "application/json",
        "created": now,
        "modified": now,
    }
    tiddlers.append(entry)


def add_todolist(tiddlers, name, tasks):
    """
    Add all five data tiddlers for a todolist priority bucket.
    tasks: list of str — the initial undone items.
    Only adds if the tasks tiddler doesn't already exist (preserves UI edits).
    """
    ts = [_ts(i) for i in range(len(tasks))]
    add_json_tiddler(tiddlers, f"$:/todolist/data/tasks/{name}",
                     {ts[i]: tasks[i] for i in range(len(tasks))})
    add_json_tiddler(tiddlers, f"$:/todolist/data/status/{name}",
                     {ts[i]: "undone" for i in range(len(tasks))})
    add_json_tiddler(tiddlers, f"$:/todolist/data/priority/{name}",
                     {ts[i]: "none" for i in range(len(tasks))})
    add_json_tiddler(tiddlers, f"$:/todolist/data/done/{name}", {})
    add_json_tiddler(tiddlers, f"$:/todolist/data/state/{name}",
                     {"itemtext": "", "markall": ""})


# ---------------------------------------------------------------------------
# Wiki content  (TiddlyWiki markup — not Markdown)
# ---------------------------------------------------------------------------

HOME = """\
''DirectoryChangeNotifier'' monitors directories for file additions, removals,
and modifications, then sends automated notifications via Gmail and/or Facebook.

Tailored for the Society for Creative Anachronism (SCA) organisation's file-tracking needs.

[[Contents]] | [[Goals]] | [[Running the Application]] | [[Configuration]] | [[Architecture]] | [[Modules]] | [[SpreadsheetDiff]] | [[Acronyms]]
"""

CONTENTS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Contents' sort[title]>>
</div>
"""

GOALS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Goals' sort[title]>>
</div>
"""

GOALS_MAIN = """\
* Email or Facebook Messenger when files are added, removed, or modified in a monitored path
* Monitor Google Drive (G:) for SCA group file changes
* Support multiple notification profiles from a single run
* Route notifications to email, Facebook Pages, Messenger, and Groups
* Track quarterly SCA Exchequer report cycles via Converter
* Provide SpreadsheetDiff tool to compare Excel workbooks
"""

RUNNING = """\
!!Running the Application

```
python DirChangeNotifier.py
```

No CLI arguments -- all configuration is file-based in `Private/`.

!!Individual Module Self-Tests

Each module has an `if __name__ == '__main__':` block:

```
python Persistence.py
python DataFrame.py
python Gmail.py
python Facebook.py
```

!!SpreadsheetDiff

```
python SpreadsheetDiff.py
```

Or double-click `SpreadsheetDiff.bat`.
"""

CONFIGURATION = """\
!!Required Files in Private/

The `Private/` directory is git-ignored and must be created manually.

|!File|!Purpose|
|`CredentialsNotifier.txt`|Line 1: Gmail address, Line 2: app password|
|`NotificationNames.lst`|List of profile names to run, one per line|

!!Per-Profile Files

For each profile name (e.g. `GoogleDrive`):

|!File|!Purpose|
|`GoogleDrive_Path_Options.txt`|Paths to monitor; append `/S` for recursive|
|`GoogleDrive_Ignore_Paths.txt`|Path substrings to skip|
|`GoogleDrive_Ignore_Files_Containing.txt`|Filename patterns to skip|
|`GoogleDrive_Notification_List.txt`|Recipients (see below)|
|`GoogleDrive_Title.txt`|Email subject prefix|
|`GoogleDrive_Signature.txt`|Optional email signature|

!!Notification List Format

```
email@example.com
FB:PageName
FBM:PersonName
FBG:GroupName
```

!!State Snapshots

Saved to `Private/{ProfileName}_DirTreeToday.txt`.
* Line 1 -- timestamp
* Remaining lines -- full file paths, one per line
"""

ARCHITECTURE = """\
!!Core Flow

# DirChangeNotifier loads profiles and scans the filesystem
# Compares current file list against saved snapshot
# Triggers notifications for any additions, removals, or modifications
# Saves new snapshot for next run

!!Change Detection

Snapshot-based comparison against `_DirTreeToday.txt`:

|!Condition|!Result|
|File only in current scan|Added|
|File only in previous snapshot|Removed|
|Same path, newer mtime|Modified|

No database -- entirely file-based state.

!!Notification Routing

```
DirChangeNotifier --> Gmail --> SMTP (email recipients)
                            --> Facebook --> FB wall post  (FB:Name)
                                         --> Messenger DM (FBM:Name)
                                         --> Group post   (FBG:Name)
```

!!Environment Detection

`HostFlavor.get_host_flavor()` switches between `TEST` (local dev) and `DEPLOYED` (production).
Check `HostFlavor.py` when paths or behaviour seem environment-dependent.

!!Dependency Order

```
DirChangeNotifier --> Gmail --> Facebook
                            --> GroupFields, HostFlavor, Persistence, PrintHelper, Substitutions
                            --> DataFrame
```
"""

MODULES = """\
|!Module|!Purpose|
|`DirChangeNotifier.py`|Entry point: loads profiles, scans filesystem, compares snapshot, triggers notifications|
|`Gmail.py`|Routes notifications: splits recipients into email vs Facebook, sends via SMTP|
|`Facebook.py`|Selenium browser automation for FB wall posts, Messenger DMs, and group posts|
|`Persistence.py`|All file I/O: config files, snapshots, path utilities, clipboard|
|`PrintHelper.py`|Styled console output with colours and indentation|
|`Substitutions.py`|Template variable substitution, signatures, date formatting|
|`DataFrame.py`|Pandas DataFrame wrapper for CSV operations|
|`HostFlavor.py`|Detects TEST vs DEPLOYED environment and resolves paths|
|`GroupFields.py`|SCA group metadata and field lookups|
|`Converter.py`|Converts Q4 Excel Exchequer reports to Q1 format for the new year|

!!Resources Directory

|!File|!Purpose|
|`Substitutions.csv`|Template variable definitions|
|`Signatures.csv`|Email signatures|
|`Group_Substitutions.csv`|SCA group-specific substitutions|
|`SCA Regions.csv`|SCA organisational reference data|
|`States.csv`|State reference data|
|`Converter the Red Test.lst`|Converter config for TEST environment|
|`Converter the Red Deployed.lst`|Converter config for DEPLOYED environment|

!!Key Dependencies

|!Package|!Purpose|
|`selenium`|Facebook browser automation|
|`pandas`|CSV/DataFrame operations|
|`pyperclip`|Clipboard utilities|
|`openpyxl`|Excel file handling (SpreadsheetDiff)|
|`sounddevice`|Audio playback (PlaySound.py)|
"""

SPREADSHEETDIFF = """\
Compares two Excel workbooks cell by cell and produces an `.xlsx` diff report
with clickable hyperlinks to the differing cells in each source file.

!!Running

```
python SpreadsheetDiff.py
```

Or double-click `SpreadsheetDiff.bat`.

!!How It Works

# File browser dialogs prompt for File A and File B
# All sheets present in both workbooks are compared cell by cell
# Sheets with no differences are skipped
# An `.xlsx` report is saved next to File A and opened automatically in Excel

!!Output Format

One tab per workbook sheet that has differences, plus a Summary tab.

|!Column|!Content|
|Cell in A|Clickable hyperlink to that cell in File A|
|Cell in B|Clickable hyperlink to that cell in File B|
|File A|Value in File A|
|File B|Value in File B|
|Type|Changed / Added / Removed|

Rows are colour-coded:

|!Colour|!Meaning|
|Yellow|Changed -- value differs between files|
|Green|Added -- cell has a value only in File B|
|Red|Removed -- cell has a value only in File A|

!!Notes

* Only cell values are compared -- formatting is ignored
* Row 1 is treated as headers but is still compared for value changes
* Sheets missing from one file are listed on the Summary tab
"""

ACRONYMS = """\
|!Acronym|!Meaning|
|FB|Facebook|
|FBM|Facebook Messenger (direct message)|
|FBG|Facebook Group|
|SCA|Society for Creative Anachronism -- the organisation this tool was built for|
|SMTP|Simple Mail Transfer Protocol -- used to send Gmail notifications|
|mtime|Modification time -- OS file timestamp used to detect changes|
|TEST|Local development environment (detected by HostFlavor)|
|DEPLOYED|Production environment (detected by HostFlavor)|
"""

TODO_LIST = """\
<<todolist-ui caption:"Critical" width:"" base:"Critical">>
<<todolist-ui caption:"High" width:"" base:"High">>
<<todolist-ui caption:"Medium" width:"" base:"Medium">>
<<todolist-ui caption:"Low" width:"" base:"Low">>
"""

TASKS_CRITICAL = []

TASKS_HIGH = [
    "Fix FULL_GROUP_NAME for unbalanced/error OTHER workbooks (save_summary only runs when balanced==True)",
]

TASKS_MEDIUM = [
    "Add SpreadsheetDiff option to skip first N header rows from comparison",
    "Verify OTHER region end-to-end with at least one balanced workbook",
]

TASKS_LOW = [
    "Add test coverage for SpreadsheetDiff",
]

DONE_SINCE_CHECKIN = """\
* Created SpreadsheetDiff.py -- compare two Excel workbooks, output .xlsx with hyperlinks
* Created SpreadsheetDiff.bat launcher
* Created TiddlyWiki project documentation (create_wiki.py)
* Updated CLAUDE.md
"""

IDEAS = ""

TEST_COVERAGE = ""

DIALOG = """\
<div class="tc-table-of-contents">

<<toc-selective-expandable 'Dialog'>>

</div>
"""

DIALOG_TODAY = """\
* I would like to create a python program that: given two spreadsheets, display all the differences in all the sheets. Please describe but don't create it yet
** Described design: openpyxl or pandas, per-sheet comparison, flag missing sheets, header row option, output to HTML or file. Asked about header row, formatting, empty cells, output format, library choice.
* use openpyxl. diff report to an html file, use header row, ignore formatting
** Asked remaining questions: output location, how files are specified, column matching by name or position, row matching by position or key column, missing sheets behaviour.
* same directory
** Noted. Asked remaining four questions.
* prompted at runtime, header name, key column, note missing sheet
** Asked: auto-detect key column or prompt user?
* Auto-detect
** Built SpreadsheetDiff.py: tkinter file prompts, header-name column matching, first-column key matching, HTML report saved next to File A.
* when you ask for the files, are you going to let the user browse to find the 2 files?
** No -- currently accepts a typed path. Can add tkinter file browser dialog if you want.
* yes
** Added tkinter filedialog.askopenfilename() for both files, filtered to Excel types.
* please add the program to git for review
** Staged and committed SpreadsheetDiff.py.
* Next time just add it to git, don't check-in. I want to look at everything before ci
** Noted and saved to memory. Will only git add, never commit unless you say ci.
* When you are done, please open the .html file in a browser
** Added webbrowser.open(out_path) at end of main().
* Please skip the sheets with no differences found
** Updated: sheets with zero diffs are skipped in both HTML output and console log.
* can we name the row and column for the differences instead?
** Asked for clarification: rename table headers, show Excel-style position (C5), or something else?
* Row Column, like C5
** Confirmed: drop key-column matching, compare cell by cell, report each diff by Excel address (e.g. C5). Simplified table to Cell / File A / File B / Type.
* let's see it
** Rewrote compare_sheets and generate_html. Output table: Cell | File A | File B | Type, colour-coded rows.
* can you create SpreadsheetDiff.bat that runs SpreadsheetDiff.py
** Created SpreadsheetDiff.bat using %~dp0 to locate the script regardless of working directory.
* ci
** Committed both SpreadsheetDiff.py and SpreadsheetDiff.bat.
* please explain the bat file line: python "%~dp0SpreadsheetDiff.py"
** Explained: %~dp0 expands to the drive + path of the .bat file itself, so Python always finds the script even if run from a different directory.
* what does %~dp0 mean?
** Explained the modifier breakdown: %0 = batch file path, ~ = strip quotes, d = drive letter, p = path. Combined gives drive+folder with no filename.
* Have you created a wiki page for this project?
** No wiki exists yet. Asked whether to create one and where.
* GitHub, and use all the rules that you use for the webdriver project
** No memory of webdriver wiki rules. Asked which project.
* another project in PycharmProjects
** Found webdriver project. No GitHub wiki exists there either. Found create_wordlebot_wiki.py using TiddlyWiki / TiddlyFile pattern.
* Yes, using webdriver's Empty Project.html
** Copied Empty Project.html to Resources/. Created create_wiki.py modelled on create_wordlebot_wiki.py. Generated DirectoryChangeNotifier.html with six tiddlers.
* I like what you did, but you didn't use the Default Tiddlers found in the special shadow tiddler GettingStarted yet
** Updated $:/DefaultTiddlers to open four tiddlers on startup: DirectoryChangeNotifier, TODO, Peter Requests, Claude Requests -- matching the Adafruit wiki pattern.
* Please create a Project wiki using Empty Project.html in webdriver as a model, and use the memory of Adafruit to help with formatting and guidance
** Read all Adafruit tiddlers. Rewrote create_wiki.py using proper TiddlyWiki markup (!! headings, |!col| tables, * lists, [[links]]), Contents TOC, Goals, Acronyms, Peter/Claude Requests with dated entries.
* The first task I want you to work on is the daily Dialog tiddler, to record the text I type here and your response, similar to what was done on the Adafruit project
** Added Dialog parent tiddler (TOC) and Dialog {today} tiddler with today's full conversation. Peter entries use *, Claude entries use **. Added Dialog to $:/DefaultTiddlers.
* I don't want you to change the GettingStarted tiddler, that is mine to change, and I have changed it. You may look at it, to see what I am paying attention to
** Read $:/DefaultTiddlers from the wiki. Removed $:/DefaultTiddlers from create_wiki.py. Added missing tiddlers it referenced: Done since last check-in, TODO List, Ideas, Test Coverage.
* Dialog looks good, please update it every time things are Ready for Review
** Saved to memory. Will update Dialog and regenerate wiki whenever work is staged for review.
* My first task is to get OTHER working. I am going to modify DriveLookup.py to use OTHER
** Read DriveLookup.py, GroupFields.py, DirChangeNotifier.py. OTHER is a special region (\\Other\\) for groups outside the standard regional structure. Two TODO FIX ME comments exist in find_all_q4s_missing_todos and create_group_status_data.
* A simple change, but ready to run
** Moved PROCESS_NAME = OTHER to be the last (active) assignment, with PROCESS_NAME = ALL above it as the prior setting.
* My goal is for OTHER to work similarly to RESOURCES, but the path I want it to get all the last year spreadsheets to look at and convert is "A:\\East Kingdom Exchequer Test\\Other\\2025\\Quarterly Reports"
** Understood. Traced code path for OTHER to understand the full flow.
* Can you look at the code path for OTHER and figure out why it produces more lines in "Other Test Group Status.csv" than the number of files in the Other Quarterly Reports folder
** Root cause: find_all_q4s_missing_todos adds the same q4_path to q4_paths once per file (N times). create_group_status_data then calls append_other_status_rows N times, and each call iterates all N files in q4_fields. Result: N x N rows instead of N.
* can you fix it, but not check-in
** Fixed: added q4_path to q4_paths once before the file loop. Per-file calls to append_q4_missing_todos pass [] for q4_paths to prevent duplicate additions. Removed TODO FIX ME comment.
* Missing: A:\\East Kingdom Exchequer Test\\Exchequer Reporting\\2026 Q1 Test Status\\Other Test To Convert.csv
** save_to_convert deletes the file when to_convert is empty; create_status_report then calls shutil.copy2 on a non-existent file. Fixed with an exists() guard before the copy.
* for OTHER, when it does append_other_status_rows, why doesn't q4_file_fields[FULL_GROUP_NAME] have the full group name from reading the workbook?
** save_summary() is the only place that reads C8 from the workbook and updates fields[FULL_GROUP_NAME]. It is only called from save_new_data(), which is only called when balanced == True. If the workbook is out of balance, negative, or errors, save_summary() never runs and FULL_GROUP_NAME stays "Other" -- the folder-derived name.
* I Fixed bug with 2 secondary accounts with hardcode data positions in Converter.py
** In save_secondary_accounts, cell positions for bank account number, balance, ledger balance, signature requirement, and interest bearing were hardcoded (B26, C31, C32, B28, B29) instead of offset from new_row_start. Fixed to use dynamic positions (e.g. B{new_row_start+4}, C{new_row_start+9}). Also commented out a flawed STATE/FULL_GROUP_NAME guard in __init__.
* I would like to have the TODO List from the Empty Project.html, and we can both update the priorities, but they are currently missing. Look at the webdriver project for details
** Found AITheRed.html uses four named buckets (Critical/High/Medium/Low), each with its own <<todolist-ui caption:"..." width:"" base:"...">> macro. Added add_json_tiddler and add_todolist helpers. TODO List tiddler now uses the four-bucket format. Initial tasks seeded: one High (fix FULL_GROUP_NAME for unbalanced OTHER workbooks), two Medium, one Low.
* I noticed and fixed a problem with the Peter/Claude Requests. Their daily tiddlers were tagged incorrectly. They need to be tagged with "Peter Requests" and "Claude Requests" not 2 tags (because of the space)
** Fixed: tags for daily Peter Requests and Claude Requests tiddlers now use [[Peter Requests]] and [[Claude Requests]] so TiddlyWiki treats the space-containing name as a single tag.
* I also fixed the Dialog to be with the correct date, since today is after midnight
** Regenerated wiki and staged. Saved note to memory: sessions past midnight need the Dialog tiddler date corrected to the actual calendar date.
* remember that too
** Saved to feedback_dialog_tiddler.md memory: sessions past midnight need the Dialog tiddler date corrected to the actual calendar date.
* ready for review
** Updated Dialog with session exchanges, regenerated wiki, staged create_wiki.py and Resources/DirectoryChangeNotifier.html.
"""

PETER_REQUESTS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Peter Requests'>>
</div>
"""

PETER_REQUESTS_TODAY = """\
* Create TiddlyWiki project documentation
* Create SpreadsheetDiff tool -- compare two Excel workbooks, show differences as cell addresses (e.g. C5), output .xlsx with hyperlinks, open in Excel when done
* Add .bat launcher for SpreadsheetDiff
"""

CLAUDE_REQUESTS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Claude Requests'>>
</div>
"""

CLAUDE_REQUESTS_TODAY = """\
* Created SpreadsheetDiff.py with tkinter file browser, cell-by-cell comparison, .xlsx output with hyperlinks, colour-coded rows
* Created SpreadsheetDiff.bat launcher
* Created create_wiki.py and DirectoryChangeNotifier.html TiddlyWiki
* Updated CLAUDE.md with project guidance
"""

# ---------------------------------------------------------------------------
# Build the wiki
# ---------------------------------------------------------------------------

shutil.copy(EMPTY_HTML, OUTPUT_HTML)
html, tiddlers, start, end = _load(OUTPUT_HTML)

today = datetime.now().strftime("%Y-%m-%d")

add_or_update(tiddlers, "$:/SiteTitle", "DirectoryChangeNotifier")
# $:/DefaultTiddlers is intentionally NOT set here -- managed by the user via GettingStarted

# Main pages (tagged 'Contents' so they appear in the Contents TOC)
add_or_update(tiddlers, "DirectoryChangeNotifier", HOME)
add_or_update(tiddlers, "Contents", CONTENTS)
add_or_update(tiddlers, "Goals", GOALS)
add_or_update(tiddlers, "Goals Overview", GOALS_MAIN, tags="Goals")
add_or_update(tiddlers, "Running the Application", RUNNING, tags="Contents")
add_or_update(tiddlers, "Configuration", CONFIGURATION, tags="Contents")
add_or_update(tiddlers, "Architecture", ARCHITECTURE, tags="Contents")
add_or_update(tiddlers, "Modules", MODULES, tags="Contents")
add_or_update(tiddlers, "SpreadsheetDiff", SPREADSHEETDIFF, tags="Contents")
add_or_update(tiddlers, "Acronyms", ACRONYMS, tags="Contents")

# DefaultTiddlers-referenced pages
add_or_update(tiddlers, "Done since last check-in", DONE_SINCE_CHECKIN)
add_or_update(tiddlers, "TODO List", TODO_LIST)
add_or_update(tiddlers, "Ideas", IDEAS)
add_or_update(tiddlers, "Test Coverage", TEST_COVERAGE)

# Todolist data tiddlers (only added if not already present — preserves UI edits)
add_todolist(tiddlers, "Critical", TASKS_CRITICAL)
add_todolist(tiddlers, "High", TASKS_HIGH)
add_todolist(tiddlers, "Medium", TASKS_MEDIUM)
add_todolist(tiddlers, "Low", TASKS_LOW)

# Dialog journal
add_or_update(tiddlers, "Dialog", DIALOG)
add_or_update(tiddlers, f"Dialog {today}", DIALOG_TODAY, tags="Dialog")

# Request journals
add_or_update(tiddlers, "Peter Requests", PETER_REQUESTS)
add_or_update(tiddlers, f"Peter Requests {today}", PETER_REQUESTS_TODAY, tags="[[Peter Requests]]")
add_or_update(tiddlers, "Claude Requests", CLAUDE_REQUESTS)
add_or_update(tiddlers, f"Claude Requests {today}", CLAUDE_REQUESTS_TODAY, tags="[[Claude Requests]]")

_save(html, tiddlers, start, end, OUTPUT_HTML)

print(f"Wiki written to: {OUTPUT_HTML}")
