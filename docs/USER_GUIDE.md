# User guide

Start ScreenInk from the Start Menu or portable EXE. The home window explains tools.
Use Ctrl+Alt+D on the desired monitor to draw. Escape closes the overlay; tray Exit
quits. Changes to defaults apply on the next activation. Closing drawings discards
them, so Save or Copy a screenshot before closing if needed.

- Pen: Solid, Dashed, Dotted, Marker, Brush, Chalk; 12 colors or custom, 2–12 px.
- Arrow/Rectangle: drag; Eraser removes whole objects; Undo/Redo and Clear work.
- Text: click to edit; Numbered steps: click to number and drag to move.
- Spotlight: drag/wheel; Magnifier: frozen desktop only; Laser fades automatically.
- Freeze/Live: frozen pixels or updating desktop. Pointer passes clicks through;
  toolbar Pointer button, Ctrl+Space, activation or tray recovery returns Drawing.
- Options > Board background: black/white/green/custom; Desktop returns to desktop.
- Click the ScreenInk logo to hide/show tools. Drag the dotted handle to move.
- Capture full screen/region, preview, Save PNG or Copy; no automatic recording.

Preferences: startup (explicit opt-in), close/minimize to tray, notifications,
Dark/Light/System home theme, diagnostics, pen defaults, overlay darkness and
spotlight opacity. Toolbar stays dark for contrast over arbitrary desktops.
Files: save folder and filename placeholders. Screenshots: export dimming.
Shortcuts: edit then Apply; conflicts are rejected. Each settings area supports
its displayed defaults; preferences reset is applied only after Apply. Startup
registration is never changed merely by launching the application.

History keeps up to 100 actions within a 32 MiB estimated geometry budget. Older
undo states may be discarded. Active artwork itself is not a fixed memory budget.
Optional logs contain exception classes and code locations only, rotate at 256 KiB
with two backups, and live under the user application-data folder.

New overlays default to Pen with Brush style (8 px for fresh settings). Preferences > Annotations lets you change the default style. Saved tool/color/width choices are retained. Each drawing tool now has a matching silhouette cursor with its exact hotspot marked, including Spotlight and Magnifier. Pointer mode uses the desktop application cursor; toolbar controls use a normal arrow.
