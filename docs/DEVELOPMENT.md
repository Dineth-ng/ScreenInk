# ScreenInk — Milestone 2

These notes describe the original drawing milestone. See the root README for
the current beta startup window, saved shortcut editor, icon assets, and packaging.

A lightweight Windows-first desktop annotation app using Python 3 and PySide6 /
Qt 6. Milestone 2 extends the existing tray/overlay architecture. No administrator
privileges are required.

## Install and run

Install Python 3.11 or newer with pip. In Windows PowerShell:

```powershell
cd F:\ScreenInk
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

To clone onto another machine first:

```powershell
git clone https://github.com/Dineth-ng/ScreenInk.git
cd ScreenInk
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Activation is unnecessary. Keep the terminal open while running. For a launch
without a console after setup:

```powershell
Start-Process -FilePath .\.venv\Scripts\pythonw.exe -ArgumentList main.py -WorkingDirectory (Get-Location).Path
```

The existing PySide6 requirement is unchanged; no additional packages are needed.

## Tools and shortcuts

Find the pen icon in the Windows tray (possibly under the hidden-icons arrow).
Move the pointer to the desired monitor and press **Ctrl+Alt+D**, or right-click
the tray icon and choose **Start drawing**. ScreenInk opens a frameless topmost
overlay of that monitor with a frozen background darkened by about 25%.

| Tool / action | Key | How it works |
| --- | --- | --- |
| Pen | P | Hold the left button to draw smooth antialiased curves with round ends. A click draws a dot. |
| Arrow | A | Drag from tail to tip in any direction. A live preview is committed on release; the arrowhead follows direction and thickness. |
| Rectangle | R | Drag between opposite corners in any direction. The outline previews live; its interior stays transparent. |
| Highlighter | H | Draw at 35% opacity. Defaults to yellow, 12 px; color and thickness can be changed. Separate overlapping strokes naturally darken. |
| Eraser | E | Click near a stroke/outline to remove the entire topmost object. Drag to erase objects along the swept pointer path. One eraser drag is one undoable action. Rectangle interiors do not count as hits. |
| Undo | Ctrl+Z | Undo completed drawings, erasing, and Clear. Repeat to go further back. |
| Redo | Ctrl+Y | Restore undone actions. A new drawing, successful erasure, or nonempty Clear discards the redo branch. |
| Clear | Ctrl+Shift+X | Remove all annotations and keep the overlay open. Undo restores everything together. Empty Clear does nothing. |
| Close overlay | Escape | Return to the desktop and keep the tray app running. Also available on the toolbar. |

The compact dark toolbar has tool icons, **red, green, yellow, white, blue**,
thicknesses **2, 4, 6, 8, 12 logical pixels**, Undo, Redo, Clear, and Close.
Hover icons for tooltips. The selected tool has a blue border. Undo/Redo are
disabled when unavailable. Drag the six-dot handle to reposition the toolbar;
it stays inside the monitor. Toolbar interactions do not create strokes.
Color/size controls are disabled for the object eraser.

On the canvas, the mouse cursor shows the selected tool's icon beside a precise
target ring. Its center is the drawing position; the icon is offset so it does
not hide the point. The ring follows brush thickness and the badge follows the
selected color. Eraser uses a neutral icon and its hit-tolerance ring. Toolbar
controls retain the normal pointer; the drag handle uses a move cursor.
Shared icon artwork lives in `icons.py`; tool cursors are built in `cursors.py`.

Each drawing tool remembers its own color/size within the overlay session.
Changes affect future objects. Switching tools during a drawing gesture cancels
its unfinished preview; an eraser gesture already performed is kept and undoable.
Geometry uses canvas-local logical coordinates; Qt handles display scaling.

Close and reopen for a fresh background and empty annotations/history. Captures
and drawings remain in memory and are discarded on close. Use the tray's **Exit**
option to quit and release the shortcut.

## Preserved Milestone 1 behavior

- Global Ctrl+Alt+D through Windows without polling or elevation.
- A warning if registration fails; Start drawing in the tray remains usable.
  Release the shortcut in the conflicting app and restart ScreenInk to retry.
- A per-user Qt instance lock prevents duplicates and recovers dead-process locks.
- Overlay lifetime stays separate from the tray application.
- Fullscreen frameless topmost overlay, darkened frozen background, Escape, and Exit.

No screenshot export, recording, text, or persistence was added. The original
in-memory background capture remains necessary for the overlay.

## Project structure and file guide

```text
ScreenInk/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── screenink/
│   ├── __init__.py
│   ├── application.py
│   ├── hotkey.py
│   ├── overlay.py
│   ├── toolbar.py
│   ├── drawing.py
│   ├── interaction.py
│   ├── annotations.py
│   └── history.py
└── tests/
    └── test_drawing.py
```

| File | Simple explanation |
| --- | --- |
| `main.py` | Starts ScreenInk. |
| `application.py` | Existing tray, instance lock, background capture, and lifecycle. |
| `hotkey.py` | Existing native Windows global shortcut registration and cleanup. |
| `overlay.py` | Fullscreen window, local shortcuts, and signal connections. |
| `toolbar.py` | Draggable dark toolbar with painted icons and tool settings. |
| `drawing.py` | Canvas widget that forwards input and renders the document. |
| `interaction.py` | Mouse gestures, previews, settings, and erasing. |
| `annotations.py` | Independent objects, smoothed paths, shape geometry, and outline hit testing. |
| `history.py` | Document state and multiple undo/redo actions. |
| `__init__.py` | Marks the folder as a Python package. |
| `tests/test_drawing.py` | Automated geometry, history, rendering, and UI checks. |
| `requirements.txt` | PySide6 dependency, including Qt. |
| `.gitignore` | Excludes virtual environments and Python caches. |
| `README.md` | Setup, tool guide, architecture, and testing instructions. |

The original application and hotkey modules are preserved. The canvas forwards
mouse positions to a controller instead of implementing gestures inside painting.
Each annotation owns its tool, copied color/width, and geometry. Committed objects
are no longer modified. History snapshots share these objects rather than copying
their paths or the screenshot.

Qt signals communicate settings, document changes, and invalidated drawing regions.
QPainter renders the screenshot, darkening, objects, then the preview; it never
paints into the screenshot. Geometry is cached between changes. Mouse moves
invalidate the union of old/new preview bounds, and painting is clipped to dirty
regions. Finished actions/history changes request a full repaint.

There are no polling loops or worker threads. Long sessions with many complex
strokes use more memory and repaint time; closing releases the session. The
toolbar is about 614 logical pixels wide at default metrics, suitable for standard
desktop resolutions.

## Automated tests

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m compileall -q main.py screenink tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use built-in unittest and PySide6.QtTest; no test package is needed. They
force offscreen Qt and use synthetic backgrounds. Coverage includes smoothing,
dots, arrows in different directions, rectangle previews/border hits, highlight
opacity, every color/width, multiple undo/redo operations, redo branching, whole
object erasing, undoable Clear, switching tools, toolbar isolation/drag bounds,
shortcuts, screen edges, background immutability, and fresh overlay sessions.

Offscreen checks do not prove real desktop focus, tray menus, capture, global
shortcut delivery, or mixed-DPI behavior. Use the real Windows checklist below.

## Manual testing checklist

- [ ] Launch without elevation; confirm the tray. Launch again and confirm only one instance remains.
- [ ] Focus another app and press Ctrl+Alt+D. Check fullscreen coverage, topmost behavior, frozen content, and background darkening.
- [ ] Pen: draw dots, slow curves, fast handwriting, and long strokes. Check smoothness and responsiveness.
- [ ] Arrow: drag up/down/left/right and diagonally, using short and long arrows. Check preview, head direction, and commit on release.
- [ ] Rectangle: drag from every corner. Check preview and transparent interiors.
- [ ] Highlighter: press H; confirm yellow/12 px defaults and readable content under approximately 35% opacity strokes.
- [ ] Try all five colors and widths. Confirm new objects use the selection, old objects keep their style, and each tool remembers settings.
- [ ] Switch with icons and P/A/R/H/E. Check the selected indicator. Switch mid-drag and confirm the unfinished preview disappears.
- [ ] Erase strokes, arrowheads, and rectangle borders. Check whole-object removal and intact background; rectangle interiors/blank areas should do nothing.
- [ ] Click overlapping objects and confirm only the topmost is removed. Drag rapidly across objects, then undo the drag together.
- [ ] Undo/redo several mixed actions. Undo then draw and confirm the old redo branch disappears. Check toolbar button availability.
- [ ] Clear with the icon and Ctrl+Shift+X. Check the overlay stays open; Undo restores all and Redo clears again.
- [ ] Click every toolbar control; check no accidental ink. Drag the handle to each edge and confirm it remains reachable and keeps its position.
- [ ] Draw along each screen boundary and release outside the canvas. Check clipping, alignment, and no stuck stroke.
- [ ] Test tool keys, Ctrl+Z/Ctrl+Y, and Escape after using color/size controls. Escape returns to the desktop while the tray stays alive.
- [ ] Close/reopen repeatedly; confirm fresh background, empty objects, and empty history.
- [ ] Repeat on each monitor, including left of primary, at 100%, 150%, and mixed DPI. Check pointer/ink alignment and toolbar bounds.
- [ ] Reserve Ctrl+Alt+D in another app before launch; confirm warning and tray fallback. Release it and restart to retry.
- [ ] Exit through the tray with an overlay open, then relaunch. Confirm shortcut cleanup. Force-stop once and confirm stale-lock recovery.

Protected content, UAC secure desktop, lock screens, and some exclusive fullscreen
apps can block capture/topmost windows. Non-Windows global shortcuts are outside
this Windows-first milestone.
