ScreenInk 0.3.0 Beta 1 adds Milestone 3 screenshots and a refreshed compact toolbar.

### Download and run

Download `ScreenInk-0.3.0-beta.1-windows-x64.zip`, extract the entire archive, and
run `ScreenInk/ScreenInk.exe`. Keep all accompanying files together. No Python
installation or administrator privileges are required. The home window explains
the tools and lets you customize shortcuts and screenshot preferences.

### New in this beta

- **Ctrl+Shift+S:** capture the annotated monitor at native pixel dimensions.
- **Ctrl+Shift+R:** drag a region in any direction, with dimensions and Escape cancellation.
- Preview with **Save**, **Copy**, and **Cancel**; lossless PNG output and image-data clipboard copy.
- Timestamp filenames, remembered folder, optional export dimming, asynchronous atomic file writes, and recoverable errors.
- Clean composition from the frozen background and annotation objects, excluding toolbar, selection UI, preview, and cursor.
- Rounded grouped toolbar, clearer selected-tool state, updated pen icon, and highlighted capture buttons.
- Existing drawing, eraser, history, tray, global activation, settings, and tool cursors are preserved.

All captured image data stays local. No cloud upload, content logging, recording,
OCR, or automatic screenshot capture is included. Only one chosen monitor is
covered at a time; the image is the frozen frame from overlay activation.

### Verification and beta limits

33 automated tests cover drawing regressions, compositing, 125%/150% crop math,
region selection, PNG round trips, clipboard image data, repeated captures,
history preservation, settings, and simulated file failures. The extracted
portable executable passes a synthetic startup/capture/PNG smoke check without
Python on its search path. Native Save As focus, real mixed-DPI layouts, and
pasting into Paint/Word/PowerPoint/Discord still require interactive Windows testing.

This Windows x64 beta is unsigned; verify the source and companion SHA-256 file
before running. Closing the overlay discards annotations; save/copy an image
first if needed. PNG exports are images, not editable annotation sessions.

See the bundled tester guide and `docs/CAPTURE.md` for the manual checklist.
Report bugs at https://github.com/Dineth-ng/ScreenInk/issues with Windows version,
display scaling, exact steps, and expected/actual behavior. Remove private data
before attaching any image to a bug report.
