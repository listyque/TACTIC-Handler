# ![TACTIC Handler](docs/assets/readme/wordmark.svg)

**A desktop workspace for the assets, tasks and files you work with every day.**

[Русский](README.ru.md) · **[Get started](#get-started)** · [Feature tour](docs/presentations/product-tour.en.md) · [Maya integration](docs/presentations/maya.en.md) · [Documentation](docs/index.md)

Picking up an asset means finding the scene, reading the review notes and understanding what the next department needs. Handler brings those pieces together around the asset itself. Follow its record to a published version, open it in Maya, then hand back a new version when the work is done. Handler connects to TACTIC Stream and compatible original TACTIC installations.

![Standard Item View: Survey Drone, production processes and published versions](docs/assets/product-tour/item-view-standard.png)

> **Development prototype.** Handler is under active development. The Perforce-like File Workspace is also a prototype.

## Why Handler

Standard Item View expands an asset into its processes, tasks and published versions. You can see what has been done and decide which file to work from. Cards help you find things visually; tables are useful for reading and editing fields. Each view works with the same records.

Artists, supervisors and technical staff need different things on screen. Panels can be rearranged, stacked into tabs and saved as layouts, while recurring actions can become script-shelf buttons.

## Get started

For a Windows source checkout, use Python 3.14 and a running TACTIC Stream or compatible TACTIC server:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

Open **Configuration → Server**, connect and sign in. Select a project, then configure repository mappings before working with files.

[Installation and first connection](docs/handbook.en.md#installation) · [Maya setup](docs/presentations/maya.en.md#connect-installed-maya) · [Original TACTIC compatibility](docs/tactic_compatibility/README.md)

## Inside Handler

### Your layout, your tools

A review needs a large preview and its notes. Planning needs objects and tasks side by side. Docks let you build either workspace from the same panels: split the window, stack tools into tabs or move some onto another monitor. Sidebar Editor gives a department a useful starting point with its own search, page and layout.

![Dock workspace: project objects, tasks and publication previews together](docs/assets/product-tour/docks-planning.png)

[Docks and saved layouts →](docs/presentations/product-tour.en.md#docks-assemble-the-interface-around-a-job) · [Sidebar Editor →](docs/presentations/product-tour.en.md#sidebar-editor-turn-navigation-into-a-workflow)

### From an assignment to a delivery

An artist starts the day with assigned tasks; a supervisor looks for the next handoff. Task Manager supports both views, and Gantt puts the work on a timeline. Review feedback stays in the object’s Notes, day-to-day coordination happens in Messages, and Workflow defines how production stages connect.

![Gantt: production stages, assignees and dates](docs/assets/product-tour/gantt.png)

[Tasks and Gantt →](docs/presentations/product-tour.en.md#plan-the-work-then-follow-it-through) · [Workflow →](docs/presentations/product-tour.en.md#workflow-is-an-execution-engine) · [Notes and Messages →](docs/presentations/product-tour.en.md#conversations-that-retain-production-context)

### Publish a version. Find it again.

Before handing over a file, you should be able to see its name, destination and version. Drop Plate and Commit Queue take you through that preparation. The resulting snapshot connects the file to its object and process, while Repository Sync brings the required versions onto your machine. Naming Editor is where the studio defines those names and paths.

![Commit Queue: a prepared publication with its version and resolved destination](docs/assets/product-tour/commit-queue.png)

[Check-in, check-out, naming and Repository Sync →](docs/presentations/product-tour.en.md#from-working-file-to-traceable-publication)

### Maya belongs in the workflow

Once you have found the right publication, the plugin can open it in the selected Maya session, import it or create a reference. The return trip stays connected too: Maya prepares the current scene, then Handler continues check-in, transfers the files and records the publication.

![Native Maya shelf created by the Handler connector](docs/assets/product-tour/maya-shelf-strip.png)

Small studio tools tend to become part of everyday work. Put a saved script on a personal or shared shelf, give it a clear label and icon, or assign it to a project tab. The editor can also create or update that shelf in connected Maya.

![Script Shelf editor: saved project tools, icons and button order](docs/assets/product-tour/shelf-editor.png)

[Maya plugin, shelves and scene workflow →](docs/presentations/maya.en.md)

### Ask the project assistant

“Can this asset go to the next department?” Answering that means reading tasks, notes and publications together. The assistant can inspect those records for the selected object and show the work behind its answer. In the example below, it noticed that modeling was marked complete even though no model had been published.

![Project assistant working with assets, tasks and published versions](docs/assets/product-tour/assistant.png)

[Assistant: providers, tools and capabilities →](docs/presentations/assistant.en.md)

### Build a page for your team

A supervisor needs workload and status; a reviewer needs a list of assets and the details of the selected one. Dashboard Editor lets you build either page from project data. Put Item View and actions beside the figures so a useful overview also gives you somewhere to go next.

![Custom dashboard: project metrics, workload and visual assets](docs/assets/product-tour/dashboard-overview.png)

[Custom dashboards and visual authoring →](docs/presentations/dashboards.en.md)

### Keep knowledge beside the work

Delivery requirements are easy to explain repeatedly and hard to keep consistent. Write them once in Knowledge Base, attach examples and link the article to the relevant assets or shots. Readers get a searchable handbook; authors get Visual / Markdown editing, drafts and article history.

![Knowledge Base: delivery guide linked to Survey Drone](docs/assets/product-tour/knowledge-base.png)

[Knowledge Base: reading, editing and publishing →](docs/presentations/knowledge-base.en.md)

For questions about the application itself, use built-in Help. A tool’s Help action opens the relevant topic, and search finds articles by their text. Read in English or Russian, or save a Markdown copy to keep nearby.

![Built-in Help: searchable topics and a contextual article](docs/assets/product-tour/help.png)

[Explore built-in Help →](docs/presentations/help.en.md)

## Configure and extend

| Area | Explore |
| --- | --- |
| **Project authoring** | [Schema and administration](docs/presentations/product-tour.en.md#administration-shape-the-project-itself), [users and access](docs/presentations/product-tour.en.md#users-groups-and-effective-access), [configuration](docs/presentations/product-tour.en.md#configuration-connection-storage-and-daily-behavior). |
| **Context and activity** | [Object overview](docs/presentations/product-tour.en.md#object-overview-the-complete-production-record) and [server history](docs/presentations/product-tour.en.md#server-activity-understand-what-happened). |
| **Automation** | [Script Editor and runtimes](docs/presentations/product-tour.en.md#script-editor-shelves-and-production-automation), [Python API](docs/handler_api.md), [DCC API](docs/dcc_api.md). |
| **Interface development** | [Tactic Frame](docs/presentations/product-tour.en.md#tactic-frame-one-ui-description-two-native-renderers): shared descriptions rendered by native Qt Quick and Vue. |

**[Full product tour →](docs/presentations/product-tour.en.md)** · [All documentation](docs/index.md)

The modern tools shown here run against TACTIC Stream; consult the compatibility map for an original TACTIC deployment. Screenshots are current application captures on isolated Orbit Studio data; records and artwork are illustrative.

Built on the [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC) ecosystem. [Eclipse Public License 1.0](LICENSE).
