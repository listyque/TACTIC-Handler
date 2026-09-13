# Knowledge Base

Knowledge Base is a native Qt Quick documentation surface. It intentionally
uses `TextEdit` and `QTextDocument` rather than Qt WebEngine, so opening an
article does not start a browser process or load a web application runtime.
The dock header and Workspace panels menu use the same open-book icon as the
Knowledge Base surface, so the feature is recognizable before it is opened.

## Data ownership

Each project owns one `PROJECT/th_knowledge_article` Search Type. The first
initialization is an explicit administrator action shared with Messages. Its
confirmation lists every schema change: it creates the article Search Type and
its seven content columns when missing, including `linked_skeys`, and adds the
`metadata` text column to
`sthpw/message` and `sthpw/message_log`. Existing columns and data are never
removed. The table stores sections
and articles in one hierarchy and adds searchable plain text beside canonical
Markdown. TACTIC remains the source of truth; the desktop controller owns only
the current catalog, article draft, revision, and presentation lifecycle.
If one of the shared collaboration Search Types resolves to TACTIC's
`Undefined` sentinel, Knowledge Base remains readable and reports Messages as
uninitialized instead of failing the complete catalog request.

The navigation hierarchy follows a compact page-tree presentation. Sections
and articles are ordinary borderless rows; disclosures stay before the item
icon, and section descriptions remain small secondary text. Only the current
entry receives a quiet neutral background, without an outline or accent rail.
The disclosure hit area is excluded from row activation: its click only
expands or collapses the branch, while the rest of the row opens the section.
Navigation owns a separate presentation identity, so selection follows a
pointer activation immediately while the selected page continues loading
asynchronously. If a request is already running, the controller retains and
loads the latest click.

Supervisors can drag an existing article or section onto a section to change
its parent, or above and below another row to order siblings. These changes are
an explicit local organization draft: the header exposes Save order and Undo
only after the first move, and the server receives the changed parents and
sort positions as one validated batch. Search, reload, creation, and deletion
stay blocked until that draft is saved or discarded. A section cannot be moved
into its own descendant. When a new article enters its editor, a compact
two-step flow first collects its title and summary, then gives the available
height to the rich-text body. The metadata step also names the parent section
(or the Knowledge Base root) so the destination is visible before content is
written. Existing articles open directly on their content with title and
summary collapsed. A labeled `Show title and summary` disclosure with a
downward chevron restores those fields without losing body edits; while they
are open, the same control becomes `Hide title and summary` with an upward
chevron. It never uses the Edit icon or implies that a second editor will open.

Unsaved article and section edits never block navigation. Before another page
is selected, the controller snapshots the current form, Markdown body, linked
objects, and attachment staging context into a project-local draft persisted
through the shared configuration write queue. While the editor is dirty, it
checkpoints the current document without blocking the UI, so a process crash or
forced restart can restore recent work.
That draft remains in the navigation tree with a Local draft badge and opens
back into the editor without a server request. A new page follows the same
path and does not create a TACTIC row until Save as draft, Publish, or the
first attachment upload.
The article viewer and editor expose an explicit Back to articles action only
when their page has replaced the navigation list. The action stays hidden when
navigation and article content are visible side by side. In the wide layout, a
dedicated header button hides or restores the navigation panel and immediately
returns its width to the viewer or editor. The editor synchronizes
the live `QTextDocument` before returning to the navigation list. Discard removes the
local draft, while Save replaces it with the server-backed entry. The feature
uses the shared `DockWorkspaceFooter` as its dock surface, including the common
lower-corner treatment, without adding a separate empty action row.

An article projects its `h1`–`h6` headings into the right-side outline. The
list action in the article header hides or restores that outline; hiding it
immediately returns the reserved width to the article body. In a narrow reader,
the inline outline uses the complete reading width whenever no vertical
scrollbar is needed and reserves the shared scrollbar gutter only while the
article actually overflows. The reader header uses neutral surfaces for the
page-kind tile, active outline toggle, and Edit action; accent color is limited
to glyphs and state cues so those three controls do not compete as primary
actions. A selected section presents its complete descendant outline in the
main reading area. Entries use one compact borderless column at every width.
Subsections use an open-folder icon, an explicit Section label, and indentation;
their descendants remain visible and receive a deeper indent instead of being
hidden behind another navigation step. Activating any row still selects that
page through `KnowledgeController`.

The article header estimates reading time from searchable plain text at 200
words per minute. A quiet metadata row after the article body shows the
immutable creator login, creation time, and latest update time. Creation and
update timestamps come from TACTIC's standard system fields and use the same
server-clock-corrected local presentation as the Activity Feed; raw server
timestamps are never shown as a fallback.

The Knowledge Base server procedure enforces the same edit permissions as the
UI. Administrators and members of supervisor groups can save entries. Saved
page removal goes through TACTIC's ordinary sObject delete permissions and
dependency review. Other users can list, search, and read entries. Optimistic
revisions prevent one editor from silently overwriting another editor's newer
article.

## Content and links

The editor stores one canonical Markdown body and exposes it through Visual and
Markdown source modes. Switching modes synchronizes the same draft; there is no
parallel HTML field or migration layer. The visual mode supports headings,
emphasis, lists, alignment, links, remote image URLs, and article attachments.
The compact formatting row exposes text styles through one `Aa` menu, list
types through one list menu, and keeps the Visual/Markdown switch visible.
Character-format buttons reflect the current selection or caret position. With
no selection they stay active as typing modes until toggled off; block actions
apply quotes or fenced code to the selected paragraphs, while Divider inserts
one horizontal rule at the caret. Selecting the active heading, quote, code, or
small-text style again returns the affected text to the normal style.
Narrow editors move secondary actions into an accessible overflow menu instead
of wrapping the toolbar. With article
metadata and attachments closed, the body expands to the remaining editor
height. Image dimensions and content-width sizing use the readable Markdown
suffix `{width=320 height=180 fit=content}`. Object links remain ordinary
`skey://` Markdown links.

The editor header also responds to the width of its own action set. Save,
Cancel, and Delete stay directly available; their labels collapse into compact
icon buttons when they no longer fit. The header row never increases the
article viewport's horizontal content width.

Hovering an existing text link reveals a compact Edit link action beside its
rendered range. It opens the shared link panel with the current address and
label. Saving replaces that exact anchor range, so moving focus to the action
does not make the edit depend on the current text selection.

Pointer hover and ordinary text selection stay inside the native `TextEdit`.
The editor resolves a link only when Qt reports that the hovered anchor changed.
Its passive tap handler does not take the pointer grab from native text selection;
an image click is resolved through the painted `QTextDocument` layout, with the
caret boundary used only as a compatibility fallback. Dragging across ordinary
text therefore performs no per-pointer-move Python calls or controller state
updates.
The editor also keeps image fitting out of the live dock-resize path. Dock
geometry continues to update normally while the pointer moves, but the live
`QTextDocument` image formats are fitted once when the resize gesture ends.
Ordinary non-dock width changes cross a coarse width bucket before fitting, so
one pixel of geometry never causes a full document rewrite. No debounce timer
or rasterized dock preview participates in this path.

The attachment library is closed by default. The paperclip in the formatting
row shows or hides it, and its close action returns the space to the body. One
Attach files action inside that library accepts images, video, and ordinary
files into a shared pre-upload library. The staging toolbar keeps only the
distinct clipboard-image and clear actions instead of duplicating the file
chooser. A new article stays local
until that action needs a server identity; its first upload reserves that
identity as an owner-only TACTIC draft and attaches the uploaded snapshots
before they are inserted into the text. Save as draft explicitly creates or
updates that owner-only server row and keeps the editor open. Publish clears
the draft status and makes the article visible to readers. Drafts are excluded
from other users' catalogs and from the Search Object link index.

Uploaded images, video, and other files are TACTIC snapshots attached to the
article. The attachment library derives file and preview URLs through the
native `Snapshot` and `File` APIs. Each file exposes an image preview when the
format supports one, and rendering tries that lightweight preview before the
full attachment. The same library inserts an image by its permanent web URL
or inserts a normal file link. The live editor renders an available bounded
preview while retaining that permanent URL as the image's storage identity;
saving, drafting, and reopening never replace the article link with the preview
URL. As in the original editor workflow, the lightweight preview is the image
resource of the live `QTextDocument`; its private storage property retains the
permanent URL used when Markdown is generated. This keeps painting, caret
placement, selection, movement, and resizing in one text layout instead of
creating a second QML image tree whose geometry depends on that layout. A
labeled Copy link action copies the permanent URL and changes to Copied as
immediate feedback without a timeout. The reader
hides linked-object previews and attachment cards by default; its paperclip
button reveals or hides both groups below the article. Attachments retain their
original name, preview, extension, and size. Activating a file card opens its permanent web URL;
the same mouse, touch, Enter, and Space paths work for image and non-image files.
Stored file names combine the article's server code with an opaque per-attachment
identity;
the original uploaded name remains metadata shown by the library and never
becomes the technical repository name. A physical-path collision is retried
with a new technical suffix without overwriting an existing repository file.
The editor library keeps every uploaded file in the same compact row regardless
of attachment count. The preview, original name, size, insert action, copy-link
action, and confirmed delete action remain visible without switching to a
separate image-card layout.
Attachment deletion accepts only a snapshot that the server has verified
belongs to the current article. Delete article is visible in both the reader
and editor. A saved page enters the shared sObject deletion window, which asks
TACTIC for the complete dependency graph before removal. The operator reviews
every related Search Type and chooses which dependencies to remove; the normal
defaults include snapshots and files. Linked sObject search keys stored in the
article body are values rather than ownership relations, so deleting the page
does not delete those objects. An unsaved local draft has no server object or
dependencies and is removed locally without opening the window.

An inserted image is placed at the current text caret, starts at no more than
560 pixels wide, and never exceeds the current text area. Clicking an image
selects its inline image character and draws a resize frame over the rendered
image. The frame uses the bounds from the live document layout rather than a
text caret rectangle. Clock, preview, and other unrelated controller updates
do not reload the editor document or clear its image selection. Dragging the
selected image itself moves that existing fragment to the drop caret without
creating a copy; the move is one undoable document edit. A
compact selection readout shows
the displayed size, saved article size when it differs, intrinsic source pixel
size when Qt has loaded it, and whether proportional resizing is available.
The selection panel offers two explicit sizing modes. `Stretch to content
width` keeps the image at the current article width. When it is disabled, the
slider and bottom-right handle set a strict proportional size from a 24-pixel
minimum up to the current content width. The editor retains that strict size
while stretch mode is enabled, so switching back restores it. The reader keeps
both modes inside the current text width. Selecting ordinary
text clears the image frame without taking mouse selection or keyboard focus
away from the editor. In the reader, each inline image is an accessible action:
clicking or pressing Enter or Space opens the original safe HTTP/HTTPS source,
while rendering may still use a local or generated preview fallback.

The reader renders stored Markdown to safe rich text and separates it into
native text and image blocks. Top-level paragraphs, headings, individual list
items, and image runs are independent layout units. Plain paragraphs, headings,
and list items use `TextEdit.PlainText`; list markers are lightweight native QML
text. Links or actual inline formatting use the rich-text engine only for that
small block. Images are asynchronous cached `Image`
items with a bounded decode size, and their decode source is independent from
live dock width. Resizing therefore reflows the affected blocks without
reparsing the article, replacing delegates, reloading images, or scaling the
complete dock as a bitmap.

## Linked Search Objects

An article can own a list of normalized Search Object keys in `linked_skeys`.
Creation remains independent from the current Search query and selection. Once
the new article editor is visible, a contextual action links the currently
selected Search Objects; it disappears when there is nothing new to link. The
editor keeps its live linked-object header visible above the body throughout
creation and later edits, so every linked object can be reviewed or unlinked.
The saved article shows the same live object header with the current preview,
title, description, and native object action. The preview itself uses that same object
action rather than acting as decoration. Left and right controls page through the
header when the article describes several objects without expanding every
preview into the reading surface. While editing, the unlink action removes
only the object currently shown in that header; the relation change remains in
the article draft until Save as draft or Publish. It never retires the linked
sObject itself. Compact article and section creation actions live in the
Knowledge Base header rather than consuming navigation height.

Search result cards and rows expose a persistent Knowledge Base action only
when the current project reports an article linked to that exact Search Object.
The action stays at the trailing edge of the item-action group, so hover-only
actions can appear without moving it. Activating it opens the linked article in
the Knowledge Base dock. The server
returns a lightweight project link index separately from article bodies, and
the application applies that index to every retained Search tab model. This
avoids loading article content or issuing one request per visible result item.
If Knowledge Base has not been initialized for a project, the same index
request returns an empty result and ordinary Search results remain unchanged.

Article search keys use the ordinary TACTIC form for
`PROJECT/th_knowledge_article`. They can be copied into Notes, Messages, and
other link-aware text. Notes and Messages render a Knowledge Base search key as
a compact article card with the page title, article or section type, and the
available summary instead of exposing the technical Search Type and code.
Activating the card opens that page in the native Knowledge Base dock. The
shared link router recognizes:

- `skey://` for Search Objects, tasks, notes, snapshots, files, users, projects,
  and Knowledge Base articles;
- `tactic-search://` for saved searches;
- `http://`, `https://`, and `ftp://` for external resources.

Plain descriptions are HTML-escaped before linkification. Article Markdown is
stored verbatim after boundary and size validation; its rendered rich text is
sanitized before presentation, so executable markup and unsafe URL schemes are
not exposed to the native viewer.

## Responsiveness and lifecycle

The dock is hidden by default. Its controller does not load the catalog or any
article body until the dock is presented. A project change may still request
the lightweight link index used by visible Search results; that request never
loads article content. Hiding the dock keeps its current request, catalog,
article, and editor state; project changes and shutdown still cancel owned work,
and stale completions are ignored. Search runs asynchronously with a short
debounce. Lists and article bodies use the shared persistent scrollbar. The
reader sanitizes and splits an article into native blocks only when the article
or its attachment candidates change. Resizing reflows those retained blocks
without calling Python or replacing their delegates. The editor finds images
through QText block fragments rather than scanning every document character
during width fitting.
A load or save that reaches the server after another client deleted the entry
returns a structured missing-entry result instead of an XML-RPC fault. Stale
loads refresh the catalog and preserve a still-valid selection; stale saves
retain the local draft and leave navigation available.

## Verification

`tests/test_knowledge_base.py` covers Markdown/visual round trips, source-mode
switching, linkification and sanitization, the native QTextDocument formatting
bridge, the shared schema-initialization warning,
missing-entry races, contextual selection linking, drag-and-drop organization,
creation-parent presentation, draft reservation before attachment upload, and
the real linked-object carousel at narrow and wide sizes. It also verifies that
navigation stashes and restores unsaved local drafts without a server read and
that the narrow editor exposes its Back to articles action.
`tests/test_sobject_delete.py` verifies that a Knowledge Base search key enters
the same dependency discovery and delete batch as a loaded Search result,
including checked snapshots and files and visible unchecked relation types.
The runtime QML coverage also verifies the shared Knowledge Base dock surface
and full-width inline outline without a scrollbar.
`tests/test_knowledge_server_links.py` verifies link persistence, revisions,
owner-only drafts, publishing, deterministic indexes, safe uninitialized
projects, batched hierarchy updates, and cycle rejection.
`tests/test_knowledge_workspace_links.py`
plus the workspace delegate test cover conditional row/card controls and native
action routing. Dock and search-key resolver suites cover layout restoration
and link navigation.
