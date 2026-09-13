# Application QML architecture contract

This is the canonical component policy for thlib/ui/qml. It supplements the
repository AGENTS.md and applies to every new or changed QML surface.

The objective is not merely a visually similar UI. The modern interface must
behave as a reusable component library: one semantic action, one shared visual
contract, one state owner, and one implementation unless a documented domain
difference requires otherwise.

## Lead engineer rule: understand, reuse, then change

Act like a lazy lead engineer, not an industrious junior.

- First inspect the existing component, controller, native TACTIC object, original
  workflow, tests, and neighboring call sites.
- Prefer reusing or minimally extending the established implementation over
  creating a parallel helper, adapter, control, cache, or data path.
- Prefer deleting duplication and unnecessary indirection over adding another
  abstraction.
- Do not rewrite stable untouched code merely to make a refactor look complete.
  Change the smallest coherent boundary that solves a measured problem.
- Line count and stylistic uniformity are signals, not reasons to refactor by
  themselves. An extraction must improve ownership, reuse, testing, or runtime
  behavior.
- If a proposed abstraction has one consumer, only renames properties, or
  requires compatibility glue, keep the direct implementation.
- Before implementation, state what is reused, what is extended, and what old
  path is removed. After implementation, verify the behavior that justified the
  change.
## Component layers

QML is split into four layers. Dependencies only point down this list.

1. **Shared controls** — thlib/ui/qml/controls.
   Theme-aware generic controls, interaction handlers, fields, menus, dialogs,
   scrolling primitives, loading states, tabs, and small presentation blocks.
   They do not import feature controllers or know TACTIC domains.
2. **Domain presentation components** — small components beside feature views,
   such as attachment cards, activity event cards, item previews, task rows,
   and snapshot presenters. They may understand model roles but do not own
   server requests or application navigation policy.
3. **Feature views** — windows and dock content such as Messages, Tasks,
   Repository Sync, and sObject Info. A feature view composes presentation
   components and binds to one domain controller. It does not reimplement
   buttons, popups, fields, loading overlays, scroll bars, or input gestures.
4. **Hosts and registries** — Main, WindowHost, DockHost, and content routing.
   Hosts own lifetime, placement, stacking, and native-window rules; they do
   not contain feature UI or domain behavior.

Python controllers own network requests, TACTIC objects, durable state,
cross-feature coordination, cancellation, and caching. QML owns presentation
state only: focus, hover, a currently open popup, local expansion, and short
view-bound animation state.

## Shared-control gate

Before writing a visual primitive, search thlib/ui/qml/controls and neighboring
feature components.

- Use Controls.Button, Controls.FilledActionButton, or
  Controls.CompactIconButton for actions.
- Use Controls.TextField and Controls.TextArea for user input.
- Use Controls.ComboBox, Controls.Popup, Controls.Menu, Controls.Dialog,
  Controls.ScrollBar, Controls.BusyIndicator, and ContentLoadingOverlay for
  their corresponding behavior.
- Shared ComboBox and menu triggers toggle their popup: activating the same
  trigger a second time closes it. Menus and selectors accept Escape, Up/Down,
  Enter, and Space by default, retain a visible keyboard focus target, and do
  not require feature views to reimplement those bindings.
- Aim for at most seven or eight commands per menu level. Split longer command
  lists into meaningful submenus; do not use scrolling as their default layout.
  Unbounded data lists (users, processes, saved presets) still need scrolling.
- A shared scrollbar drag navigates only content that is already loaded. The
  control arms pagination from a wheel, touch-drag, or flick gesture and a
  paged view must consume `Controls.ScrollBar.takePaginationPermit(...)`
  before requesting another page. The permit stays blocked through the final
  release frames, so a thumb drag or a transient content-extent change cannot
  trigger loading. Feature views must not reimplement this state or override
  scrollbar geometry, visibility, policy, or press handling.
- Qt's attached scrollbar connection is the sole owner of its Flickable's
  scroll position. Shared scrollbar presentation must never mirror its
  `position` back into `contentX` or `contentY`; doing so corrupts virtualized
  delegate placement and makes lazy-loaded lists jump.
- The shared control owns physical placement as well as behavior: vertical
  scrollbars stay on the right edge and horizontal scrollbars stay on the
  bottom edge, regardless of inherited layout mirroring. Feature views do not
  override scrollbar anchors, coordinates, width, or height.
- Use Controls.ActivationHandler for touch/mouse activation and preserve its
  release-based de-duplication contract.
- Use the shared semantic icon mapping in Controls.MaterialIcon. An icon-only
  action is always centered by the shared control.

Extract a shared component when either condition is true:

- the same semantic UI appears in two surfaces; or
- a feature view contains a generally useful visual block with its own states,
  sizing rules, or interaction behavior.

Do not extract a one-use wrapper that merely renames properties. Reuse is based
on shared behavior and semantics, not on reducing line count.

## Theme, type, motion, and spacing

- All colors come from Theme.qml; feature QML contains no color literals.
- Typography comes from Controls.Typography and the shared theme font.
- User-facing dates and times always use the shared localized pretty/full
  timestamp presentation. Raw database or ISO-8601 values belong only in
  transport, persistence, and diagnostics; they must never be used as a UI
  fallback label.
- Radii, control heights, dock heights, and established spacing come from the
  theme or an existing shared component.
- View transitions and fades use theme.motionFast, theme.motionMedium, or
  theme.motionSlow. Pointer feedback uses the matching clickMotion or
  hoverMotion token. Feature QML must not introduce numeric duration values.
- Animation preferences are read once by ApplicationController and projected
  through the shared Theme. Delegates and controls never read configuration
  storage. When a preference is disabled its duration tokens resolve to zero;
  functional loading indicators remain available.
- Menu, dropdown, popup, tooltip, and scrim transitions follow the independent
  `popupAnimationsEnabled` preference. Shared Popup/ToolTip controls own their
  enter/exit transitions instead of inheriting Qt's fixed durations; scrims
  use `popupMotion*` tokens. Content fades do not control popup motion.
- The same state transition uses the same duration and easing everywhere.
- Symmetric outer margins and equal spacing are required in both narrow and
  wide layouts.

## Responsive layout

Responsive behavior is content-driven and declared once per component.

- Prefer ResponsiveFlow or a shared adaptive presenter over duplicated rows.
- Give every resizable dock and window a usable minimum through WindowSizing;
  secondary content scrolls or reflows.
- Name local layout states (compact, narrow, wide) once and bind all dependent
  visibility and sizing to those properties.
- Do not repeat raw width comparisons throughout a component. A breakpoint is
  allowed only when it represents that components measured content boundary,
  is exposed as one named property, and is not already covered by shared sizing.
- Hidden controls remain reachable through the standard three-dot overflow.
- Resizing must not restart data requests, image discovery, or decoding when
  the selected identity did not change.

## View size and responsibility budget

Line count is a warning, not an architectural goal, but it exposes mixed
responsibilities early.

- New shared controls should normally stay below 300 lines.
- New feature views should normally stay below 600 lines.
- A feature file above 800 lines must not gain another responsibility. Extract
  the new or touched responsibility first.
- `tests/contracts/ui_architecture_debt.json` records the current oversized QML
  and UI Python modules. The architecture test permits those files to shrink but
  rejects new oversized files, growth beyond the recorded maximum, and stale
  records for deleted files.
- Hosts and registries contain routing and lifetime only. They may not absorb a
  new feature presenter.
- Timers, dialogs, popups, network-state rendering, and list delegates are
  separate responsibilities. A view containing several of each is a mandatory
  decomposition candidate.

Existing large views are tracked debt, not examples to copy. The current split
order is:

1. DockContentRegistry.qml: search chrome, search tabs, result presenters,
   versions presenter, and routing become separate components.
2. MessagesView.qml: conversation list, timeline, composer, selection/actions,
   and modal workflows become separate components.
3. Task, configuration, check-in, and report surfaces are decomposed along the
   same controller/presenter boundaries.

## Localization and server data

Source UI strings are English and use qsTr. Project names, Search Type names,
pipeline/process names, statuses, groups, roles, contexts, and other
server-configured labels are data: they are neither hardcoded nor translated.
Translate only the surrounding application phrase.

## Review checklist

A QML change is complete only when all applicable checks pass:

- no raw common Qt Quick Control was added outside qml/controls;
- no local color literal or duplicate semantic icon was added;
- no numeric animation duration was added to feature QML;
- no duplicate local implementation exists in another surface;
- narrow, wide, touch, hover, disabled, loading, and error states are valid;
- scrolling consumes pointer/wheel input without leaking to content behind it;
- controller ownership and cancellation remain explicit;
- QML smoke and structural tests pass;
- The matching `help_articles/*.en.md` and `*.ru.md` files are updated for
  user-visible behavior; `HelpView.qml` and the translation catalog contain
  only viewer chrome.

## Enforcement

tests/test_ui_structure.py and tests/test_theme_controls.py are architecture
tests, not snapshots of incidental markup. New rules should be encoded there
when they can be checked mechanically. A temporary exception must name the
legacy file and may not authorize new violations.
