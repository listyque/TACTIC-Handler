# ![TACTIC Handler](docs/assets/readme/wordmark.svg)

**Desktop client for TACTIC and TACTIC Stream.**

[Русский](README.ru.md) · **[Get started](#installation-and-connection)** · [Feature tour](docs/presentations/product-tour.en.md) · [Maya integration](docs/presentations/maya.en.md) · [Documentation](docs/index.md)

Handler lets you find an asset, read its tasks and review notes, open a published scene in Maya and check in a new version. It works with local files and repositories while the server stores project records. It connects to TACTIC Stream and compatible original TACTIC installations.

![Standard Item View: Survey Drone, production processes and published versions](docs/assets/product-tour/item-view-standard.png)

> **Development prototype**, including the Perforce-like File Workspace.

## Item View

Item View is Handler’s main view. Expand an object to see its processes, tasks and publications, with file versions directly in the search results. Cards provide a visual view; tables support editing fields across many records.

Tasks, notes and file previews can sit beside the results. Save the arrangement as a layout and put project scripts on a personal or shared shelf.

## Installation and connection

For a Windows source checkout, use Python 3.14 and a running TACTIC Stream or compatible TACTIC server:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

Open **Configuration → Server**, connect and sign in. Select a project, then configure repository mappings before working with files.

[Installation and first connection](docs/handbook.en.md#installation) · [Maya setup](docs/presentations/maya.en.md#connector-installation) · [Original TACTIC compatibility](docs/tactic_compatibility/README.md)

## Handler tools

### Docks and workspace layouts

Docks divide the window into panels that can be rearranged, stacked into tabs or moved to a second monitor. Save a review or planning layout and assign it to a sidebar entry, along with the search and view the department needs.

![Dock workspace: project objects, tasks and publication previews together](docs/assets/product-tour/docks-planning.png)

[Docks and saved layouts →](docs/presentations/product-tour.en.md#docks-and-layouts) · [Sidebar Editor →](docs/presentations/product-tour.en.md#sidebar-editor)

### Tasks and scheduling

Task Manager shows personal assignments, a department’s work or the whole project. Gantt lets you edit dates and progress and see overlapping assignments. Object feedback stays in Notes, team conversations in Messages. Workflow defines the transitions between production stages.

![Gantt: production stages, assignees and dates](docs/assets/product-tour/gantt.png)

[Tasks and Gantt →](docs/presentations/product-tour.en.md#planning) · [Workflow →](docs/presentations/product-tour.en.md#workflow-graph-and-execution) · [Notes and Messages →](docs/presentations/product-tour.en.md#messages-and-notes)

### Check-in, versions and synchronization

Add files through Drop Plate, then review the version, description and resolved path in Commit Queue. Check-in saves a snapshot against the object. Repository Sync downloads selected versions to a local repository; Naming Editor defines the file and directory rules.

![Commit Queue: a prepared publication with its version and resolved destination](docs/assets/product-tour/commit-queue.png)

[Check-in, check-out, naming and Repository Sync →](docs/presentations/product-tour.en.md#check-in-and-check-out)

### Maya and script shelves

The plugin opens, imports or references a file in the selected Maya session. To publish, Maya saves the scene and Handler performs check-in: transferring the files and recording the publication on the server.

![Native Maya shelf created by the Handler connector](docs/assets/product-tour/maya-shelf-strip.png)

Script Shelf holds saved scripts with labels, icons and tooltips. Shelves can be personal, shared or assigned to a project tab. The editor can export a shelf to Maya and update it there when the tools change.

![Script Shelf editor: saved project tools, icons and button order](docs/assets/product-tour/shelf-editor.png)

[Maya plugin, shelves and scene workflow →](docs/presentations/maya.en.md)

### Project assistant

Ask the assistant to read an asset’s tasks, notes and publications and prepare a report. The screenshot shows that request for Survey Drone. Modeling is marked complete, but there is no published model file; the assistant called out the missing delivery.

![Project assistant working with assets, tasks and published versions](docs/assets/product-tour/assistant.png)

[Assistant: providers, tools and capabilities →](docs/presentations/assistant.en.md)

### Custom dashboards

Dashboard Editor builds pages from metrics, charts, Item View and object actions. The example below shows workload and project statuses. Pages open from the sidebar and can be configured for each department.

![Custom dashboard: project metrics, workload and visual assets](docs/assets/product-tour/dashboard-overview.png)

[Custom dashboards and visual authoring →](docs/presentations/dashboards.en.md)

### Help and Knowledge Base

Knowledge Base stores studio instructions: delivery requirements, onboarding material and technical notes. Articles can link to assets and shots, contain attachments and be found through search. Authors have Visual / Markdown editing, drafts and revision history.

![Knowledge Base: delivery guide linked to Survey Drone](docs/assets/product-tour/knowledge-base.png)

[Knowledge Base: reading, editing and publishing →](docs/presentations/knowledge-base.en.md)

Built-in Help opens from working tools and the main menu. It covers commands, settings and procedures in English and Russian, with full-text search and Markdown export.

![Built-in Help: searchable topics and a contextual article](docs/assets/product-tour/help.png)

[Explore built-in Help →](docs/presentations/help.en.md)

## Configuration and APIs

| Area | Explore |
| --- | --- |
| **Project authoring** | [Schema and administration](docs/presentations/product-tour.en.md#project-administration), [users and access](docs/presentations/product-tour.en.md#users-and-permissions), [configuration](docs/presentations/product-tour.en.md#configuration). |
| **Context and activity** | [Object overview](docs/presentations/product-tour.en.md#object-overview) and [server history](docs/presentations/product-tour.en.md#activity-feed-and-project-history). |
| **Automation** | [Script Editor and runtimes](docs/presentations/product-tour.en.md#script-editor-and-automation), [Python API](docs/handler_api.md), [DCC API](docs/dcc_api.md). |
| **Interface development** | [Tactic Frame](docs/presentations/product-tour.en.md#tactic-frame): shared descriptions rendered by native Qt Quick and Vue. |

**[Full product tour →](docs/presentations/product-tour.en.md)** · [All documentation](docs/index.md)

Project editors, dashboards and the assistant are shown here with a TACTIC Stream server. Use the compatibility map for original TACTIC. Screenshots were captured in the current application using the Orbit Studio demonstration project.

Built on the [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC) ecosystem. [Eclipse Public License 1.0](LICENSE).
