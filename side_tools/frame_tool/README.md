# Small native Frame tool

Run on the Handler GUI thread from a saved local Python script:

```python
from side_tools.frame_tool.showcase import show

show([{"id": "asset-a", "title": "Robot Arm"},
      {"id": "asset-b", "title": "Robot Body"}])
```

The three small source files deliberately show the boundary:

- `selection.ui.mjs` composes existing Field, List, Label and Button controls.
  It owns geometry and enabled state, not data access.
- `Main.qml` is a nonmodal native window and the small event adapter. It reuses
  Handler Theme and FrameView; the operating system owns its title bar/resize.
- `showcase.py` uses the existing GUI engine and releases the window/component
  after close. It creates no browser, application instance, thread or server.

Preview produces the exact explicit selection as JSON. It performs no write,
queue submission, render or repository synchronization. Supply real identities
from the calling script and put execution in that script's existing owner.
Long selections use the shared virtualized list and reserved visible scrollbar.

Batch Manager keeps its scheduler, public API integration, local QML entry point
and existing web UI. This example demonstrates its reusable presentation pieces;
it is not a replacement scheduler or another web version. Native and browser-only
capabilities must remain explicit when sharing a description.

Close the example before reloading its Python module during development.
