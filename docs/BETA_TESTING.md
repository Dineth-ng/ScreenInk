# ScreenInk 0.2.0-beta.1 — Windows test build

This is a portable Windows x64 beta. Python and administrator access are not needed.

## Start

1. Extract the complete ZIP to a writable folder.
2. Open the extracted ScreenInk folder and double-click ScreenInk.exe.
3. The home window opens with a tool guide, Start drawing, and Keyboard shortcuts.
4. Press Ctrl+Alt+D to annotate the monitor under your mouse.
5. Press Escape to return to the desktop. Right-click the tray icon > Exit to quit.

Keep ScreenInk.exe and its _internal folder together. Do not run inside the ZIP.
The beta is unsigned; Windows may display an unknown-publisher warning. Verify
the download source and SHA-256 checksum before deciding whether to run it.

## Customize shortcuts

Open Keyboard shortcuts, select a field, press a combination, and click Apply.
Activation supports Ctrl/Alt/Win plus a letter, digit, or F1–F24. All tool, history,
Clear, and Close shortcuts can also be changed. Escape is always available.
Duplicate shortcuts are rejected, and failed global changes keep the previous
registration. Preferences persist after restart. Close the home window to hide
it; double-click the tray or use Open ScreenInk / Settings to reopen it.

## Tools

P: Pen | A: Arrow | R: Rectangle | H: Highlighter | E: Object eraser
Ctrl+Z: Undo | Ctrl+Y: Redo | Ctrl+Shift+X: Clear all | Escape: Close overlay

Pick colors and sizes on the toolbar. Drag its dotted handle to move it.
The cursor's target center marks the drawing position; its badge shows the tool.

## Tester checklist

- [ ] Executable and tray show the ScreenInk icon. Launch works without Python.
- [ ] Home opens on launch and explains all tools. Start drawing hides it before capture.
- [ ] Change activation and tool/history shortcuts, Apply, and verify the new keys work.
- [ ] Restart and confirm saved shortcuts remain; restore defaults and Apply to reset.
- [ ] Duplicate/blank shortcuts show useful errors; a conflicting global key leaves the previous key working.
- [ ] Main-window Close hides to tray; tray Open restores it; Exit ScreenInk quits fully.
- [ ] Ctrl+Alt+D opens the correct monitor; Escape closes only the overlay.
- [ ] Pen curves are smooth; all five colors and widths work.
- [ ] Arrows point correctly in every direction and preview while dragging.
- [ ] Rectangle previews work in every drag direction; interiors stay transparent.
- [ ] Highlighter starts yellow and is translucent.
- [ ] Cursor icons change with tools, colors, and sizes; ink follows the target center.
- [ ] Eraser removes whole objects and leaves the background intact.
- [ ] Undo/redo work for drawing, erasing, and Clear; new drawing clears redo.
- [ ] Toolbar dragging/buttons create no accidental ink.
- [ ] Screen edges and mixed-DPI monitors keep cursor/ink aligned.
- [ ] Closing/reopening creates a fresh background and empty annotation history.
- [ ] A second launch is prevented; Exit removes the tray and releases the shortcut.

## Known beta limits

Windows 10/11 x64 is the target; clean-machine compatibility and mixed-DPI setups
still need tester verification. Drawing covers one selected monitor at a time.
No save/export, recording, installer, auto-update, or code signing is included.
Closing an overlay discards its drawings. Protected windows/UAC may not capture.
The global shortcut can conflict with another app; use Start drawing in the tray.

## Report a bug

https://github.com/Dineth-ng/ScreenInk/issues

Include version 0.2.0-beta.1, Windows version, monitor layout/scaling, selected
tool, exact reproduction steps, expected result, and actual result. Include a
picture or short recording if it helps; remove private information first.
