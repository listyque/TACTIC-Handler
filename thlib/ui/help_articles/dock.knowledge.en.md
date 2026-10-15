---
group: Docks
icon: book-open
order: 31
---
# Knowledge Base dock

> Knowledge Base stores searchable project documentation as sections and Markdown articles. Readers
> get navigation, an outline, attachments and history; authorized authors get drafts, rich editing,
> object links and controlled publishing.

## Access and search

Everyone can browse and search article titles, summaries, and full text. Supervisors can create
sections, write formatted articles, insert web or skey links, attach files, images, and videos, and
copy an article search key into Notes or Messages.

## Browse and navigate

Sections and articles form a compact page tree. The disclosure arrow only expands a section; clicking
the rest of the row opens it. Selecting an entry changes selection immediately while the page loads,
and a stale response is ignored if another entry wins.

An article shows a heading outline when width permits. Choose a heading to jump to it, or hide the
outline to return that space to reading. The header shows estimated reading time, author, created and
updated time. **Change history** loads TACTIC transactions on demand and previews an earlier title,
summary and body without changing the current article.

Opening a section shows its complete contents as an expanded outline with labeled, indented
subsections. **Back to articles** appears whenever the viewer or editor replaces or hides navigation.
Hiding navigation on a wide dock switches to the same single-page flow as a narrow dock: **Back to
articles** opens the full-width tree, and choosing an article returns to the article page.
If navigation is hidden from the header, resizing the dock does not show it again; only pressing the
same button changes that choice.

## Write and format

Article bodies are stored as ordinary Markdown. Use Visual for the formatted editor or Markdown to
edit the same source directly; switching modes synchronizes one draft rather than keeping a second
HTML copy. Image size settings remain editable as `{width=… height=… fit=content}` after the image.
CommonMark normally collapses repeated blank rows between blocks. Knowledge Base preserves extra
rows as empty paragraphs, so spacing between text, images, quotes, or code remains visible after
publication.
Articles left by the former rich-text editor are converted in memory when opened. This does not
change server data until you explicitly save the article.
Bold, italic, underline, and strikethrough buttons follow the current selection or caret. Without a
selection, an active button formats the text you type until you switch it off. Quote, Pull quote,
and Code block open an insertion panel and prefill it from the current selection. Choose the code
language there; Python blocks receive syntax highlighting. Quotes have visible quote marks and a
distinct surface, while code is shown as one framed block with a language header.
The dedicated Divider button inserts a horizontal rule and leaves an editable paragraph after it.
History, text, block, and alignment actions are separated into groups. When space permits, alignment
and other formatting actions appear directly. On a narrow toolbar, the Visual / Markdown switch
collapses to icons and remains within the panel. Visual mode uses the same background, typography,
spacing and formatted surfaces as the saved article; only the caret, selection and editor controls
are added.

The new-article flow collects title and summary before content. Existing articles keep those fields
collapsed until requested. Save, Cancel and Delete remain in the editor header; labels compact to
icons when space is tight. Unsaved edits are checkpointed in the background and remain as local
drafts in the tree when another page is selected. A forced restart restores the latest checkpoint,
so navigation or an application failure does not silently discard the article text.
Moving the caret or changing selection does not leave edit mode.

## Links

Knowledge Base links in Notes and Messages appear as compact article cards with the page title,
type, and description; selecting a card opens the native Knowledge Base. Hover over an existing text
link to reveal its Edit link action.

The same link panel opens with the current address and label, and saves changes back to that exact
link without relying on the current text selection. Link hover uses native text hit testing and
never intercepts or continuously synchronizes ordinary mouse selection.

## Attachments, drafts and publishing

The paperclip in the formatting row shows or hides the attachment library; the library does not
reserve editor height while it is closed. Attach files or drop any files onto the staging area.
Hidden library thumbnails do not load; images inserted into the article remain visible in the text.
Images appear there immediately as local previews; other file types use an extension tile. Files
are then uploaded into the article's server-backed library. The same area also accepts an image
from the clipboard and can clear the pending selection.

The first upload reserves a new article as a private server draft. Save as draft creates or updates
the owner-only server draft without leaving the editor; Publish makes it visible to readers.

Images can be inserted into the text by their permanent web URL, while other files can be inserted
as links. Every item has labeled Insert and Copy link actions, and copying changes the label to
Copied as immediate feedback.

## Image layout and preview

Inserted images start no wider than 560 pixels or the current text area. Select an image to see its
displayed, article, and original pixel sizes.

Enable Stretch to content width to keep the image as wide as the article; leave it disabled to use
the fixed-width slider and resize handle. The handle keeps the resize active even when a fast drag
crosses the image or editor boundary. The reader loads each image independently, tries the
original first and uses the lightweight preview only on failure, and always keeps images inside the
available text width.

The visual editor also renders the original over a transparent document placeholder and keeps its
permanent URL in Markdown. On failure it switches to the lightweight preview without blocking the
article editor.

Large article images use a bounded viewing texture and stay loaded. Ordinary paragraphs and headings
use small plain-text layouts; rich formatting is laid out only for the affected block.

During a live dock resize the editor keeps its current image layout and fits every image once when
the drag ends, while opening an image still uses its original file. Switching back to a fixed width
redraws the image immediately, and the selection frame stays on the rendered image for every
paragraph alignment.

Every image preview in the reader opens its original file or linked object. All article attachments
are also listed after the body as file cards.

Images are inserted at the current text caret. Drag a selected image itself to move it to another
caret position in the article.

The visual editor and reader prefer reduced attachment previews and keep original URLs in Markdown;
the permanent file remains the fallback and the target opened from the article. Compact attachment
cards use the same previews.

Article titles and original upload names never become technical file names. Stored attachments
combine the stable article code with an opaque attachment identity, while the library keeps showing
the original name.

Unicode file names are supported by the upload transport. Uploaded files stay in one compact list
with their preview, name, size, insert, copy-link, and confirmed delete actions.

## Organize and archive

Deleting an article archives all of its attached file snapshots, but never deletes linked sObjects;
nested pages must be moved or deleted separately. Drag an article or section onto a section to move
it there, or above and below another row to sort it.

Save order appears only while organization changes are waiting to be saved. The new-page editor
identifies its parent section before you start writing.

## Link project objects

Articles can link to one or more selected sObjects. Their live preview and description appear in the
article header; arrow buttons page through multiple links.

While editing an article, a contextual action links the current Search selection without occupying
navigation space. The unlink action removes only the object currently shown in the article header.

The relation is updated when the draft is saved or published; the sObject itself is never deleted.

## Permissions and initialization

- A TACTIC administrator confirms one initialization shared with Messages.
- It creates the project-local article table and adds the two Messages metadata columns when
  missing; the warning lists every change before it is applied.
- Markdown is stored as the article source; its rendered rich text is sanitized before display.
- Ctrl+B, Ctrl+I, Ctrl+U, and Ctrl+K format text or insert links.
- HTTP, HTTPS, FTP, saved-search, object, file, and article links use the same application
  navigation.
- A Search result shows the Knowledge Base action only when the project's lightweight link index
  contains an article for that sObject; the action opens the article.
- Projects without an initialized Knowledge Base return an empty index, so normal Search results
  remain unchanged and no article query errors are shown.
- The Knowledge Base action stays at the right edge of the item-action group when hover-only actions
  appear.
