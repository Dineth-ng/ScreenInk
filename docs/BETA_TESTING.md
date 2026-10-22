# ScreenInk 0.4.0-beta.2 — Windows test build

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

## Presentation testing

See [PRESENTATION.md](PRESENTATION.md) for all new controls and the detailed Windows checklist.
Live/Pointer mode needs interactive testing; offscreen tests do not verify native click-through.
Click the toolbar Pointer button (or a drawing tool), use Ctrl+Space, or choose tray Return to Drawing Mode to recover mouse input. The toolbar stays clickable.

## Tools

S: Spotlight | T: Text | N: Steps | M: Magnifier | L: Laser
F: Freeze/Live | Ctrl+Space: Drawing/Pointer (Live only)

P: Pen | A: Arrow | R: Rectangle | H: Highlighter | E: Object eraser
Ctrl+Z: Undo | Ctrl+Y: Redo | Ctrl+Shift+X: Clear all | Escape: Close overlay
Ctrl+Shift+S: Capture full screen | Ctrl+Shift+R: Capture region

Pick colors and sizes on the toolbar. Drag its dotted handle to move it.
The cursor's target center marks the drawing position; its badge shows the tool.

The redesigned toolbar groups drawing, style, capture, and history controls.
Click the camera or region icon to preview the frozen screen plus annotations
without toolbar/cursor artifacts. Save a timestamp-named PNG or copy image pixels
for pasting. Escape cancels region selection; Cancel closes preview and returns
to drawing. The Screenshots tab controls export dimming and remembers your folder.

## Tester checklist

- [ ] Executable and tray show the ScreenInk icon. Launch works without Python.
- [ ] Home opens on launch and explains all tools. Start drawing hides it before capture.
- [ ] Change activation and tool/history shortcuts, Apply, and verify the new keys work.
- [ ] Restart and confirm saved shortcuts remain; restore defaults and Apply to reset.
- [ ] Duplicate/blank shortcuts show useful errors; a conflicting global key leaves the previous key working.
- [ ] Main-window Close hides to tray; tray Open restores it; Exit ScreenInk quits fully.
- [ ] Ctrl+Alt+D opens the correct monitor; Escape closes only the overlay.
- [ ] Pen curves are smooth; all preset/custom colors and five widths work.
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
- [ ] Full capture includes all annotations, without toolbar/cursor, at native pixel dimensions.
- [ ] Region selection works in all directions with dimensions; Escape cancels only selection.
- [ ] Save PNG, repeat capture, and paste Copy into Paint; annotations and Undo/Redo remain unchanged.
- [ ] Test last-folder persistence, export dimming on/off, and a failed save/retry.
- [ ] Verify capture/cropping at 125% and 150% scaling, including mixed-DPI monitors.

## Known beta limits

Windows 10/11 x64 is the target; clean-machine compatibility and mixed-DPI setups
still need tester verification. Drawing covers one selected monitor at a time.
PNG export and clipboard copy are included; no editable-session saving, recording,
installer, auto-update, or code signing is included.
Closing an overlay discards its drawings. Protected windows/UAC may not capture.
The global shortcut can conflict with another app; use Start drawing in the tray.

## Report a bug

https://github.com/Dineth-ng/ScreenInk/issues

Include version 0.4.0-beta.2, Windows version, monitor layout/scaling, selected
tool, exact reproduction steps, expected result, and actual result. Include a
picture or short recording if it helps; remove private information first.
