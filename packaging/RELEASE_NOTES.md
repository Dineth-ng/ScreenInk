# ScreenInk 0.4.0 Beta 1 - Presentation tools

Adds spotlight (S), editable/movable text (T), numbered steps (N), and a bounded
2x/3x/4x magnifier (M). Text/markers participate in undo/redo and PNG exports.

New Live mode (F) uses a transparent overlay. Ctrl+Space toggles native Windows
click-through; tray Return to Drawing Mode and the activation hotkey recover input.
Live capture uses an isolated one-shot hide/capture/restore path. Magnifier remains
Freeze-only. Exports optionally include spotlight dimming and the enabled lens.

Also adds 12 preset colors, a custom RGB/hex picker, solid/dashed/dotted/translucent
marker pen styles, and a fading laser pointer (L). The toolbar wraps on narrow
screens and places presentation controls in Options. No new runtime dependencies.

Extract the entire Windows x64 ZIP and run ScreenInk.exe. Keep its runtime DLLs
and _internal directory alongside it. Read START_HERE.txt and PRESENTATION.md.

Automated offscreen regression tests and the synthetic executable smoke check
cover geometry, history, composition, editor isolation, laser expiry, mode state,
and mocked Windows pointer flags. Actual desktop click-through, global keys,
compositor timing, mixed-DPI monitors, and protected-content capture still require
manual Windows testing. The 200 ms live-capture hide delay is best effort, not a
platform compositor guarantee. This is an unsigned test prerelease.
