# ConnectDrive 1.1.1 – Release Notes

Date: 2025-10-09

## Highlights
- Installable Debian/Ubuntu package (`.deb`) built with `build_deb.sh` —
  application menu entry, icon, `connectdrive` command, declared dependencies.
- Fixed `setup.py` packaging: `pip install .` now installs the `src` package
  and the `connectdrive` command correctly.

## Fixes
- Mount options entered in the UI are now actually applied to the mount
  command (previously ignored).
- The app no longer crashes at startup when the log directory cannot be
  created (console-only logging fallback).
- Removed the debug log file that was written to `$HOME` on every launch.
- Added a missing logger in `fstab_service.py` (potential `NameError`).
- `build.sh`: removed obsolete PyQt5/libc flags (the app is Tkinter-based).
- Unit tests updated to the current API — 20/20 green.

## Upgrade notes
- No breaking changes in config or CLI.
- `sudo apt install ./dist/connectdrive_1.1.1-1_all.deb` replaces the 1.1.0
  package if it was installed.

## Notes
- this release was created with the Help of DeepSeek-V46Flash
