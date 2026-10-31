# Content spacing

`shared_ui/core/foundation.mjs` owns the palette-independent logical-pixel scale.
Handler ships its independent copy. Vue receives `--space-<role>` variables from
`cssVariables`; native components read `theme.spacing.<role>` or the same module.
Do not define a second scale in CSS, QML or a feature controller.

| Role | DIP | Use |
| --- | ---: | --- |
| none | 0 | Edge-to-edge table/dock/page body; a host around an already padded surface |
| text | 2 | Closely related small text |
| tight | 4 | Compact adjacent tools, text details |
| compact | 8 | Related controls, field-to-action gap, stacked label/editor gap |
| content | 12 | Window body, panel/form interior, column gap, ordinary content separation |
| section | 16 | Separate sections and document blocks |
| major | 24 | Large empty-state/content clearance where the composition needs it |

The old browser xs/sm/md/lg variables refer to tight/compact/content/section.
Themes change control heights and radii; they do not change content insets.

## Ownership

- Table and dock backgrounds, data/header rows and authored page bodies reach
  their allocated edges. A containing page must not add an implicit horizontal
  gutter. Table cell text has one 12-DIP inset, including the first data column.
- A bordered panel/ordinary form owns one 12-DIP interior. Its parent owns the
  separation from neighboring panels. Do not add another body margin merely
  because the child is rendered through a Frame View port.
- Mixed forms align labels, full-width editors, action rows and choice grids on
  the same interior edge. Their last row ends one interior inset from the bottom;
  the row gap is not added again to the scroll extent. Long captions wrap before
  deciding between columns and stacked controls.
- A dialog title bar meets the window edges. Body content starts one 12-DIP
  inset after it; there is no second header/content gap. Browser borders consume
  one CSS pixel, so Dialog and EditorPanel account for that border once. QML
  painted borders do not consume the content box.
- A settings row measures the actual column gap for its stack decision. Browser
  ResizeObserver updates are deferred through the existing Frame size observer.
- Author-specified XML padding, margin, offsets and gaps remain authoritative.
  Tree indentation, virtual row extents, icon optical alignment, hit areas,
  font line boxes and scrollbar/splitter reserves have their own owners. A
  numeric value in one of those roles is not an extra page gutter.

The semantic defaults reach Administration, Configuration, object forms,
messages/notes, search chrome, help/diagnostics and file/task editor compositions.
Native file pickers and the legacy HTML interface keep platform/legacy layout.
This contract does not imply every custom XML view has been visually inspected.

## Checks

`frontend/tests/frame_spacing.mjs` exercises mixed/long forms at four widths in
both languages and all themes, including trailing actions and scroll extents.
`frontend/tests/frame_spacing_browser.mjs` and Handler `tests.test_frame_spacing`
exercise actual controls, 320/800px layouts, palette changes, Apply and dialog
content bounds. Set `FRAME_SPACING_CAPTURE` to retain matching real captures.
Keep scrollbars visible when capturing. Existing configuration, field editor,
table, window and messaging tests remain part of integration verification.
