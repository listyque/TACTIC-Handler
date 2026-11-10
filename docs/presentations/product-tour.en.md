# TACTIC Handler: from asset to delivery

[Visual presentation](../../README.md)

**Handler is a desktop client for TACTIC and TACTIC Stream.** This tour follows an ordinary working day: find an asset, understand its tasks and notes, open the right version and publish the result. Along the way, it covers the tools a studio uses to set up that process.

**Start with an asset, then follow its work through the team.**

[Русский](product-tour.ru.md) · [Workflow](#workflow-what-runs-when-a-stage-is-complete) · [Tasks & Gantt](#assign-the-work-and-keep-track-of-dates) · [Files & naming](#check-in-and-check-out-hand-files-to-the-next-person) · [Tactic Frame](#tactic-frame-a-shared-ui-language-for-handler-and-stream) · [Administration](#administration-define-your-projects-objects-and-relationships) · [Get started](#install-connect-and-add-your-own-tools)

[Docks](#docks-for-review-planning-and-publishing) · [Sidebar Editor](#sidebar-editor-a-starting-screen-for-each-department) · [Object overview](#the-work-and-history-behind-an-asset) · [Server history](#activity-feed-who-changed-what-in-the-project) · [Users & access](#bring-people-into-the-project-and-set-their-access)

| Explore the assistant | Build your own workspace |
| --- | --- |
| [**The built-in project assistant →**](assistant.en.md) — Ask about real records, prepare changes and inspect the operations behind an answer. | [**Custom dashboards →**](dashboards.en.md) — Combine metrics, charts, Item View and selection-driven tools into a project page. |

![TACTIC Handler — Item View with six Orbit Studio production assets](../assets/product-tour/item-view.png)

*Fresh captures of the current application in Orbit Studio, a disposable demonstration project with fictional people and concept artwork. The interfaces and records are real; the artwork is illustrative.*

> **Development prototype.** The product is under active development. The Perforce-like File Workspace is also a prototype. Evaluate your actual schema, permissions, scripts and file workflows on isolated data before production use.

## Why an artist needs a desktop client

An artist’s work moves between a project record, files on disk and an open scene. Handler works at that boundary: it handles local directories, repositories and connected Maya while retaining the link to server records. Connected to **TACTIC Stream**, the same client also provides the modern project editors, workflow, dashboards and assistant shown here.

The server remains responsible for project records, permissions, workflows and publications. Handler handles desktop interaction, local files, queues and the selected DCC connection. This division lets the studio keep a shared record of the work while artists use their own machines and applications.

Stream is the server fork of [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC); Handler is its independent desktop companion and also connects to original TACTIC within the verified compatibility scope. Stream retains TACTIC's configurable model and workflow foundation while developing a current Python core, visual authoring and a Vue interface sharing Frame descriptions with Handler.

Consider an asset moving from modeling to rigging. The completed task describes progress, review notes record decisions, and a snapshot identifies the files that were actually handed over. The next person needs all three. Objects, pipelines, tasks, conversations and publications are connected so you can work out what happened and where to pick up.

```mermaid
flowchart LR
    Model["Project schema\nObjects and relationships"] --> Work["Workflow\nProcesses and rules"]
    Work --> Team["Tasks and review\nPeople, dates, decisions"]
    Team --> Publish["Check-in\nNaming, versions, files"]
    Publish --> Delivery["Delivery and reuse\nRepository and clients"]
    Publish --> Team
```

## Item View: find an asset and see what belongs to it

Work usually starts with something specific: an asset, shot, document or another project object. **Item View** lets you recognize it by its preview, read useful fields and reach its actions. The tree reveals related records, processes and publications. When you need to compare or edit many fields, a table gives you sorting, filters and selection.

Each search tab keeps its working state when you move elsewhere. Filters narrow the server query; tags and quick filters help you return to familiar sets of records. Put tasks, notes, snapshots, details or a calendar beside the results, then save the arrangement so the department can start there next time.

### Standard Item View: processes and versions in one tree

The standard continuous tree exposes object previews, related records, processes, tasks and snapshot versions inline. Expand a publication to inspect the actual versions, descriptions and file previews. Compact rows and versions-right/versions-bottom modes reorganize the same native object view; custom Item Layouts are an additional authoring option.

![Standard Item View](../assets/product-tour/item-view-standard.png)

### Item Layouts: useful fields and actions on each card

A review needs an image and useful actions; a dense list needs a few short fields. **Item Layouts** can provide either by connecting text and images to object data. Supported actions can sit inside the card. Preview the result on project records and save it as a presentation you can use again.

![Item Layouts — structure, live object preview and editable properties](../assets/product-tour/item-layouts.png)

**Page layouts, item layouts and columns have distinct jobs:** a page composes a workspace, an item layout composes one object, and a table view chooses its fields and widgets. The sidebar connects these definitions to project navigation. [Item Layouts Help](../../thlib/ui/help_articles/item_layouts.en.md)


## Docks for review, planning and publishing

During a review, give the preview most of the screen and keep its notes nearby. For planning, that space may be more useful split between objects and tasks. **Docks** let you build both arrangements from working panels: place them side by side, stack them into tabs or put a tool away until it is needed.

![Review arrangement — visual objects with a following context panel](../assets/product-tour/docks-review.png)

### Arrange the panels and make room

Drag a panel's grip toward an edge to split the target, toward its center to create a tab stack, or toward the title to exchange positions. Resize the dividers, reorder stack tabs, maximize a panel temporarily or hide it and recover its space. A cancelled drag restores the previous arrangement.

Handler supports floating panels and detached native dock windows, including a second-monitor arrangement. Panel geometry is restored within available screens.

![Planning arrangement — object browsing and tasks share the workspace](../assets/product-tour/docks-planning.png)

| Workspace | A useful composition |
| --- | --- |
| **Review** | Item View + Snapshot Browser + Description/Notes: choose a record, inspect the publication, keep its discussion visible. |
| **Planning** | Results + Task Manager/Gantt + task details or calendar where supported: connect assignments and dates to production objects. |
| **Publishing** | Results + Drop Plate + Commit Queue: identify the destination, prepare files and inspect the pending publication. |
| **Documentation** | Results + Knowledge Base: keep project records beside the team's reference material. |

Selection connects the panels: choose an object, process or snapshot in Search, and the tools following that selection show its data. Open a task and Inspector goes to that task. Rearranging the panels keeps this connection between selection and content.

### Save a layout for yourself and the team

Personal workspace state retains placement, sizes, visibility and stacks in its owning client/tab. **Layout presets** save named project arrangements on the server: apply, refresh, save, replace and delete are separate operations. Assign a preset to a sidebar entry so a department opens into a useful default; later personal tab state can retain that user's arrangement.

A preset describes panels and their layout. It does not save credentials, commit an editor draft or become a saved search. Reset restores workspace geometry without deleting project records or saved searches. In combination with Item Layouts, Columns Editor, page layouts and script shelves, docks let a studio compose a wide range of working interfaces from implemented tools. [Docks and windows](../../thlib/ui/help_articles/windows.en.md)


## Sidebar Editor: a starting screen for each department

Two departments can work with the same assets and need different starting screens. “Asset review” can open a visual presentation and review panels; “Asset planning” can open the relevant search and tasks. Sidebar Editor assigns each entry its Search Type, initial search, view, dock layout and script shelf. Navigation then opens a workspace that is already prepared for the job.

![Sidebar Editor — an asset-review entry and its workspace settings](../assets/product-tour/sidebar.png)

| Editor area | What you build |
| --- | --- |
| **Navigation tree** | Links, sections and separators; order, nesting and visible entries. |
| **Item** | Display title, icon, Search Type, predefined search, initial item presentation, assigned dock preset and shelf. |
| **Configure search** | Prepare the actual search workspace, including saved search, quick filters, process visibility, sorting and grouping. |
| **Access** | Groups allowed to see an item; preview the draft for a selected group. Hidden entries remain editable. |
| **Technical / XML** | Stable internal identity, child views and the supported widget/view configuration. |

Handler's `tactic_handler` sidebar and TACTIC's `project_view` are independent definitions. The editor chooses the target explicitly. Its project selector controls the authoring scope, even if another project is open in the main workspace.

Rename the display title to change the label while retaining the internal identity. A configured Saved Search initializes the entry's first tab; reopening retains its working state instead of adding a duplicate tab. XML Apply updates the draft, and Save publishes the sidebar. Group preview changes what the editor shows; it does not impersonate that group or replace server data permissions. [Sidebar Editor Help](../../thlib/ui/help_articles/sidebar_editor.en.md)


## The work and history behind an asset

Before picking up an asset, it helps to see who worked on it, which notes remain and what has been published. **Details / SObject Report** brings that history together for one record. The header shows its preview, identity, description and figures; the sections lead into tasks, notes, relationships, files and activity.

![SObject Report — identity, work summary and participants for Survey Drone](../assets/product-tour/object-overview.png)

| Section | What it answers |
| --- | --- |
| **Tasks and participants** | Who is involved, what statuses/processes exist, and how much work has been logged? Participants are gathered from tasks, notes, publications and work entries. |
| **Notes** | Which decisions and comments belong to the object or its processes? Open a note in its original context. |
| **Children and relations** | What related production objects sit underneath or alongside this record? |
| **Snapshots and files** | Which processes have publications, how many files do they contain, and what is their total size? Expand the process tree for versions and previews. |
| **Activity** | Who created or changed the object, tasks, notes, publications, work entries and supported relationships? |

A task opens the matching Task Manager scope and selects the exact task in Inspector. A note returns to its process discussion. Publications retain their source project. Cost information is shown only with the corresponding permission. The report helps explain what is behind an object’s status and opens the records you need to inspect. [SObject Report Help](../../thlib/ui/help_articles/sobject_info.en.md)


## Workflow: what runs when a stage is complete

After modeling, an asset might move through look development and rigging in parallel, then wait for approval before publication. A pipeline describes that route. The server runs configured responses to events: updating tasks, handling dependencies, calling scripts and sending notifications. The asset’s production route and a task’s progress within one stage have different jobs, so their pipelines are configured separately.

![Workflow canvas — Concept, Model, Look development, Rig, Review and Publish](../assets/product-tour/workflow.png)

*A configured production graph with parallel look development and rigging, an approval stage and an automatic action. The screenshot demonstrates the definition; it is not evidence that every branch has executed.*

| Node or rule | What it contributes |
| --- | --- |
| Manual and approval | Work assigned to people; review and sign-off stages. |
| Action and condition | Run configured server behavior or choose a route from a condition. |
| Hierarchy, input and output | Organize nested pipelines and their entry/exit points. |
| Dependency and progress | Coordinate related work and process completion. |
| Status and process events | React to pending, action, complete, revise, reject or error transitions. |
| Process rules | Update task or parent status, create downstream tasks, record actual dates, invoke a saved script or class, and configure notifications. |

Author in **Administration → Workflow**: choose a pipeline, arrange its graph, inspect the selected process, edit its type-specific settings, and save the draft. Technical views expose XML and advanced configuration when a studio needs precise control. Dependencies, triggers, notification rules and naming are related configuration, not interchangeable concepts. Saving a graph does not execute its actions or send mail.

The server stores and executes the pipeline. Handler provides a native editor and views for working with its tasks, so the team uses the same rules from either client.

## Assign the work and keep track of dates

### Task Manager: your assignments and the team’s work

An artist needs assigned work; a supervisor needs the department or project plan. Task Manager can change that scope, from selected objects and a Search Type to personal and team tasks. Table and compact views show assignees, supervisors, statuses, dates, progress and effort. Search, filters, grouping and sorting help you focus on the part of the plan you need.

Edits remain explicit drafts until saved. Bulk changes apply to the selected tasks; the inspector keeps a task's object and discussion accessible. Server permissions determine the readable fields and available edits.

![Task Manager with project tasks, assignments, progress and dates](../assets/product-tour/tasks.png)

### Gantt: dates, overlapping work and time spent

A list can hide the fact that one person has two assignments due at the same time. Gantt places tasks on a timeline and shows scheduling warnings. Move or resize bars, adjust progress, change scale and group by assignee. Existing dependencies are visible, and tasks without dates remain accessible.

![Gantt view with overlapping assignments, progress and scheduling warnings](../assets/product-tour/gantt.png)

*Orbit's sample schedule deliberately contains overlaps. The warnings are part of the real interface. Dependency visualization does not imply automatic cascading rescheduling.*

The task calendar and agenda provide a date-oriented view; milestones represent project checkpoints. Work-hour entries and cost reports connect effort to people and work where the account has access. [Task Manager Help](../../thlib/ui/help_articles/dock.tasks.en.md) · [Calendar Help](../../thlib/ui/help_articles/dock.task_calendar.en.md)

## Messages and Notes: discuss the work and keep decisions

Use **Messages** to bring reviewers together, clarify a deadline or reach a colleague in another project. It has direct and group conversations, Favorites, replies, mentions, reactions, pins, forwarding, search and member management. Add files through the picker, drag and drop or the clipboard; unfinished messages stay in drafts.

![Messages — a production review conversation with four project participants](../assets/product-tour/messages.png)

When a conversation settles a decision about an asset, record it in **Notes** against the object, process or task. The next person can find it with the work. Recurring instructions belong in **Knowledge Base**, with its article tree, attachments and revision history. Notifications and the activity journal help people notice changes and return to the affected records.

[Built-in Help: search and contextual instructions →](help.en.md) · [Knowledge Base: articles, editor and history →](knowledge-base.en.md)


## Activity Feed: who changed what in the project

When a status or file has changed and you need to understand why, open **Activity Feed**. It shows supported project events: notes, publications, tasks, field changes and work hours. Each entry includes the actor, time, details and a way back to the object or task. An object’s Activity section narrows the history to that record and supported child and relationship events.

![Activity Feed — server-backed project events and their actors](../assets/product-tour/activity-feed.png)

Filter by people and activity category, exclude your own actions, search loaded events or choose a day from the calendar. Older events load while scrolling; calendar counts cover accessible history beyond the currently loaded list. Dates follow the user's local timezone, while relative ages use synchronized server time.

Three histories serve different purposes. **Activity Feed** explains project changes. **Notifications** records notices from the current client session and links to their sources. **System Activity / Debug Log** exposes runtime work and diagnostics. Clearing a notification list does not erase the server journal, messages or file versions. History coverage depends on the events recorded by each operation or extension.


## Check-in and check-out: hand files to the next person

Publishing is the point where work on your machine becomes available to someone else. It needs an object, process, version and description attached to it. The path goes through preparation, queue review and a saved snapshot:

1. Select an object and its process/context. Add local files or folders through **Drop Plate**, or prepare a scene through the selected DCC connection.
2. Match and group files or sequences. Review the prepared publication in **Commit Queue**: description, version options, resolved paths and file roles.
3. Submit the operation. Each queue item reports its progress and result; the queue is not one atomic transaction for every item.
4. Browse the resulting snapshots, compare image versions, and open or check out the files needed for the next task.

![Commit Queue — a real prepared Survey Drone publication with its next version and resolved path](../assets/product-tour/commit-queue.png)

Check-in supports grouped or separate publications and native ingest relationships. Destination collisions preserve existing files. Move removes its source only after confirmed success; uncertain completion must be reconciled rather than blindly repeated. Local preparation and transfer remain visible instead of being hidden behind the final snapshot record.

A snapshot ties a version to its object, process/context, author, description and files. New versions and revisions are different operations. `latest` and `current` naming rules are separate from versioned storage. File sequences retain their range information so checkout can resolve the published frames.

### Naming Editor: file names and paths by studio rules

A naming convention is useful when it is applied to each publication. Naming Editor defines rule conditions, contexts, filename and directory patterns, sandbox paths and repository aliases. Names can use object, snapshot and file values, with TSQL conditions or a trusted saved script where needed. Try the rule on an example before saving it.

![Naming editor — context matching, path patterns and native preview](../assets/product-tour/naming.png)

For example, a rule can derive a filename from the object's name, version and extension: `{sobject.name}_v{version}.{ext}`. The native naming engine resolves the actual paths at publication time. A preview is not a reservation: the final check-in still validates the version and collisions. Script-based naming executes trusted project code.

### Repository Sync: the versions you need on your machine

Synchronize the scope you need: selected objects, processes, versions or related children. Presets retain recurring choices; full/partial synchronization and update-only discovery support different working sets. The queue exposes discovery, transfer, cancellation, retry and conflict policy.

![Repository Sync — process and version scope for the current project](../assets/product-tour/repository-sync.png)

**Watch Folders** bind a project and a local path to matching/check-in rules and feed discovered work into Commit Queue. They do not turn saving a repository setting into an implicit move or deletion. These are Handler desktop capabilities; they are distinct from Stream's browser upload/download workflow.

## Tactic Frame: a shared UI language for Handler and Stream

Handler and Stream run in different environments, but many of their windows serve the same purpose. **Tactic Frame** provides a shared language for describing those interfaces: their elements, geometry, state and actions. Qt Quick and Vue render the description with their own controls. The structure can be developed in one place while Handler keeps its native Qt interface.

Frame uses standard JavaScript modules (`.mjs`) and ordinary data structures. A feature's `describe(model, width, height, language)` builds its visible structure from state. Controllers handle actions and domain operations; the description does not become a second server API.

```mermaid
flowchart TB
    Description["Tactic Frame\nShared descriptions, controls and state rules"] --> Qt["Qt Quick\nNative Handler UI"]
    Description --> Vue["Vue\nStream browser UI"]
    Qt --> Client["Desktop controllers\nLocal files and DCC routing"]
    Vue --> Web["Web controllers\nBrowser interaction"]
    Client --> Server["TACTIC Stream commands and permissions"]
    Web --> Server
```

A small description module saved beside this document illustrates the contract. The host supplies `model` and handles the `name` action; production modules also use the shared translation helpers.

```javascript
import { label, node, rect } from "../../thlib/ui/qml/tactic_frame/core/frame.mjs";

export function describe(model, width, height, language) {
    return { nodes: [
        label("title", rect(16, 12, width - 32, 28), "Review"),
        node("Field", "assetName", rect(16, 48, width - 32, 38), {
            label: "Asset", text: model.name, action: { type: "name" }
        })
    ] };
}
```

Shared building blocks cover fields, buttons, selectors, virtualized lists, tables, graphs, editors and window structure. Themes, translations, focus and input behavior belong to the contract as well as geometry. **Component showcase** makes those building blocks inspectable inside the application.

![Component showcase — shared controls rendered in the application](../assets/product-tour/frame-showcase.png)

Project XML views and visual layout documents configure content above this layer. They are not a replacement file syntax for Frame modules. Both products ship independently and carry their own shared-description copy; supported behavior must be checked in both renderers. [Frame contracts](../frame/index.md)

## Script Editor: turn a script into a team tool

A one-off command can grow into a department tool. In Script Editor, write it, run the whole script or a selection, inspect the result and errors, then save it in the project library. Tabs, drafts, undo, highlighting, completion, search/replace and outline navigation support the editing work. Folders and clear names help colleagues find the finished tools.

![Script Editor — saved project script and production record query](../assets/product-tour/script-editor.png)

| Runtime | Owner and context |
| --- | --- |
| **Local Python / QML tools** | Handler's native objects and UI; GUI operations obey the Qt thread boundary. |
| **Server Python** | The connected TACTIC server and its project/permission context. |
| **Selected DCC** | The explicitly selected registered session and its supported capabilities. |

The editor makes the execution target visible. Local/DCC output can return to the tab; server Python exposes its returned result while process stdout stays in the server log. A script's language alone does not identify the machine or objects it will run against.

**Script shelves** put saved actions beside the work: shared studio tools, personal tools and tools attached to a search tab. **Before/After hooks** bind automation to selected events with process, context and Search Type filters. A Before failure can block its operation; an After failure cannot undo an operation that has already completed. Code execution is a trusted capability, separate from merely viewing a script.

[Script Editor Help](../../thlib/ui/help_articles/script_editor.en.md) · [Script Shelf Help](../../thlib/ui/help_articles/script_shelf.en.md)

## Administration: define your project’s objects and relationships

Projects differ in what they need to track, how those things relate and which information people need. Administration describes that model through Search Types and a schema, then defines its views and actions. Asset and Shot are possible object types; a project can use its own. The schema graph helps you see their relationships together.

![Project schema — entities and relationships in Orbit Studio](../assets/product-tour/schema.png)

| Section | What you configure |
| --- | --- |
| **Search Types** | Entity definitions, fields and their naming rules. |
| **Project schema** | Relationships between entities and the project graph. |
| **Workflow** | Pipelines, process properties, dependencies and automation. |
| **Columns Editor** | Table views, columns and native field widgets. |
| **Raw database** | Direct authorized table inspection/editing and CSV work, with protected-table restrictions. |
| **Page layouts** | Whole dashboard pages, their blocks, data sources and navigation. |
| **Item layouts** | Reusable cards, rows and object presentations. |
| **Sidebar Editor** | Navigation groups, entries, views and workspace entry points. |
| **Plugins** | Packages, versions and project activation. |
| **Component showcase** | The control vocabulary used by the interfaces. |
| **Users** | Accounts and their project access. |
| **Groups** | Membership and shared access configuration. |
| **Access rules** | Inherited and explicit allow/deny rules; effective access checks for a user. |

![Access rules — group permissions and explicit allow/deny configuration](../assets/product-tour/access-rules.png)

Authoring sections keep their own drafts. Save/discard controls and revision checks make changes explicit; permissions remain enforced by server operations. A visual editor does not grant its user unrestricted database access. [Administration Help](../../thlib/ui/help_articles/administration.en.md)


## Bring people into the project and set their access

One person may work on several projects and appear in tasks, conversations, publications and activity records. A shared server account carries that identity, profile, contact information, settings and group memberships. Moving between projects does not lose the connection to who did the work.

![Users — directory, profile, account and group editing](../assets/product-tour/users.png)

### Create an account, retire it or bring someone back

Create an account, set its initial password and profile, and assign the required groups. Edit existing profile/account fields without reading back a password. Retire an account when access should stop and reactivate it when appropriate; the existing production history retains its author identity. A retired account and a deleted project object are different operations.

### Groups and rules: what a person can actually access

Groups manage membership and descriptions. Access rules manage the policy: access level, project scope, supported object/process/status/action rules, inheritance and explicit allow/deny. Sidebar visibility is a separate part of the interface policy; hiding a link is not the same as denying access to its records.

![Groups — membership and server group configuration](../assets/product-tour/groups.png)

A person may belong to several groups, and rules can be inherited or overridden. After configuring access, check the result for that particular user. A group matrix shows one part of the policy; effective-access checks help establish what the combined rules allow.

A practical onboarding sequence is **account → groups → project/data permissions → sidebar visibility → check the resulting user access**. Administration's selected project scopes project definitions; it does not turn server-wide users into project-local accounts. Drafts, confirmation and native server checks remain in force throughout.

## Configuration: server, repositories and personal settings

Server addresses, repository paths and personal theme choices change for different reasons than the project schema. They live in Configuration. Each page keeps a draft: Apply affects the current page, Save handles pending changes, and leaving unsaved settings is guarded. Appearance can be previewed before you keep or revert it.

![Configuration — appearance, theme and workspace preferences](../assets/product-tour/configuration.png)

| Area | Purpose |
| --- | --- |
| **AI providers** | Provider profiles, model discovery and executor selection for the assistant. |
| **Server** | Connection and supported server options, live service information and explicit lifecycle actions. |
| **Database resources** | Configure/test resources and bind existing schemas; this does not migrate data. |
| **Repositories** | Repository names, colors, mappings and supported server storage settings. Saving a path does not move files. |
| **Projects** | Project creation, templates and project-level setup. |
| **Check-in Options** | Defaults for file preparation, naming and publishing behavior. |
| **Global** | General interaction and update preferences applicable to the current client. |
| **Appearance** | Light/dark themes, palettes, icon choices and English/Russian interface language. |
| **Cache** | Cache policy, visibility and maintenance. |
| **Tasks** | Task defaults and effort/time preferences. |
| **DCC plugins** | Install/configure supported application integration. |
| **Client plugins** | Desktop extension discovery and configuration. |
| **Application-specific pages** | Settings supplied by the active integration, such as Maya scene behavior. |

Supported server XML settings expose service, network, security, directory and scheduling controls with validation and restart requirements. Changing configuration and restarting a service are separate actions. Repository and database migration require their own procedure. [Configuration Help](../../thlib/ui/help_articles/configuration.en.md)

## Let the assistant check an asset’s readiness

Ask what is ready for review, which version is published or what is missing from a handoff. The built-in **External agent** window captures the project, page, Search Type and selected objects. Its executor reads or changes data through scoped native tools.

![Built-in assistant — a real handoff generated from Survey Drone tasks, notes and file versions](../assets/product-tour/assistant.png)

In this demonstration it found a useful discrepancy: modeling was marked Complete, but no model publication existed. It distinguished review comments from proof of approval. The full presentation covers conversations, attachments, provider choices, project configuration, task changes, script trials and the limits of undo.

**[Explore the built-in assistant →](assistant.en.md)**

## Dashboards for supervisors and reviewers

A production overview should help you decide where to look next. A custom page can place metrics, reports and charts beside Item View, forms and actions. A supervisor gets a route from the bigger picture to an asset; a reviewer gets a tree with the selected object’s details nearby. The blocks use project data and the current access rules.

![Production overview — live task metrics, status distribution, workload and Item View](../assets/product-tour/dashboard-overview.png)

**[Explore custom dashboards and their visual editor →](dashboards.en.md)**

## Install, connect and add your own tools

### Connect Handler to the selected Maya session

The shipped Maya connector registers with **Handler Server**, the local bridge. Select the intended session before sending a native open, import, reference or scene-save action. Maya prepares the scene; Handler performs TACTIC check-in and file transfer. Other applications require a connector with explicitly registered native capabilities.

```mermaid
flowchart LR
    Maya["Selected Maya session"] <-->|Local bridge| Handler["TACTIC Handler"]
    Handler <-->|TACTIC API| Server["TACTIC / TACTIC Stream"]
    Handler <-->|Local mappings| Files["Repository files"]
    Server <-->|Snapshots and naming| Files
```

[Maya installation](../../installer/README.md) · [DCC API](../dcc_api.md) · [Thin-client protocol](../thin_client_protocol.md)

### Install Handler from source on Windows

Use a modern source checkout with Python 3.14 and a running TACTIC server.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

Open **Configuration → Server**, test the server preset and generate a ticket. Select a project and configure repository mappings before file operations. [First connection](../handbook.en.md#first-connection) · [Getting started](../../thlib/ui/help_articles/getting_started.en.md)

### Use the Handler API in your own tools

The public `tactic_handler_api` exposes client objects, file operations and supported UI actions. Its standalone, Script Editor and DCC entry points preserve their execution context.

```python
from tactic_handler_api import local

with local() as handler:
    assets = handler.project("orbit").stype("orbit/asset")
    result = assets.query(limit=12, order_by=["name asc"])
    for asset in result.items:
        print(asset.get_code(), asset.get_value("name"))
```

Replace the demo project and Search Type with your own. [API and examples](../handler_api.md) · [Architecture](../application_architecture.md) · [Handbook](../handbook.en.md)

## Compatibility, limitations and licenses

The presentation shows Handler connected to Stream. Stream-specific project authoring, dashboards and the assistant require that server; their presence here does not imply the same service exists in every original TACTIC deployment. Consult the [compatibility map](../tactic_compatibility/README.md) for an existing installation.

The Perforce-like File Workspace remains a prototype. The implemented check-in queue and Repository Sync do not establish full Perforce behavior. Maya is the connector shipped here; other DCC applications are extension work unless their connector is present and verified. [Documentation index](../index.md)

The screenshots illustrate configured workflows on a small demo project. They are not a performance benchmark or a claim of release acceptance. Studio-specific scripts, schemas, integrations and permissions need validation against the deployed version.

TACTIC Handler is distributed under the [Eclipse Public License 1.0](../../LICENSE). Its server integration builds on [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC).

[Maya plugin and shelves](maya.en.md)
