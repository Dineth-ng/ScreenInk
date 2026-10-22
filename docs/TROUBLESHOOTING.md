# Troubleshooting

- Shortcut unavailable: another program may own it. Start from tray or change it.
- Pointer recovery: click the floating toolbar, Ctrl+Space, Ctrl+Alt+D, or tray
  Return to Drawing Mode. Tray Exit always remains available.
- Duplicate instance: use the existing tray icon. No second copy is started.
- Missing DLL: extract/reinstall the whole distribution. Do not move the EXE alone.
- Save failed: choose a writable folder. Atomic PNG saves preserve existing files.
- Display changed: overlay closes to avoid drawing against invalid capture geometry.
  Reopen it on the desired screen; save annotations before changing displays.
- Logs: opt in through Preferences. No screenshots, clipboard data, exception
  messages or variable values are logged. Startup failures show a generic dialog.
- Startup: registry entry is HKCU/Software/Microsoft/Windows/CurrentVersion/Run,
  value ScreenInk; Preferences controls it. If an old portable path was moved,
  turn startup off, Apply, turn it on and Apply from the desired installation.
- Per-user settings: QSettings under HKCU/Software/ScreenInk/ScreenInk. Restore
  defaults in the relevant settings page. Do not delete personal screenshots.
- Installer refuses update/uninstall: tray Exit first. It intentionally does not
  force-kill a running app and discard unsaved drawings.

Known unverified cases: clean Windows 11 without developer tools, OBS recording,
Windows mixed-DPI display changes, secure desktops/UAC, HDR, Remote Desktop and
protected video. Unsigned artifacts may trigger Windows reputation warnings.
