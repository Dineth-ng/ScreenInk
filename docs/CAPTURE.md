# Milestone 3: screenshot pipeline

The original tray, Windows shortcut registration, annotation data model, rendering,
and undo/redo engine remain in use. No additional dependency is required.

| Component | Simple explanation |
| --- | --- |
| `capture.py` | Starts explicit full/region captures, manages preview state, and reports save/copy outcomes. |
| `composition.py` | Copies the frozen background at native pixel dimensions, optionally dims it, draws annotations, and crops a selected region. It cannot include toolbar/cursor widgets because it never captures widgets. |
| `region_selection.py` | A temporary input layer for dragging in any direction, showing pixel dimensions, rejecting empty regions, and canceling with Escape. |
| `capture_preview.py` | Fits the captured image into a preview with Save/Copy/Cancel. Save As uses `open()` instead of a blocking `exec()` loop. |
| `exporting.py` | Encodes lossless PNG on Qt's thread pool. QSaveFile writes a temporary file and commits it atomically, preserving existing files on failure. |
| `clipboard.py` | Copies QImage pixel data through the Qt clipboard on the GUI thread. |
| `settings.py` | Remembers folder, PNG format, and export dimming; adds editable capture shortcuts without taking existing custom drawing keys. |
| `toolbar.py` / `icons.py` | Modern rounded grouped toolbar with camera/region buttons, clearer selection, and custom painted icons. |

Composition runs once per explicit request on a separate QImage. QPainter uses
the original annotation objects so pen, arrow, rectangle, and highlighter output
matches the drawing engine. No annotations are baked into the source screenshot.
PNG compression/file I/O use a worker; QObject signals deliver results back to UI.
Preview and selection layers do not edit the document or clear redo history.

The monitor origin is irrelevant to crops: all selections are canvas-local. Scale
factors use physical image dimensions divided by logical canvas dimensions,
including fractional/rounded display sizes. Bounds round outward and clamp to
the image. PNG and clipboard images have DPR 1 metadata with native physical
dimensions, avoiding accidental double scaling in other applications.

Only one chosen monitor is covered per overlay. Cross-monitor selection and
stitched screenshots are outside this milestone. Protected-content and secure
desktop restrictions apply to the original freeze-frame capture.

## Exact run/test/build commands (PowerShell)

```powershell
cd F:\ScreenInk
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe tools\build_beta.py
```

## Real Windows manual checklist

- [ ] Open the overlay and draw pen strokes, arrows in different directions, rectangles, and highlighter strokes.
- [ ] Capture full screen with Ctrl+Shift+S and the camera button. Check every object is present once, without toolbar, cursor, toast, or preview-window artifacts.
- [ ] Check full image dimensions equal the original monitor's physical resolution, not logical/scaled dimensions.
- [ ] Select a region using Ctrl+Shift+R and the region button. Drag from each corner; compare the displayed pixel dimensions with the resulting PNG.
- [ ] Test boundaries, tiny drags, click-only selections, and dragging outside the monitor. Empty selections must not create a preview.
- [ ] Press Escape during selection. Confirm only selection is canceled, drawing remains open, and toolbar/input return.
- [ ] Save PNG to a chosen folder; check timestamp naming, image quality, overwrite confirmation, and success feedback. Restart ScreenInk and verify the folder is remembered.
- [ ] Try a read-only folder and a failing/full destination. Confirm a useful error, no damaged existing file, and a successful retry to another folder.
- [ ] Copy from preview and paste into Paint. Confirm pixels (not a path), correct dimensions, and no toolbar/cursor. Repeat with Word/PowerPoint/Discord as available.
- [ ] In Screenshots settings, toggle export dimming off/on. Compare exported background brightness; on-screen dimming should stay unchanged. Restart and confirm the preference remains.
- [ ] Cancel preview and capture repeatedly. Save or copy again. Verify annotations stay editable, Undo/Redo and Clear still work, and the app never exits after saving.
- [ ] Test at 100%, 125%, and 150% Windows scaling; compare selection bounds, stroke placement, and saved pixel dimensions.
- [ ] Repeat on a monitor left of the primary display and on mixed-DPI monitors, one overlay at a time. Do not expect a region to span monitors.
- [ ] Confirm native Save As and preview stay visible above the topmost overlay, with responsive input while PNG encoding runs.
- [ ] Change both screenshot shortcuts. Confirm duplicate detection, settings persistence, and unchanged existing custom keys after upgrade.
- [ ] Retest global activation, tray, instance lock, all drawing tools/colors/widths, dragging the toolbar, Escape, and Exit.

Automated tests use synthetic images and an offscreen Qt platform; no real desktop
screenshots are saved or uploaded by the tests. Clipboard integration and DPI math
are checked, but real application paste compatibility and display behavior need
the interactive checks above.
