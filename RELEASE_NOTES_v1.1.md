# ConnectDrive 1.1.0 – Release Notes

Date: 2025-10-09

## Highlights
- Simplified UI: removed the problematic “Parcourir…” share picker and reverted to clean form-only workflow.
- Better sudo prompt: authentication dialog resized and improved for readability and keyboard usability (Esc closes).
- New fstab menu: `File > fstab > View` and `Edit…` (opens `/etc/fstab` in `nano` with sudo, in a terminal).
- Robust terminal launch: picks the first available terminal (x-terminal-emulator, gnome-terminal, xfce4-terminal, …) and stops after launching.
- Name resolution fallback: automatic resolution of server names (DNS → nmblookup → mDNS `.local`) before mounting to avoid “could not resolve address”.
- Bug fixes and polish: fixed syntax errors, cleaned up exception handling, and logs.

## Changes (technical)
- src/gui/main_window.py
  - Removed browse/picker flows; simplified `_setup_connection_form()`.
  - Added `_edit_fstab()` with terminal detection and single-launch behavior.
  - Added `_resolve_server()` used by `_mount_share()`; logs and uses resolved IP.
  - Restored `_unmount_share()` as standalone; fixed try/except structure in `_mount_share()`.
  - Menu: replaced "View fstab" with submenu `fstab` → `View`, `Edit…`.
- src/gui/dialogs/sudo_password_dialog.py
  - Larger default size, wrapped message, wider password entry, Esc to close.
- setup.py
  - Bumped version to `1.1.0`.

## Upgrade notes
- No breaking changes in config or CLI.
- Ensure at least one terminal emulator is installed to use `fstab > Edit…`.
- Optional: install `samba` tools to enable `nmblookup` for NetBIOS name resolution (`sudo apt install samba` or `samba-common-bin`).

## Known limitations
- If no terminal emulator is installed, `fstab > Edit…` shows an error.
- Name resolution depends on local network services; specifying the NAS IP remains the most reliable.
