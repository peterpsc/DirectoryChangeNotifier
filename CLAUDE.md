# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

DirectoryChangeNotifier monitors directories (primarily Google Drive) for file additions, removals, and modifications, then sends automated notifications via Gmail and/or Facebook (Messenger, Pages, Groups). It is tailored for the Society for Creative Anachronism (SCA) organization's file tracking needs.

## Running the Application

```bash
python DirChangeNotifier.py
```

No CLI arguments — all configuration is file-based in `Private/`.

Individual module self-tests (each has an `if __name__ == '__main__':` block):
```bash
python Persistence.py
python DataFrame.py
python Gmail.py
python Facebook.py
```

## Required Private Configuration

The `Private/` directory (git-ignored) must contain:

- `CredentialsNotifier.txt` — line 1: Gmail address, line 2: app password
- `NotificationNames.lst` — list of profile names to run, one per line

For each profile name (e.g., `GoogleDrive`):
- `GoogleDrive_Path_Options.txt` — paths to monitor; append `/S` for recursive
- `GoogleDrive_Ignore_Paths.txt` — path substrings to skip
- `GoogleDrive_Ignore_Files_Containing.txt` — filename patterns to skip
- `GoogleDrive_Notification_List.txt` — recipients: `email@x.com`, `FB:PageName`, `FBM:PersonName`, `FBG:GroupName`
- `GoogleDrive_Title.txt` — email subject prefix
- `GoogleDrive_Signature.txt` — (optional) email signature

State snapshots are saved to `Private/{ProfileName}_DirTreeToday.txt` (line 1 = timestamp, remaining lines = file paths).

## Architecture

### Core Flow

1. **DirChangeNotifier.py** — entry point and main logic: loads profiles, scans filesystem, compares against saved snapshot, triggers notifications, saves new snapshot
2. **Gmail.py** — routes notifications: splits recipients into email vs. Facebook, sends via SMTP or delegates to Facebook.py
3. **Facebook.py** — Selenium browser automation for FB wall posts, Messenger DMs, and group posts
4. **Persistence.py** — all file I/O: reading config files, writing snapshots, path utilities, clipboard ops
5. **PrintHelper.py** — styled console output with colors/indentation
6. **Substitutions.py** — template variable substitution, signatures, date formatting
7. **DataFrame.py** — pandas DataFrame wrapper for CSV operations
8. **HostFlavor.py** — detects TEST vs DEPLOYED environment and resolves paths accordingly
9. **GroupFields.py** — SCA group metadata and field lookups
10. **Converter.py** — converts Q4 Excel Exchequer reports to Q1 format for the new year

### Dependency Order

```
DirChangeNotifier → Gmail → Facebook
                          ↘
                    GroupFields, HostFlavor, Persistence, PrintHelper, Substitutions
                          ↗
                    DataFrame
```

### Change Detection

Snapshot-based: current file list vs. `_DirTreeToday.txt`. Files only in current = added; only in previous = removed; same path with newer mtime = modified. No database — entirely file-based state.

### Environment Detection (HostFlavor)

`HostFlavor.get_host_flavor()` switches behavior between `TEST` (local dev) and `DEPLOYED` (production). Resource paths and some behaviors differ between modes. Check `HostFlavor.py` when paths or behavior seem environment-dependent.

## Resources Directory

`Resources/` contains:
- `Substitutions.csv`, `Signatures.csv`, `Group_Substitutions.csv` — template data
- `SCA Regions.csv`, `States.csv` — SCA organizational reference data
- `Converter the Red Test.lst` / `Converter the Red Deployed.lst` — Converter config per environment
- Excel/xlsm files — quarterly financial reports used with Converter.py

## Key Dependencies (no requirements.txt — inferred from imports)

- `selenium` — Facebook browser automation
- `pandas` — CSV/DataFrame operations
- `pyperclip` — clipboard utilities
- `sounddevice` — audio playback (PlaySound.py)
- Standard: `smtplib`, `os`, `re`, `csv`, `datetime`
