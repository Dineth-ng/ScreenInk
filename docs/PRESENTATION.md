# Milestone 4: presentation tools and testing

## What changed

The existing overlay, canvas, object history, and screenshot pipeline remain in use.
`Spotlight` paints a movable circular or rectangular cutout before annotations.
`TextAnnotation` and `StepMarker` implement the same `bounds`, `paint`, and
`intersects` interface as earlier objects. Moving/editing replaces an object instead
of modifying a historical snapshot. One drag produces one undo action.

The modal `TextEditor` receives typing and text undo itself. Applying creates one
document action. Empty text cannot be committed. Selected text/markers can be
deleted with Delete/Backspace; the object eraser also removes them.

`Magnifier` maps logical coordinates to the original image's physical pixels.
It never samples a widget or its own output. Its zoom is 2x, 3x, or 4x. Live mode
disables it rather than showing an outdated frozen sample as if it were live.

`DisplayModeController` switches canvas painting. Live clears the canvas backing
store and paints annotations over a nearly transparent input-sensitive surface.
`PointerPassthrough` adds Windows WS_EX_LAYERED and WS_EX_TRANSPARENT to the actual
overlay HWND and restores the previous extended style when drawing resumes.
The toolbar becomes an owned native Tool window during Pointer mode so its controls remain clickable, then returns to the canvas in Drawing mode. Its dark rounded background is painted explicitly across both window types. No clicks are simulated. Ctrl+Space uses a separate RegisterHotKey ID while the
overlay is open; tray recovery remains available if registration fails.

`DesktopCapture` is the isolated live capture interface. It hides ScreenInk, waits
200 ms using a GUI-thread timer, and captures the selected QScreen once. Captures
and mode changes serialize; errors restore drawing. Region selection uses the new
frame, and closing the preview returns to Live. This delay is best effort, not
compositor synchronization; validate it on target Windows machines.

`LaserTrail` stores only recent segments, fades them for 0.9 seconds, repaints their
dirty bounds, and stops its timer when empty. It is separate from persistent
annotations, undo, and PNG export. Pen styles and custom colors are copied into
permanent annotation objects and therefore survive undo/redo and export.

All widget operations and screen/clipboard access stay on the GUI thread. Only
PNG file encoding/writing uses the existing worker. No dependencies were added.

## Controls

| Key | Action |
| --- | --- |
| Ctrl+Alt+D | Activate or recover Drawing mode |
| P / A / R / H / E | Pen / Arrow / Rectangle / Highlighter / Eraser |
| T / N / L | Text / Numbered steps / Laser pointer |
| S / M | Toggle spotlight / magnifier |
| F | Freeze / Live |
| Ctrl+Space | Drawing / Pointer, in Live mode |
| Ctrl+Z / Ctrl+Y | Undo / Redo |
| Ctrl+Shift+X | Clear annotations |
| Ctrl+Shift+S / Ctrl+Shift+R | Full / Region capture |
| Delete / Backspace | Delete selected text or marker |
| Escape | Cancel editor/selection/preview, otherwise close overlay |

Except Delete/Backspace, these actions can be rebound in the home window. Escape
remains the cancel/close fallback. In Pointer mode another app has focus: recover
Drawing via Ctrl+Space, activation, or tray before using local tool/Escape keys.

**Options** contains spotlight shape/dimming, marker diameter/Reset 1, lens zoom,
and Export lens. Click/drag the canvas to move spotlight/lens; use the wheel to
resize spotlight. Select a normal drawing tool to leave a visible effect in place
while drawing. Press S/M again to disable it. Clear removes document annotations
and laser trails; it does not toggle spotlight or magnifier. Those effects are not
part of undo history.

## Run automated checks

From the repository in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py screenink tests
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe tools\build_beta.py
.\dist\ScreenInk\ScreenInk.exe --smoke-test
```

Tests use synthetic images, offscreen Qt, and mocked native calls. They do not
establish real desktop click-through, native shortcut delivery, timing/flicker,
clipboard interoperability, or multi-monitor hardware behavior.

## Manual Windows acceptance checklist

- [ ] Start the EXE without Python; confirm home, icon, tray, duplicate-instance prevention, and Exit.
- [ ] Activate on primary and secondary monitors, including a monitor left of the primary (negative origin).
- [ ] Repeat at 100%, 125%, 150%, and 200% scaling; verify cursor/ink/text/region alignment and toolbar wrapping.
- [ ] Draw smooth pen strokes, arrows in every direction, rectangle previews, and translucent highlighter strokes.
- [ ] Try all 12 colors and a custom hex color. Try all widths and Solid/Dashed/Dotted/Marker/Brush; confirm old strokes retain their style.
- [ ] Use Laser: continuous dragging fades older trail segments; release fades everything. It is absent from exports/history.
- [ ] Toggle spotlight, move to screen edges, resize with wheel, change circle/rectangle and dimming. Turn it off; ink remains intact.
- [ ] Press T, type text containing P/A/R/H/E/T/N/S/M/F/L, use Ctrl+Z in the editor, and confirm tools/mode stay unchanged.
- [ ] Apply text with different sizes, colors, and bold. Drag, double-click/edit, delete, Undo/Redo. Cancel adds no object.
- [ ] Place steps 1, 2, 3; change color/diameter, move/delete, Undo/Redo, Reset 1, and continue numbering.
- [ ] Magnify detailed code at 2x/3x/4x. Move to every screen edge. Lens never samples itself or appears outside the monitor.
- [ ] Export with lens enabled and Export lens unchecked/checked. Text/markers remain readable, including fractional DPI.
- [ ] Run an animated app/video, press F: underlying content keeps updating while annotations stay fixed. Draw without click leakage.
- [ ] Press Ctrl+Space: click/type/scroll in another app. The canvas passes input through; the toolbar stays dark and clickable. Click its Pointer button or a drawing tool to recover Drawing mode.
- [ ] Recover Drawing with Ctrl+Space, activation, and tray Return to Drawing Mode separately; confirm drawing intercepts clicks again.
- [ ] Hold/reserve Ctrl+Space in another app before opening ScreenInk. Confirm a warning and tray recovery still work.
- [ ] Switch Live/Freeze repeatedly. Fresh frozen frames contain no ScreenInk toolbar/annotations baked into the background.
- [ ] In Live mode, full/region capture takes a fresh frame, briefly hides the overlay, and excludes all ScreenInk controls.
- [ ] Cancel selection/preview, then confirm Live resumes and history is unchanged. Retry captures several times.
- [ ] Save PNGs, check dimensions/crops at fractional DPI, and paste Copy into Paint/Word/PowerPoint/Discord.
- [ ] Test failed saves, remembered folders, optional export dimming/spotlight, and undoable Clear.
- [ ] Close/reopen the overlay; effects, document, and counters reset. Exit while a capture is pending; no window reappears.
- [ ] Change saved hotkeys and restart. Check upgrade preserves old bindings even when they use S/T/N/M/F/L.
- [ ] Change monitor layout while drawing; live capture reports the need to reopen instead of silently misaligning exports.

## Remaining platform limitations

Live/Pointer implementation is Windows-specific and requires interactive validation.
The capture delay may be insufficient under unusual compositor load; protected
content, secure desktops, remote sessions, and exclusive fullscreen applications
are not guaranteed. No high-frequency live capture or live magnification is used.
Each overlay covers one chosen monitor; no cross-monitor canvas/stitching exists.
Annotations are screen-fixed and do not follow scrolling documents or moved windows.
Opening Settings closes the session, and closing drawing discards editable objects.

## Platform references

The native input implementation follows Microsoft's [layered-window hit testing](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features#layered-windows). Capture uses [Qt QScreen.grabWindow](https://doc.qt.io/qt-6/qscreen.html#grabWindow); its returned physical pixel size can exceed logical screen dimensions on high-DPI displays.

Brush style stores its smooth variable-width outline as one annotation. It uses mouse speed for thickness, rounded ends/joins, and shares geometry with PNG rendering and erasing. Undo/redo preserves the original geometry.
