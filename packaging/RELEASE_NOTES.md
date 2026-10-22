# ScreenInk 0.4.0 Beta 2 - Live pointer recovery and brush ink

Fixes the reported Live > Pointer > Drawing trap: the toolbar now remains clickable
in its own floating window while the canvas passes mouse input to underlying apps.
Click Pointer or select a drawing tool to return to Drawing. Ctrl+Space, activation,
and tray recovery remain available.

Restores a solid dark rounded toolbar background in both window modes. Also fixes
stale tool/cursor selection after leaving Magnifier for Live, incorrect mode-button
state after failed Freeze capture, and restoration of unrelated Windows window flags.

Adds Brush to the pen style selector: smooth, rounded, variable-width ink inspired
by the supplied examples. An input stabilizer reduces small mouse tremors, and Brush starts at 8 px. Mouse speed controls thickness; colors and width controls
still apply. Brush is one undoable/erasable object and appears in PNG exports.

Validation: 61 automated checks, native Windows toolbar/canvas hit testing and
button-recovery checks using synthetic test windows, and source/packaged smoke
checks. Broad application interoperability and mixed-DPI monitors still need manual
Windows testing. Extract the entire ZIP and keep all runtime files together.
