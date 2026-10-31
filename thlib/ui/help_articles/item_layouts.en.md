---
group: Administration
icon: table
order: 39
---
# Build your own view

In Handler, a custom page follows the dock frame's rounded upper corners. Its header remains a single continuous edge above the page content.

> Open **Administration → Item layouts**. Start from a template, arrange one
> card or row, check the result, then save your view. Ordinary layouts need no XML.

Handler and Stream share the Tactic Frame editor structure and rules. Handler
renders the editor with native QML controls; Stream uses Vue controls. Validation
and saving require a server with the layout-authoring API. **Open saved view**
opens the system browser in Handler and a separate browser tab in Stream, without
a ticket in the URL. Sign in there normally. The editor remains open and can be
closed independently. Standard views and the
original SObject Item remain separate.

## Page and card are separate documents

**Administration → Page layouts** edits the whole dashboard linked from navigation.
Choose a saved page or **New page** beside the page picker to start an empty draft. The ordinary sidebar
editor also has **Edit page layout** for a saved dashboard link. On a dashboard,
**Edit layouts** opens its page document. Select a block on the canvas or in
**Page blocks**. Drag it to reorder or move it into a row/column; resize with the
right, bottom or corner handles. Rows retain responsive flow, rather than absolute
screen coordinates. Properties contain pixel width/height, four padding/margin
values and a container gap. Empty width means flexible width. An Items block's
**Edit card layout** opens its referenced native item view.

**Administration → Item layouts** edits one object's card or row. Its existing
grid uses the same canvas selection and resize handles. Movement snaps to grid
cells; padding and margin are four pixel values. The original automatic shared
item composition stays automatic; grid positioning is an explicit container
setting. This does not change the appearance of other views.

**Escape** cancels an unfinished gesture. Arrow keys move a selected page block
among siblings or move a card element by grid cells; **Shift** uses a larger step.
**Alt + arrows** resizes by pixels. Narrow windows have labelled layer/canvas/
properties tabs. The canvas uses the normal runtime renderer and actual available
records; it does not create a second object tree. Previews are drafts. Saving is
explicit, checked on the server, and rejects a stale revision. After an uncertain
save, refresh to check the result before attempting another save. **Open saved view**
opens the published result without closing the editor.


Item blocks preview up to three actual records in both clients; the published page keeps normal paging and expansion.

The details pane previews the first accessible item using the current draft. Business controls are inactive on the canvas; use the saved page to work with records.

## 1. Choose a starting point

Select the **Search Type** and **View** in the top row. The **Views** list above
the element layers also opens saved layouts. Both remain outside technical
Configuration settings. Three ready examples are available:

| Example | Result |
| --- | --- |
| Cards example (`cards_example`) | Large preview, title, description, object details and notes badge. |
| Table example (`table_example`) | Preview, title, description and action columns. |
| Tree example (`continuous_example`) | Original SObject Item composition, including children and snapshots. |

**Open saved view** opens an example immediately. To create your own version, click
**New view**, enter a name such as `my_asset_cards`, choose **Cards**,
**Table View**, **Continuous Tree**, **Blank view** or **Copy current view**, then
click **Create draft**. **Blank view** is selected initially. Start names with a Latin letter or `_`; use Latin
letters, digits, `_`, `.`, `@` or `-`. Creating a view opens a draft; it does not save.

## 2. Understand the editor

| Area | Purpose |
| --- | --- |
| Views and elements on the left | Open saved layouts, then select or add images, text, links, buttons and groups. Arrows change element order. |
| Preview in the middle | One object, using sample data from your Search Type. Click a part or select it on the left. |
| Properties on the right | Content and position of the selected element. Images, buttons and text have different settings. |
| More element settings | Row variants, display conditions, shared item styles, groups and custom bindings. |
| Advanced layout settings and XML | Whole-item grid, configuration source and direct XML editing. |

On a narrow window, use the labelled Elements, Item preview and Element settings tabs.

**Collection layout** repeats objects as cards, a list, a tree or a table; it does
not position an image inside a card. **Card width** controls how many cards fit across.

## 3. Build a card

1. Create `my_asset_cards` from **Cards**.
2. Select **Preview**. Set **Data binding** to **Object preview**. Set **Image
   height**, for example `200`, and choose to fill the image area or show it whole.
3. Select **Title**. Bind **Object title** or a record field such as `name`.
4. Select **Description**. Bind **Object description** or the `description` field.
5. Select **Notes**. Choose the **Notes** action and **Number of notes** for its badge.
6. To add a button, choose **Button** in **Add widget**, give it a label and select
   an action such as **Object details**. Its icon is optional. Actions reuse
   existing object operations; the configuration contains no executable code.
7. Add **Link** for a hyperlink. Enter **Text** and **Link URL**. For a record URL,
   expand **More element settings** and select **Link URL binding**.

Bindings read each object's data. **Fixed text** means a constant you enter.
Buttons use their label when text is empty. Element labels do not rename database records.

## 4. Position elements and overlap them

| Position setting | Meaning |
| --- | --- |
| Row | `1` is the first row; `2` is the next. |
| Column | `1` is the left edge. |
| Column span | With 12 columns, `12` fills a row and `6` fills half. |
| Row span | Number of grid rows occupied. |
| Layer | Higher values appear in front. |
| Container | View root or the group containing this element. |

Move buttons change row/column. Expand **Place on the grid** to drag an element
from the list onto a cell. Moving does not change its spans.

To place a title over an image, give both row `1`, column `1`, column span `12`
and the same row span. Set image layer `0` and title layer `1`. Overlap is local
to one container.

The tree example uses **Shared item layout**, so grid position fields are hidden.
For free positioning, choose **Grid** for the relevant container in advanced
settings and remove **Style roles** that position parts absolutely. A single
group can use Grid while the rest of the item keeps its original appearance.

## 5. Build a table or reusable widget

Start from **Table View**. The preview immediately shows one table row. Click a
column heading to edit it. Each top-level element becomes a column. **Move
element earlier/later** below the list changes column order. Configure each
column's content. To place image and text in one cell, add a **Group** and assign
it as their **Container**. A group has its own grid. Separate table cells cannot
overlap. This table renders item widgets; use **Columns Editor** for specialized
editable TACTIC cells.

To reuse a composition, save a separate named view made of elements and groups.
In another layout, add **Reusable view** and enter that saved view's name.
References use the saved configuration; self-reference and cycles are rejected.

## 6. Check, save and open

1. **Check and preview** validates XML, inheritance and nested widgets, then
   shows the resolved result without saving.
2. Fix any reported error and repeat the check.
3. **Save to server** publishes the configuration. It stays disabled until a
   successful check.
4. **Open saved view** displays the saved view independently of the editor. Its name also appears in workspace view actions.

Any edit invalidates the previous check. **Discard** restores the saved version.
Switching Search Type or view asks whether to keep editing or discard the draft. On a revision
conflict, reload and reapply changes. If a network failure leaves the save result
unknown, reload before retrying. Test long names, missing descriptions and absent
previews. **Preview item type** switches between main/child objects, processes,
relations, versions and snapshots.

## Advanced settings explained

**Item variant** restricts an element to all/main/child objects, processes,
relations, versions, snapshots or files. **Display conditions** combine with AND:
`desktop`, `mobile`, `tree`, `not-tree`, `object`, `object-or-process`, `not-branch`,
`description`, `snapshot`, `branch`, `relation`, `mobile-upload`. For example,
`desktop object` shows an element only on a desktop object row.

`record.name` and `record.description` read record fields. `node.title`,
`node.preview.image`, `node.task_count` and `node.note_count` read prepared item
data. Enter a custom path in **Custom data binding**. Links allow safe HTTP/HTTPS,
relative URLs, mailto and tel. Configuration HTML/JavaScript is not executed.

## XML for moving a layout between projects

```xml
<config>
  <my_cards layout="sobject-layout" collection="grid" columns="12" card_width="280">
    <element name="picture" row="1" span="12" height="200">
      <display class="image"><bind>node.preview.image</bind></display>
    </element>
    <element name="title" row="2" span="12">
      <display class="title"><bind>node.title</bind></display>
    </element>
    <element name="notes" title="Notes" row="3" span="12">
      <display class="button"><action>notes</action><badge>node.note_count</badge><icon>FAS_COMMENT_ALT</icon></display>
    </element>
  </my_cards>
</config>
```

The source of truth is project `config/widget_config`, keyed by Search Type/view.
Shared examples and templates live in `config/search_type/widget/DEFAULT-conf.xml`;
project overrides take priority and are preserved on software updates. Quick
filters and saved searches have their own editors.

Limits: 128 elements, 12 columns, 8 nesting levels and 64 compositions. New
arrangements of supported widgets need only XML. Entirely new executable widgets
need a renderer implementation. Legacy Mako/Python CustomLayoutWdg is not executed.

## Native Handler editor

Handler edits layouts with the same Frame controls and XML operations as Stream,
without WebEngine. **Open saved view** opens the actual configured view in
the system browser; it needs its own normal login. The design preview remains
native and selecting its elements edits the configuration rather than executing
object actions. Check and preview the exact XML before Save. Changes made after
the check require another check. An unknown save result requires server readback.


## Live tree preview and project cards

The Design canvas uses actual records and the working result renderer. Expand
records and relationship/process branches to inspect their real children.
Changing element properties updates the draft preview without saving. Selecting a
widget edits its properties; mutation buttons do not execute in the editor. An
invalid draft keeps the last valid picture and shows its error. Check and preview
still validates the exact draft before Save.

For a custom card choose Grid, add groups, images, titles, text, links and native
action buttons, and set their row, column, span and height. Use Search Type in
More element settings to target a particular record type. A Reusable view widget
loads its named item view for that Search Type. This lets a project and its task
records use different cards inside the existing tree. Unmatched branches keep
their ordinary presentation. Existing relationships control which children load.

The internal agent can read, preview and save these item views using
`ts_item_layout_read`, `ts_item_layout_preview`, `ts_item_layout_save` and
`ts_item_layout_operation`, with the administrator's normal configuration rights,
revision checks and durable save receipts. A dashboard's Items widget selects the
saved parent view. Custom cards are declarative widgets and normal actions;
executable scripts keep their separate Script Editor workflow.

### An item navigator and its content

A dashboard can place the existing item tree on the left and a details pane on
the right. Selecting a project or task shows its configured fields, rich text and
related tables on the same page, preserving expanded branches. Ask the agent to
compose an `items` and `details` row; each actual Search Type can have its own
details fields. This uses the normal dashboard tools and saved project settings.

## Canvas selection and clean preview

Click a visible element to select it. Alt-click cycles through overlapping layers,
including their container; Layers remains available for virtual/contents groups.
Children in row/column flow can be selected, but grid drag/resize handles are shown
only where grid positioning applies. This does not replace the native item tree.

In Item layouts, **Resolved preview** removes editor outlines and handles. In
Page layouts, **Clean preview** hides the layer/property panels and canvas guides;
**Back to editing** restores your selection. Both show the current draft without
publishing it. Preview does not activate business mutations.

Visual card edits generate indented XML. **Format XML** on the Source XML tab also
formats an imported compact definition as a draft change. Opening a view does not
rewrite saved XML. Text, CDATA/scripts, mixed content, comments and xml:space
sections are preserved; use ordinary Check/Save to publish any formatting change.

## Page data without XML

In Administration → Page layouts, select a widget on the canvas or in Layers.
Its Properties panel now has a **Data** section:

- **Data source** selects a real project/system table. Table and Items widgets
  also offer the saved views available for that source.
- **Filters** are conditions that all must match. Choose a field, comparison
  and value. Numbers and Yes/No remain typed; zero and No are valid values.
  Is empty / Is not empty test missing database values, not blank text.
  Matches text pattern uses `%` as a wildcard, for example `%robot%`.
- Text and Markdown offer **Static text**, **Current project**, **Selected
  object** inside a Details pane, or **Specific record**. For a fixed record,
  choose its type, enter part of its name/code, click Find records, select the
  result and its Source field. No search key has to be typed.

Selected-object fields follow the existing item tree selection; a type-specific
field appears only for that type. A Current project field keeps reading the
project even inside Details. Markdown expects a text field; Text accepts scalar
values. A condition group in Details can target a particular record type.

Changing the source keeps the old view and conditions visible for review.
Unavailable choices are marked; replace or remove them explicitly. Invalid
conditions show an error and retain the last valid preview. Blank values must
be filled or replaced with Is empty. Nothing is saved until Check/Save succeeds.

The internal agent can discover these same real sources, fields and views through
`ts_dashboard_sources`, then preview and save the ordinary page document. It
does not need XML, a new tree, or generated application code for these bindings.
Existing permissions, revision checks and save recovery still apply.

## Shared page filters, charts and grouped reports

Select Page in the page editor's Layers. In Properties → Shared page filters,
add a filter, give it a label, choose its source and field, comparison and default
value. Enable it by default if required. For a date range add From and To
conditions. Values stay typed; zero, No and missing values are distinct.

Data widgets inherit enabled page filters for the same source. For a different
table choose Shared page filters → Choose fields explicitly in that widget and
map each shared filter to a real field of the same type. Not applied excludes
that filter. An empty explicit mapping excludes all shared filters. Local widget
conditions continue to apply too; all conditions are combined with AND.

Add a Bar chart or Grouped report widget. Choose its source in Data, then use
Grouping and aggregates to add grouping fields and measures. Date/timestamp
groups can use UTC years, months or days. Count accepts all rows or a particular
non-empty field; Sum, Average, Minimum and Maximum use numeric fields. A metric
can show one aggregate without grouping. Give measures meaningful labels.

**Chart type** selects bars, a line with area fill, or a donut. Hover a mark to
read its full label and value. Bars and lines support signed values; missing line
values leave a gap. Donuts require non-negative values and show their total with
a scrollable legend. A single date remains a single point; dates are not invented.

The server computes aggregates over all visible matching records before limiting
displayed groups. Choose group order or sort by the first measure, and a group
limit. If more groups exist, the widget shows a truncation notice. The report grid
uses normal native scrolling and virtualization; charts support negative values.
No matching rows leave numeric aggregates empty instead of inventing zero.

On the published page, use the single **Search this page…** field. Type a value
or a filter name, choose a suggestion with the mouse or arrows and Enter, or
enter `Field: value`. Matching text is highlighted. A chosen condition appears
below the search and immediately refreshes the page's charts, metrics and tables.
Click the condition's close action to disable it. Numbers, booleans, dates and
empty values keep their native types. Search and conditions are local runtime
state; they never rewrite the saved dashboard. Resizing does not start a query.
Suggestions retain the source/project/read-access constraints and are limited;
an explicit field and typed value can be submitted without choosing a hint.

The internal agent uses the same dashboard schema and native tools for shared
filters, explicit mappings, groupings and measures. Source permissions, revision
checks and save recovery still apply. Limits: eight page filters, three grouping
fields, eight measures, 100 displayed groups per report. Arbitrary joins,
formulas, editable forms and printable report
pagination are separate features.

## Page structure and local Undo/Redo

In Administration → Page layouts, select a widget on the canvas or in Page
blocks. The breadcrumb above the canvas shows its ancestors; click one to select
the container or the page. Add widget inserts inside a selected row, column or
Details, or beside an ordinary widget. The existing item tree is unchanged.

The compact editing toolbar provides Undo, Redo, Duplicate widget and Move up/down.
Duplicate copies a complete subtree with its data bindings, filters and spacing;
it selects the new copy. The editor refuses copies that exceed structural limits
or duplicate the page's single item workspace or Details pane. In Properties,
Parent container moves the selection to the end of the chosen container. It
cannot move a widget inside itself or its descendants. Reorder works among siblings.

Undo/Redo retains the last 20 committed draft edits and restores the corresponding
selection. A new edit after Undo clears Redo. Pending text must first be committed
or discarded. Ctrl+Z, Ctrl+Shift+Z/Ctrl+Y and Ctrl+D work inside the page editor;
text fields retain their native text editing shortcuts. All operations also have
explicit buttons. Preview is read-only; busy, uncertain and read-only editors
cannot mutate the draft through these actions.

This history is local to the current draft, not the transaction rollback of a
saved project. Reloading, discarding or switching pages clears it. Replacing the draft with a server-normalized version also clears its old history. Editing and
undoing may request an ordinary checked preview, but never save the page.
Publish only with the normal validated Save to server and revision check.

## Page canvas size and zoom

The toolbar inside the page canvas controls its preview size. Automatic width
uses the available editor area. Phone 360, Tablet 768, Desktop 1280 and Wide 1920
presets show the same native page at those logical widths. Enter a custom width
from 320 to 3840 pixels in the adjacent field; clear it to restore Automatic width.
Changing preview width reflows the page as it would at that viewport size.

Choose 25–200% or Fit in the zoom selector, or use Zoom in/out. Fit fits the page
width without enlarging a small preview. Zoom changes its display scale, not
widget sizes, data filters, layout width or history. Use the normal wheel and
visible scrollbars to move around a large page; Shift+wheel scrolls horizontally.
The scrollbars and resize handles stay usable at small scales. Mouse resizing
uses logical pixels: at 50%, a 20-pixel pointer movement changes geometry by 40px.

Clean preview keeps the selected width and zoom while hiding editor guides and
disabling mutations. These viewing settings are local to this editor session;
they are not saved in DashboardDocument and do not make the published page fixed
width. Switching pages restores default viewing settings. Changing size/zoom
does not create Undo entries or reload an existing item tree.

## Multiple selection, alignment and guides

In Page layouts, Ctrl/Cmd-click or Shift-click toggles blocks in the selection.
The compact Multiple selection button gives the same operation without a
modifier. Shift-drag draws a selection rectangle; dragging empty canvas also
draws a rectangle. Whole blocks inside the rectangle are added. Selecting a
container includes its descendants once, so a parent and child are never moved
twice. Click an unselected block normally to return to a single selection.

Drag selected blocks together, or use arrow keys (Shift: 10px). The Align menu
matches left/right/top/bottom edges or horizontal/vertical centers against the
selection's bounding box. A movement or alignment is one local Undo step. Escape
cancels a drag. Multiple-block resize is deliberately unavailable; resize blocks
individually. Structure actions apply to a single selection.

Guides snap dragged edges/centers to other visible blocks within six screen
pixels, including at a different zoom. The Snap button toggles this; hold Alt
during movement to bypass snapping. Alt-click still cycles underlying layers.
Guides and the selection rectangle are transient and are never saved.

Mouse movement now changes Horizontal/Vertical offset in the current container;
it preserves the existing layout slots, hierarchy and data bindings. Positive
and negative offsets are supported (X: -2400..2400, Y: -1600..1600). Fixed-height
containers still clip their contents. Use Parent container and Move up/down to
change structure. Offsets are part of the page and follow normal revisioned Save.

## Block appearance

Appearance controls the block wrapper: fill, stroke color/width (0..8px), corner
radius (0..48px), shadow and layout-change animation. Colors accept six-digit
hex values. Fill also accepts transparent, panel, workspace, surfaceContainerLow
and surfaceContainerLowest (Raised card);
stroke accepts outlineVariant, contentAccent and transparent. Theme roles adapt
to light/dark mode. Existing content widgets retain their native inner styling.
For multiple selection the appearance change applies to every selected block;
the inspector displays the primary block's current values. Undo is atomic.

Shadow paints a cached blurred surface without rendering the card's content into
an intermediate image. Animation transitions
geometry when a live page changes; it is suppressed while editing and respects
global motion/reduced-motion settings. It is not an autoplay or script animation
builder. Clean preview hides selection/guides while preserving actual styling.

## Responsive grids and native page elements

Add widget now includes Grid layout, Heading, Icon, Object image, Button, Divider
and Spacer. Existing tables, item trees, details, metrics and reports remain the
same native components. Add a grid to a blank page, then add its children. Empty
grids keep one visible row so the canvas remains selectable.

Grid columns (1..12) and minimum cell width (80..1200px) determine the actual
column count at the current width. A cell may span several columns/rows (1..12).
Column spans shrink when there are fewer columns. Row height (40..800px) and Gap
define the tracks. The editor fills free cells in row order; offsets are not
required. Set Row/Column span on a selected child. Increase span/track height for
more room. Contents remain bounded by the cell. A grid grows with its rows unless
you set a fixed height. Row containers also expose their Stack below width.

Width/Height behavior: Auto retains existing numeric-size or automatic behavior;
Fixed uses the numeric field; Fill container uses the available cell; Fit content
uses the natural content size. Minimum/maximum sizes constrain these preferences.
Leave a maximum empty for no additional limit. Narrow hosts/cells bound preferred
minimums rather than forcing shell overflow. Height and its limits refer to
content, with padding/margins outside. Changing a numeric width/height or resizing
with the mouse selects Fixed. Content sizing uses native font metrics in both
clients. Geometry edits remain local Undo steps until ordinary revisioned Save.

Heading/Text expose shared typography roles, weight, alignment and theme/custom
colors. Icons use the existing native icon picker. Buttons expose native normal,
primary and tonal styles and an optional icon. Set Link URL to an HTTP(S) or
TACTIC address; an empty new button stays disabled until configured. Editing and
clean preview never execute actions. Published buttons use existing native link
navigation. TACTIC links and connected-server custom page/dashboard URLs open
inside the workspace as search tabs, preserving the current application. Links
to other sites retain the normal external-browser behavior.

Object image uses the project's/selected object's/specific record's normal
ThumbWdg preview, including the existing initials fallback. Choose its binding
and record in Data. Contain keeps the whole image; Cover crops to fill the area.
The block does not load arbitrary image URLs or local file paths. Use native
check-in to provide the object's thumbnail. Divider/Spacer use the same layout
and sizing rules; the spacer remains selectable on the editor canvas.

Native record forms are described below; arbitrary script actions and new
chart types remain separate. These elements use the same schema as the internal agent and need
no project-specific frontend code or XML editing.

## Record fields, forms and native actions

Use the existing Items/Details composition for Project -> parts -> nested parts.
Choose the selected-record binding inside Details; its content follows the native
item selection. Field/Form/Action also support the current project or a specific
record from Data. No separate hierarchy or application sidebar is created.

Record field displays one actual scalar field as text, badge, progress (0..100),
date, date/time or number. NULL displays a dash; zero/false retain their values.
Set a suffix for units, for example %. A badge's color is the configured theme
color; it does not guess workflow completion from a label.

Record form uses the existing native edit view. Choose the data source/record,
then select Form fields from its actual edit-view catalogue. Native edit view
selects another configured form view. Grid columns, minimum cell width and gap
arrange the existing inputs. Text, multiline, selection, checkbox and date/time
controls use native EditWdg metadata; options/statuses come from the project.
Read-only records show read-only fields; protected fields cannot be submitted.
Uploads, parent reassignment, multivalues and custom action handlers use the full
native editor or existing relationship tools, not a replacement write path.

Save is explicit and atomic for changed fields, using EditCmd. Both record and
form configuration revisions are checked. Native transactions keep ordinary
Undo. Cancel drops the draft. Drafts belong to their target record and survive
selection changes within this page (up to 20 pending forms). They are not saved
as project data or persisted across closing/reloading the page.

After a lost response Save becomes Check saved state. Check does not repeat the
write. A saved result refreshes the values; unchanged permits another Save;
a conflict offers cancellation against refreshed data. The selected pane updates
without reloading the item tree. Never execute changes from editor/clean preview.

Record action offers Open details, Edit record, Notes, Copy link and Refresh.
These invoke the existing native owners for the bound object; Edit record opens
the full native editor. Copy link uses the object's actual TACTIC search key.
Notes keep the record's process where configured. No generated script is run by
these named actions; custom script launch remains a separate native integration.

## Search inside dashboards

A row containing Items followed directly by Details is a two-pane workspace.
Both panes fill the remaining page height and scroll independently. Drag the
divider, or focus it and use the arrow keys, to adjust their widths. The chosen
ratio belongs to the open page, not the saved configuration. Narrow pages stack
the panes. Other rows keep their ordinary layout behavior.

For a narrow navigator, choose a dedicated item view with a readable title and
one short secondary line. Use images only when those records have useful images.
Avoid a table view that repeats column headings inside every item. Put record
actions in Details; its Refresh updates the selected record without reloading
the item tree. Set Details' outer padding to zero to align its own surface with
the Items panel.

Items and embedded tables use the ordinary search field with suggestions. Type a
title, keyword or description fragment; use the mouse or arrow keys and Enter to
choose a suggestion. Enter without a selected suggestion runs the typed search.
Clear the text and press Enter to return to the page's original selection.
Typing alone does not replace the executed query used by paging and refresh.

Suggestions and results retain the source's parent, project, saved search and
page conditions. Embedded suggestions refine that same table rather than opening
an unrelated search tab. Short summary tables can hide Search in their controls;
full lists retain it. The agent should reuse these controls, not add a second
plain-text filter bar. In the editor, the Items search is shown disabled.


Resizing a dashboard pane keeps measured item heights, expansion and selection.
Custom cards and child rows retain their spacing while the splitter moves;
changes in the content height are measured without reloading the tree.

## Readable cards and field colors

In the Item layout editor, add **Field**, choose its data binding and a display:
plain text, date, date/time, status badge or progress. **Label** is an optional
caption; dates hide the unused time and progress draws a percentage and track.
Choose **Text / icon color** for a field, or **Value color** for values found in
the preview and saved color rules. These are presentation rules for the actual
project values; they do not change workflow meanings. Choose another preview
record to inspect its value. Removing a value color restores the field default.

Groups expose **Fill color**, **Stroke color** and **Corner radius** to separate
related information without changing the application theme. Keep action rows at
least 40 px high. Named actions show their count alongside the label once;
narrow action cells keep the icon and count with a full tooltip. Icon-only
actions use a square control with a separate corner count. Tasks and
Notes still open their ordinary inspector. The same saved view renders in TH
and TS, including the editor's clean preview. Native revision checks and
transaction history apply to saves.

## Header, content and footer

Select a top-level block in **Page layouts** and choose **Page region**:
**Header** for context and instructions, **Content** for records and reports,
**Footer** for page actions and navigation. Shared page filters are in the
header automatically. The title and filter zone, scrolling content and footer
have distinct shared surfaces and dividers. Footer actions stay available while
you scroll data. On a short/narrow page, an oversized header or footer gets its
own visible scrollbar so controls remain reachable. Empty regions add no bar.

Use **Height → Fill container** on the last content block to use the remaining
working area, for example a full table. Use the region setting to move a block
between these areas; canvas positioning works within its area. Nested containers
inherit their parent's area; moving a header/footer block into one changes its
region to Content. Filters, table search, selection and pagination keep their
normal state and stable widget identity during resizing.

The Search Type list uses the selected project's current server catalog.
Shared types are available when their tables exist in that project. The editor
does not choose a type from another project's cached list. A failed preview shows
its error instead of continuing to show Loading interface.

The page editor's **Page blocks** tree uses widget icons. Its header contains
**Add widget**. Click a branch chevron to fold or unfold its children; when a tree
row has focus, Left folds and Right unfolds. Selecting a block on the canvas
reveals its ancestors in the tree. Drag either panel divider to resize the tree
or properties; the header chevrons collapse and restore each panel at its last
width. The tree starts narrower, and collapsed Administration navigation uses a
compact icon rail. Narrow windows keep the labelled panel selector.

The page editor has one toolbar above the tree, canvas and properties. The
first row groups the page picker, **New page**, **Clean preview**, **XML** and the
labelled **Actions** menu. **New page** opens name/title fields and **Create draft**;
it does not save automatically. With no selected page, the toolbar shows only
page selection and creation, with a hint below. The second row groups Undo/Redo,
size presets, zoom and selection tools. Actions holds Open saved view, Duplicate
widget, Move up/down and Canvas settings. Controls wrap together on narrow
windows. Canvas settings reveals a custom pixel width.
**XML** shows the current validated draft's server configuration in a read-only
source viewer with selection, copy and search. **Design** returns to the canvas.
This is the XML generated for Save, including the dashboard definition. Viewing
XML, folding branches or changing panel widths does not save a layout.

Open a referenced layout directly with the small **Open** icon beside
**Saved view** in the page widget's Data settings: Items opens that exact Search
Type and view in **Item layouts**, and Table opens its saved definition in
**Columns Editor**. A page Link/Button that points to an existing dashboard in
this project also has **Edit linked page layout** beside **Link URL**. External
addresses and pages from another project do not open a local layout editor.

The destination header has **Back to page layout**, named after the source page.
Back restores the selected widget and its tree branch. Page view state (panel
widths, folding and canvas scale) is retained during linked navigation. Card and
column editors remain open with their drafts; returning does not save or discard
them. Reopening that same card/column definition reuses the draft. Opening a
different definition or replacing a page first requires saving or discarding its
changes. Canvas selection automatically unfolds and scrolls its widget into view
in the tree, while keyboard input remains on the canvas.

In **Item layouts**, select a **Reusable view** widget and click the small
**Edit nested item layout** icon beside its **Reusable view** field. The editor
opens the named view for the widget's explicit Search Type, or the current
Search Type when that field is empty. **Back to item layout** in the header
returns one level and restores the configuration source, selected widget, editor
tab and panel widths. Multiple nested levels work in order; returning from the
first level restores the existing **Back to page layout** action when applicable.
Save or discard changes before opening another layout or returning. Navigation
never saves automatically. A missing nested view shows an error and still allows
return; it does not create a blank override. Unavailable Search Types and invalid
or self-referencing names cannot be opened. Native draggable widget-tree rows
also support ordinary click, keyboard and touch activation without duplicate
actions; dragging still moves the widget.

When there are no records for the preview, **Item layouts** displays
**Item preview · Sample data** with example values. Selecting a widget also
uses sample data when the available records do not match its Search Type or
variant. Matching real records take priority. You can select widgets and resize
them on this canvas normally; Save writes the layout configuration only.
Example values never create or change business records. Read and permission
errors remain visible instead of being replaced by sample data.

Page backgrounds may fill the available area. Header controls, content cards and footer actions retain shared inner spacing and scrollbar clearance; authored padding and margins are preserved inside it.
