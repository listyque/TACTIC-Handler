---
group: Workflows
icon: code
order: 19
---
# Script Editor

> Script Editor stores and runs scripts with syntax highlighting, line numbers, search and replace,
> occurrence highlighting, completion, scrollbars, output, and server-backed script folders.

## Main controls

The source editor supports Python keywords and built-ins, names declared in the current script, and
TACTIC Handler gf and tc APIs. Open scripts use the shared workspace tabs.

The scripts tree can be hidden with the directional arrow; Local Python and Server Python use the
same Python glyph with distinct colors. Unsaved source from new and server-backed tabs is restored
locally for the current project.

Local Python runs on Qt's GUI thread, so trusted scripts can import or reload native PySide6 UI
modules and show their windows directly.

## Usage notes

- The Source toolbar provides 120-step undo and redo history, a history list, cut, copy, paste, text
  sizes, search, selection execution, and help.
- Output is read-only but supports a text cursor, selection, copy, collapse, horizontal scrolling,
  and automatic word wrap.
- Right-click a server script in the tree to copy its runner or delete it from TACTIC.
- Run only trusted scripts.
- Copy Script Runner creates the original execute_custom_script call for a server-backed custom
  script.
- An explicit local Python file path can use the same API without refreshing or publishing the
  script in TACTIC.

## Shortcuts

| Key | Action |
| --- | --- |
| Ctrl+S | Save the current script |
| F5 | Run the whole script |
| Ctrl+Enter | Run the selection, or the whole script when nothing is selected |
| Ctrl+Z / Ctrl+Y | Undo or redo an edit |
| Ctrl+X / Ctrl+C / Ctrl+V | Cut, copy, or paste |
| Ctrl+F | Open search |
| Ctrl+H | Open search and replace |
| F3 / Shift+F3 | Go to the next or previous match |
| Ctrl+Space | Show code completions |
| Ctrl+/ | Toggle comments for selected lines |
| Tab / Shift+Tab | Indent or unindent selected lines |
| Ctrl+D | Duplicate the selection or current line |
| Esc | Close completions or search |

## Script identity and server storage

Folder and Title are separate fields. Together they form the project script path shown by the tree.
Save writes the current server-backed script through TACTIC; Refresh downloads the published tree and
reconciles open tabs without discarding an unsaved local draft. A dirty marker identifies source that
differs from its last saved version.

The history button lists saved revisions for the active script. Closing one dirty tab or all tabs
asks whether to save, discard or return to editing.

## Execution targets

| Target | Behavior |
| --- | --- |
| **Standalone** | Runs supported Python in Handler for Handler UI and public API work. |
| **Selected DCC** | Sends a validated action to the exact selected client and runs on its native thread. |
| **Server** | Executes supported server-side Python through TACTIC and returns output or traceback. |

The target includes application, scene and PID when available. A missing `execute_custom_script`
capability disables DCC execution instead of routing to another client.

Local Python is a trusted developer mode and intentionally runs on Handler's Qt UI thread. Do not
perform blocking TACTIC, repository or large filesystem work there. DCC Python follows the DCC's
native thread rules; submit Handler data work rather than waiting on that UI thread.

## Output and debugging

Each tab owns its output. Standard output, standard error, completion detail and tracebacks appear in
the Output splitter for the producing script. Trigger output is appended to its script tab when
possible. Collapse, resize, wrap, select, copy or clear Output without changing source.

The completion notification is only a summary. Use Output for prints and the real traceback, and
Debug Log for request IDs, runtime commands and remote details.
