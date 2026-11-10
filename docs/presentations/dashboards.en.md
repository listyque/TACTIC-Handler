# Custom dashboards

**A useful place for your team to start work.**

[TACTIC Handler](../../README.md) · [Русский](dashboards.ru.md) · [Project assistant](assistant.en.md)

The overview and editor below run in **native Qt Quick in Handler**, connected to Stream. The Asset desk example is shown in Stream's browser. Saved page definitions belong to the server.

A supervisor and an artist ask different questions of the same data. One needs workload and delays; the other needs an asset and its review notes. Build a page for each by choosing the figures, objects and actions they need. It appears in ordinary project navigation and uses the project’s records and permissions.

![Production overview with four metrics, grouped reports, a status chart and an asset navigator](../assets/product-tour/dashboard-overview.png)

*This page is saved in the disposable Orbit Studio project and opened through its regular sidebar. Counts and reports are computed from its records.*

## One page for the production overview

This page gives a supervisor a view of the current work: **6 assets and 18 tasks, with 6 in progress and 2 complete**. The chart breaks down statuses; reports show processes and planned hours by artist. Item View sits below them, so the overview leads into individual assets.

The figures are calculated from project records. When tasks change, refreshing the page updates the report. Metrics and aggregates respect the current user’s access to the underlying data.

## Another page for working with an asset

An artist may find the **Asset desk** more useful: objects on the left and details of the selection on the right. Inspect the preview and description, then open editing or notes. It uses the same records as the production overview, with a different focus for the page.

![Asset desk with Item View, selected-object information and native actions](../assets/product-tour/dashboard-desk.png)

Select another object and the detail area follows it; the buttons act on that exact record. A tree containing several object types can use a different group of details for each type.

## Compose the page in the visual editor

Build the page in **Administration → Page layouts**. The block tree sits alongside a preview using project data and the selected block’s properties. Move things around, try sizes and spacing, undo a change and check a narrower window. Snapping and alignment help with placement; the XML view exposes the saved definition.

![Page layouts editor with block structure, production-data preview and properties](../assets/product-tour/dashboard-editor.png)

| Building blocks | What they add |
| --- | --- |
| **Row, column, grid** | Containers, weights, spans and structured composition. |
| **Heading, text, Markdown, icon, image** | Context, instructions, previews and visual hierarchy. |
| **Metric** | A number computed from the selected data source and filters. |
| **Chart** | Bar, line or donut presentation of supported grouped aggregates. |
| **Summary** | Grouped report with count, sum, average, minimum or maximum. |
| **Table** | An existing native table view with a configurable set of workspace controls. |
| **Items** | Item View with its object tree, previews, relationships and native actions. |
| **Details, field, form** | Selection-aware content and supported object editing. |
| **Action, button, link** | Native operations and navigation. |
| **Divider, spacer** | Separation and breathing room without empty data widgets. |

Header, content and footer regions establish a page hierarchy. Width/height rules, minimums and maximums, padding, gaps, fill, border, radius and shadow tune presentation. Theme tokens allow the page to fit the application's appearance.

## Connect the blocks to real data

Each data block needs a source: its Search Type, fields, filters and view. Several reports can use a shared page filter so they change together. Grouping supports up to three fields and the available aggregate calculations.

If the project already has a useful table or object card, reuse it on the page: Table takes a configured table view, and Item View takes an item layout. Open their settings from the page editor and return when done. The object keeps its familiar presentation on the dashboard.

There is currently **one Items workspace per dashboard**. Use it as the selection source for the page's details. Multiple metrics, reports and tables can accompany it. Reports read data; forms and native action blocks provide explicit write operations where permitted.

## From draft to a navigation entry

1. Create a page in Page layouts and give it a meaningful name and title.
2. Establish containers and the primary data source; choose views for object/table blocks.
3. Add metrics, reports and supporting text or actions.
4. Test the preview with real project records, selection and the intended viewport sizes.
5. Save the definition and open its project navigation entry.

The saved page uses native `config/widget_config` definitions, sidebar configuration and a project URL such as `/projects/orbit/dashboard/production_overview`. Saving checks the source revision. Supported command retries use operation identities and durable receipts to avoid duplicating an uncertain save.

## Visual editing and assistant authoring use the same page

Ask the [project assistant](assistant.en.md) to prepare a layout from supported blocks, then inspect its preview and open the saved result in the visual editor. An assistant-created page remains editable project configuration.

For example: “Create a production overview with task counts by status, planned hours by assignee and an asset navigator. Use existing project records.” The request still needs the corresponding project permissions and enabled change tools.

## Shared description, native workspace

The page document and shared Frame descriptions support **Vue in Stream and Qt Quick in Handler**. Handler renders native controls without embedding HTML. The server owns query permissions, validation and saved definitions; the client owns interaction and selection. Sharing the layout does not merge client and server execution environments.

Dashboard authoring belongs to project administration. A reader's access still determines which records and actions are available. Validate the saved page under the intended user roles, including empty data and narrower windows.

[Frame contracts](../frame/index.md) · [Administration](../administration.md)

> Dashboards are part of the development prototype. The examples demonstrate current configured pages; they do not guarantee layout parity or performance for every custom composition and data volume.
