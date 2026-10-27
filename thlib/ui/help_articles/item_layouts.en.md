---
group: Administration
icon: table
order: 39
---
# Build your own view

> Open **Administration → Layout Editor**. Start from a template, arrange one
> card or row, check the result, then save your view. Ordinary layouts need no XML.

Handler and Stream share the Tactic Frame editor structure and rules. Handler
renders the editor with native QML controls; Stream uses Vue controls. Validation
and saving require a server with the layout-authoring API. Handler's **Open view
in browser** opens the system browser without a ticket in the URL; sign in there
normally. Stream opens custom views in its workspace. Standard views and the
original SObject Item remain separate.

## 1. Choose a starting point

Select the **Search Type** whose objects your view will display.
**Configuration view** offers three ready examples:

| Example | Result |
| --- | --- |
| Cards example (`cards_example`) | Large preview, title, description, object details and notes badge. |
| Table example (`table_example`) | Preview, title, description and action columns. |
| Tree example (`continuous_example`) | Original SObject Item composition, including children and snapshots. |

**Open view** opens an example immediately. To create your own version, expand
**Create custom view**, enter a name such as `my_asset_cards`, choose **Cards**,
**Table View**, **Continuous Tree**, **Blank view** or **Copy current view**, then
click **Create custom view**. Start names with a Latin letter or `_`; use Latin
letters, digits, `_`, `.`, `@` or `-`. Creating a view opens a draft; it does not save.

## 2. Understand the editor

| Area | Purpose |
| --- | --- |
| Elements on the left | Select or add images, text, links, buttons and groups. Arrows change element order. |
| Preview in the middle | One object, using sample data from your Search Type. Click a part or select it on the left. |
| Properties on the right | Content and position of the selected element. Images, buttons and text have different settings. |
| More element settings | Row variants, display conditions, shared item styles, groups and custom bindings. |
| Advanced layout settings and XML | Whole-item grid, configuration source and direct XML editing. |

On a narrow window, properties move below the preview.

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
4. **Open view** displays the saved view. Its name also appears in workspace view actions.

Any edit invalidates the previous check. **Discard** restores the saved version.
Search Type/view switching stays disabled while a draft is pending. On a revision
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
without WebEngine. **Open view in browser** opens the actual configured view in
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
