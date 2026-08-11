# Modern UI structure

- Group Python and QML files by user-facing domain, not by implementation phase.
- Keep `controller.py` and `workspace.py` as stable public import facades.
- Put new behavior in the narrowest existing domain module; do not grow a universal controller or model.
- A module should have one clear reason to change and remain practical to review and edit by hand.
- Prefer explicit domain names and direct control flow over generic helpers, registries, or wrappers with one use.
- Preserve existing QObject properties, signals, slots, model roles, imports, and launcher behavior when moving code.
- Mention QWidget or compatibility constraints only when they materially explain a design decision.
- Split a growing module at a real responsibility boundary before adding another unrelated subsystem.
- Before adding an adapter, inspect the relevant `thlib` class, its native methods, and nearby call sites.
- Keep TACTIC objects on the Python side and call their native methods directly from the appropriate worker or model.
- Expose strings, numbers, booleans, lists, dictionaries, QObject instances, and Qt model roles to QML.
- Do not create pass-through wrappers that only rename a method, unpack its return value, or duplicate an object cache.
- Add an adapter only for a real boundary: QML-safe role projection, thread coordination, or QWidget integration.
- Name modules and comments by their domain and behavior, not by the age or origin of the implementation.
