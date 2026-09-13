# Application QML component map

Use this map before creating or moving a QML component. The canonical rules are
in [ui_component_policy.md](ui_component_policy.md).

## Decision order

1. Find the existing feature view and controller that own the behavior.
2. Search `thlib/ui/qml/controls` for the visual or interaction primitive.
3. Search sibling feature components for a domain presenter with the required
   model roles and signals.
4. Extend the narrowest existing owner.
5. Create a component only when it has a stable responsibility and a smaller
   public contract than the block it replaces.

Do not extract a component merely because a file is long. Local labels, one-use
wrappers, and feature-specific rows stay local unless a second real consumer
requires the same semantics.

## Shared controls

`thlib/ui/qml/controls` contains application-wide primitives. Feature views may
depend on these controls; controls never import feature QML.

### Actions and input

- `Button`, `FilledActionButton`, `CompactIconButton`,
  `ItemCountActionButton`: shared button states and semantic icon behavior.
- `TextField`, `TextArea`, `ComboBox`, `SpinBox`, `Slider`,
  `DateField`: project input behavior and context menus.
- `SearchField`: shared search icon, clear button, accessible name and
  `searchEdited` intent. Feature controllers own query debounce, tags and
  suggestions; `TacticSearchField` extends it for native Search navigation.
- `ImagePicker`, `ImageFileDialog`: native image-file selection and staged
  preview/undo presentation. `previewUrl` and `stagedPath` belong to the caller's
  controller; the picker emits a selection intent and does not upload files.
- `ColorField`, `ColorPickerDialog`: shared theme-aware HSV/HEX selection,
  staged until acceptance; used by workflow and node properties.
- `CheckBox`, `Switch`, `SegmentedButton`, `TabButton`: selection and
  mode controls.
- `Popup`, `Dialog`, `DialogActions`, `ToolTip`: transient surfaces.
- `ActivationHandler`: consistent mouse, touch, keyboard, and cursor behavior.

### Layout and presentation

- `ResponsiveFlow`: adaptive cell wrapping.
- `SmoothListView`: shared scrolling and bottom-anchor behavior.
- `ItemSurface`: hover, press, selection, rail, and separator states.
- `ItemPreview`: image/fallback preview with one loading and error contract.
- `EmptyState`: standard empty-result presentation. It owns a bounded,
  viewport-aware content width, including when centered with anchors outside
  a Qt Quick Layout; feature views must not recreate that sizing contract.
- `ProfileInfoRow`, `InfoValueStrip`, `StatusChip`, `SettingsRow`:
  repeated semantic presentation rows.
- `DockWorkspaceFooter`, `DockDragGrip`: dock geometry and footer language.
- `Typography`, `MaterialIcon`, `MaterialRipple`: centralized type, icon,
  and interaction vocabulary.

## Domain presenters

These components may be used by sibling views in the same domain. They should
receive models or narrow controller-facing properties and emit user intents.

### Search and sObjects

- `SearchWorkspaceView`: owns one search workspace lifecycle.
- `SearchResultsPane`: shared result presentation for the workspace and sidebar
  preview, including card navigation, process menus and split versions.
- `SearchResultSurface`: retains one tab's live result lists and viewport.
  `SearchTabSwitchMonitor` uses the shared `UiPerformanceMonitor` frame lifecycle;
  data swapping remains in the navigation controller.
- `WorkspaceResultItem`, `WorkspaceCard`: result presentations.
- `AdvancedSearchView`: query-card editing and saved searches.
- `SearchPresetBar`: saved-search selection and preset actions used by Advanced
  Search in both docked and modal contexts.
- `SearchResultMenus`: the workspace and sidebar preview share process filters,
  saved-search application, sorting and grouping; editor placement stays with
  the invoking view.
- `SnapshotBrowser`, `SObjectInfoView`: focused object reporting surfaces.
- `SObjectFieldGrid`: compact variable-height column layout shared by
  Edit/Create and Duplicate, with the existing `SObjectFieldDelegate` and field
  model roles. Field definitions, values and validation stay in their controllers.

`DockContentRegistry` is only a kind-to-component router. Search behavior does
not belong in the registry.

### Messages and notes

- `MessagesView`: chat orchestration, overlays, selected conversation, and
  message timeline lifecycle.
- `MessagesTimeline`: the retained per-conversation list and its delegates;
  models and the bounded recent-conversation cache belong to `MessagesController`.
- `MessagesConversationList`: conversation model presentation; emits new-chat
  and selection intents and does not know the controller or dialogs.
- `CommunicationView`: process/task notes timeline.
- `NotesTimelinePosition`: bounded object/process viewport state, without
  reloading note data or unconditionally jumping to the newest note.
- `MessageComposerField`, `MessageSendButton`,
  `AttachmentComposerControls`: shared composing path.
- `MessageBodyText`, `MessageReplyPreview`, `MessageReactionChip`,
  `AttachmentCard`, `SKeyPreviewCard`: message content presenters.
- `CollaborationInitializationState`: the shared first-run state and explicit
  server-schema confirmation used by Messages and Knowledge Base.

Do not introduce another message cache, navigation path, composer, or attachment
workflow in QML.

### Users

- `UserProfileView`: profile and user-directory window composition.
- `UserWorkSummary`: current-project task aggregates and authorized
  current-week work-hour presentation for the viewed profile.
- `UserProfileEditorDialog`: editable login profile and group membership.
- `UserFilter`: native Qt proxy over directory roles, shared by
  `UserPicker` and `UserProfileView`. `UserSearch.js` supplies the same search
  predicate to choice-based `UserComboBox`; group sections use filtered records.
  `RecordListModel.lookup` supplies profile-by-login without rescanning the
  directory for every row or opening a second profile data source.
- `controls/SectionLabel`, `controls/SummaryChip`: shared compact profile
  section and aggregate-chip presentation.

Signed-in identity remains owned by `UserController`; selecting a viewed
profile never changes the top-bar identity or authentication state.

### Knowledge Base

- `KnowledgeBaseView`: responsive dock composition and initialized/empty state.
- `KnowledgeNavigation`: searchable section and article hierarchy.
- `KnowledgeArticleViewer`: sanitized rich-text presentation and resolved
  `skey://` cards.
- `KnowledgeArticleEditor`, `KnowledgeRichTextToolbar`,
  `KnowledgeImageSelectionOverlay`: native QTextDocument editing, formatting,
  and inline-image move/resize presentation; they never own persistence or
  server permissions.
- `KnowledgeLinkedObjectHeader`: one live sObject preview at a time, with a
  lightweight previous/next carousel for multi-object articles.

`KnowledgeController` owns the catalog request lifecycle, current draft, and
the project-scoped article-to-sObject index. Catalogs and article bodies remain
visible-only; the lightweight index may refresh while the dock is hidden
because visible Search rows consume it. The index is applied to retained result
models in one batch and delegates never query it individually. Its
initialization action also supplies the two structured Messages metadata
columns described by `CollaborationInitializationState`.
`AttachmentUploadController` remains the single file check-in path.

### Tasks

- `TasksWorkspaceView`: task workspace orchestration.
- `TaskBrowserTable`: one table presenter; it already delegates to
  `TaskBulkBar`, `TaskHiddenDetails`, and `TaskTableEditorCell`.
- `TaskGanttView`, `TaskCalendarView`: schedule presentations.
- `TaskInspector`: selected-task summary and editing intent.

Task data mutation, bulk updates, caches, and server requests remain in the
existing Python controllers.

### Configuration

- `ConfigurationPage`: page-id router only.
- `ConfigurationServerPage`, `ConfigurationProjectPage`,
  `ConfigurationGlobalPreferencesPage`,
  `ConfigurationTaskPreferencesPage`, and
  `ConfigurationDccPage`: independent built-in and manifest-driven settings
  pages. `DccSettingField` renders the shared DCC field schema.
- `CheckinOptionsPage`: check-in configuration page.
- `ConfigurationSection` and `Controls.SettingsRow`: shared configuration
  presentation.

Every persistent user setting uses the existing configuration controller and
project config API; pages do not own parallel storage.

### Check-in and repository operations

- `CommitQueueView`: one selected-operation editing workflow.
- `RepositorySyncView`: synchronization progress and queue presentation.
- `CheckinOptionsPage`, `DropPlateView`, `NamingEditorView`: focused
  workflow presenters.

Transport, cancellation, progress, and source-object semantics remain in Python
controllers and native TACTIC objects.

### Administration

- `AdministrationView`: project/section navigation inside the native modal host.
- `AdminDocumentShell`: document selector, draft actions, errors and confirmation.
- `AdminSearchTypesView`, `AdminGraphView`, `AdminSecurityView`,
  `SecurityGroupsView`: native domain editors.
- `AdminGraphProperties`, `AdminProcessSettings`, `AdminProcessFields`, `AdminXmlEditor`: property and
  source editing within the selected document.
- `Controls.NodeGraph`: theme-aware, scrollable node/edge input surface, reused
  by project schemas and workflows. It emits edits without knowing controllers.

Native storage, ownership and verification are documented in
[Administration](administration.md).

## Hosts and registries

- `DockHost`, `DockPanel`, `WindowHost`, `FloatingWindow`: native window
  and dock composition.
- `DockContentRegistry`: dock content routing.
- `Main`: application composition, not feature behavior.

Hosts may instantiate feature views. Feature views and shared controls must not
reach back into hosts.

## Review questions

Before accepting a QML change:

- Which existing owner was inspected and reused?
- Is the new public API narrower than the code it replaces?
- Was the superseded inline or duplicate path deleted?
- Are controller state and server work still outside presentation QML?
- Does the component use shared theme, typography, motion, icons, input, popup,
  and scroll behavior?
- Do architecture, QML smoke, and affected domain tests pass?
