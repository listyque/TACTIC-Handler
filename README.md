# ![TACTIC Handler](docs/assets/readme/wordmark.svg)

**The native workspace for assets, tasks, files and Maya.**

[Русский](README.ru.md) · **[Get started](#get-started)** · [Feature tour](docs/presentations/product-tour.en.md) · [Maya integration](docs/presentations/maya.en.md) · [Documentation](docs/index.md)

Handler brings a studio's production context to the desktop. Browse an asset, follow its tasks, review published versions and send a scene to Maya from the same workspace. Connect to TACTIC Stream, or to original TACTIC within the supported compatibility scope.

![Standard Item View: Survey Drone, production processes and published versions](docs/assets/product-tour/item-view-standard.png)

> **Development prototype.** Handler is under active development. The Perforce-like File Workspace is also a prototype.

## Why Handler

- **Start with the object.** Ordinary Item View expands assets into related records, processes, tasks and file versions. Cards and tables offer additional views of the same data.
- **Keep the handoff connected.** Review notes, naming rules, publications, local repository files and Maya actions retain their project context.
- **Build the workspace around the job.** Arrange docks, save layouts and put department tools on a personal or shared script shelf.

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

Split areas, stack tabs and detach panels onto another monitor. Keep Item View beside tasks, notes and a publication preview. Sidebar Editor turns saved searches, pages and layouts into department navigation.

![Dock workspace: project objects, tasks and publication previews together](docs/assets/product-tour/docks-planning.png)

[Docks and saved layouts →](docs/presentations/product-tour.en.md#docks-assemble-the-interface-around-a-job) · [Sidebar Editor →](docs/presentations/product-tour.en.md#sidebar-editor-turn-navigation-into-a-workflow)

### From an assignment to a delivery

Task Manager, Gantt and the calendar connect work to people and dates. Notes keep feedback on the object; Messages carries the team conversation. Workflow defines the route through production and review.

![Gantt: production stages, assignees and dates](docs/assets/product-tour/gantt.png)

[Tasks and Gantt →](docs/presentations/product-tour.en.md#plan-the-work-then-follow-it-through) · [Workflow →](docs/presentations/product-tour.en.md#workflow-is-an-execution-engine) · [Notes and Messages →](docs/presentations/product-tour.en.md#conversations-that-retain-production-context)

### Publish a version. Find it again.

Prepare files in Drop Plate, inspect names and destinations, then publish through Commit Queue. Return to a specific snapshot or synchronize selected publications into the local repository. Naming Editor makes the project's filename and path rules visible.

![Commit Queue: a prepared publication with its version and resolved destination](docs/assets/product-tour/commit-queue.png)

[Check-in, check-out, naming and Repository Sync →](docs/presentations/product-tour.en.md#from-working-file-to-traceable-publication)

### Maya belongs in the workflow

The plugin connects the selected Maya session to Handler. Open a publication, import a file, create a reference or prepare the current scene for check-in. Maya handles scene operations; Handler handles publication and transfers.

![Native Maya shelf created by the Handler connector](docs/assets/product-tour/maya-shelf-strip.png)

Save a script as a personal, shared or project-tab shelf button. Choose its icon, label and order; create or update the corresponding shelf in connected Maya.

![Script Shelf editor: saved project tools, icons and button order](docs/assets/product-tour/shelf-editor.png)

[Maya plugin, shelves and scene workflow →](docs/presentations/maya.en.md)

### Ask the project assistant

Ask about the selected object, inspect records behind the answer and review the operations used to prepare a change. The assistant works with the project's context and available tools.

![Project assistant working with assets, tasks and published versions](docs/assets/product-tour/assistant.png)

[Assistant: providers, tools and capabilities →](docs/presentations/assistant.en.md)

### Build a page for your team

Combine live metrics, charts, Item View and actions into a production overview or review desk. Dashboard Editor, page layouts and Tactic Frame connect custom interfaces to project data.

![Custom dashboard: project metrics, workload and visual assets](docs/assets/product-tour/dashboard-overview.png)

[Custom dashboards and visual authoring →](docs/presentations/dashboards.en.md)

### Keep knowledge beside the work

Write the team's handbook in Visual or Markdown, attach files and link articles to actual objects. Sections, search, drafts and article history support onboarding and repeatable production procedures.

![Knowledge Base: delivery guide linked to Survey Drone](docs/assets/product-tour/knowledge-base.png)

[Knowledge Base: reading, editing and publishing →](docs/presentations/knowledge-base.en.md)

The built-in Help explains the application itself. Open a tool's contextual article, search across topics, read in English or Russian and save a Markdown copy.

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
