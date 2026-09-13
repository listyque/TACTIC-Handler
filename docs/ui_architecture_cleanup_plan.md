# Application UI architecture cleanup plan

This plan applies the rules in ui_component_policy.md. It is deliberately
incremental: preserve working behavior, remove duplicate paths, and extract only
a responsibility that has a stable contract and tests.

## Baseline

The current UI already has a strong shared foundation:

- feature QML uses shared controls instead of raw common Qt Quick Controls;
- colors are centralized in Theme.qml;
- common actions, popups, scroll bars, loading overlays, tabs, previews, and
  activation handling are reused broadly;
- QML smoke and structural tests cover the main composition contracts.

The remaining debt is concentrated rather than systemic:

- DockContentRegistry.qml and MessagesView.qml own several independent
  presenters and workflows;
- some task, configuration, and check-in surfaces remain large;
- responsive state is usually named but a few components still repeat local
  width tests;
- a small number of presentation components still exist as local duplicates.

## Working method

For every cleanup slice:

1. Inspect the existing implementation, original workflow, controller, model
   roles, tests, and all call sites.
2. Name the single responsibility being moved and its smallest public API.
3. Add or strengthen a behavior/structure test before moving it.
4. Reuse an existing component when possible; otherwise extract exactly one
   shared or domain presenter.
5. Replace all consumers and delete the superseded path in the same change.
6. Run structural, theme, QML smoke, and relevant domain tests.
7. Stop if the extraction adds adapters, compatibility readers, duplicated
   state, or indirection without measurable benefit.

## Completed foundation cleanup

- Replaced the stale component policy with the canonical architecture contract.
- Added repository and UI instructions for layer direction, reuse, motion,
  responsive state, and responsibility budgets.
- Added architecture tests for shared-control use, theme colors, motion tokens,
  qmldir integrity, and reverse imports.
- Centralized feature animation durations in Theme motion tokens.
- Moved ItemPreview, ItemSurface, ResponsiveFlow, ProfileInfoRow, and EmptyState
  into the shared controls library.
- Removed the duplicate root Typography singleton; feature QML now uses
  Controls.Typography.
- Replaced repeated anonymous breakpoints in Advanced Search, task bulk fields,
  and project configuration with named responsive states.

## Next slices

### Search workspace composition

Extract from DockContentRegistry only after the existing search lifecycle tests
cover the boundary:

- SearchWorkspaceChrome: search field, search tabs, overflow, sort/group/view;
- SearchResultsPresenter: tree, card, compact, paging, loading, empty/error;
- VersionsPresenter: snapshot/version placement;
- DockContentRegistry remains a kind-to-component router.

Acceptance: restored tabs, selection, paging, infinite scroll, resize, and
context actions behave identically. No controller state moves into QML.

### Messaging composition

Split MessagesView around existing controller ownership:

- ConversationList;
- MessageTimeline and message delegates;
- MessageComposer;
- selection, forwarding, reply, pin, reaction, and attachment action surfaces.

Acceptance: cached chat switching remains immediate; unread/read/delivery
state, focused-message navigation, pinned/replied links, and scroll-to-latest
retain their tested behavior.

### Task and operational surfaces

Review large task, configuration, check-in, and report files one by one. Extract
only repeated cells, presenters, and modal workflows. Keep data mutation,
server requests, caching, and cancellation in the existing Python controllers.

Acceptance: column alignment, responsive access to hidden controls, task
selection synchronization, repository/check-in progress, and restored window
geometry remain unchanged.

### Responsive consolidation

Continue replacing repeated width expressions with one named state per
component. Extend shared controls only when two surfaces share the same
content boundary. Do not impose one global breakpoint on unrelated content.

Acceptance: every primary action remains reachable at minimum sizes; resizing
does not trigger data reloads or preview redecoding when identity is unchanged.

## Definition of done

The cleanup is complete when:

- architecture tests and QML smoke tests pass;
- no reverse dependency exists from controls to feature QML;
- no duplicate semantic primitive or parallel data path remains;
- feature animations use theme motion tokens;
- oversized views contain one orchestration responsibility rather than several
  independent presenters;
- narrow and wide layouts preserve all primary actions and symmetric spacing;
- user-visible behavior changes, if any, are documented in HelpView and Russian
  translations in the same change.
