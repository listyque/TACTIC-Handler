# TACTIC-Handler UI engineering rules

This file refines the repository-wide `AGENTS.md` for everything under
`thlib/ui`. The root rules remain mandatory; this file adds UI-specific
architecture, interaction, visual, and verification requirements.

## Canonical component architecture

- Treat `docs/ui_component_policy.md` as the canonical QML composition contract.
  Apply its layer boundaries, extraction gate, motion tokens, responsive rules,
  and review checklist to every new or changed QML surface.
- Dependencies flow from window hosts to feature views, then to domain
  presentation components, and finally to `thlib/ui/qml/controls`. Shared
  controls never depend on a feature controller or application singleton.
- Group Python and QML files by user-facing domain, not implementation phase.
  Keep `controller.py` and `workspace.py` as stable public import facades.
- Put behavior in the narrowest existing domain module. Do not grow a universal
  controller, model, registry, or catch-all QML view.
- Existing oversized feature views are tracked debt, not templates. Do not add a
  new responsibility to a QML file above 800 lines; extract the touched
  presenter, delegate, popup workflow, or state owner behind a narrow API first.
  A focused bug fix that adds no responsibility does not require unrelated file
  splitting.
- Keep TACTIC objects on the Python side. Expose QML-safe primitives, lists,
  dictionaries, QObject instances, and explicit Qt model roles.
- Add a presentation adapter only for a real boundary such as QML-safe role
  projection, thread coordination, or QWidget integration. Never add a
  pass-through wrapper that only renames a native method, unpacks its result, or
  duplicates its cache.

## QML structure and data flow

- Follow Qt's QML declaration order: `id`, property declarations, signals,
  JavaScript functions, object properties, then child objects. Keep each section
  readable and separated when the component is non-trivial.
- Give reusable components an `id: root`, reference outer properties through an
  explicit id, and declare external inputs as typed `required property` values
  whenever possible. Avoid unqualified context lookup.
- Prefer declarative bindings for derived presentation state. Keep bindings
  simple, acyclic, and side-effect free; use signal handlers for commands and
  lifecycle events rather than hidden mutation inside bindings.
- A QML component does not own server truth. Send mutations through the owning
  controller, let the model publish the committed state, and reject stale async
  results after selection or project changes.
- Preserve QObject properties, notify signals, slots, model roles, imports, and
  launcher behavior when moving code unless the task explicitly changes the
  contract.

## Shared controls, visual language, and icons

- Preserve the established `thlib/ui` Material Design 3 visual language. A
  functional request does not authorize an unrelated redesign.
- Search neighboring QML and `thlib/ui/qml/controls` before creating or changing
  a button, field, popup, menu, dialog, tooltip, shadow, scrollbar, indicator,
  delegate surface, or animation.
- Reuse an existing shared control first. If the same inline visual is needed in
  two places, extract one general shared control and replace both call sites.
  Do not create a local variant with slightly different spacing, radius, state,
  or animation.
- Use only current theme roles and typography/motion tokens. Do not introduce
  local colors, numeric animation durations, or repeated anonymous width
  breakpoints in feature QML.
- Use the established hover, pressed, selected, focused, disabled, loading,
  empty, and error states consistently. Selection must remain legible in every
  base and accent theme.
- Do not mix raw Qt Quick Controls styling with the project MD3 controls. Extend
  a shared control minimally when it lacks a required capability.
- Choose the semantic icon that directly describes the action, entity, or state.
  Verify every name through the shared `MaterialIcon` mapping and extend that
  mapping centrally for project vocabulary.
- Never use `o`, `circle`, `category`, or another generic glyph as an unresolved
  placeholder. The same action uses the same icon throughout the application.
- Use the three-dot overflow icon for secondary actions or compact view options.
  Reserve settings and tune icons for an actual settings editor.
- Center a lone icon on both axes in every icon-only button. Compacting a labeled
  button must preserve that centering and its accessible name.

## Input, focus, and accessibility

- Every primary action must work through mouse, keyboard, and touch when the
  platform supports them. Use the shared activation, menu, popup, drag/drop, and
  focus controls rather than parallel local event handlers.
- Distinguish a tap from a scroll or drag using the shared gesture policy. Do not
  let synthesized mouse events duplicate an authentic touch action, and do not
  let a child control steal a deliberate Flickable gesture.
- Keep interactive hit targets at least as large as the shared sizing policy
  requires. A compact visual may use a larger invisible hit area when it does
  not overlap neighboring targets.
- Interactive custom items require a meaningful `Accessible.role`,
  `Accessible.name`, keyboard focus, visible focus state, and standard activation
  keys. Mark purely decorative items as ignored by accessibility tools.
- Define predictable Tab and arrow-key order for compound widgets. Never create
  a keyboard trap; focus must remain visible and recoverable after popups close,
  delegates recycle, or docks move.
- Do not encode meaning by color alone. Keep text, icon, state, and focus contrast
  readable across every supported base/accent pair and Windows title-bar mode.
- Tooltips supplement labels; they do not replace an accessible name or the
  visible explanation of a destructive or ambiguous action.
- Context menus and combo popups must anchor to the current invocation, replace
  stale instances, remain inside the active screen's usable bounds, preserve
  their shadow margin, and close without leaving an input-blocking overlay.
- Drag and drop must show what is being dragged, whether the target accepts it,
  and what action will occur. Reject duplicate identities before mutating the
  destination model.

## Layout and responsive behavior

- Keep outer margins symmetric and spacing consistent between equivalent
  controls, buttons, cards, sections, and footer actions.
- During adaptive reflow, verify both sides in narrow and wide geometry. Avoid
  edge adhesion, doubled gaps, asymmetric padding, clipped shadows, and controls
  that overlap after translation or font changes.
- Do not compensate for a cramped layout with one isolated margin. Set shared
  spacing or paired margins on the owning container.
- Use one named responsive state per component and shared breakpoints. Primary
  actions remain visible; secondary actions move to a semantic overflow menu
  rather than disappearing unpredictably.
- **Content that can exceed its viewport must use the shared scrollbar and
  reserve breathing room for it; a hidden, transient-only, clipped, or
  content-overlapping scrollbar is a defect.** All docks use the shared footer
  and corner treatment in every state.
- Calculate resize and drag deltas in stable parent, scene, or window coordinates,
  never in the moving handle's local coordinates.
- Persist final geometry when interaction finishes, not on every pointer move.
  Apply shared minimum sizes and clamp restored geometry to the current screen
  and current minimums.
- Minimum geometry keeps primary controls usable. Secondary content scrolls or
  reflows instead of forcing the window beyond the screen.

## Localization and project data

- Write every source user-facing string in English regardless of the request
  language. Wrap QML strings in `qsTr` and maintain
  `thlib/ui/translations/ru.json` with a structure that supports more languages.
- Never put translated literals directly in QML or Python presentation code.
- Project names, Search Type names, pipelines, processes, statuses, groups,
  roles, contexts, and other server-configured labels remain unchanged project
  data. Never pass those values themselves through `qsTr`.
- Translate only the surrounding interface template and interpolate the project
  value separately. Do not construct a single translatable phrase that embeds
  server data.
- Layout tests must include longer translated strings and narrow geometry; do not
  fix localization overflow by truncating essential actions or data.

## Rendering and performance

- Keep delegates lightweight and recyclable. Do not instantiate editors, menus,
  large images, shadows, or heavy nested models for every row before they are
  needed.
- Lazy-load genuinely heavy pages or editors, but do not wrap trivial controls or
  delegates in `Loader`; a loader is itself an object and context with overhead.
- Avoid unnecessary `clip`, layer effects, opacity on large subtrees, overlapping
  translucent surfaces, and bindings that recalculate across an entire model.
- Decode previews at an appropriate requested size and reuse the established
  image/cache path. Do not trigger server or queue work when a valid local file
  can be returned directly.
- Defer hover-only editors during active scrolling and release temporary
  delegates, image sources, menus, and connections when they leave their
  lifecycle owner.
- No server, repository, large filesystem, or expensive CPU work runs on the UI
  thread. Measure frame pacing, memory, delegate count, and request count before
  and after performance changes.

## Functional windows, Configuration, and help

- A requested modal functional window is a separate native top-level `Window`
  hosted by `WindowHost` or `FloatingWindow`, like the profile window. Do not
  implement it as an `Md3Dialog`, `Popup`, or overlay in `Main.qml`.
  Embedded dialogs are only for short confirmations inside an open functional
  window.
- Every user-facing persistent setting belongs on the logically appropriate
  Configuration page and uses the same controller API and key as the feature.
  Do not expose caches, temporary state, geometry, or individual tab/window
  working state as settings.
- Treat `thlib/ui/help_articles/*.md` as required product documentation.
  Describe every new or changed feature, window, dock, control, workflow, and
  shortcut in the matching English and Russian Markdown articles in the same
  change.
- Keep help routes and article filenames current when windows or docks are added
  or renamed. `HelpView.qml` owns only the viewer chrome; article prose and code
  examples never belong in QML or the UI translation catalog.

## UI verification gate

- Do not accept a UI change from source inspection alone. Instantiate the real
  QML component and exercise the relevant model, controller, and input path.
- Verify normal, hover, pressed, selected, focused, disabled, loading, empty, and
  error states that the change can reach.
- Inspect narrow and wide layouts, long localized text, multiple DPI scales,
  scrolling, resizing, dock movement, popup edges, and native window boundaries
  when relevant.
- For input bugs, generate the real event class in tests: touch events for touch,
  drag sequences for drag/drop, keyboard events for focus/shortcuts, and pointer
  events for menus. A string-presence assertion is only a supplemental guard.
- Run focused tests and the QML smoke harness, and treat runtime warnings,
  binding loops, invalid contexts, clipped content, and visual jumps as failures.

## Additional UI reference baseline

The repository-wide reference baseline also applies. These sources add the
accessibility requirements specific to UI work:

- [Accessibility for Qt Quick Applications](https://doc.qt.io/qt-6/accessible-qtquick.html)
- [Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
