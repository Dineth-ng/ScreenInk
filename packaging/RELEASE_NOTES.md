ScreenInk's first portable Windows beta brings the Milestone 2 drawing tools to a build that runs without Python.

### Download and run

Download `ScreenInk-0.2.0-beta.1-windows-x64.zip`, extract the complete archive,
then run `ScreenInk/ScreenInk.exe`. Keep `_internal` beside the executable.
The app opens its home window and adds a tray icon. Press **Ctrl+Alt+D** to draw and **Escape** to close
the overlay. Quit using the tray's **Exit** option.

### Included

- Smooth pen, directional arrows, outlined rectangles, translucent highlighter, and object eraser.
- Five colors, five brush widths, tool-specific mouse cursors, and a draggable dark toolbar.
- Multiple undo/redo actions and undoable Clear.
- ScreenInk icon on the executable, application windows, and system tray.
- Startup home window with a tool guide and saved, customizable activation/tool/history shortcuts.
- Portable ZIP, SHA-256 checksum, and a bundled tester guide.

### Beta status

Targets Windows 10/11 x64. This build is unsigned and may trigger an
unknown-publisher warning. Verify its source and checksum before running.
Automated drawing tests and packaged startup checks pass on the build machine;
clean-machine compatibility, real global shortcut delivery, tray interaction,
and multiple monitors/mixed DPI still need interactive tester verification.
Closing the overlay discards annotations. No installer, recording, or export.

Report reproducible bugs at https://github.com/Dineth-ng/ScreenInk/issues with
your Windows version, monitor scaling, and steps to reproduce.
