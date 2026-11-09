# TACTIC Handler

### From the first asset to the published scene

A native studio workspace connecting objects, tasks, files and Maya tools in one production context. Python · Qt Quick · TACTIC / TACTIC Stream.

[Русский](README.ru.md) · [Full feature tour](docs/presentations/product-tour.en.md) · [Maya & shelves](docs/presentations/maya.en.md) · [Get started](#start)

![Review workspace: visual assets beside a full publication preview](docs/assets/product-tour/docks-review.png)

> **Development prototype.** The Perforce-like File Workspace is also a prototype.

<a id="workspace"></a>
## The whole object, in view

The **standard Item View** expands an asset into a continuous tree of related objects, processes, tasks, snapshots and file versions. Previews, status and discussions stay beside the work. Cards, compact rows, tables and separate version panes offer other ways to browse the same records.

![Standard Item View: object, processes and expanded version history](docs/assets/product-tour/item-view-standard.png)

[Search, presentations and object workflows →](docs/presentations/product-tour.en.md#workspace)

<a id="maya"></a>
## Bring Maya into the workflow

Open a published scene, import a file or create a reference in the selected Maya session. Prepare the current scene for check-in; Handler takes it through naming, versioning and the publication queue. The plugin provides the Handler connection and a native launch shelf.

![Native Maya 2023 shelf created by the Handler connector: TH launch and project tools](docs/assets/product-tour/maya-shelf-strip.png)

[Maya plugin: capabilities, installation and scene workflow →](docs/presentations/maya.en.md)

<a id="scripting"></a>
## Studio tools on your shelf

A saved script becomes a button with its own icon, label and tooltip. Build a personal or shared shelf, or assign a dedicated set to a project tab. **Create or update that shelf in connected Maya as well.** Script Editor provides the workspace for developing tools and choosing their runtime.

![Shelf editor: actual demo-project scripts, labels, icons and action order](docs/assets/product-tour/shelf-editor.png)

[Shelves and Maya export →](docs/presentations/maya.en.md#shelf) · [Script Editor and automation →](docs/presentations/product-tour.en.md#scripting)

<a id="docks"></a>
<a id="sidebar"></a>
## Compose your own interface

Docks turn one application into a review desk, an artist's workspace or a planning station. Split areas, stack tabs and move panels to another monitor. Presets, Sidebar Editor and presentation editors connect the layout to each department's work.

![Objects, tasks and published files in one dock composition](docs/assets/product-tour/docks-planning.png)

[Docks and presets →](docs/presentations/product-tour.en.md#docks) · [Sidebar Editor →](docs/presentations/product-tour.en.md#sidebar)

<a id="planning"></a>
<a id="workflow"></a>
## Turn a process into a team plan

Workflow defines an object's route. Task Manager and Gantt connect its stages to people, dates and progress. Notes preserve review decisions; Messages keeps the team talking across projects.

![Gantt: production tasks, assignees and dates](docs/assets/product-tour/gantt.png)

[Workflow →](docs/presentations/product-tour.en.md#workflow) · [Tasks and Gantt →](docs/presentations/product-tour.en.md#planning) · [Messages →](docs/presentations/product-tour.en.md#communication)

<a id="files"></a>
## Publish with a clear destination

Drop Plate prepares files. Commit Queue shows the pending publication. Naming Editor defines names and paths. Snapshot Browser takes you back to the required version, while Repository Sync brings selected files into the local repository.

![Commit Queue: prepared publication, version and resolved destination](docs/assets/product-tour/commit-queue.png)

[Check-in, check-out, naming and Repository Sync →](docs/presentations/product-tour.en.md#files)

<a id="assistant"></a>
<a id="dashboards"></a>
## Two more ways into the project

| Project assistant | Custom dashboards |
| --- | --- |
| ![Assistant analyzing tasks and published versions](docs/assets/product-tour/assistant.png) | ![Production overview with live metrics and objects](docs/assets/product-tour/dashboard-overview.png) |
| Ask about the selected object, inspect the answer and see the operations behind it. **[Explore the assistant →](docs/presentations/assistant.en.md)** | Compose metrics, charts, Item View and actions into a working page. **[Explore dashboards →](docs/presentations/dashboards.en.md)** |

<a id="administration"></a>
<a id="people"></a>
<a id="history"></a>
<a id="object-overview"></a>
<a id="configuration"></a>
<a id="frame"></a>
## Built around your studio

[Schema and administration](docs/presentations/product-tour.en.md#administration) · [Users and access](docs/presentations/product-tour.en.md#people) · [Object overview](docs/presentations/product-tour.en.md#object-overview) · [Server history](docs/presentations/product-tour.en.md#history) · [Tactic Frame](docs/presentations/product-tour.en.md#frame) · [Configuration](docs/presentations/product-tour.en.md#configuration)

<a id="start"></a>
## Get started

[Install and connect](docs/presentations/product-tour.en.md#start) · [Maya setup](docs/presentations/maya.en.md#setup) · [Python API](docs/handler_api.md) · [All documentation](docs/index.md)

The modern tools shown here run against TACTIC Stream. For original TACTIC, consult the [compatibility map](docs/tactic_compatibility/README.md). Captures use current applications on isolated Orbit Studio data; the records and artwork are illustrative.

[Eclipse Public License 1.0](LICENSE) · Built on the [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC) ecosystem.
