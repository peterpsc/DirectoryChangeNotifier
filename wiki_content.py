"""
Static TiddlyWiki content for DirectoryChangeNotifier.html.
Edit this file to update documentation tiddlers.
Session-specific content (tasks, dialog, requests) lives in create_wiki.py.
"""

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

DIALOG = """\
<div class="tc-table-of-contents">

<<toc-selective-expandable 'Dialog'>>

</div>
"""

PETER_REQUESTS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Peter Requests'>>
</div>
"""

CLAUDE_REQUESTS = """\
<div class="tc-table-of-contents">
<<toc-selective-expandable 'Claude Requests'>>
</div>
"""
