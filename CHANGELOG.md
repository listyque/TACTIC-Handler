# Changelog

Each completed change receives a new version and a dated entry below.
Versions use `major.minor.build.revision`; routine updates increment `revision`.

## 0.6.0.333 - 2026-10-31

- Keep the primary search workspace header actions round; preserve square icon buttons in local service toolbars.

## 0.6.0.330 - 2026-10-31

- Render pipeline progress nodes as legacy-style completed-object rings with related-task navigation, and give ordinary workflow cards quiet aligned rows. Keep native lazy task editors and compact preview geometry.

## 0.6.0.329 - 2026-10-31

- Arrange smaller process hover cards in a responsive grid with equal spacing, vertical scrolling and a separate Task Manager footer in both clients.
- Keep editing and Task Inspector navigation available, keep native hover handling active across popup padding.

## 0.6.0.327 - 2026-10-31

- Open Task Manager single-choice cells directly in the existing picker in Stream; preserve combined date editing and staged task changes.
- Use shared progress sliders with percentage readouts and quarter-hour planned-time steppers with visible units in both clients.
- Keep immediate single-field editors compact with one field title and preserve project duration units and field permissions.

## 0.6.0.326 - 2026-10-31

- Compact workflow hover cards in both clients; show up to three processes with horizontal scrolling for additional processes, bounded by the current window.
- Preserve status, assignee and date editing; prevent covered native inline cards from intercepting preview input.

## 0.6.0.325 - 2026-10-31

- Keep worker settings and explicit Stream restart in Configuration > Server; remove the duplicate Backend server section from Administration in both clients.
- Move the native editor/presenter to configuration ownership and embed its existing card in the server settings scroll before connection fields.
- Include remote worker drafts in configuration Save/Apply/Close guards, await save acknowledgement and discard stale continuations on session loss. Preserve restart confirmation and server-side access checks.

## 0.6.0.324 - 2026-10-31

- Match custom workspace page backgrounds and header corners to the native rounded dock interior.
- Keep the header bottom edge straight and text directly rendered; no whole-dock opacity mask or texture layer.

## 0.6.0.322 - 2026-10-31

- Center table headings, plain values and status chips on the same column axis, retaining explicit display justify/align choices.
- Use symmetric cell/header insets and preserve wrapping, status colors, selection, column grouping and resize behavior in Handler and Stream.

## 0.6.0.321 - 2026-10-31

- Expose 151 actual house-control variants in Component showcase, alongside the 29 family overviews. Search variant names, inspect their settings/code and reset the selected local example.
- Show round/square image previews, initials, outlines, contain/crop, loading, selection, shaded image cards and real image/file attachments.
- Reuse product-owned native/browser example adapters in the development fixtures. Keep showcase people and emoji models private, with explicit user-picker model injection.

## 0.6.0.320 - 2026-10-31

- Replace page filter checkbox/forms with one house search and matching field/value suggestions, highlighted as users type.
- Apply and remove typed conditions immediately across dashboard metrics, charts and tables; retain the focused input and all saved configuration.
- Read hints through the existing native custom-layout command with project/ACL constraints, query limits and stale-result guards in Handler and Stream.

## 0.6.0.319 - 2026-10-31

- Make modern service buttons square with the same small corner across themes: tables/count actions, search/paging tools, editors, pickers, chips, spin controls and dock tools.
- Reserve circular actions for primary navigation and window titlebars. Keep circular avatars, media, status marks and input indicators unchanged.
- Share button shape defaults and titlebar exceptions in Frame, with matching native/browser input and state checks.

## 0.6.0.318 - 2026-10-31

- Keep page panel backgrounds full width while header, content and footer children use symmetric shared inner spacing in Handler and Stream.
- Inset dashboard filters, report cards and footer actions without changing authored padding, margins or styles; keep scrollbar space and fitted navigator panes within their viewport.
- Verify actual narrow/wide filter input, authored grid breakpoints, canvas selection geometry and paired native/browser bounds.

## 0.6.0.317 - 2026-10-31

- Raise the active expanded related table with a shared shadow and dim the remaining parent table. Background input closes the same expansion without selecting a parent row.
- Remove the empty toolbar when search is disabled and put its remaining actions in the existing footer, using square service icon buttons. Enabled search retains the main suggestion workflow and related-object scope in both clients.

## 0.6.0.316 - 2026-10-31

- Add Administration > Backend server with shared worker-count controls, saved/running counts and an explicit restart confirmation in Handler and Stream.
- Apply saved configuration through the authenticated Stream monitor, reject stale revisions and repeated restart requests, and reconnect with a bounded status check.
- Preserve application, executor and project data ownership; require administrator access for remote server control.

## 0.6.0.315 - 2026-10-31

- Keep the task-count action clickable without triggering workflow expansion on hover; retain its Task Manager route and bulk selected-row editing.
- Show wider hover cards with normal-height status/assignee fields and dates, independently of the compact table-row height. Keep the manager action and both scroll directions usable inside constrained previews.
- Share expanded geometry and date-range labels with Stream and verify actual badge input and date editing.

## 0.6.0.314 - 2026-10-31

- Unify content spacing through shared Frame roles: consistent panel/form interiors, related-control gaps and section separation in both clients.
- Align mixed form rows, remove doubled dialog/body padding and trailing form gaps, and keep table/page bodies edge-to-edge.
- Apply the same spacing to object editors, settings, search/dock chrome, messages and file/support surfaces; preserve authored XML, scrollbar reserves and hit areas.
- Verify actual native/browser form, panel and dialog bounds, narrow layouts and actions across three themes and both palettes.

## 0.6.0.313 - 2026-10-31

- Complete live examples for all 29 component families with source, local drafts, eight state choices, real menus/confirmations, editable virtual cells, files, graphs, source editing and task fragments.
- Add neutral Frame adapters for existing search, identity, progress, empty-state and file controls; keep native file input behind a URL loader so Frame's type dependency remains acyclic and Handler starts normally.
- Keep sample operations local, preserve project records and validate real QML input, popup lifetime and both palettes alongside the browser implementation.

## 0.6.0.312 - 2026-10-31

- Sample all 50 load-balancing requests with up to eight independent authenticated clients, without stopping after repeated replies from one worker.
- Preserve the captured site in diagnostic clients and clarify that observed workers are a sample, not the configured process count, in both clients and EN/RU Help.


## 0.6.0.310 - 2026-10-31

- Restore System Info facts and diagnostics through the shipped client SDK's authenticated class-method API for XML-RPC and JSON.
- Clone the server address rather than its RPC proxy for parallel performance probes; verify real HTTP transports, session forwarding and remote permission errors.

## 0.6.0.308 - 2026-10-31

- Reserve two full shared heading line boxes for narrow showcase titles, so long EN/RU family names do not clip or collide with the subtitle.

## 0.6.0.307 - 2026-10-31

- Add Administration's local Component showcase: 29 inventoried families in six groups, with live examples for 16 families, search, state selection and read-only shared-API examples.
- Reuse the same canonical inventory for both clients and the source audit; distinguish shipped components, completed examples and remaining gaps. Cover typography, semantic surfaces, headings, badge/counter sets and grouped list rows alongside existing inputs and charts.
- Keep examples independent of project records and server commands, with EN/RU guidance and the shared source-editor service for native code presentation.

## 0.6.0.306 - 2026-10-31

- Add shared native bar, line and donut charts with hover values, signed/null handling and accessible labels; keep chart types editable through the page editor.
- Compose Workspace Pulse 1.1.0 with compact metrics, aligned chart/table cards and cached soft shadows in both themes.
- Remove implicit page side gutters, include table titles in block height, and fit embedded tables across all configured columns. Preserve main-table menus, editors, selection and virtualization with quieter dividers and passive status badges.

## 0.6.0.305 - 2026-10-31

- Verify Administration closes after viewing Plugins and after discarding changes, while preserving unsaved drafts; synchronize plugin closing guidance with Stream's public component-ref fix.

## 0.6.0.304 - 2026-10-31

- Keep plugin catalogue, resource and file-row selection and hit areas inside the shared list row bounds, so QML and browser gaps match.

## 0.6.0.303 - 2026-10-31

- Complete the shared plugin resource workflow: create/edit reusable widgets, table columns, light/dark project themes, selected data/schema, Python actions and installation/removal hooks through the native package lifecycle.
- Render modern nested item compositions in CustomLayout pages and cells; preserve native operations and personal appearance fallback across project changes and package removal.
- Verify the complete Studio Review plugin in both clients, including typed creation, theme editing, confirmed Python writes, export/reinstallation/removal and rollback after a late install failure. Extend English/Russian Help.

## 0.6.0.302 - 2026-10-30

- Remove five unused global QML model aliases while preserving the 179-binding architecture limit and existing feature controllers.
- Verify real startup binding publication and controller ownership; run the authentication-menu probe after loading the QML root and with fresh session authorization.
- Correct isolated regression imports, activity schema fixtures, Windows test timezone dependencies and window Help coverage.

## 0.6.0.301 - 2026-10-30

- Bind the shared column editor during application startup so embedded dashboard and nested tables can load their columns and open scoped definitions.

## 0.6.0.300 - 2026-10-30

- Document the installable Workspace Pulse example: portable task and VFX dashboards using existing native Handler and Stream components.

## 0.6.0.299 - 2026-10-30

- Keep the agent conversation sidebar rectangular in both clients, including its clipping container.

## 0.6.0.298 - 2026-10-30

- Remove the duplicate Search Type title and code above Summary statistics in both clients.

## 0.6.0.297 - 2026-10-30

- Remove passive explanatory paragraphs from the shared Search Types summary and bring the relationship map directly below its statistics. Keep the explanations in EN/RU Help.

## 0.6.0.296 - 2026-10-30

- Add shared project chat rules to the ordinary chat options in both clients, with native project/template storage, revision checks, per-turn snapshots and compatible-host detection.

## 0.6.0.295 - 2026-10-30

- Rebuild the shared plugin manager around guided package installation, content review and explicit project activation. Add first-run choices, contextual instructions, project status, visible creation controls and grouped maintenance actions; retain native file/manifest/distribution operations and EN/RU Help.

## 0.6.0.294 - 2026-10-30

- Remove the unused legacy sidebar-cache clearing control from System Info in both clients, its deletion command and redundant refresh wiring. Preserve normal navigation loading and client memory.

## 0.6.0.293 - 2026-10-30

- Compact the Search Types summary in both clients: group its counters, size explanations to their content and bring the relationship map closer to the statistics.

## 0.6.0.292 - 2026-10-30

- Add the complete legacy plugin manager to Administration in Handler and Stream: package creation, ZIP/URL staging, project activation, manifest/docs/files editing, export, publication and confirmed removal through native commands.

## 0.6.0.291 - 2026-10-30

- Port the complete legacy System Info panel to shared native/browser sections: server/client facts, load-balancing and sequential/parallel performance tests, email sender/recipient test, native handoff checks, project-page load test, saved Python script execution and fixed sidebar-cache clearing. Reuse original commands, preserve administrator authorization and report browser filesystem limits explicitly.

## 0.6.0.290 - 2026-10-30

- Remember the last chat connection, model, reasoning effort and change/internet permissions across new conversations and application restarts, scoped to the current account and server preset.
- Preserve each existing conversation's captured permissions and each unsent draft's explicit choices when restoring history.

## 0.6.0.289 - 2026-10-30

- Let the agent read/add native task and process comments with per-turn retry protection, and set actual object previews through the built-in icon check-in.
- Keep comments on secondary tasks in the owning project and render operation details as a compact disclosure instead of a full-width button.

## 0.6.0.288 - 2026-10-30

- Run the external agent beside Handler with local Codex authentication; offer server execution as an explicit alternative in both clients.
- Let the browser control its account's connected Handler through fixed project-scoped start/stop operations; stop owned local processes on sign-out/exit.
- Bundle the portable HTTP/MCP host and indexed references independently, preparing agent dependencies in a private cached environment only on Connect.

## 0.6.0.287 - 2026-10-30

- Align the project subtitle with the conversation title when the working indicator is present in All projects history.

## 0.6.0.286 - 2026-10-30

- Render Simple Table and expanded related tables with the main native table and column controller; share row, column and process menus, resizing, editing and view management.
- Remove the separate row drag grip and outer table gutters. Keep nested search, paging, checked rows, project/view context, cached branches and snapshot galleries independent of the main search.

## 0.6.0.285 - 2026-10-30

- Keep double-click inline editing separate from checkbox selection: focus the edited row without checking it or opening the bulk-selection bar.
- Preserve existing checked rows and bulk edit targets; verify ordinary focus, editor cancellation, explicit checkboxes and Shift ranges in both clients.

## 0.6.0.284 - 2026-10-30

- Connect and disconnect a project-scoped server-side agent executor from chat and AI provider settings, with shared progress/errors and duplicate protection. Preserve current-session scope and explicit per-request write permission.

## 0.6.0.283 - 2026-10-30

- Keep navigation badge glyphs in the theme text color for light Search Type accents; preserve automatic contrast on other previews.

## 0.6.0.282 - 2026-10-30

- Add a searchable native table-view manager with create/copy, label rename, guarded deletion and column-editor navigation. Preserve view codes, default protection, project scope, native undo and revision checks; exclude service definitions from table choices.

## 0.6.0.281 - 2026-10-30

- Wrap ordinary table text and links to the column width, preserving explicit line breaks and configured row heights.

## 0.6.0.280 - 2026-10-30

- Center icon-only table action cells, including wrapped action groups, while retaining text/value alignment and existing actions.

## 0.6.0.279 - 2026-10-30

- Add an optional Horizontal scrolling table mode that keeps all configured columns and existing widths on narrow screens; Auto Fit restores adaptive layout.

## 0.6.0.278 - 2026-10-30

- Preserve an untouched new AI connection while background host checks run or Configuration pages switch. Resume polling when returning to an existing connection.

## 0.6.0.277 - 2026-10-30

- Add column menus to nested tables, opening the native definition editor focused on the selected child column and preserving its project/view scope.
- Support right-click context actions on native Frame Action controls, matching the browser renderer.

## 0.6.0.276 - 2026-10-30

- Let expanded tables use the search viewport height instead of a fixed 320 px cap; keep short results fitted and preserve cached data during resize.

## 0.6.0.275 - 2026-10-30

- Fit expanded tables to short results, while keeping long lists bounded and preserving nested selection, cached data and paging.
- Remove duplicate outer padding; reserve horizontal scrollbar space and keep the footer next to the data.
- Use compact default checkbox/preview columns while retaining explicit column widths.

## 0.6.0.274 - 2026-10-30

- Let the native window own the Cell editor title; remove the duplicate title row from the shared content layout.
- Keep column context, value input and Apply/Cancel inside the available content area; preserve typed-value, NULL, default and draft-save behavior.

## 0.6.0.273 - 2026-10-30

- Reuse the task value display as the inline editor base, removing its duplicate host and property forwarding while preserving popup and pointer lifetime.
- Share real body/caption font metrics per QML engine; retain native measurement for other font families and roles.
- Cover font changes, editor surface reuse and 200% display scaling; document measured creation costs without dropping table rows, cards or actions.

## 0.6.0.272 - 2026-10-30

- Embed the existing AI connection editor directly in Configuration; remove the intermediate launch button and unrelated header save actions on that page.
- Preserve provider drafts while navigating, stop hidden polling and retain the standalone editor from the agent chat, including credential and revision checks.

## 0.6.0.271 - 2026-10-30

- Give Configuration projects a bounded catalogue surface with filter header and count footer, alongside a separate project action surface.
- Keep both panels aligned with 12 px padding and stack them on narrow windows without changing project operations.

## 0.6.0.270 - 2026-10-30

- Compact Access rules navigation with 30 px rows, smaller group gaps and centered icons while retaining the text size and scrolling.
- Align Administration content and headers with consistent 12 px outer padding in both clients.

## 0.6.0.269 - 2026-10-30

- Center collapsed administration navigation on the full rail when sections fit; reserve scrollbar space only when scrolling is needed.
- Use square compact selection targets and remove inactive selection stripes; retain short-window scrolling and expanded section labels in both clients.

## 0.6.0.268 - 2026-10-30

- Reduce warm QML creation by reusing task-field geometry/fonts, detaching table cell values once per revision, and skipping image/mask allocation for fallback avatars.
- Preserve live avatars, rounded previews, resize pixels, inline task editing and row reuse; share unchanged task-cell scenes with Stream.
- Keep one owned response copy and resolve display XML once per row batch; cover cache isolation and definition refresh.

## 0.6.0.267 - 2026-10-30

- Replace the administration project combo with a compact searchable project picker: cached previews/initials, readable titles/codes, selection marks and bounded scrolling.
- Keep all available built-in, template and archived projects accessible without changing workspace filters; retain draft locks and keyboard/touch selection in both clients.

## 0.6.0.266 - 2026-10-30

- Explain application feature rules with named choices, descriptions, Allow/Deny and explicit legacy-screen limits; preserve non-binary native levels and provide inheritance reset.
- Reveal focused Frame buttons inside scrolling editors; verify feature selection and draft changes in native and browser clients.

## 0.6.0.265 - 2026-10-29

- Add a saved effective-user permission report with native access checks, direct/inherited groups, combined defaults and source rules.
- Configure separate group allowlists for chat and MCP tools through the existing revisioned Access rules editor; retain native operation authority and show agent eligibility explicitly.
- Keep newly focused navigation actions visible in scrolling Frame sections, with matching native and browser behavior.

## 0.6.0.264 - 2026-10-29

- Modernize the Access rules editor with grouped icon navigation, section explanations, bounded work panels and a readable permission legend.
- Replace clipped checkbox captions with explicit access labels, square matrix surfaces and row dividers; add icons to rule actions and guarded navigation back from technical views.
- Preserve native permission semantics and drafts across wide/compact layouts, keyboard and touch input.

## 0.6.0.263 - 2026-10-29

- Require authenticated native administrator authority for administration, account/group writes and privileged directory reads; group/login names no longer grant these operations.
- Add a shared group-inheritance editor with project/group choices, transitive cycle guards, preserved external entries and native revision-checked saves.
- Document additive TACTIC access semantics and verify inherited permission revocation with the same ticket on private data.

## 0.6.0.262 - 2026-10-29

- Verify that stock preview upload fields with icon_size display metadata retain the native image picker. Document staged selection and the existing shared check-in path alongside the Stream preview fix.

## 0.6.0.261 - 2026-10-29

- Use the common small dialog radius in every theme and the standard themed native frame for sign-in. Document shared window chrome, while preserving native controls and editor close guards.

## 0.6.0.260 - 2026-10-29

- Keep a consistent icon-to-label gap in Sidebar Editor tree rows, including nested entries and secondary text, without reducing the folder-toggle clearance.

## 0.6.0.259 - 2026-10-29

- Add the native Related objects window using existing scoped tables, creation/edit operations and standard window hosting. Add its relationship-menu entry, shared toolbar and menu styling, with cancellation and cleanup on close or context changes.

## 0.6.0.258 - 2026-10-29

- Document restored stock Task Workflow and expression-column availability from TACTIC Stream, retaining native edit permissions and rejecting unknown callbacks.

## 0.6.0.257 - 2026-10-29

- Document the corrected shared CG Episode configuration: native previews, names and task controls, with scoped asset and saved shot tables.

## 0.6.0.256 - 2026-10-29

- Document the existing table-width contract: headers and rows fill the viewport, reserving space only for scrollbars that actually overflow. Verify native scrollbar transitions alongside the Stream workspace-gutter fix.

## 0.6.0.255 - 2026-10-29

- Show empty link placeholders such as Not script as ordinary text, without an underline or link cursor. Keep saved URLs clickable and document the CG Script column's link-only presentation.

## 0.6.0.254 - 2026-10-29

- Verify that the native Name-column resize materializes a missing schema column while retaining existing options and column order. Document matching first-resize and retry behavior alongside the Stream fix.

## 0.6.0.253 - 2026-10-29

- Document that existing table column widths persist without adding Undo or activity-history entries on TACTIC Stream. Creating views and changing other definition settings remain audited; the server owns this rule for both clients.

## 0.6.0.252 - 2026-10-29

- Identify local Python and DCC shelf actions with a TH marker and a runtime tooltip. Preserve server/browser execution distinctions, permissions and dispatch. Verify controller metadata, native shelf input and shared EN/RU presentation.

## 0.6.0.251 - 2026-10-29

- Measure tag labels in the rendered font and include actual button icon, padding and spacing. Keep short and wide Latin/Cyrillic names visible and wrap complete chips into the next row in both clients. Verify native text elision, editing and browser bounds.

## 0.6.0.250 - 2026-10-29

- Center resize hit strips on dividers, including the outer edge of the final column beside header tools. Keep manually resized columns visible during and after width acknowledgement so the final adaptive column does not disappear mid-drag. Preserve the previous width on native drag cancellation, accept changed authoritative widths, and retain ordinary adaptive hiding in Handler and Stream. Update EN/RU Help.

## 0.6.0.249 - 2026-10-29

- Bind hidden-table disclosure and loading icons to the active row, column and nested scope. Keep neighboring arrows unchanged, including columns that reuse the same view, in Handler and Stream. Preserve expansion/caching behavior and update EN/RU Help.

## 0.6.0.248 - 2026-10-29

- Make the table Check-in button toggle Drop Plate through the existing dock owner. Hide without clearing files or preparing the target again; raise covered tabs and preserve explicit Task Work opening in Stream. Retain existing target/discard guards and update EN/RU Help.

## 0.6.0.247 - 2026-10-29

- Use square workspace-tab backgrounds in Handler and Stream. Preserve the selection underline, close feedback and all other component radii; check actual tab rendering and input in both clients.

## 0.6.0.246 - 2026-10-29

- Keep ready table cells visible while an unchanged definition refreshes, preventing History disclosure blanking between definition and row responses. Reject late definition replies from another project. Add symmetric breathing room to expanded nested tables in Handler and Stream. Verify native/browser input and narrow/wide bounds; update EN/RU Help.

## 0.6.0.245 - 2026-10-29

- Bound native graph connection backing surfaces to their painted content instead of the full viewport. Preserve zoom, selection and input while avoiding blank bitmap reallocation on resize. Add a native resize regression and shared paint-bounds checks; verify nine paired graph states.

## 0.6.0.244 - 2026-10-29

- Give main and nested table headers a distinct neutral theme surface and strong foreground. Keep grouped labels and indicators readable in light/dark themes, preserve sorting and geometry, and match Stream. Update EN/RU Help.

## 0.6.0.243 - 2026-10-29

- Keep object-card titles and descriptions readable over bright previews. Share the image-shading stops with Stream and use the theme primary/selection foreground for object-card captions. Verify real preview paint and contrast in light/dark and selected states; update EN/RU Help.

## 0.6.0.242 - 2026-10-29

- Restore the original CG Episode Storyboard and Renders hidden snapshot galleries. Preserve episode/project/process filters, use virtualized preview tiles with the existing checkout dialog, and show explicit empty results and bounded pagination. Match Stream and update EN/RU Help.

## 0.6.0.241 - 2026-10-29

- Keep Refresh visible beside the search field in narrow docks and reserve its space before the field. Preserve collapsed phone search behavior and verify resizing, mouse and keyboard activation with the normal refresh command.

## 0.6.0.240 - 2026-10-29

- Avoid blocking Windows OpenGL resize synchronization on VSync, preserving the existing renderer and explicit environment overrides. Reuse notified item-layout document snapshots during resizing instead of repeatedly copying the XML tree. Add native read-budget and rendering-policy regressions.

## 0.6.0.239 - 2026-10-29

- Load the saved column definition on the first table activation after launch, even when the table surface was created before its search tab. Reuse an in-flight definition request for repeated activation signals; preserve explicit reloads and context changes.

## 0.6.0.238 - 2026-10-29

- Regroup Page layout controls in a shared toolbar: explicit New page beside the picker, direct preview/XML actions, a labelled secondary Actions menu, and Undo/Redo beside canvas tools. Keep empty catalogs clear, preserve draft/save guards and keep paper-edge resize handles usable under zoom. Match Stream and update EN/RU Help.

## 0.6.0.237 - 2026-10-29

- Read page editor documents, metadata and catalogs through detached presentation snapshots instead of repeatedly converting nested QVariant property references. Coalesce custom page and editor viewport dimensions within one event turn, preserving immediate data/actions, native input, drafts and the existing UI. Add native snapshot and nested resize regressions.

## 0.6.0.236 - 2026-10-29

- Show labeled editor-only sample data in Item layouts when real records are absent or do not match the selected widget. Preserve real previews and errors, support canvas selection/resizing, and save configuration without creating sample records. Match Stream and update EN/RU Help.

## 0.6.0.235 - 2026-10-29

- Open nested reusable Item layouts directly from widget properties and return through the parent chain with the original configuration source, widget and panel state. Protect unsaved edits and reject unavailable references. Restore ordinary mouse/keyboard/touch activation of draggable native widget rows while retaining drag/drop. Match Stream navigation and EN/RU Help.

## 0.6.0.234 - 2026-10-29

- Follow page widget references directly to the exact item layout, table-column definition or linked page, with a return action and retained editor drafts/view state. Reveal canvas selection in the widget tree without taking keyboard focus from the canvas. Use the same compact field actions and navigation rules in Stream.

## 0.6.0.233 - 2026-10-29

- Let configured item trees show an explicit per-type navigation path using existing relationships, with native task branches and meaningful relationship labels. Keep ordinary views and access rules unchanged; pair this with Stream's project-scoped task relationship discovery.

## 0.6.0.232 - 2026-10-28

- Compact Page Layout tools above the canvas, move uncommon actions into the existing menu, and place Add widget inside the icon-bearing collapsible block tree. Add resizable, collapsible tree/properties panes and a narrower Administration icon rail. Show the exact generated draft XML in the shared read-only source viewer. Initialize the native item preview splitter and resume the latest detail preview after a stale reply even when the document is unchanged. Keep draft history and server saves explicit.

## 0.6.0.231 - 2026-10-28

- Discover Item Layout Search Types from the selected project's current server catalog instead of cached/global registry metadata. Share table availability and read-policy checks with Stream; replace failed-preview loading placeholders with their actual error.

## 0.6.0.230 - 2026-10-28

- Separate configured pages into shared header, scrolling content and footer regions. Expose region placement in the page editor; retain stable widget paths and bounded header/footer scrollbars. Give nested tables clear toolbar and pagination surfaces, matching Stream.

## 0.6.0.229 - 2026-10-28

- Stop readonly Markdown reports and Help articles from continuously reformatting and repainting while idle. Apply only changed paragraph/table formats and avoid empty QTextDocument edit blocks that emit textChanged. Check real idle readers and content updates. Restore Qt-compatible catch syntax so the Layout Editor loads.

## 0.6.0.228 - 2026-10-28

- Explain how configured pages display stored record fields, how Edit opens the native edit definition, and how to expose missing long-text fields without changing the page layout or record data.

## 0.6.0.227 - 2026-10-28

- Verify painted task and note counter badges on configured cards, including changing counts, hidden zero, 99+, exact tooltip values and native mouse/keyboard actions. Document the matching Stream behavior.

## 0.6.0.226 - 2026-10-28

- Render configured item fields as colored statuses, dates and progress using existing native controls. Add card group surfaces and editor value colors. Keep action buttons square and usable; show named-action counts once and preserve native task/note routing, matching Stream.

## 0.6.0.225 - 2026-10-28

- Fix first-opening custom sidebar pages remaining behind the empty workspace, collapse mouse-focused section labels after pointer leave, and hide the Search drag grip on custom pages. Cancel dock gestures through their real panels. Move frame diagnostics and navigation feedback off Python render-thread callbacks to prevent GUI/GIL deadlocks while preserving per-frame readiness cutoffs.

## 0.6.0.224 - 2026-10-28

- Fit dashboard content to the available body width and reserve the outer scrollbar gutter only when the page overflows. Verify both responsive grid thresholds; document bounded composer growth and status-card color fallback in Inspector Help, matching Stream's browser fixes.

## 0.6.0.223 - 2026-10-28

- Verify configured item height and native action identity through repeated pane resizing. Document retained tree geometry; the Stream counterpart preserves measured custom-card heights while moving splitters instead of reverting to default estimates.

## 0.6.0.222 - 2026-10-28

- Synchronize relative event ages with server UTC over monotonic request timing in polling and SSE, preserving actual local event dates when workstation clocks differ. Match Stream's activity day filters and calendar counts to the user's IANA time zone, including DST boundaries, and isolate calendar caches by zone.

## 0.6.0.221 - 2026-10-28

- Verify that dashboard buttons to connected-server pages use native workspace tabs, including work, tasks and analytics. Clarify internal versus external links in page-layout Help; the Stream counterpart now uses the same routing.

## 0.6.0.220 - 2026-10-28

- Reserve scrollbar gutters in the MCP form and permission list at normal and high display scales. Add explicit Select all tools and server-advertised No expiration while preserving revocation, project scope and owner authentication.

## 0.6.0.219 - 2026-10-28

- Keep expanded note attachment images decoded while resizing. Reuse the loaded image and rounded mask instead of re-requesting pixel sizes, preventing fallback flashes and aspect-ratio jumps. Preserve compact thumbnail decoding.

## 0.6.0.218 - 2026-10-28

- Share plain JavaScript icon glyph dictionaries once per QML engine instead of repeatedly crossing the QVariantMap boundary in each icon. Preserve icon packs, aliases and live font-context updates.
- Create task-card preview popups and hidden count-button surfaces on first use, retaining created controls for repeat interactions. Coalesce duplicate opening notifications for the same in-flight table layout while preserving explicit refreshes and context changes.
- Benchmark actual bundled icon fonts and report synchronous component creation, table activation and row population separately from rendering and frame presentation.

## 0.6.0.217 - 2026-10-28

- Render MCP permission captions, descriptions and read/write access as compact bounded rows, with explicit selection counts and a separated action footer. Align connection name/lifetime and reduce unused form space without changing access policy.

## 0.6.0.216 - 2026-10-28

- Add a native table-render diagnostic using Qt renderer logs and asynchronous GPU timestamps. Report rendering, synchronization, layout and presentation wait separately; retain end-to-end page timings as a different metric.

## 0.6.0.215 - 2026-10-28

- Reuse the sidebar base tab for its assigned Saved Search instead of opening a duplicate preset tab. Retain personal tabs and other saved searches by their actual identity.

## 0.6.0.214 - 2026-10-28

- Fit native Items/Details dashboard pairs to one viewport with independent scrolling and the existing mouse/keyboard splitter. Preserve the item tree when resizing.
- Keep implicit single-column item groups readable instead of assigning zero text width; document compact report cards without unused previews.

## 0.6.0.213 - 2026-10-28

- Populate search table, list and tile delegates only when each presentation is first opened. Retain already opened models, visible delegates and scroll positions across tab switches, and restore pending table scroll after the first layout.
- Instantiate task-card date content only when the row is tall enough to display it. Extend the offline QML benchmark to cover the complete search surface and report the actual rendering API.

## 0.6.0.212 - 2026-10-28

- Clip table text to its own cell so long multiline descriptions cannot paint over adjacent columns or rows. Keep one column resize grip per header and remove the duplicate marker in the drag area.

## 0.6.0.211 - 2026-10-28

- Reuse native smart search and suggestions in dashboard item trees and embedded tables. Keep parent/page constraints and submitted-query paging, reject stale suggestions, and show matching disabled editor search. Match Stream's NULL-presence filters in native scoped tables. Localize search labels and validation messages in EN/RU.

## 0.6.0.210 - 2026-10-28

- Render idle task values directly from shared cell geometry, without recursive Frame trees. Skip empty child scenes and avoid transferring all table cells when no summary is configured. Preserve lazy editors, avatars, scrolling and task-card interactions.

## 0.6.0.209 - 2026-10-28

- Use a full-row selection fill for table keyboard focus and active records instead of a separate outline; keep checked selection independent.

## 0.6.0.208 - 2026-10-28

- Let the shared search header omit reserved grip space in the browser while retaining native header geometry.

## 0.6.0.207 - 2026-10-28

- Render the shelf toggle as a round unfilled icon action; indicate an open shelf through the icon color instead of a persistent filled button.

## 0.6.0.206 - 2026-10-28

- Document floating dock chrome as the visual reference for floating windows and require quiet integrated resize grips.

## 0.6.0.205 - 2026-10-28

- Show the same visible column-boundary grip in result tables and task table headers, with accent feedback on hover.

## 0.6.0.204 - 2026-10-28

- Combine the selected-record count and clear action into one compact left-aligned Deselect button.

## 0.6.0.203 - 2026-10-28

- Highlight the active table row independently from checked records. Plain clicks show the active row without enabling its checkbox or the selected-record bar.

## 0.6.0.202 - 2026-10-28

- Remove the dark strip beneath result table headers and reserve scrollbar space only while the corresponding scrollbar is needed.

## 0.6.0.201 - 2026-10-28

- Keep table row focus separate from checked selection: use Shift-click or checkboxes to select, and clear checks directly from the selected-record bar.

## 0.6.0.200 - 2026-10-28

- Use square corners for inline notices and task pending-change bars in shared screens.

## 0.6.0.199 - 2026-10-28

- Add record-bound field displays, native inline forms and named record actions to dashboard composition. Reuse native EditWdg/EditCmd permissions, revision checks and transaction Undo; retain local drafts by record and recover uncertain saves without retrying writes. Preserve the existing item hierarchy and update only the selected detail pane.

## 0.6.0.198 - 2026-10-28

- Add responsive dashboard grids, row/column spans and fixed/fill/content sizing with native font measurement. Expose headings, icons, object thumbnails, native link buttons, dividers and spacers through the page editor and shared agent schema. Keep existing data/record permissions and revisioned Save.

## 0.6.0.197 - 2026-10-28

- Add page-canvas multiple selection, marquee, group movement, alignment and snap guides with atomic local Undo. Preserve container hierarchy with validated pixel offsets. Expose block fill, stroke, radius, shadow and opt-in layout animation through the same saved dashboard contract in Handler and Stream.

## 0.6.0.196 - 2026-10-28

- Add page-editor viewport widths, custom pixel width, zoom and fit-to-width using native Frame rendering and scrollbars. Keep data/history independent of view settings and preserve logical resize coordinates at every scale.

## 0.6.0.195 - 2026-10-28

- Add local page-draft Undo/Redo, subtree duplication, explicit parent selection, sibling reorder and ancestor breadcrumbs in the shared native/web page editor. Keep text editing shortcuts native and all page changes behind the existing validated save.

## 0.6.0.194 - 2026-10-28

- Keep shared page-filter button captions fully visible in Russian in both native and web dashboards.

## 0.6.0.193 - 2026-10-28

- Add shared page filters with transient Apply/Reset and explicit field mappings. Compose grouped reports and bar charts with native count/sum/average/min/max, UTC date buckets, bounded result groups and numeric metrics directly in the page editor. Use existing native grid/tree controls, revisioned configuration and agent tools; requires Stream 0.112.251.

## 0.6.0.192 - 2026-10-28

- Add page data-source, saved-view, typed filter and content-binding controls backed by a compact native catalog. Pick fixed records and bind project/selection/record fields without XML; preserve source references for review. Guard late metadata replies and retain false, zero and empty predicates through native search cards. Requires Stream 0.112.250 for the page data catalog and binding contract.

## 0.6.0.191 - 2026-10-27

- Generate readable structural layout XML while preserving mixed text, CDATA and xml:space. Add explicit XML formatting, clean read-only draft previews and overlapping-layer selection with Alt-click. Allow selecting flow children without unsupported grid resize handles; preserve runtime item flow and global UI.

## 0.6.0.190 - 2026-10-27

- Add regression coverage that workspace layout resizing preserves the existing table owner, selection and filter. Verify native dashboard detail selection does not reload its result tree; the corresponding web fix watches data scope independently of geometry.

## 0.6.0.189 - 2026-10-27

- Fix clipped icons and selection in collapsed Administration navigation. Reserve the scrollbar gutter, keep usable section targets and align the expand control with the icons; preserve expanded navigation.

## 0.6.0.188 - 2026-10-27

- Add a separate Page layouts editor for saved navigation dashboards, using the existing native dashboard, table and item renderers with isolated preview scopes. Resolve draft details against a private sample record and keep business controls inactive on the canvas. Keep Item layouts as a separate document level. Add canvas selection, responsive-flow drag/reorder, pixel resize handles, grid card movement and spacing properties; preserve automatic item flow and global UI styling. Validate geometry and retain revision/operation protection when saving.

## 0.6.0.187 - 2026-10-27

- Expose Search Type/current view, saved-view navigation and explicit blank/template/copy creation in Layout Editor. Keep document selection outside technical settings, confirm dirty switches, and open the saved result independently of the editor. Preserve view navigation after failed reads; refresh preview even when views share their source XML.

## 0.6.0.186 - 2026-10-27

- Keep labelled Administration navigation in Workflow; use the existing editor library and panel tabs on narrow widths. Add inner spacing to library and inspector controls and show configured Search Type colors without replacing pipeline/process colors.

## 0.6.0.185 - 2026-10-27

- Unify Configuration and Administration window headers: one full-width header, aligned section actions and window controls, and one contextual Help action in the embedded Layout Editor. Preserve draft/close guards and workspace restoration.

## 0.6.0.184 - 2026-10-27

- Compose dashboards with the existing item tree on the left and selected-record content on the right. Keep expansion and pagination when selection changes; discard stale detail responses. Administrator agents can save this arrangement through the normal dashboard tools.
- Preview item layouts on actual expandable result records. Compose project-specific grid cards from shared widgets and reusable views, target their actual Search Types, and retain ordinary tree actions and branches.
- Render configured grid cards in the native result list using shared Frame geometry; keep draft previews read-only and reject stale preview replies.

## 0.6.0.183 - 2026-10-27

- Add a compact branch-search button to expanded relationship/process rows in the existing item tree. Filter only that branch, retain the original children and restore them when cleared.

## 0.6.0.182 - 2026-10-27

- Embed the existing expandable item workspace in agent-authored dashboards, retaining native search-tab models, relationship/process branches, selection and object actions. Keep general UI geometry unchanged.
- Keep snapshot geometry valid during the existing wide/compact loader transition.

## 0.6.0.181 - 2026-10-27

- Use square corners only for embedded table headers and data-row backgrounds. Restore the prior theme geometry, control sizes and existing item views after reverting the rejected dashboard tree redesign.

## 0.6.0.179 - 2026-10-26

- Open configured dashboard/navigation layouts as native workspace pages instead of document windows. Reuse the shared responsive layout, metric cards and embedded table controls; retain per-tab filters and ordinary object layout windows.

## 0.6.0.178 - 2026-10-26

- Expose native task preparation and batch creation/editing to the external agent through the shared server tools. Use actual inspector fields/status workflows, revision checks, retry protection and native transactional rollback; show task operation progress in chat.

## 0.6.0.177 - 2026-10-26

- Keep agent connection, model and reasoning choices in the compact composer toolbar at ordinary chat widths, including with history open. Bound chooser widths when the toolbar wraps in narrow windows.

## 0.6.0.176 - 2026-10-26

- Handle mouse-wheel and trackpad scrolling in shared Frame scroll containers, including Configuration. Keep native scrollbars and let nested containers pass unused wheel movement to their parent.

## 0.6.0.175 - 2026-10-26

- Copy a single scoped agent link from MCP connections. The link carries its token in a fragment; project startup instructions arrive through authenticated discovery and MCP initialization. Normal MCP header-based clients remain supported.
- The server can update connection tools/instructions with revision and retry guards, preserving the existing token. External clients can upload local files through bounded native attachment chunks before check-in.

## 0.6.0.174 - 2026-10-26

- Open connected-server custom page URLs as native tables/layouts with captured project context and stale-response protection.
- Render shared dashboard bricks, including Markdown and fixed-filter tables, and honor navigation icon/color overrides. The agent can preview/save existing sidebar organization through native commands.
- Add the ordinary MCP connections window: selected project/tools, instructions, expiry, one-time token collection and revocation. The server listener remains off until explicitly enabled. Arbitrary legacy HTML/Python widgets remain outside this portable renderer.

## 0.6.0.173 - 2026-10-26

- Let the external agent find and read the current user's earlier chats across projects. Add an explicit source-chat link from the shared conversation library without changing the target project's selection or permissions.
- Compact the chat composer by moving change/internet permissions and provider settings into the existing toolbar menu; retain visible checked states and frozen permissions after Send.

## 0.6.0.172 - 2026-10-26

- Document the shared external host's opt-in all-project discovery so newly created projects can become available in both clients without a manually edited project list.

## 0.6.0.171 - 2026-10-26

- Clear chat refresh errors after the next successful automatic read, so a temporary connection loss does not hide the saved task result. Keep rejected operation errors separate and never resend writes during reconnection.

## 0.6.0.170 - 2026-10-26

- Show the signed-in user's conversations across accessible projects by default and add a direct project filter to the shared sidebar. Show each chat's project and keep execution, attachments, folders and unsent drafts bound to their original project when switching.

## 0.6.0.169 - 2026-10-26

- Expose ordinary related-task reading and bulk status edits to the external agent through Stream's native table-task command, including real workflow choices, revision/permission checks and durable retry protection. Show task activity in the shared chat.
- Let the agent derive final statuses from the actual status graph. Companion Stream repairs four CG template callbacks that selected a foreign project and removes one connection to a missing process while preserving existing processes.

## 0.6.0.168 - 2026-10-26

- Show agent activity and completion in the assistant transcript column, after messages and tool details, instead of the chat window corner. Preserve the same status/error semantics in both clients.

## 0.6.0.167 - 2026-10-26

- Replace the agent conversation picker with a persistent sidebar: time/type/folder grouping, named drafts, pins, search and archive, with revision-checked per-user/project storage on Stream. Preserve unsent messages when switching chats.
- Use plain list rows and quiet group captions in chat history, workflows and related administration/project/object lists. Keep secondary row actions available on hover, keyboard focus and touch.

## 0.6.0.166 - 2026-10-26

- Open the external agent from the basic object context menu, with the clicked object or selected group captured in a new chat. Keep existing conversations and protect unsent drafts/attachments when switching objects. Companion Stream exposes the same action.

## 0.6.0.165 - 2026-10-26

- Add the native AI providers editor in Configuration and the chat: Codex account, OpenAI, compatible/local APIs, Anthropic and Gemini; write-only credentials, revision checks, connection/model discovery and defaults through Stream.
- Choose the connection and its actual offered models in the shared chat, preserving choices between turns. Submitted data is bound to the explicitly selected destination; changing or disabling that profile stops API execution until another Send.
- Preserve unsaved connection drafts on close and clear them on sign-out. Companion Stream stores credentials encrypted and exports only packages bound to the registered external host.

## 0.6.0.164 - 2026-10-26

- Align operation details with the assistant's transcript column at wide and narrow sizes, using the shared message geometry.
- Show readable object-definition/relationship/creation activity. The companion Stream agent can create native project records and linked children, and attach existing assets through native instance relationships without duplicate links; answers use display names rather than replacing them with codes.
- Link the captured selection with only the target object's key. Handle retry identity internally and return confirmed display names; skip mandatory manual/catalogue reads for routine record/link tasks.

## 0.6.0.163 - 2026-10-26

- Label the external agent's optional network permission as internet access. The companion Stream host can download public HTTPS references into conversation attachments, preserving source URLs, hashes and native check-in receipts.
- Show download/history progress and let the companion agent inspect native file history and continue an existing version series without changing naming or overwriting files.

## 0.6.0.162 - 2026-10-26

- Keep Commit Queue visible in one host: opening its window hides the queue dock, and showing the dock closes the separate window. Closing either host preserves the prepared queue.

## 0.6.0.161 - 2026-10-26

- Send attachment-only agent messages, show sent image thumbnails after reopening, enable desktop Enter/Shift+Enter input, and describe current tool activity in the transcript column.
- Offer optional native web search for new conversations independently of TACTIC write permission. Requires Stream 0.112.219, which also repairs attachment source extensions and native image/latest naming.

## 0.6.0.160 - 2026-10-26

- Select model-supported reasoning effort in the shared external-agent chat and retain it between turns. Reset effort when switching models and preserve an explicit return to Agent default. Requires Stream 0.112.218.

## 0.6.0.159 - 2026-10-26

- Replace the external-agent form with a native shared chat, compact context chips, Markdown answers, attachments from the clipboard/file picker/drop, account-supplied model selection, active-turn corrections, retained follow-ups and completion notifications.
- Extend the companion Stream tools to native existing-project workflows, entity edits and attached-file check-in with revisions and durable retry receipts. Offer guarded Undo for the latest entity-field patch; preserve later edits and explicitly exclude other operation kinds.

## 0.6.0.158 - 2026-10-26

- Use compact 40 px captions with 13 px titles, neutral themed header colors and visible outer frames for shared dialogs. Keep native operating-system frames on standalone windows; synchronize Stream window styling and Help.

## 0.6.0.157 - 2026-10-25

- Send requests to a connected external agent from the native modal, capturing the current project, page, table view and selected objects. Review context, authorize configuration changes, follow progress, cancel and reopen durable requests. Script activation remains separately reviewed.

## 0.6.0.156 - 2026-10-25

- Review agent-authored drafts and isolated trial reports inside Script Editor, using the same Frame layout as Stream. Inspect the exact source and binding, distinguish stale reports, and explicitly confirm activation with revision checks and durable retry receipts. The review panel never executes draft code.

## 0.6.0.155 - 2026-10-25

- Open table column display declarations from the header menu instead of form input definitions. Resolve inherited definitions and custom named views, show exact widget identifiers, and search saved configuration XML in both clients.

## 0.6.0.153 - 2026-10-25

- Render VFX Planner and Shot Sheet as shared native compositions with independently scoped tables, configured filters, asset drag/link controls, retained script tabs and complete report printing. Resolve configured CustomLayout sidebar links.
- Run the ordinary snapshot-to-Review picker through the isolated JavaScript worker and transactional Stream submission command, preserving the exact version, actor, duplicate protection, cancellation and stale results. Require the corresponding Stream server; old production Submit/Bin, RV applets and Maya remain excluded.
- Synchronize native table/query contracts, workflow Help and paired Planner/Review captures with Stream. Existing project XML still requires explicit reviewed repair.

## 0.6.0.152 - 2026-10-25

- Render VFX TextInputWdg through the native text editor and transport WikiElementWdg as safe multiline text, including the original-server table query. Retain configured form values, required/read-only flags and ordinary EditCmd saving.
- Synchronize the standard Wiki table catalogue with TS 0.112.209 and document the paired VFX checkpoint: scoped Review tables, guarded Planner Drop links, parent task notes and the prepared Camera form. Old production submission/detail and Maya/applet workflows remain excluded; VFX composition and scripts are not declared complete.

## 0.6.0.151 - 2026-10-25

- Add project-scoped automation authoring to the public and fixed remote Handler API: inactive drafts, guarded activation and durable receipts are stored by native TS commands. The trigger editor now saves its complete rule set atomically; TS 0.112.207 and the normal schema upgrade are required.
- Supply captured input files, operation identity and completed snapshot to check-in hooks. Reject overlapping Before actions instead of bypassing validation, defer After hooks, respect cancellation during a validator and preserve failure output. Add an explicit executable/argv helper with timeout and exit-code checks.
- Pass a captured project/tab/selection context to Local Python shelf scripts; native modal Frame tools reuse the current engine and dispose on close. Keep draft saving separate from code activation; no isolated arbitrary-code runner is provided.

## 0.6.0.150 - 2026-10-24

- Organize maintained documentation around client APIs, native UI contracts and shared Frame ownership. Rename former implementation-plan documents as contracts, move Frame guides into one directory, and keep historical verification journals outside the repositories. Runtime behavior and product Help are unchanged.

## 0.6.0.149 - 2026-10-24

- Separate Handler client APIs, native structures and Help from Stream server references in agent documentation. Keep shared UI/table contracts in English and move development journals and the cleanup backlog out of the product repositories. Product localization and runtime behavior are unchanged.

## 0.6.0.148 - 2026-10-24

- Resolve legacy template IconWdg symbols and known raster names/paths through the shared modern icon catalogue, including VFX navigation, Bootstrap LIST_ALT and the old Font Awesome TELEVISION spelling. Preserve project XML and custom icon diagnostics. Pair with Stream 0.112.202; all five supplied icon sets use the same policy.

## 0.6.0.147 - 2026-10-24

- Fix Check-in (Full) cells for tasks and notes: remove a conditional import that shadowed the query-level re module and caused UnboundLocalError. Preserve parent/self target resolution and numeric context suffix normalization. Pair with Stream 0.112.201 regression coverage; restart Handler to load the new Python procedure.

## 0.6.0.146 - 2026-10-24

- Preserve configured nested search/edit/insert views and open the VFX bidding form for child task creation and editing. Pair with Stream 0.112.200, including scoped saved conditions, computed totals and safe currency formatting under C locale.

## 0.6.0.145 - 2026-10-24

- Register the migrated SnapshotInfoWdg value adapter for Checkin Log owner captions, preserving names, codes and missing-reference labels without a pyasm.prod alias. Pair with Stream 0.112.199.
- Share the supported log definition and its exact snapshot file rows; omit the excluded legacy RenderSubmission entry from the built-in log.

## 0.6.0.144 - 2026-10-24

- Support legacy SnapshotFilesWdg hidden rows as scoped file tables, with file links, directory metadata, types, ranges and sizes. Use the exact snapshot XML file membership, including empty versions, in the independently shipped native procedure. Pair with Stream 0.112.198.
- Restore ordinary nested-table record values when no computed cell exists, and filter file tables by filename.
- Recursive contents of directory packages and Maya/applet actions are outside this checkpoint.

## 0.6.0.143 - 2026-10-24

- Open imported legacy ViewPanel sidebar searches as tables by default, including direct searches for a configured type. Preserve explicit view modes, Handler-specific preferences and retained tabs. Pair with Stream 0.112.197.
- Fix task SObject Info refresh without a project Search Type, resolve the task's own project and work hours, and show process and referenced object code in its title.
- Initialize reports on the first native window opening and retain their selected object through background selection restores.
- Make object reports, record editors and relation editors modal; close reports when navigating to workspace task, note and object contexts. Match Stream report geometry to the native report.

## 0.6.0.142 - 2026-10-24

- Query related objects through the saved owner's identity, including native connection relations and ID-only records. Keep excluded record classes out of the expandable tree, matching navigation availability.
- Pair with Stream 0.112.195: show check-in history in the scoped snapshot table and preserve readable headers and code columns in nested VFX tables. The adapted VFX example uses native frame fields and the object inspector instead of excluded production widgets.
- Honor the sidebar's configured table view when opening its section, saved searches and new search tabs; Sequence now opens its Shots and schedule columns instead of silently selecting the default table.
- Retain wildcard child relations, filter evaluated objects by identity instead of walking the same relation twice, and preserve formatted expression cells. Apply server width hints to clean table layouts without replacing explicit or unsaved widths.

## 0.6.0.141 - 2026-10-24

- Honor global and wildcard navigation grants, project-specific overrides and view access for ordinary users; keep each project's parsed rules in an independent cache.
- Pair with Stream 0.112.194: recognize legacy CustomLayout records identified by `search_type` as well as category in both table request paths. Keep data-only rendering validation and administrator access checks; stored legacy code does not gain permission to execute imports, writes or I/O.

## 0.6.0.140 - 2026-10-24

- Pair with Stream 0.112.193 for the portable Windows/Electron delivery. Support `TACTIC_HANDLER_SETTINGS_DIR` through the existing configuration owner and instance guard so packaged Handler settings survive replacing the program directory; isolated test settings retain priority. Reuse shared EN/RU desktop confirmations and avoid the bundled NTLM regex escape warning under Python 3.14.

## 0.6.0.139 - 2026-10-23

- Pair with Stream 0.112.192 for the L12 delivery checkpoint: synchronize Stream release metadata and verify its installed wheel, unchanged Handler client, and standalone PostgreSQL/Apache server package. Windows EXE/Electron and migration acceptance remain pending.

## 0.6.0.138 - 2026-10-23

- Close legacy stage 2.4 (L11 SQLite/PostgreSQL matrix and Stage 2 as a whole) with Stream 0.112.191: fix multi-filter `Update.get_statement()` `WHERE` conjunction on SQLite (`' AND '` instead of `', '`), enable named savepoints (`has_savepoint`, `set_savepoint`, `rollback_savepoint`, `release_savepoint`) on `SqliteImpl` to match `PostgresImpl`, and wire the L08/L09 workflow/trigger/notification/expression/persistence/remote-repo/checkin matrix and `FileUndoReplay` check-in/undo/redo compensation into the side-by-side SQLite and Docker PostgreSQL 18.6 verification suites (`foundation`, `schema`, `project`, `plugin`, `command`, `queue`, `diagnostics`).

## 0.6.0.137 - 2026-10-23

- Close legacy stage 2.3 (L08 API, native Python, TEL/Naming) with Stream 0.112.190: resolve `palette` in `ExpressionParser` (`@SOBJECT(palette)`, `@GET(palette.<key>)` with and without root `sobjects`), implement `BaseInputWdg` persistence (`FilterData` display values and `WidgetSettings` DB state) and `SelectWdg` method-based `query` options (`sthpw/login|get_code()|get_name()`), support IP-masked remote repository matching (`Common.match_ip`, `Web.get_request_host`, `DirNaming.get_remote_repo`), enable `File.makedirs`, and accept `Snapshot.add_file` `upload`/`uploaded`/`manual` modes while preserving all transaction, Sudo, ACL, and request-context guards.
- Add `SelectWdg` method-based `query` and persistent default coverage in `tests/test_sobject_editor.py`.

## 0.6.0.136 - 2026-10-23

- Close legacy stage 2.2 (L09 Workflow, Triggers, notifications) with Stream 0.112.189: port and verify pipeline task rule triggers (`PipelineTaskStatusTrigger`, `PipelineTaskTrigger`, `PipelineParentStatusTrigger`, `PipelineTaskCreateTrigger`, `PipelineTaskDateTrigger`, `RelatedTaskUpdateTrigger`, `TaskCreatorTrigger`, `TaskCompleteTrigger`), async/queued trigger wrappers (`SubprocessTrigger`, `QueueTrigger`, `ScriptTrigger`), deferred trigger deduplication without dropping distinct scripts/notifications, and email/notification delivery (`GroupNotification`, `EmailHandler`, `EmailTrigger`, `EmailTrigger2`, `EmailTriggerTest`, `EmailTriggerTestCmd`, `SendEmail`, `NotificationTestCmd`, `NotificationLogScope`) with project privacy filtering and recipient deduplication.
- Add `NotificationController` unit test coverage in `tests/test_notifications_qml.py` for 5-second/active signature deduplication, message and activity notification sinks, history group filtering, and active toast retention when quick reply is open.

## 0.6.0.135 - 2026-10-23

- Polish UI layout and controls across Handler and Stream 0.112.188: align Configuration and Administration titlebar window controls with header buttons (`chromeTop`, `chromeHeight`, `chromeRight`), stabilize Notes message bubbles and attachments, align Task Inspector header/task card labels with Handler, fix LoginDialog clipping/scrollbar and AppearancePopup menu in QML, and ensure snapshot preview loading on first Notes open.

## 0.6.0.134 - 2026-10-22

- Close legacy stage 2.1 (L10 projects, plugins, schema/import/export) with Stream 0.112.187: align Handler remote procedures (`schema_api.py`, `schema_delete_api.py`, `workflow_api.py`, `search_types_api.py`) with Stream's server command contracts (`schema_cmd.py`, `schema_delete_cmd.py`, `workflow_cmd.py`, `search_types_cmd.py`).
- Add `PluginReloader` (`PluginUninstaller` + `PluginInstaller`), verify `ProjectTemplateInstallCmd` / `ProjectTemplateDownloadCmd` / `ProjectTemplateDeleteCmd` / `ProjectTemplateExportCmd`, and exercise live `is_template=True` cloning and rollback in `ProjectTemplateInstallerCmd`.
- Guard built-in `admin` and `sthpw` projects in `ProjectArchiveAction`, allow `EditCmd` to reactivate retired `sthpw/project` rows through `ProjectArchiveAction`, and preserve `PartialCommitException` when a database has already committed.

## 0.6.0.133 - 2026-10-22

- Close legacy stage 1.5 (L07b and Stage 1 / B07) with Stream 0.112.186: support `bottom`, `group_bottom`, and `total_summary` across table views, nested `show_gear` column authoring, ordinary-user ACL on table/object operations, and `expected_revision` conflict detection in `EditCmd` / `RecordForm.vue`.

## 0.6.0.132 - 2026-10-22

- Close legacy stage 1.4 (L06 Gantt and time tracking inside the table) with Stream 0.112.185: complete `GanttWdg`, `GanttElementWdg` (`GanttCbk` default/cascade), `TimecardInfoTableElement`, `WeekTableElement`, and `WorkHoursElementWdg` (`WorkHoursElementAction`).
- Support `ResourceUsageGanttWdg` user workload bars on `sthpw/login`, cascade `@SOBJECT(...)` parent resolution, project schedule scope, and week/daily totals across `WeekTableElement` and `WorkHoursElementWdg`.
- Route table schedule bars to the existing Task Manager Gantt in object, user, project, or related-objects cascade scope and daily hours to the existing Timesheet owner while respecting cell and bar editability.

## 0.6.0.131 - 2026-10-22

- Close legacy stage 1.3 (remaining L03 saved layouts and configured actions) with Stream 0.112.184: support nested CustomLayout wrappers with `icon_size` (`columns.thumb_view` → `custom_col`), `HiddenRowElementWdg` portable document/action CustomLayouts (`cg/scenes` `script` → `episodes/columns/script` with `show_resize_scroll`), and clear `ValueError` diagnostics on unsupported Mako syntax/tokens.
- Default empty `config/custom_script` `language` values to `'javascript'` in `ButtonElementWdg`, and align browser `runConfiguredScript` target/selection context with native `TableServicesController.run_script`.
- Preserve XML comments when parsing table views in `ColumnsEditorController._view_tree` and check server `config` revision before saving catalog XML; keep unresolved config references (`asset_panel_wdg`, `asset_cost_breakdown`, `inline_add_item`, bare `custom_col`) explicit.

## 0.6.0.130 - 2026-10-22

- Close legacy stage 1.2 (L04 and file remainder of L03) with Stream 0.112.183: CheckoutButtonElementWdg expands sequence and UDIM groups from file_range and metadata templates, checks local conflicts across all member files and cancels remaining transfers on close/failure.
- Support shipped configured publish widgets (ThumbInputWdg and UploadWdg with multi-slot names and NullAction fallback to MultiUploadAction) in both native and browser editors while keeping NullAction explicit on SimpleUploadWdg.
- Add DropElementWdg folder_drop / FileIngestCmd callback with an explicit Choose files button, native/browser file drop and staged upload check-in across default, file_group, {leaf} and {folder} subcontext modes.

## 0.6.0.129 - 2026-10-22

- Close legacy stage 2.1 (L01) with Stream 0.112.182: nested tables honor initialLimit paging, keep selected rows outside the loaded page and refresh the parent scope after editing.
- RowAddElementWdg falls back to related_types before sthpw/task; hidden-row and AuxData adapters ignore empty/insert records.
- Workspace moved to d:/grav/Tactic Stream; tools and tests use the new Handler/Stream roots. Ordinary-user ACL and totals remain in 2.5.

## 0.6.0.128 - 2026-10-21

- Continue combined legacy stage 2 with Stream 0.112.181: PublishTableElement and GeneralPublishElementWdg open their configured views in the existing native editor; preserve optional preview and explicit Multi Publish header.
- Run the configured field actions, including real uploads and rollback. A legacy NullAction does not silently become a check-in. Keep the excluded production Publish Browser and old HTML/Mako Custom Layout Editor excluded.
- Route shipped object/task editor callers through one admission check: preserve dirty, busy, batch or uncertain sessions and raise the existing editor; allow a clean editor to switch records.
- Stage 2/B07 remains open: sequence/UDIM transfer, ingest, residual layout callbacks, time writes, ordinary-user ACL, scoped authoring and full option acceptance remain pending. Typed registration is not full legacy acceptance.

## 0.6.0.127 - 2026-10-21

- Continue combined legacy stage 2 with Stream 0.112.180: ParentGroup groups by full parent identity, shares its rich header and picker state, and opens child creation through the existing configured insert form.
- Adapt ParentGroupAction, including computed Expression cells, to explicit revision-checked reparenting. Preserve physical source identity, source project, paged literal search, dirty drafts and uncertain-save verification; reject cycles, retired targets and stale definitions.
- Keep original-server procedures independently shipped. Fix native and browser table drop handlers to read the actual Frame event payload; preserve browser table state when the retained card presenter saves collapse state.
- Stage 2/B07 remains open: configured publish, sequence/UDIM transfers, ingest, residual layout callbacks, time writes, scoped column authoring and ordinary-user ACL acceptance remain pending. The old HTML/Mako Custom Layout Editor and excluded production subsystem stay excluded.

## 0.6.0.126 - 2026-10-21

- Continue combined legacy stage 2 with Stream 0.112.179: DependencyLink opens the existing modeless table document with a shared snapshot tree, cached branches, cyclic/missing/retired references and branch-local retry/loading.
- Preserve concrete versions, source project, revisions, instance/node metadata and contextual level references. Page sequence member names without eagerly expanding the whole range; sequence/UDIM transfer remains L04.
- Open a selected ordinary file with the existing native file owner. Run dependency reads in workers and discard completions after close, refresh, project change or sign-out.
- Keep document captions localized and reject older generic document responses after replacement/close. Stream thumbnail reads expand only the first sequence frame.
- Add actual QML input/lifetime checks, native procedure XML-RPC and Edge file-byte/pagination checks, fresh paired examples and EN/RU Help. Stage 2/B07 and ordinary-user ACL remain open.

## 0.6.0.125 - 2026-10-21

- Continue combined legacy stage 2 with Stream 0.112.178: project-scoped connection cells batch target/preview reads, retain retired/missing endpoints and remove only the revision-checked connection after confirmation. Refresh after success or a lost response.
- Add object/project summary counts and SQL straight-time aggregation; task and check-in buttons own distinct nested tables and project contexts. Recursively expand configured tables, preserve each selection/cache, reject ancestor cycles and stale hidden-branch results.
- Extend the existing Frame array list with shared variable extents and focused-header scroll correction; retain bounded delegates for 10k records. Fix the parallel-process action intercepting the group disclosure button.
- Require painted summary/header labels in actual input and paired captures. Document Stream’s separate quiet Inspector refresh, which keeps Enter/composer input enabled while preserving captured context.
- Keep independent product copies and native workers. This is an L01 checkpoint; stage 2/B07, ordinary-user ACL, original-server/PostgreSQL execution and physical hardware acceptance remain open.

## 0.6.0.124 - 2026-10-21

- Continue combined legacy stage 2 with Stream 0.112.177: table checkout opens one shared Frame file list in an ordinary native window. Resolve a concrete snapshot, keep its selected file/project and reuse native File paths and the existing transfer queue.
- Require explicit local overwrite; cancellation and closing invalidate stale results. Preserve files created during download even with skip/cancel policies, retain an active transfer's captured source/policy, and encode native URL path metadata correctly.
- Open from metadata without a local disk walk; retain the selected-file worker check. Match browser/native Unicode ordering, nullable legacy metadata, selection paint and narrow translated footer labels.
- Keep the house native progress indicator on Material regardless of Qt module load order; paired captures verify accent, track thickness and fill.
- Add actual-input and real-file checks. This checkpoint covers ordinary files; sequence/UDIM checkout, publish and the remaining B07/stage-2 acceptance are still open.
- Verify all 147 Frame platform steps, 89 native table tests and 65 server table tests. Fresh paired comparison covers 708 current states, including 120 checkout states; 36 historical B06 captures remain separate references.

## 0.6.0.123 - 2026-10-20

- Continue combined legacy stage 2 with Stream 0.112.176: snapshot append uses one shared Frame form and an ordinary native modal window, with file type and keep-name options.
- Capture the concrete snapshot/project/revision; upload off the GUI thread and append through native FileAppendCheckin/FileUndo. Preserve local originals, block uncertain write repeats and clean cancelled clipboard drafts even when workers suppress their result signal.
- Isolate each draft in its own ticket upload subdirectory; support image Ctrl+V without consuming ordinary text paste, reject directories/file overflow and refresh concrete/current rows.
- Add actual-input, lifecycle, rollback, real HTTP-byte and paired form-state checks. Checkout/publish and the remaining stage-2 acceptance are still open; this checkpoint does not close B07.

## 0.6.0.122 - 2026-10-20

- Start the combined second legacy stage with Stream 0.112.175. Retain the delivered first-stage checkpoint and move its remaining acceptance into stage 2; exclude the old HTML Custom Layout Editor while retaining portable saved definitions.
- Add scoped expanded tables and original-server projections, isolated selection/filter/page state, cached reopening, existing record editors and disclosure loading feedback. Keep ordinary table delegates within the existing visual-item budget.
- Add shared table schedule/daily-hours presentation and routes to the existing Gantt/Timesheet owners, including captured task/day context. Legacy inline/cascade callbacks, remaining file operations and full B07 acceptance stay open.
- Preserve separate Frame resources and native scripting; no embedded browser or new Batch Manager web UI.


## 0.6.0.121 - 2026-10-20

- Share the table tags editor and add service/task/action/link presenters with Stream 0.112.174. Keep existing native object, task, administration, check-in and script-editor owners; preserve custom views, group identity, revisions and first-click activation.
- Execute configured client JavaScript in an isolated QJSEngine process with the original SDK, captured context, safe confirmation and cancellation on session teardown. No embedded browser or new web Batch Manager.
- Preserve independent Frame/SDK resources. Document the supported CustomLayout subset and the still-open nested-table/file-ingest/report dependencies; B07 and full legacy parity remain open.

## 0.6.0.120 - 2026-10-19

- Activate only the first six profile activity cards until Show more. Hidden rich-text snapshot filename lists no longer lay out at zero width on every frame; keep loaded records, full titles, actions and the first cards intact across expansion/collapse.
- Reproduce the one-second scroll stall with actual locally replayed profile events and verify the fix with software and Windows/OpenGL rendering. Add real native/browser lifecycle input regressions and synchronized profile Help; document the existing Qt bytecode/cache path separately from possible release AOT compilation.

## 0.6.0.119 - 2026-10-19

- Connect the four L02 legacy table classes to existing notes/task owners and independent Frame adapters. Add plain formatted messages with shared author/progress presentation; preserve the task context prefix and inline assignment/date options.
- Use configured per-process note values (including empty branches) in native cells, retaining ordinary Inspector/notes navigation and task draft/save/discard owners. Do not introduce another Messages or Tasks application.
- Extend native input and source-checked Qt/Vue table fixtures. Keep Submission excluded with pyasm.prod; legacy setting subcontexts/CGI state and the old HTML calendar/preview are not full presentation parity. The catalogue has 41 classes / 98 named aliases; B07 remains open.

## 0.6.0.118 - 2026-10-19

- Move Knowledge Base workspace, navigation/outline, editor/viewer commands and formatting controls to independent Frame descriptions. Preserve native rich text, image tools, Markdown, attachments, revision/ACL and draft owners.
- Share Timesheet, Work/Cost Reports and work-hour forms with Stream; keep native controllers, approvals and permission-filtered reports. Retain complete narrow forms and virtualized report rows.
- Share explicit Messages/Knowledge schema confirmation and align the browser Messages action with Handler’s existing combined schema procedure. Reads never initialize storage. Close confirmation on project changes; reject stale browser Knowledge mutation completions after context changes. Preserve API-console and journal browser capabilities with their existing authorization and transport.
- Add a complete QML/Vue source ownership ledger, connected input/lifecycle checks and source-verified original/native/browser comparisons. Keep B07's 40 usable legacy widget classes open and Batch Manager's existing UI intact.

## 0.6.0.117 - 2026-10-18

- Share Script Editor workspace/source commands, shelf bar/editor, native triggers, DCC options, Handler Server and selected-object Database presentation through independent Tactic Frame modules. Retain existing execution, revisions, ACL, drafts, transport and native window owners.
- Reject stale DCC confirmations after switching the selected client. Keep tab shelf drafts bound to their original context and guard delayed picker results by identity/scope. Fix completion at a newline in Handler and Stream.
- Add a small native script-created Frame tool example using house controls and the existing record model; preserve Batch Manager and its existing web UI. No embedded browser, duplicate web scheduler or required user-script rewrite.
- Add native input/selection/save/recovery checks, browser workflows, original/current composition comparisons and EN/RU Help. Fix hidden Frame labels intercepting browser clicks and obsolete editor styles shifting shared geometry.

- Route snapshot arrays through the array-list adapter even with declared fields, avoiding a native resize/clear access violation without delaying normal input. Preserve row indexes in both list adapters. Accept literal Unicode grouping spaces in Qt numeric patterns.

## 0.6.0.116 - 2026-10-18

- Move File Workspace panes, metadata, inspectors and operation dialogs, Matching Templates, Drop Plate, ingest, Commit Queue, Repository Sync, repository confirmations and screenshot selection onto independent Tactic Frame descriptions shared with Stream. Retain native Qt controls, filesystem/DCC capabilities and existing ACL, revision, transfer, cancellation and mutation owners.
- Keep natural workspace-tab widths and horizontal scrolling, editable template mappings, complete narrow forms and virtualized large queues. Remove superseded queue and workspace presenters.
- Fix Repository Sync preset updates to address real settings records by their returned search keys. Guard delayed clipboard/capture/intake and validation results by their queue, account and operation lifetime; uncertain check-in results require inspection before retry.
- Add pinned original/current visual comparisons, native/browser input and authenticated file/check-in/preset journeys; extend the platform gate and EN/RU Help. Browser local-file reselection and native-only operations remain explicit capabilities.
- Restore Escape focus in native Screenshot Maker and stop fake-pool fixture timers through the real shutdown owner. The combined 137-case owner suite and the 121-stage platform gate pass.

## 0.6.0.115 - 2026-10-18

- Move conversations, message metadata/body/reference/pins, composer rules, membership/search/history/file forms, attachment staging, activity cards/calendar, notification history and toast content to independent shared Tactic Frame descriptions with Stream. Keep native Qt controls and existing request, permission, draft, receipt, upload and notification owners.
- Restore natural message widths and usable Knowledge preview cards; retain the first input in member filters, multiline references, keyboard metadata tooltips, visible scrollbar room and correct activity paging after controller completion.
- Add isolated original/native/browser capture tools and real native/Chromium communication regressions. Document native file and Repository Sync capabilities separately from browser phone presentation.

## 0.6.0.114 - 2026-10-18

- Move production Gantt, the independent Task Calendar dock, milestone presentation and the explicit schedule editor onto shared Tactic Frame descriptions with Stream; retain native controls, virtualized models and existing mutation owners.
- Share row/bar/timeline/overview geometry, operation menus, zoom anchoring, progress input and pointer previews. Show real loaded task dependency links, preserve cancel/undo and original times, and stage form dates/progress as one undo entry.
- Add native Agenda and explicit schedule editing; reject invalid dates and stale editor context. Keep independent Calendar ownership and native SObject milestone storage capabilities explicit.
- Add pinned original/current QML/Vue comparisons across themes, languages and DPI, real Qt/browser/server scheduling journeys and platform-gate coverage. Fix missing palette projection, menu anchoring/focus and named quarter scale; update EN/RU Help.

## 0.6.0.113 - 2026-10-18

- Share Task Manager tables/expanded fields, Quick Tasks, scope/filter/options/columns, pending changes, bulk editors and task menus with Stream through independent Tactic Frame copies. Move the native management heading/summary/workload to the same description layer; retain native controls, virtualized models and existing revision/ACL/mutation owners.
- Keep virtual creation, context-safe inline edits, hour/minute conversion, field opt-in and bulk preview/apply. Guard manual scope/page changes while dirty; preserve armed input during quiet refresh and keyboard activation for filled toolbar actions.
- Preserve live profile avatars across lazy picker activation and honor tooltip suppression on hover and keyboard focus.
- Add production original/native/browser comparisons, actual Qt/browser/server workflows, source freshness checks and EN/RU Help. Existing Gantt/Calendar scheduling remains B10; B07 legacy-widget gaps remain open.

## 0.6.0.112 - 2026-10-17

- Share object description, configured forms/batch tools, report sections, dependency deletion, five-step duplication, two-list linking and snapshot/watch presentation with Stream through independent Frame copies. Retain native controls, file/DCC adapters, existing query/ACL/revision and mutation owners.
- Share Inspector context/quick/task/hour fragments and complete note body/attachment layout plus modeless edit and modal delete content. Preserve per-context drafts, exact task/project navigation and measured rich text/file heights; keep failed note edits open and prevent another write after a lost reply.
- Add original/current QML/Vue comparisons across themes, languages and narrow/wide widths, real Qt/browser input, protected report projections and object-operation workflows, source-fresh evidence tooling and EN/RU Help. Full Task Manager/Messaging remain separate batches; B07 legacy-widget gaps remain open.

## 0.6.0.111 - 2026-10-17

- Share Table View geometry/paint, column/view menus, typed inline editor composition and task-cell rules with Stream. Retain native ListView, search sessions, existing XML revision, edit and task mutation owners; ship an independent Frame copy.
- Add typed completion/lock/file/due/subcontext/selection/metadata cell adapters and one explicit 37-class catalogue. Keep unknown classes/options unsupported. Fix boolean action classification, cancelled column drag, group selection count, completion padding and unassigned task labels.
- Add real Qt/browser input and paired production-component checks. This is a B07 checkpoint, not completion: 40 usable classes in shipped/CG widget configs still need full workflows, including nested tables and specialized legacy action/forms.

## 0.6.0.110 - 2026-10-17

- Move search conditions/suggestions, presets, tag/quick-filter headers and editor parts, process visibility, menus, paging and result-card geometry to independent Frame search descriptions. Keep existing query, revision, ACL, mutation and native operation owners; use an Advanced Search dock in both products.
- Preserve per-tab drafts and stable preset commands, normalize/reorder the first condition, reconcile unknown writes and group by actual task status. Bound browser collection delegates; remove empty native metadata/preview allocations without raising render budgets. Add real Qt/browser workflows, source-checked original/current comparisons and EN/RU Help.

## 0.6.0.109 - 2026-10-17

- Move Configuration navigation and all preference pages, repository summary/editor, project catalogue, four-step creation, project editing and template manager to independent Tactic Frame configuration/projects modules. Keep existing persistence, native local/DCC/preset capabilities and operation owners; declare browser XML/web-path additions explicitly.
- Preserve per-page drafts, Reset/Apply/Save/Close, preset saves without losing other drafts, TEAM confirmation, project image queues, modal project/template confirmations and unknown-creation reconciliation. Add real Qt/browser workflows, lifecycle/retire history checks, original/current comparisons and EN/RU Help.

## 0.6.0.108 - 2026-10-17

- Move Debug Log, UI responsiveness, profile/editor, sign-in, presets and update/error/confirmation composition to independent Tactic Frame modules. Keep existing authentication, logging, profile ACL/revisions, updater and native file owners; Help and connection menus retain their established Frame contracts.
- Preserve full diagnostics and off-screen keyboard focus, password clearing, dirty/unknown-write guards and owned child closure. Save both profile-editor pages through one existing mutation rather than skip the hidden page. Retain native preset/ZIP capabilities and browser current-origin/history differences explicitly. Add real Qt/browser workflows and original/current paired evidence across themes, languages and widths; update EN/RU Help.

## 0.6.0.107 - 2026-10-17

- Close Frame B03 Administration review against the tracked pre-Frame Handler archive. Keep independent native and browser products, existing controllers, command/revision/ACL owners and explicit capabilities.
- Restore visible plain-checkbox captions, reuse the existing compact settings sections throughout Administration, and restore Columns Wizard up/down ordering without losing comments, custom XML or the selected column. Complete missing Russian labels and diagnostics.
- Keep native drawer keyboard focus inside its activating row when ListView selection changes. Refresh native graph/connection/type-creation and navigation scenarios to exercise actual current controls, owned popup windows, drafts and confirmations. Document editing and save/readback behavior in EN/RU Help.

## 0.6.0.106 - 2026-10-16

- Deliver Frame B02's reusable control kit and 144 neutral executable examples with Stream: grouped source atlas, native/offline catalogs and explicit boundaries between primitives, neutral composites, infrastructure and domain forms. Keep independently shipped modules and existing controller/script APIs; no browser engine or runtime UI translator.
- Align pixel typography, icon slots, preview selection borders, numeric/segmented controls, fields, chips, identity, neutral headers and feedback. Extract reusable SearchField suggestions while retaining TacticSearchField's controller, debounce and result-opening behavior. Preserve native scaled-integer SpinBox APIs and external model/locale bindings. Correct native OpenGL crop/contain masks and selected preview borders; export the shared error-container role to CSS.
- Skip disabled ComboBox options during keyboard selection, prevent repeated PopupAction releases from duplicating an action, and measure hidden sizing chips before painting. Exercise actual input, recreation/disabled/readonly lifetimes and three scales. Keep original/current/Main/project comparisons and explicit font/compositor/system-dialog limits; document behavior in EN/RU Help.

## 0.6.0.105 - 2026-10-16

- Close Frame B01 root composition: Main.qml and Stream App.vue consume the same toolbar/section-rail/dock-host skeleton from independent local copies. Preserve public dock identity, expanded native rail input, all existing workspace controllers and saved formats; no embedded browser or second state store.
- Verify integrated dock/tab/layout restore, draft retention, project/account transitions and native lifecycle. Extend the platform gate with native workspace tests and disposable-server desktop/phone/session journeys. Correct an obsolete layout-preset test fixture to use the actual project_view root.
- Capture the real original/current Main window and browser in three themes and both languages, compare host/control geometry, background and avatar contrast, and exercise actual menu input. Keep native compositor and phone hardware limits explicit; screen contents and the full control kit remain later batches. Document workspace/session behavior in EN/RU Help.
- Stream counterpart fixes superseded bootstrap/sign-in/logout replies, cancellation of queued background reads, phone panel retention across desktop widths and shared preview contrast. Native session workers retain their existing cancellation owners.

## 0.6.0.104 - 2026-10-16

- Compose the complete vertical section rail from the shared Frame module: panel, surfaces, badges, labels, close bounds, context records and vertical drag targets. Preserve the existing section/workspace model, commands, scroll, saved formats and native input.
- Fix native drag targeting of collapsed neighbors; cancel with Escape, window deactivation or model removal/reset. Preserve the immediate first mouse click/tap while the close control is still appearing. Add right-click, Shift+F10 and 500 ms touch-hold actions using the existing shared menu rows; resolve section identity again before applying a command.
- Extend archived/native/browser comparisons with actual colors and coherent focus/hover. Stream now matches native preview contrast and unknown-icon fallback. Include section input at three scales, real touch/drag/menu checks and matching EN/RU help. Workspace session/layout closure remains separate.

## 0.6.0.103 - 2026-10-16

- Share project chooser header, category grid and expanded cards with Stream using Frame; preserve native discovery/ACLs, filters, previews and project/session ownership. Reserve scrollbar space, highlight the active project and translate missing categories without translating server data.
- Share search-tab paint, selection motion and keyboard decisions. Preserve house-control input and the existing workspace activation/close/reorder owner; retain focus after delegate changes. Share section-rail dimensions and manual-activation keyboard rules while leaving its full paint/gesture migration explicitly pending.
- Add native/browser input and archived/native/browser project/card/tab comparisons, phone and inline chooser checks, EN/RU help and required platform verification at three scales. Ship independent copies; no embedded browser or additional runtime dependency.

## 0.6.0.102 - 2026-10-16

- Compose the navigation drawer from the shared Frame module: measured original header/list geometry, native house buttons/scrolling, keyboard decisions and hover-exit threshold. Keep the independent shipped copy, script sidebar definitions, controller state and saved formats.
- Arm mouse dismissal only after entering the panel, keep touch unaffected, follow the active controller section, and restore focus on close. Navigate off-screen/recycled rows while skipping unavailable/hidden items and separators; ListView no longer overrides the shared arrow-key policy.
- Add real native mouse/touch/keyboard tests and archived/native/browser drawer comparisons. Preserve Stream phone navigation slots and explicitly keep project chooser, section/search-tab and remaining session composition pending.

## 0.6.0.101 - 2026-10-16

- Complete shared dock keyboard navigation/reorder/close and transfer focus through the stable host after delegates change. Share footer height, divider and corners while preserving native dialog framing.
- Move main user, configuration and connection menus to a shipped action catalog and shared Frame row composition. Preserve MenuRegistry replacement/extensions, native popup lifecycle, platform-only actions and existing command/settings/authentication owners.
- Add native mouse/touch/key checks, script extension and update-state checks, paired original/current/browser menu/footer comparisons, and private-server browser command/error/session workflows. Keep full navigation/project/session migration and unverified control families open.

## 0.6.0.100 - 2026-10-16

- Execute dock tree projection, recursive minimum constraints and floating-edge sizing from the same portable Frame module as Stream. Preserve preferred split ratios, native Python state ownership, detached-window capability and saved layout format.
- Preserve hidden tab slots when reordering visible dock tabs. Share the reorder threshold, cancel unfinished tab gestures with Escape, and avoid accessing deleted QML delegates after committing their new order.
- Add the three missing floating resize corners and put all resize handles above the panel body so title movement cannot steal their input.
- Verify whole-layout geometry against the archived Handler algorithm and actual Qt/browser panels; cover real mouse/touch, eight handles, nested minimums, restore and cancellation at three native scales.

## 0.6.0.99 - 2026-10-16

- Move Help to one shared Frame composition and state contract with Stream. Retain the native window and per-article positions; preserve filters, contextual navigation and language changes across reopening. Add atomic local Markdown export and shared document typography metrics.
- Share docking targets and previews with Stream, preserve native detach, and cancel unfinished grip/resize gestures without saving their preview. Move floating panels by the title while retaining the grip for docking.
- Share the neutral project-navigation row with Stream, including section/link/separator geometry, badges, icons and selection. Keep routing, model filtering and runtime procedural menu definitions with their existing owners.
- Extend actual native/browser checks for Help, first mouse/touch activation, window ownership and focus, gesture cancellation, navigation and layout restoration. Keep original/current/browser evidence separate from unverified full-workspace and control-atlas coverage.

## 0.6.0.98 - 2026-10-15

- Unify Frame control paint and metrics across the independent native and browser products: button states, field errors, mixed checkboxes, disabled switches, tooltips and pickers. Resolve house-control fonts as complete pixel values without conflicting with existing custom fonts.
- Share strict local-date validation and calendar arithmetic, including leap years and years below 100; retain valid server precision/zone suffixes until the user changes a value. Expose DateChoice and UserChoice with separate edit/acceptance semantics.
- Share Sidebar tree rows and keyboard navigation; preserve edit guards and stable public control names. Close popups when owners become unavailable and add keyboard activation to compact icons and user selections.
- Share semantic icon aliases and fallback policy, verify actual font-family/glyph identity, and align fractional text advances and inner control positions. Remove duplicate TextArea padding and reserve its scrollbar space.
- Add executable native/Vue control examples, paired state captures and real pointer, touch, keyboard, popup, tree and table regressions. Extend the platform gate and keep independent packaging and existing Administration checks.

- Clarify primitives, neutral composite controls, infrastructure and business forms; add a source-linked UI atlas and explicit verification gaps. The 372-state control gallery remains a verified subset; phase 1 is still in progress.

## 0.6.0.97 - 2026-10-15

- Harden the Frame preparation contract: named pixel typography roles, validated scene bindings, unique record keys and finite viewport geometry. Replace inherited fonts as complete values to remove point/pixel conflicts without changing deployed Frame sizes.
- Virtualize array-backed native lists by visible keyed rows; keep native role models direct. Preserve editor identity, caret, selection, drafts and IME preedit across record reorder, and clamp empty/shrinking views.
- Batch all observed browser sizes without losing another target's delivery; cancel pending work on unobserve/dispose. Preserve composition semantics and escaped control lookup across engines.
- Inventory registered windows, docks, source surfaces and dynamic entry owners; document explicit platform boundaries and remaining migration work. Verify original/current list timings, native/browser input, smoke and independent packaging.

## 0.6.0.96 - 2026-10-15

- Organize portable Frame modules into core, controls, shell and Administration domains; move native Administration and window/dock adapters into matching folders while retaining public QML type names. Format source and keep stable LF endings for independent product copies.
- Share Handler theme, typography, motion, control metrics, tab sizing, window geometry/minimum sizes, dock-header composition and main-toolbar positions with Stream. Preserve native controllers, scripts, ownership and persistence; this is a foundation checkpoint, not completion of all five UI migration blocks.
- Restore graph connections, Parameters/Advanced JSON order, Pipeline settings guards and the Workflow library in the Administration sidebar. Keep catalog search/drafts across responsive host changes and prevent narrow graph actions from overlapping layout controls.
- Verify independent original/Frame comparisons, native mouse/touch/keyboard behavior, paired Administration captures and recursive update packaging. Keep existing unrelated architecture/lint failures explicit without increasing their budgets.

## 0.6.0.94 - 2026-10-15

- Establish continuous Git tracking for completed Handler and Stream work while preserving Handler history. Exclude local settings, file-transfer databases, caches, logs and build/test artifacts; retain source, tests, documentation and shipped resources.

## 0.6.0.93 - 2026-10-15

- Complete Administration's Tactic Frame migration: shared shell, all ten sections and nested Search Type fields/preview/naming/relationships, schema/workflow process settings and dependencies, column wizard, raw cells, typed deletion review and native Layout authoring. Ship 37 independent local UI/state modules in each client; retain existing domain controllers, ACLs and revision guards.
- Preserve hidden drafts and pending child context across section switches; route Workflow and Groups links to the main section. Confirm writes explicitly and require successful readback after an unknown result. Keep schema creator cancellation distinct from deleting a saved type.
- Keep Layout project resets free of synchronous metadata RPC; discover a cold project's types through the existing read-only worker and captured server identity, with cancellation and malformed/empty response guards. Align canonical icon aliases, compact element movement controls and new Russian captions; reject fallback glyphs in captures.
- Replace the Layout Editor's embedded-browser host with native QML and the house source editor. Keep XML extensions, checked preview/save, undo/redo, find/replace and system-browser Open view without a ticket in the URL. Handler no longer initializes WebEngine for this editor.
- Add real-input paired QML/Edge fixtures, independent native regression execution, full-application private SQLite integration and EN/RU help. Retain unused legacy QML files pending their separately reviewed removal. Live PostgreSQL, the user's production database and Windows compositor behavior are not certified by these fixtures.

## 0.6.0.92 - 2026-10-14

- Document the existing shared JSON /admin/rpc and XML-RPC server log in English/Russian Debug Log Help, including method/argument blocks, failures, timing boundaries and the distinction from other browser endpoints.
- Verify identical logs over real HTTP for successful reads, JSON kwargs, scripts, authentication/unsupported-method/signature errors, argument-secret redaction and one unique block per request. Retain the original shared formatter and current Handler XML-RPC transport.
- Record optional Handler JSON transport with retained Legacy XML-RPC compatibility as a separate future stage; no transport switch is implemented in this change.

## 0.6.0.91 - 2026-10-14

- Move the complete Administration Users directory and Profile/Account/Groups editor to local Tactic Frame modules and native controls. Share field definitions, responsive layout, selection, confirmations and UI permissions with Stream while retaining native Python profile writes. Remove the old independent AdminUserDetails markup.
- Preserve passwords, retired-account identity/search, immutable logins, group edits, draft guards and source translations. Block repeated account writes after an unknown save result until a confirmed successful reload; notify the shared scene after filtering.
- Align Frame scrollbars, semantic creation icons, row text/content insets and full English/Russian button labels in the paired Vue renderer. Ship independent local .mjs copies; ordinary product builds require no neighboring checkout or WebEngine.
- Qualify native Groups/Users keyboard and touch, isolated API/state checks, update packaging and paired QML/Edge states (108 Groups, 132 Users); check native Users geometry at 150% scale. Refresh Stream and restart Handler. Live PostgreSQL and other display scales were not tested for this UI change.

## 0.6.0.90 - 2026-10-14

- Allow Task Manager + without a selected object, including empty file projects. Reuse the native project-owned sthpw/task workflow, standard status pipeline and current-user assignment; retain object-owned task creation when an object is selected. Keep draft/save behavior and real project identity for Inspector, comments, hours and changelist links.
- Resolve project task choices locally and obtain status choices through the existing worker catalog; do not load search schemas on the UI thread. Route a project task's Inspector context through the normal search-key opener when its owner is not already a Results row.
- Qualify 127 native controller/catalog/QML checks, real Vue plus/edit/save/Inspector input against an isolated file-project server, project isolation, stale revisions and task-to-changelist publication. Synchronize EN/RU Help with Stream 0.112.140. Restart Handler and Stream. This change was not tested with PostgreSQL or the user's live data; existing Task Manager layouts were not migrated to Tactic Frame.

## 0.6.0.89 - 2026-10-14

- Bundle the selected search result's tasks, notes, status history and complete snapshots with files into the existing query_sobjects response. Reuse native hydrated objects instead of issuing three additional detail RPCs on refresh; other page rows keep lightweight previews.
- Preserve all-process queries, code/id parent scope, private-note ACLs, explicit snapshot refresh and cache invalidation. Keep the browser's distinct native search/inspector path and synchronize English/Russian Help.
- Validate the real Handler consumers against an isolated Stream API: the reproduced refresh falls from four RPCs to one while retaining task history, notes, snapshots and preview-file metadata.

## 0.6.0.88 - 2026-10-14

- Count search-result notes and task-branch notes through grouped native searches, preserving privacy, process totals, code/id parents and existing retirement behavior. Custom Note classes retain row evaluation and their overridden getters.
- Use TACTIC Stream's validated physical-column grouped counts; retain the original TACTIC Select path and disable its timestamp ordering only for aggregation. Before/after parent and task-branch results match in the actual original runtime.
- Synchronize English/Russian Search help with Stream's bounded compiled-script reuse. Per-request inputs, execution state, source updates and permission checks remain fresh; no workflow/UI behavior changes.

## 0.6.0.87 - 2026-10-14

- Fixed Material-style insets moving and clipping avatars and names in Tactic Frame group member rows; content now uses the entire shared row rectangle.
- Guarded invalid transient list delegates during filtering and added single-line member, production Material and 150% scale geometry checks.
- Kept Handler and Stream independently packaged with local UI source copies; cross-product comparison/copying is explicit and separate from ordinary builds.

## 0.6.0.86 - 2026-10-14

- Migrated the complete Administration Groups view to Tactic Frame: one shared JavaScript layout and UI state, rendered through native QML and Vue controls without embedded web views.
- Preserved group drafts, identifiers, descriptions and membership deltas; added revision checks and confirmed reload recovery after unknown save results.
- Added shipped module hashes, paired production-view captures, real keyboard/touch and transactional backend checks, plus synchronized English/Russian help.

## 0.6.0.85 - 2026-10-14

- Adopted the shared QML/Vue UI contract for agent work: one skeleton, native controls, paired verification, and an explicit ban on embedded web views without user instruction.

## 0.6.0.84 - 2026-10-14

- Fixed Reconcile Ctrl+A UI hangs by reading file-filter state once and building target-changelist models only while the dialog is visible.
- Made the selected-file preview use one state projection and a path set, preserving all 1000 selected rows and name/status filters.
- Added real QML keyboard, preview, responsiveness and selection-retention checks, plus Stream keyboard-selection parity and synchronized English/Russian help.

## 0.6.0.83 - 2026-10-14

- Added matching Handler/Stream recovery guidance for failed storage GC tasks; retained the original error instead of relabeling the task.
- Corrected the shared Stream backend's compressed-record decoding during GC maintenance, with checks for unused-page reclamation, published-file preservation and immutable stored state.
- Updated English/Russian file-workspace help with the failed-task restart workflow.

## 0.6.0.82 - 2026-10-14

- Completed Depot creation/editing with configured repository aliases, revision checks, paged lists and retained drafts.
- Added Storage Administration quotas, retention settings, resumable bounded indexing, GC dry run, confirmed safe GC, live status and cancellation.
- Kept policy integers exact across the QML boundary; guarded project changes with unsaved Depot/Storage drafts.
- Matched Stream forms, synchronized English/Russian help and verified both actual UIs against an isolated file-project server.

## 0.6.0.81 - 2026-10-14

- Treat a closed HTTP-200 SSE feed and interrupted HTTP-200 update reads as transport failures: reconnect with the existing bounded backoff instead of opening an Application error dialog. Preserve authentication and permission handling and ignore stale/cancelled subscriptions.
- Record each SSE failure at ERROR level, visible with default Debug Log recording settings. Include endpoint, host/port, project/channels, HTTP status, Qt network reason, error code and attempt; retain actual parser tracebacks without logging request tickets or proxy credentials. The previous EXCEPTION-only dialog path could be filtered out by default.
- Verify 33 native transport/service checks (including real EOF, truncated payloads, 503/403, default on-disk logging) and the Handler/native Stream integration. Browser SSE already retries EOF. Synchronize EN/RU server Help; restart Handler. The cause of the user's individual connection closures has not been established from the screenshot alone.

## 0.6.0.80 - 2026-10-14

- Align the file-workspace View button and toolbar actions with the view tabs. Reserve the horizontal scrollbar gutter only when tabs overflow, outside the button alignment area. Keep shared tab hover/selection styling.
- Reproduce the previous six-pixel offset in real QML; verify narrow/wide geometry, English/Russian, both themes, tab activation/closing and splitter/log behavior. This is a Handler layout correction; the browser has no equivalent desktop file-workspace toolbar.

## 0.6.0.79 - 2026-10-14

- Render the RAW sticky heading above ListView delegates, whose default stacking level previously tied the heading and let row text, hover backgrounds and delete actions cover it during scrolling. Retain the existing opaque theme surface, square grid and virtualization.
- Reproduce the overlap with rendered pixels before the fix; qualify sixteen header-image comparisons across narrow/wide, dark/light and vertical/horizontal scroll positions, plus all fourteen native RAW checks. The corresponding Stream header already renders correctly and passes sixteen browser comparisons on identical fifty-row data. Synchronize EN/RU Help with Stream 0.112.128. Restart Handler; production Windows display scaling was not tested.

## 0.6.0.78 - 2026-10-14

- Add a compact Streams tree/list with parent nesting, loaded-record filtering, disclosure, context menus and New/Edit entry points. The shared movable modal editor also opens from Stream Graph. Create real mainline/development/release branches and edit title, description, parent and owner-only settings protection through native API commands.
- Keep spec revision conflicts separate from published file revisions. Serialize topology edits, reject cycles and incompatible parents, preserve immutable fork ancestry on reparenting, enforce depot rights/owner locks and native rollback. Graph pages detect spec changes and distinguish reparent links from published branch links.
- Qualify native hierarchy, merge base, stale editor, ACL, trigger rollback and real HTTP/Qt editor/tree/graph flows across themes/languages/sizes. Synchronize Stream 0.112.127 and EN/RU Help. Restart both applications. Virtual/task/sparse streams, inherited path views, automatic merge/copy policies and type conversion remain unimplemented and are explicitly identified in the editor; this is not full P4 stream compatibility. Production PostgreSQL and large physical datasets were not tested.

## 0.6.0.77 - 2026-10-14

- Replace RAW inline editing with a registered native modal Cell editor matching Stream: plain text display, a multiline value field, schema-based conversion, explicit Value/NULL/new-row Database default, Apply/Cancel, Enter/F2 opening and Ctrl+Enter/Escape. Keep exact integers, decimal/JSON text, readonly viewing, sparse drafts and conflict protection. Register the window under Administration, invalidate its state on close/reload and synchronize EN/RU Help.
- Qualify fourteen real QML checks, native ownership/keyboard/default handling, Vue save flows and 39 shared conversion cases; field/selector geometry matches eight identical-value language/size/theme comparisons. Native and browser window chrome retain platform differences. Live PostgreSQL and higher-DPI native Windows checks remain unverified. Restart Handler and refresh Stream to load the client update.

## 0.6.0.76 - 2026-10-14

- Keep immediate folder siblings visible in Files when a Depot/Workspace file is selected. Highlight and reveal selected rows, preserve multi-selection, skip list reloads for other files on the same page, and clear the old inspector on folder selection. Reuse bounded native directory pages and the existing refresh snapshot; keep fixed-source and changelist tabs independent.
- Replace separate Files/History detail implementations with one shared inspector for copyable metadata, description, checkout/integration information and lazy text/image/binary preview. Preserve revision-specific content, permissions, splitter sizes, localization and themes.
- Qualify native/HTTP/Qt folder selection, local-only files, nested-folder exclusion, selection after row 200, single-request refresh, restricted metadata and preview/geometry in EN/RU light/dark narrow/wide layouts. Synchronize Help and Stream 0.112.125. Restart Handler and Stream; production PostgreSQL and million-file/terabyte acceptance were not run.

## 0.6.0.75 - 2026-10-14

- Replace History revision cards with a compact virtualized table and file header. Show revision, changelist, submitted date/author, type/extension, size and description with action icons. Add a lower Details/Integrations/Preview pane and independently persisted splitter; retain selection, comparison, sync, save and restore actions.
- Load revision text/image/binary preview only on demand, reject stale content by revision identity and avoid hidden-pane preview requests. Reuse the same bounded history response for workspace metadata, preserving restricted changelist privacy and the existing 1000-revision limit with an explicit truncation notice.
- Qualify actual EN/RU light/dark narrow/wide Qt selection, keyboard, preview and geometry, pinned tabs, native permissions, merge history and bounded query counts. Synchronize Help with Stream 0.112.123. Restart Handler and Stream. Labels remain unavailable because the server has no file-project label system; live PostgreSQL and production-data checks were not run.

## 0.6.0.74 - 2026-10-14

- Add Revert unchanged files directly to the changelist context menu. Compare the full pending change against checkout bases with bounded reads, progress and cancellation; reuse the same safe comparison for selected files. Preserve modifications, additions, missing files, deletions and renames, and never upload or alter local bytes.
- Use one native removal for up to 1000 matches and the existing atomic server bulk worker for larger sets. Qualify local races/cancellation, stale revisions, permissions, real HTTP Handler dispatch, EN/RU Qt menu activation and 1003-file late-trigger rollback; retain normal Revert regression coverage. Synchronize SDK and Help with Stream 0.112.122. Restart Handler and Stream; physical million-file/terabyte and live PostgreSQL acceptance remain unqualified.

## 0.6.0.73 - 2026-10-14

- Replace metadata-only Details with View changelist, opened by double-click or the context menu in the existing movable native window. Show metadata and description above separate collapsible Files, Shelved Files and linked Tasks tables, with shared controls, state icons, shelf selection and bounded file pages. Keep the opened identity pinned and enable description editing explicitly through Edit.
- Read contents in one native server request with restricted-metadata/task permissions and revision-pinned pagination. Qualify 13 native, HTTP and real Qt checks covering inspection, paging, Save and Submit regressions; inspect EN/RU narrow/wide light/dark layouts. Synchronize Help with Stream 0.112.120. Restart Handler and Stream; no production-data or live PostgreSQL qualification.

## 0.6.0.72 - 2026-10-14

- Save only modified RAW rows/cells, new rows and explicit deletions, matching Stream. Untouched page rows no longer produce conflicts when a background task updates them; retain original revisions and rejection of concurrent edits to the selected row. Qualify twelve real QML checks, Vue save parity and native XML-RPC/JSON conflict/rollback checks on private data. Synchronize English/Russian Help. Restart Handler and refresh Stream; no production writes or live PostgreSQL qualification.

## 0.6.0.71 - 2026-10-14

- Add a centered, movable Submit dialog with editable description, paged checked files and separate shelf inspection, conflict-resolution protection, reopen and restricted-metadata options, and unchanged-file policies. Use shared controls with EN/RU narrow/wide layout checks; retire Submit from the old shelving/integration review dialog.
- Link existing Task Manager tasks and choose a permitted configured status after publication. Save/Apply persist metadata without upload; Submit uploads only selected changed files. The native server atomically publishes the selected set and moves remaining/reopened files to pending. Task statuses update afterward through normal native task commands, with concurrency checks and an explicit retry action.
- Qualify native rollback, metadata privacy, real HTTP selected-file uploads, 1003-file shelving regression and Qt Save/Apply/Cancel/Submit interaction. Synchronize the shared SDK and EN/RU Help with Stream 0.112.118; its browser remains inspection/admin only. Physical million-file/terabyte acceptance remains deferred.

## 0.6.0.70 - 2026-10-14

- Synchronize English/Russian engine maintenance Help with Stream 0.112.117: request-local schema connection indexing and TEL batch cache reuse preserve native invalidation, relationships, permissions and file results. The shared server change requires worker reload; SQLite tree/TEL measurements and 106 executed engine/SDK checks pass, while real PostgreSQL and complete desktop repository sync timing remain unqualified.

## 0.6.0.69 - 2026-10-14

- Replace the file-workspace View pill with the shared circular icon button, using a columns icon, localized tooltip and accessible name. Keep the existing View menu and verify its real Qt interaction at narrow/wide sizes.

## 0.6.0.68 - 2026-10-14

- Enable deletion of multiple selected empty changelists and owned shelves from the context menu and Delete key. Pin the selected codes/revisions in a shared confirmation, retain local files, and send one native atomic request. Reject mixed file/header selections and active or foreign changes; nonempty pending changes still require Move or Revert first.
- Verify native batch rollback on stale revisions, permissions and trigger failures, retry behavior, and real EN/RU Qt confirmation in narrow/wide layouts. Update the server API and synchronized Help; the browser file workspace remains inspection/admin only.

## 0.6.0.67 - 2026-10-14

- Keep dragged and reconciled files local: register checkout and content comparisons in bounded native batches without allocating blobs/upload tasks. Reconcile opens a changes-only results tab with an existing/new changelist chooser. Remove standalone upload actions; review itself is read-only, and confirmed Submit/Shelve uploads the reviewed contents. Validate staged hashes, retain reviewed fingerprints and explicit transfer recovery.
- Make following Files views display selected Depot/Workspace files, including multiselection, while Pending/Submitted and fixed-source views remain independent. History follows file selection, clears stale revisions, and respects pinned tabs.
- Center the changelist/shelf target dialogs on the application, make them modal and movable by their headers, and use shared Handler action buttons. Qualify actual EN/RU narrow/wide Qt interaction, native HTTP, 1003 metadata-only additions, shelving/submission, unchanged-file comparison, changed-source rejection, recovery and Revert regression checks. Synchronize the shared SDK and EN/RU Help with Stream's inspection/admin scope.

## 0.6.0.66 - 2026-10-14

- Expose Revert at the top level of every file context menu; enable it for owned opened workspace files across file/tree/pending views. Add one shared-control Revert options dialog for a file, selected files or a whole changelist, capturing the target and defaulting Delete files not in depot to off.
- Use native bounded revert plans and one atomic workspace selection command across owned pending changes, with current permissions, edit revisions, rename pairs and idempotent receipts. Whole-change revert also checks edit revisions and active operations. After confirmed server success, optional local cleanup moves only new additions absent from the published stream to Trash; tracked and rename-lineage files remain. Recheck Head, other opens, mappings and local fingerprints before cleanup; changed/blocked files remain with a warning.
- Keep large cleanup plans in a private disk-backed journal and read them in 1000-file pages. Qualify 1003 files, native HTTP, late trigger rollback without local deletion, stale/foreign requests, changed/newly published files, receipt replay, and real EN/RU narrow/wide light/dark QML menus/options. Synchronize Help with Stream's inspection/admin scope; reload both applications for the new native API.

## 0.6.0.65 - 2026-10-14

- Start local Workspace/Files and Explorer workspace drops without Add/Cancel confirmation. Validate the entire bounded Explorer root selection in the worker before any server request; reject outside-workspace and mixed selections with one shared MD3 OK notice. Keep mappings, ownership, permissions and target edit-revision checks.
- Remove external-file copying/import destinations from drop handling. Retain original workspace paths, stream folder discovery and overlapping-root deduplication. An outside drop leaves files, server state, upload journals, recovery and connection status unchanged. Keep explicit confirmation for internal pending moves, Depot checkout and shelf review.
- Qualify native Qt drag/drop and HTTP uploads, mapped nested folders, Unicode, mixed/outside/sibling-root refusal without RPC, and the localized OK popup at narrow/wide light/dark layouts. Synchronize EN/RU Help with Stream's agreed inspection/admin scope.

## 0.6.0.64 - 2026-10-14

- Replace raw Qt standard buttons in the File workspace destructive confirmation with shared MD3 Button/DialogActions controls. Use a short operation heading, wrapping plain-text explanation and a labeled action with its semantic icon. Keep compact actions inside the popup on narrow Russian layouts, focus Cancel and preserve Escape/Cancel and single acceptance dispatch.
- Qualify the actual QML confirmation and its other destructive actions in English/Russian, light/dark themes and 360/760px windows. Synchronize EN/RU Help with Stream's read-only inspection scope; no browser changelist mutation UI is added.

## 0.6.0.63 - 2026-10-14

- Synchronize administration Help with Stream 0.112.111: a background service replaces an expired/revoked ticket before its next job for both ordinary and administrator accounts; account status and current submitter permissions remain enforced. Existing Handler connection/SDK behavior is unchanged.
- Document measured shared-engine lookup indexes and bounded request-local key parsing. Nine indexes are already applied to the local SQLite system database without record changes; worker restart loads the parsing optimization. Preserve existing journal/history/permissions and avoid whole-request claims based on SQL microbenchmarks. Live PostgreSQL remains unqualified.

## 0.6.0.62 - 2026-10-14

- Synchronize EN/RU administration Help with Stream 0.112.110: background file/check-in executors reuse per-account service tickets, rechecking validity and current permissions. Client sign-out does not cancel previously submitted jobs. The shared server needs a restart to load the fix; Handler's SDK and connection behavior are unchanged.
- Document journal indexes and the planned expired-ticket cleanup boundary. Preserve unfinished transaction/upload state and Undo history; keep sobject_log, which existing history and editor revisions use. Its own change markers remain subject to a separate dependency review. Eight indexes are already applied to local SQLite without deleting records; live PostgreSQL is not qualified.

## 0.6.0.61 - 2026-10-14

- Initialize the selected Columns Editor Wizard element when its derived element list changes, so the first saved column shows its actual title, width, visibility and widget immediately.
- Commit inline table text on editingFinished rather than the first textEdited signal. Preserve the default SObjectValueEditor behavior for other callers; Enter/blur commit the full value and Escape cancels.
- Verify real current QML creation and key events on an isolated fixture, plus both offline QML smoke checks. Capture current Table View and Columns Editor at 1496 x 660, Segoe UI, MD3 dark/light, alongside Stream. User projects, settings and running clients were not changed.

## 0.6.0.60 - 2026-10-14

- Combine active changelist list/files and file Details/Preview reads. Reconcile validates up to 1000 rename sources per native file_entries request instead of one request per file; retain server revision checks and atomic native writes.
- Keep transfer status lightweight without a workspace snapshot. Back off unchanged SDK task/bulk polling to at most two seconds and reset on meaningful progress; preserve terminal errors, timeout and fast final staging feedback. Synchronize Handler and Stream SDKs.
- Share Search Type definitions and project routes within the existing request metadata cache, including native write/rollback invalidation. Prefetch history in bounded indexed segments and read changelists in batches, following only the authorized previous links and verifying published roots. Synchronize EN/RU Help and Stream's read-only browser inspector.
- Owned paired replays: Refresh 58 to 35 SELECTs; thirty-version history 113 to 56 SELECTs (version/change reads 30+30 to 2+1). Fifty Reconcile renames use one source-read request; Preview and changelist activation use one request each. A simulated unchanged thirty-second task uses 20 polls instead of 121. Timings exclude network delay.

## 0.6.0.59 - 2026-10-14

- Replace File workspace Refresh and dependent post-operation reloads with a bounded native workspace snapshot. Share metadata, current/expanded file pages, tasks, Head/Have and checkout holders; prefetch up to 16 expanded directory pages. Group catalogue/conflict reads, skip metadata reloads for transfer cancellation and load file inspection only while Files is visible. Retain off-page selection, workspace switching, review and rollback behavior.
- Fix changelist state filtering before paging, newest-first numbering, filtered-page continuation and the owner index after handoff. Keep existing empty changes; support idempotent native Create retries. Native read records are reused only inside one request, with depot/workspace authorization retained.
- Synchronize EN/RU Help with Stream's inspection bootstrap batch. Qualify real HTTP/Qt workflows and fix a catalogue SplitView polish loop with one fill owner and the existing scrollbar. An owned original-sequence replay falls from 16 API calls/521 SELECTs/175.1ms to one snapshot/58 SELECTs/23.2ms; this includes security/schema reads and excludes network delay.

## 0.6.0.58 - 2026-10-14

- Synchronize EN/RU Raw database Help with the Stream 0.112.106 XML-RPC integer response fix. Large integer cells and row keys no longer produce Fault 500 during server serialization; the unchanged Handler SDK reads native integer tags and matches Stream JSON values. Keep JavaScript precision strings, draft guards and native client behavior. Document that the Stream service must reload the fix and an uncertain write must be reloaded before retrying because dispatch may have committed it before response serialization failed.

## 0.6.0.57 - 2026-10-14

- Add native Gantt scroll regression coverage on the same fixture and fractional dock sizes as Stream, in Russian MD3 dark at 100/125/150% scale. Verify idle viewport/content extents with empty, normal and overflowing task models. Native QML already uses real-valued extents; Stream now avoids rounded client-size feedback. Preserve the native geometry algorithm and task operations.
- Synchronize the empty-scope message and EN/RU scroll guidance with Stream. These checks establish scroll stability, not complete Gantt layout parity or verification of an existing user session.

## 0.6.0.56 - 2026-10-13

- Host the shared declarative Layout Editor in native Administration through Qt WebEngine, using the selected Stream server, authorized session and native appearance. Synchronize example/copy selection, kind-specific properties, element order, table preview, grid/layers, publishing guards and EN/RU Help with Stream. Keep original native items and standard views separate; custom views use the embedded renderer and require a Stream server.
- Prevent draft-state notifications from reloading the editor; reject stale bridge reports, release private profiles on reset and preserve project/close guards. Keep new-window links outside the editor and save Help downloads through the native file chooser. Put Configuration Close last on the right using the shared icon control.
- Verify actual Qt/browser editor geometry in two languages, themes and sizes; real input, copy/check/save, Help download/link and card/table/tree opening; controller guards, Administration navigation, Configuration header and all-window smoke. The broader Help/schema suite still reports unrelated Changelist and XML-format expectations.

## 0.6.0.55 - 2026-10-13

- Fix Raw database headings overlapping row one on first asynchronous load of a full page. Reserve the existing 40px ListView header before the first response, matching Stream's table behavior. Reproduce the failure from a fresh empty view with 50 rows; verify initial separation, sticky scrolling/return, native Windows at 150% scale and the existing raw editing cases. Preserve virtualization, square cells and lazy menus; synchronize EN/RU Help with Stream 0.112.104.

## 0.6.0.54 - 2026-10-13

- Add the used Table View Array/XML/JSON/SnapshotVersion value block with Stream: typed source values, plain-text structured cells, configured height, source diagnostics and version labels. Keep SDK raw values and existing edit/permission paths; correct NULL array/version display errors. Compare native QML and Vue captures, source algorithms and both original/native server transports. Add EN/RU Help with references. Complete legacy table migration remains open.

## 0.6.0.53 - 2026-10-13

- Put the Perforce-like changelist working pane at the top, move workspace navigation to the left and replace repeated headings/toolbars with grouped context menus. Keep secondary file-state, query, column, recovery and sync commands accessible in narrow layouts.
- Add a draggable Log splitter, hide/show controls and persisted height/visibility. Fit a compact themed status footer, retain log records while hidden and preserve geometry across worker completion.
- Open a separate native changelist window on double click or Enter. Show description first and owner/workspace/stream/revision metadata below; save owned pending descriptions through the existing API and keep other changes read-only. Preserve submit/shelve reviews and Classic project routing. Update shared EN/RU Help without expanding Stream's browser inspection/admin scope.

## 0.6.0.52 - 2026-10-13

- Fix the remaining Raw paging delay in shared TextField: instantiate its themed text context menu only on first right click and reuse it. Eager menus cost about 1.9s when presenting a real 50-row/9-column change_timestamp page; presentation now takes about 0.16s, with a follow-up next-page profile at 0.11s. Native RPC and Stream JSON return the same page in approximately 54/41ms. Preserve selection, copy/paste, readonly actions, keyboard editing, square grid geometry and draft protection; verify native Windows menus and a complete worker/RPC/QML transition on an owned temporary server. Live full-transition measurement was interrupted by the running server refusing connections.
- Synchronize EN/RU Help with Stream 0.112.102, retain one Layout Editor loader in Administration and scroll navigation entries into view in the existing narrow-window smoke check.

## 0.6.0.51 - 2026-10-13

- Remove slow Raw database page construction by using the established Qt ListView virtualized-row pattern. A private 50-row/12-column fixture creates 84 editors instead of 600; local construction falls from 8.4s to about 1.15s and a different next page builds in 0.87s. Newly visible cells read the current draft rather than a stale QVariant snapshot. Preserve square grid geometry, sticky headings, edits, readonly guards and server operations; cover full-page navigation and offscreen drafts. Synchronize EN/RU Help and qualify the matching Stream pagination flow.

## 0.6.0.50 - 2026-10-13

- Add physical local rename with replay journals, Local/Have/Head columns, indexed per-change local counts and file-level failure details.
- Restore interrupted exact uploads/downloads and lost Submit replies without republishing; retain reconnect progress and expose Resume in the workspace toolbar. Restore off-page directories and selections, bound retained trees and cursor history, and reject stale read completions.
- Add paged Workspaces, Streams, Depots, storage inspection and Stream Graph views using real submitted branch/merge references. Preserve independent tabs across workspace switching; keep Classic Commit Queue separate.
- Synchronize the native transfer SDK with Stream 0.112.100; show manifest/transfer/verification/staging phases, measured rate/ETA, and faster waiting only for the final staging chunk. Qualify real Explorer/Notepad launches, Unicode paths, themes and DPI. Native external drag input and physical TB acceptance remain explicitly open in the complete checklist.

## 0.6.0.49 - 2026-10-13

- Align Raw database with Stream: the same table filter and toolbar order, inline discard/drop confirmation, direct draft save, row numbers and icon actions, fixed 84/230px grid, sticky 40px headers, page ranges and responsive toolbar. Keep square cells, readable read-only values, atomic server operations and unknown-write guards. Compact JSON display and finite-number validation match Stream 0.112.99. Align table/export icons and synchronize EN/RU Help. Record the requirement to keep corresponding interfaces identical.

## 0.6.0.48 - 2026-10-13

- Verify raw table cell corners in focused, new, deleted and disabled rows. Document that updated QML requires an application restart; server reload only refreshes data. Fresh rendering confirms the existing square cell style.

## 0.6.0.47 - 2026-10-13

- Protect unsaved changelist descriptions during workspace switching. Reset workspace-bound rows, selection, inspector/review/navigation/progress and cached tab data; retain tab/filter/column preferences, previous local bytes, Have, pending changes and server tasks. Read the new workspace's own local cache.
- Check absolute download roots and available space per bounded manifest page, accounting for resumable large-file partials. Pause before receiving an unfittable page, show a normal bottom-Log warning, retain confirmed Have and resume the same task after space is freed. Keep native permissions, revision guards and transactional task updates.
- Continue the file-workspace checklist in the standalone Handler and shared Stream server/API. Browser scope remains inspection/administration; synchronize EN/RU operational help without adding a browser editing workflow.

## 0.6.0.46 - 2026-10-13

- Present Raw database as a compact continuous table with shared square cell editors, transparent idle cells and a visible focus outline. Remove the separate rounded input boxes and gaps; preserve cell editing, drafts and server operations. Match Stream and synchronize EN/RU Help.

## 0.6.0.45 - 2026-10-13

- Validate complete file/changelist selections in contextual actions; expose native depot write hints without replacing server permissions. File checkboxes start file-only selections; explicit Ctrl mixtures retain actionable restrictions.
- Explain valid/invalid drag targets and selected root/file counts. Offer move/revert for nonempty changelists and move every file through a pinned native server query, independent of view filters. Preserve ordinary/exclusive locks, triggers, revision checks, local bytes and atomic batch rollback.
- Open permitted changelists/shelves by number or current-project link. Route shelf drops and menu Unshelve through the same target/preview flow, preserving the shelf tab and displaying the pending target. Synchronize Stream and EN/RU Help; Classic paths remain separate.

## 0.6.0.44 - 2026-10-13

- Add Administration → Raw database for physical SQLite/PostgreSQL tables, including unregistered tables, composite keys and rows without a primary key. Edit JSON cell values, insert rows with database defaults, stage row deletion, save atomically with row conflict checks, export CSV and confirm DROP TABLE by its full name. Restrict server access to administrators; redact secret columns and keep generated/binary columns read-only. Raw SQL intentionally bypasses SObject hooks and undo history. CSV export is limited to 50000 rows.

## 0.6.0.43 - 2026-10-13

- Rename Configuration's main Cancel button to Close, matching Stream 0.112.88 and its actual guarded-close action. Preserve unsaved-setting confirmation, Save/Discard/continue-editing behavior and the stable control identifier; synchronize EN/RU Help.

## 0.6.0.42 - 2026-10-13

- Route local Workspace and Local Files drops through native staged uploads instead of server checkout. Preserve nested workspace paths, skip excluded mappings and deduplicate overlapping folder/file roots without retaining all descendant paths in memory. Keep existing workspace paths when dragging from Explorer.
- Replace the oversized generic drop confirmation with a centered, bounded Handler dialog, shared icon buttons and descriptions for local addition, Depot checkout, pending-file moves and shelves. Synchronize drag context, terminology and EN/RU Help with Stream 0.112.84; local filesystem editing remains desktop-only.

## 0.6.0.41 - 2026-10-13

- Persist stopped downloads on the server instead of leaving a running workspace sync after a local-file conflict or recoverable transfer error. Resume the same pinned selection; atomically replace a stopped selection when requesting another file, folder or revision under the same local root. Keep local changes, partial bytes, confirmed Have and native rights/triggers/rollback.
- Synchronize the shared transfer SDK, server task status, Stream Transfers inspection and EN/RU Help with Stream 0.112.83. Cover Handler Get Latest after a stopped workspace download, lost acknowledgment recovery and replacement rollback.

## 0.6.0.40 - 2026-10-13

- Stop serializing retained tab files and duplicate tree rows into hidden QML dialogs on Depot selection. Keep tree rows in their Qt models and route navigation through the cancellable read worker without changing transfer progress or the write busy state.
- Open changelists at their current server revision after folder additions; keep continuation pages and all mutations guarded against concurrent edits. Synchronize native metadata, browser inspection and EN/RU Help with Stream 0.112.82.
- Add real pointer latency, stale-row expansion and concurrent-page/write regressions. Remaining full-plan and large physical-transfer acceptance stays open.

## 0.6.0.39 - 2026-10-13

- Connect pending changelists to the desktop editing flow: create from blank-area context menus, materialize missing mapped checkout copies without replacing local edits, show modifications in expanded changes, open pending files in the associated editor and close view tabs without also activating them.
- Prepare only opened local contents before submit/shelve review, reject edits after approval and concurrent edit revisions, and preserve edited rename pairs/history through the native API.
- Add server-owned pinned query/range batches, mapping/exclusion forms and preview, workspace-switch warnings and safe setup cancellation. Keep QML JS objects out of worker snapshots; synchronize the SDK, EN/RU Help and remote inspection/admin behavior with Stream 0.112.81.
- Record fresh million-record catalog measurements separately from physical transfers; full Stage 3 scale, restart, advanced-view and packaged-GUI acceptance remains open.

## 0.6.0.38 - 2026-10-13

- Stop chat summary/history reads and shared server updates while re-authentication is required, even when the rejected ticket and cached login records remain present. Prevent the authentication signal from requeuing failed hidden chat reads.
- Resume reads after sign-in without discarding unsent chat text during session expiry. Add regression coverage for the real Debug Log authentication signal and update service lifecycle; synchronize the browser background-read gate and EN/RU communication help with Stream 0.112.76.

## 0.6.0.37 - 2026-10-12

- Extend the separate file-project lifecycle with bounded review dialogs, selected shelving and immutable shelf replacement history, explicit ownership handoff, integration comparison and undoable paired rename resolution.
- Add Files Details / Checked Out By / Preview, cancellable local reconciliation, native Windows change notifications and verified external comparison copies. Read-only views remain usable during a write without replacing its progress or selection.
- Show manifested upload names and per-file transfer states, phase progress and lost-submit reconciliation. Synchronize native APIs, SDK and EN/RU help with Stream 0.112.75; Classic remains separate.
- Full lifecycle acceptance is tracked in FILE_WORKSPACE_SCOPE.md. Million-file/TB, production PostgreSQL, complete restart recovery and packaged delivery are not claimed; the existing PySide6 shutdown ResourceWarning remains open.

## 0.6.0.36 - 2026-10-12

- Fix Show in Explorer for files opened in a changelist before sync: keep the menu enabled for missing local copies, resolve the selected source through workspace mappings, and open the nearest existing parent inside an existing workspace. Existing files retain Explorer selection; the action creates no directories and transfers no bytes.
- Treat absent workspace roots and absent local open/delete targets as normal unavailable outcomes with concise bottom-Log notices. Preserve genuine process/transport diagnostics; a successful retry clears the previous error in the worker snapshot.
- Keep submenu height bounded by the parent menu when screen geometry is unavailable, rather than clipping it to the anchor row. Verify actual popup clicks and command delivery.
- Add native-mapping and real-QML menu regression checks and update shared EN/RU help. Stream's browser has no desktop Explorer-launch counterpart; Classic is unchanged.

## 0.6.0.35 - 2026-10-12

- Fix dragging a Depot folder or stream into a pending changelist: distinguish folder roots from file paths and use one recursive native checkout. Preserve nested paths, skip excluded mappings, deduplicate overlapping folder/file selections and map Workspace directories correctly.
- Expand server metadata in chunks of at most 1000 paths inside one transaction; preserve ownership, writable mappings, ordinary/exclusive locks, triggers, idempotency and full rollback on a late failure. A folder opens files from the changelist's immutable base revision; Classic is unchanged.
- Explain internal folder drops separately from Explorer imports and report the opened file count. Synchronize the corresponding Stream administration drag/drop and EN/RU help.

## 0.6.0.34 - 2026-10-12

- Add scoped Get Latest/Get Revision to file, selected-file, nested folder, stream, depot, workspace and history menus. The separate MD3 dialog selects latest, per-file #N, submitted changelist, stream revision or ISO date/time, with explicit Force off by default.
- Keep dirty-file protection, pinned downloads and Have acknowledgement. Force repairs unchanged-Have local copies; missing file revisions preserve local bytes/Have and report a concise warning in the bottom Log. Depot selection remains correct while Files shows local rows.
- Share the native historical-selection SDK/API with Stream, including ranged downloads, case-insensitive mapped paths, indexed metadata and bounded administrator backfill. Classic remains separate; browser UI remains inspection/administration. Update EN/RU help and Russian strings.

## 0.6.0.33 - 2026-10-12

- Add a compact bottom operation Log to the Perforce-like workspace: timestamps, operation/outcome, affected path, collapse/expand, copy, clear and explicit Debug Log access. Retain at most 1000 summaries independently of worker/view snapshots.
- Return a normal blocked SDK download result for modified or untracked local files, retaining the task/path/reason and preserving local bytes. Stop before Reconcile; resume the same task after resolving the local conflict.
- Report unexpected file-worker failures in the operation Log while preserving full Debug Log tracebacks without a forced exception dialog or worker stdout traceback. Keep Classic queues and native rights/transactions unchanged.
- Synchronize the SDK and EN/RU help with Stream. Verify dirty-file protection/resume, real QML log/copy/clear/bounds, retained errors after refresh and Chromium error/cancel/narrow-layout behavior.

## 0.6.0.32 - 2026-10-12

- Preserve the Perforce-like Commit Queue after bootstrap, ping and connection-status changes. Reset its workers and view only on project changes or the existing sign-out/server-switch lifecycle signal.
- Add a regression for the full bootstrap notification sequence, retained workspace/selection during connection changes, native dock presentation and session teardown; verify real QML dock persistence and equivalent browser offline/ping behavior.
- Update EN/RU file-workspace help. Classic projects retain their existing queue; project mode remains server-defined.

## 0.6.0.31 - 2026-10-12

- Restore the full 16-topic file-workspace backlog grouped into three stages; keep explicit acceptance requirements and cross-stage limits.
- Implement scoped Ctrl/Shift/keyboard selection, selected-group context menus, independent view state, column settings, target changelist selection and native drag/drop. Keep depot/workspace trees separate from work views and preserve Classic components.
- Show current Head/Have, checkout holders, workspace/stream context and combined local/server states through bounded native requests. Add exact-file and subtree sync with local dirty-file protection.
- Add native rename lineage, empty/shelf retirement, permitted read-only changelist inspection, immutable query selections and atomic published-revision restoration. Keep ACLs, hooks and rollback authoritative; no direct business SQL.
- Run Explorer import, local Trash, local diff, real QML gestures, browser gestures and native failure/permission checks on owned temporary projects. Synchronize the shared SDK, EN/RU help and Stream behavior; retain the recorded PySide6 shutdown warning and outstanding scale/lifecycle acceptance.

## 0.6.0.30 - 2026-10-12

- Select managed Search tab read commands from authoritative server-side Search Type metadata. Older or absent client policy caches no longer route administrator file-table queries through protected generic Search.
- Preserve native permissions, column filters, bounded pagination, counts and compressed/raw query payloads. Keep Classic queries and guarded generic file access unchanged.
- Retry unsupported optional query keywords only; a permission traceback mentioning include_progress no longer triggers a duplicate request.
- Verify all ten managed tables over local XML-RPC with owned projects, stale metadata, pagination and non-admin denial; synchronize Stream regression checks and EN/RU help.

## 0.6.0.29 - 2026-10-12

- Separate Depot/Workspace tree navigation from the right changelist/work area. Folder selection no longer switches away from changelists or applies tree prefixes to their children.
- Open work views through View. Use native tabs with icons/close controls; create, rename, move and filter tabs, preserving the layout per server/user/project. Pending includes shelved changes through an explicit bounded native state set.
- Browse Workspace Have through native indexed child cursors, with owner/depot checks and pinned roots. Reconciled local trees use indexed cache seeks and skip descendant ranges. Preserve file-source filters independently of tree selection.
- Keep unique changelist numbers, shelving/unshelving, copy-number commands, checkout locks, atomic submit and Classic presentation. Synchronize Stream views/help; Stream Workspace uses server Have, while local filesystem inspection stays in Handler.

## 0.6.0.28 - 2026-10-12

- Populate an empty file-project administrator sidebar from its registered Search Types. Read availability, project applicability and native read commands from server metadata rather than hardcoding type namespaces in the client.
- Read managed Search tab pages through the authenticated, bounded native file API. Keep generic file writes and immutable revision guards unchanged.
- Display all coincident schema nodes using a local grid without modifying stored XML or creating a dirty draft. Indent the technical XML view while preserving custom elements, comments and attributes. Retain the toolbar layout picker for flow, clusters and grid.
- Verify sidebar activation, native HTTP result/cell reads, real QML schema/technical/layout controls and browser counterparts. Browser-only UUID and deferred DOM observer errors have no Qt counterpart; Handler uses Python IDs and native QML geometry.

## 0.6.0.27 - 2026-10-12

- Resolve file-project presentation on cached project restoration and controller startup. Open Perforce-like work in the native Commit Queue dock, stacked with Search, instead of the legacy utility window.
- Restore ordinary object Search tabs in file projects; keep managed file tables on their native API. Add reversible dock maximization without changing the saved layout or split ratios.
- Synchronize Stream dock routing, genuine visibility of its teleported Classic Queue and ordinary search navigation. Cover cached startup, native dock clicks, browser search/queue switching and administrator Search Type summaries for every managed table.

## 0.6.0.26 - 2026-10-12

- Replace the file-project navigation with a depot/stream/directory tree on the left and numbered expandable changelists in the main work area on the right, explicit disclosure, paged children and state icons. Label primary upload/submit/new-change actions using the existing compact controls.
- Fetch directory children through native FileProjectCmd.browse without scanning descendants. Keep immutable publication cursors, project/depot permissions, original changelist identity and Classic UI unchanged.
- Accept project changelist numbers (`#42`) for native status, move and shelf operations without bypassing owner/depot permissions. Clear directory filters when selecting a changelist; retain expanded branches while requesting more children. Synchronize Stream browsing/administration, EN/RU help and actual Qt/browser interaction checks.

## 0.6.0.25 - 2026-10-12

- Open file-project workspaces without Classic metadata/sidebar/object-search restoration; keep depot and stream access in the native FileProjectCmd path. Preserve Classic project tabs and server ACLs.
- Add cached/fresh project-selection regression coverage and synchronize EN/RU help with Stream.

## 0.6.0.24 - 2026-10-11

- Qualify PostgreSQL concurrent bulk uploads using a native batch blob read with storage/changelist fencing; preserve each file permission, SHA, hooks and rollback.

- Retry only explicitly marked pre-mutation file-project lock contention; keep background tasks resumable instead of turning SQLite writer waits into failed uploads. Test two ordinary/admin HTTP clients publishing and syncing fresh files simultaneously.

- Reject new bulk uploads before server allocation if the file-processing service is disabled; report how to enable it and restart, while retaining durable task/journal recovery and completed-task retries.
- Synchronize the transfer SDK and EN/RU recovery/installation help with Stream. Add source delivery packaging without workstation settings, tickets, logs or databases.
- Qualify fresh-byte roundtrips, lost seal/Have responses with a new client, native ACL/hooks/whole-change rollback, concurrent clients and owned worker recovery. Keep target-machine and EXE/manual acceptance separate from automation.

## 0.6.0.23 - 2026-10-11

- Use the existing compact toolbar/action menus and separate editors instead of persistent command button flows; resize the lower history/conflict/transfer panel and open the tree on demand in narrow windows.
- Add a separate project-selected Perforce-like workspace: paged changelists/files, local SHA reconciliation and Have, ordinary/exclusive checkout, upload/resume/Get latest, shelves, move/remove, immutable history and three-way/manual conflict resolution.
- Keep Classic Commit Queue intact; expose the native Perforce-like project template. Run disk/network work in the commit pool, persist upload journals outside workspace roots, and keep progress/cancellation responsive.
- Sync the native transfer SDK with Stream. Active uploads block mid-stage Submit; cancellation/failure restores the complete original draft while publication preserves native ACL, triggers and atomic rollback.
- Add EN/RU workspace help and verify actual QML clicks, local upload/download/history, light/dark/EN/RU layouts, native server rollback and Classic application smoke. Stream provides browser inspection and administration rather than local file transfers.

## 0.6.0.22 - 2026-10-11

- Fix Activity Feed instance links by resolving the requested project schema when the journal procedure runs in `sthpw`. Preserve custom link columns and both endpoint identities.
- Verify both Handler and Stream procedure bodies through XML-RPC on a private Stream fixture, with schema-selection regressions and synchronized EN/RU help.

## 0.6.0.21 - 2026-10-11

- Configuration → Server exposes the SSE batching delay (100/200/500/1000 ms, default 200 ms), persisted through the existing configuration owner. Changing it preserves the live stream and pending reads.
- Handler identifies its SSE connection to TACTIC Stream's administrator connection list. This metadata is informational and does not grant access.
- Real Qt network coalescing, narrow/wide Configuration controls, normalization and persistence checks cover the new option. EN/RU help distinguishes SSE connections from presence and describes server collection tuning.

## 0.6.0.20 - 2026-10-11

- Restore SSE invalidations for persistent reference data, script catalogs, shelf/widget configuration and triggers; include native connections and status logs in active-search subscriptions.
- Verify initial cache invalidation without a journal cursor, configuration update delivery and native project/recipient routing against Stream; retain polling, drafts and lifecycle behavior.
- Document initial synchronization and its model reads in Server configuration help in English/Russian.

## 0.6.0.19 - 2026-10-11

- Add optional Server push (SSE) in Server configuration and the Connection menu, using the TACTIC Stream collector and asynchronous Qt HTTP. Keep existing XML-RPC polling available.
- Subscribe to active Search Types, tasks/notes, chat recipients and enabled activity notifications; coalesce invalidations and permit one update read at a time. Preserve drafts/cursors, pause during check-in, use jittered reconnect backoff, and cancel all requests on shutdown.
- Verify real Qt transport, 100 merged notifications, Handler against a native Stream fixture, configuration QML and polling regressions; document behavior and deployment limits in English/Russian help.

## 0.6.0.18 - 2026-10-11

- Hide the File Offline label on the missing-versionless placeholder in Search results. File availability is displayed only for an actual snapshot; existing snapshots with unavailable files retain their offline status.
- Verify placeholder, offline and available-file transitions through the real QML result item at narrow and wide widths.

## 0.6.0.17 - 2026-10-11

- Enforce legacy numbered-only check-ins for `multi_file`, `dir` and `sequence` in preparation, queue edits and execution. Grouped Drop Plate operations also skip latest/versionless while retaining their existing filename rules.
- Disable both versionless controls for these operations. Normalize restored unsent operations while preserving the contract of work already submitted to the server.
- Build server manifests from the normalized operation so legacy and server queues use the same versionless policy; ordinary file and DCC multi-input preferences remain available.

## 0.6.0.16 - 2026-10-11

- Defer Commit Queue result-tree, Snapshot Browser, task-summary and Search Type preview refreshes across the entire running selection in both legacy and server modes. Keep per-operation results, hooks and progress live; refresh successful results once per object/context when work finishes, fails or is cancelled.
- Invalidate client snapshot/relation/search/activity caches once per affected project at that boundary. A failed server status read refreshes only already confirmed successes without resubmitting or declaring pending work complete.
- Pause automatic background server polling while the queue is active; retain one in-flight response and deliver it on resume without advancing its persisted cache cursor prematurely. Activity and notification updates catch up when the queue stops.
- Clear a completed operation's queue flag before emitting its finish signal so the previous callback cannot overwrite the next operation's state.

## 0.6.0.15 - 2026-10-11

- Persist the Commit Queue horizontal splitter ratio through native UI configuration once on drag release, and restore it when the view/application reopens.
- Bound both panels to the current viewport without losing the saved ratio when the window narrows; restore the preferred split when it widens again.
- Place Auto-clean below the queue toolbar and use the primary send button's compact presentation in narrow details panels so actions stay inside their panels.

## 0.6.0.14 - 2026-10-11

- Clear retained server progress, errors and its timer when explicitly clearing an idle queue; clearing the last completed rows does the same.
- Keep Clear queue available after auto-clean removes all rows while the completed progress panel remains visible. Preserve automatic completion totals and active server jobs.

## 0.6.0.13 - 2026-10-11

- Preserve zero-byte sizes in native FileObject measurements and metadata, including mixed file sequences, instead of dropping them and sending None to extended check-in.
- Retain missing-file behavior and native server validation, permissions, triggers and rollback.

## 0.6.0.12 - 2026-10-11

- Coalesce queue persistence during bulk before-check-in hooks and row removal; a server update page persists once after auto-cleaning its completed rows.
- Show overall server-queue progress independently of selection: preparation, current source file, acknowledged upload files/bytes, completed/failed/cancelled check-ins, elapsed time and inactive-progress duration.
- Keep progress totals after auto-clean, report interrupted transfers and unavailable status reads, and invalidate completed snapshot caches once per project in each update page.
- Retain native transactions, source checksums, client hooks, stable chunk identities and recovery without resubmitting confirmed check-ins.

## 0.6.0.11 - 2026-10-11

- Add Separate files to Commit Queue with one model insertion and one persistence write, avoiding UI stalls from repeatedly serializing the growing queue.
- Prepare legacy naming previews in bounded batches of up to 50 operations with one batch in flight; retain per-file naming execution, fresh naming at commit and native request rollback.
- Coalesce preview persistence, retain duplicate decisions and ignore stale validation responses; server queue mode requires no preview RPCs.

## 0.6.0.10 - 2026-10-11

- Wrap long diagnostic lines in Error Dialog and Debug Log to avoid Qt render-thread stalls after large check-in failures.
- Preserve complete messages, runtime requests, stacktraces, clipboard actions and structured session logs.

## 0.6.0.9 - 2026-10-11

- Add an optional server queue mode to Commit Queue; legacy execution remains the default.
- Transfer prepared files in bounded multipart chunks, allocate final naming on the server and read results for all submitted batches together.
- Preserve submitted jobs across client restarts, resume interrupted chunk submissions by identity, and keep native per-check-in rollback and client hooks.

## 0.6.0.8 - 2026-10-10

- Save inplace and preallocated check-ins in one server Command/RPC with native
  transaction titles, history, triggers and rollback; keep fresh naming before staging.
- Preserve the upload transaction for repositories transferred over HTTP.
- Verify single-call failures and native CG versions, history, undo/redo and late rollback.

## 0.6.0.7 - 2026-10-10

- Cache procedure source parsing by exact source content with bounded retention;
  preserve fresh per-file arguments, naming execution, and bundled source updates.
- Reuse an HTTP opener per transport, rebuild on host/proxy/auth changes, and
  close XML-RPC responses on success or parsing failures. Repository downloads
  explicitly use the configured transport without changing urllib globally.
- Added source-update, proxy/auth, worker isolation, request failure, and response
  cleanup regressions; exclude the client cache helper from the query plugin.

## 0.6.0.6 - 2026-10-10

- Fixed snapshot-version lookups for id-based Search Object keys using the
  native sObject filter in both naming preview and snapshot creation.
- Refresh ordinary check-in naming before transfer so queued previews do
  not overwrite earlier numbered files. Preserve prepared DCC save paths.
- Added a filesystem regression for stale previews and native CG integration
  coverage for upload and inplace check-ins with code and id keys.

## 0.6.0.5 - 2026-10-08

- Added optional local versionless symbolic/hard links in Check-in Options;
  copies remain the default. Main files and previews link to numbered versions,
  aliases are replaced atomically, and versionless-only check-ins keep copies.
- Preserved numbered files when updating an existing alias; documented Windows
  privileges, same-volume hard links, and remote-server configuration.

## 0.6.0.4 - 2026-10-07

- Prevented editor QML test hangs during input and window cleanup by selecting
  the fixture render loop before application imports. Added a bounded subprocess
  regression for the complete editor lifecycle suite; production rendering is
  unchanged.
- Ran native saved-search popup checks on Windows and synchronized keyboard
  view-selection checks with layout frames to remove test-order dependencies.

## 0.6.0.3 - 2026-10-07

- Documented the Project Templates window in both help languages, restoring
  registered-window help coverage. Updated the help check to use current Server
  page controls instead of removed connection/presence interval settings.
- Isolated the sidebar saved-search dropdown check in a bounded native Windows
  process so offscreen focus handoff and test order cannot invalidate the check.

## 0.6.0.2 - 2026-10-07

- Displayed TACTIC's built-in schema for admin and sthpw projects in read-only
  mode, with node/connection inspection and Technical XML viewing. Disabled
  schema editing and rejected server-side attempts to save these definitions.

## 0.6.0.1 - 2026-10-07

- Made error-window requests readable with Python syntax highlighting, separate
  argument lines, decoded multiline script blocks, and persistent scrollbars.
  Original requests remain unchanged in Debug Log.

## 0.6.0.0 - 2026-10-04

- Added an offline Changelog tab to the Application updates window.
- Included the changelog in release ZIPs and used the matching version's notes
  as the default release description in the archive generator. Archives now
  require a changelog entry for their version.
- Established mandatory changelog entries and revision increments for every
  subsequent completed change.
