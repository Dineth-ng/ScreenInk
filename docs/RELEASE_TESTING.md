# Release validation and remaining gates

Local 1.0.0 candidate; no public release has been approved or published.

## Automated/developer-machine evidence
- 74 unittest checks passing (settings, drawing, effects, clipboard, exports,
  pointer recovery, boards, collapse, history and fractional cropping).
- Native synthetic display checks: 2560x1440 primary and 1920x1080 secondary at
  (-1920,-135), Windows scale 100%. Boundary input and toolbar clamping pass.
- Separate native Qt processes with QT_SCALE_FACTOR=1.25 and 1.5 pass. These are
  simulated application scaling, not a Windows mixed-DPI test.
- docs/PERFORMANCE.json contains actual process CPU/RSS measurements, synthetic
  1280x720 canvas, 3-second samples. Static modes measured 0% at timer resolution;
  drawing ~10.34% of one core. These are not performance improvement claims.

## Required hands-on release checklist
- [ ] Start, tray icon, activation, all tools, text/effects, Escape and tray Exit.
- [ ] Live/Pointer recovery over browser, terminal, fullscreen applications.
- [ ] Preferences, startup opt-in/off across logon, theme and close/minimize behavior.
- [ ] Full/region PNG, clipboard paste, permission failure, filename and folder.
- [ ] Installer desktop checkbox on/off, Start Menu, update, reopen and uninstall.
- [ ] Save a screenshot and custom settings, uninstall, verify both survive.
- [ ] Clean Windows 11 x64 VM without Python: install, draw, save, uninstall.
- [ ] Physical Windows 100/125/150%, mixed DPI, left/right/above arrangements.
- [ ] OBS Studio Display Capture: activate, draw, record, play back, check tools
      visible, collapse toolbar, save PNG without toolbar. Record OBS version.
- [ ] Final license/source/third-party notices audit and signing/reputation decision.
- [ ] Explicit owner approval before publishing a public release.

Developer-machine package tests do not substitute for clean-machine/OBS testing.

## Installer developer-machine run

The compiled installer passed install, Start Menu shortcut creation, two reopened
EXE smoke checks with system-only PATH, update after exit, mutex refusal of both
update and uninstall while running, and clean uninstall. A synthetic user-created
PNG in the installation folder and a unique QSettings test value survived.
See INSTALLER_TEST.json. This is not clean-machine validation. Desktop checkbox
UI and normal interactive launch remain manual checklist items.
