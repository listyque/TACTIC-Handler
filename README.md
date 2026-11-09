# TACTIC-Handler

**English** · [Русский](README.ru.md) · [Handbook](docs/handbook.en.md) · [Changelog](CHANGELOG.md)

**Native desktop client for TACTIC production workflows.** Browse assets and
shots in Item View, inspect their tasks and snapshots, and prepare file
publications from a Python and Qt Quick workspace.

Handler connects to a configured [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC)
or TACTIC Stream server.
The server owns project data, permissions, pipelines, and repository rules.
Handler owns the desktop workspace, local file operations, and Maya integration.

> **Development prototype.** The Perforce-like file workspace is an unfinished
> prototype within Handler.

![TACTIC-Handler Item View displaying cards for the Orbit Studio demo assets](docs/assets/github-item-view.png)

## Item View

Browse individual objects as cards, compact rows, or an expandable tree.
Follow relationships, tasks, notes, and snapshots from the same search
workspace. With a Stream server that provides layout authoring, use the native
Item Layouts editor to build a card or row from bound fields and actions.
[Item Layouts guide](thlib/ui/help_articles/item_layouts.en.md) · [Table view screenshot](docs/assets/github-workspace.png)

## What you can do

- **Organize work.** Save workspace layouts, keep multiple search tabs open,
  and work with tasks, notes, relationships, and project records.
- **Review and publish.** Browse snapshots, compare image versions, and prepare
  check-ins through Drop Plate and Commit Queue.
- **Work with local files.** Map and sync repositories. Changelists and shelves
  are part of the Perforce-like prototype.
- **Connect Maya.** Route supported scene operations to the selected Maya
  session through the local Handler Server bridge.

## Start on Windows

Use Python 3.14, a TACTIC account, and access to the target server. Run these
commands from a modern source checkout that contains `launch.py`.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

Open **Configuration → Server**, add a server preset, test the connection, and
generate a ticket. Select a project and configure the local repository mapping
before working with files. [First connection guide](docs/handbook.en.md#first-connection)

## Documentation

| I want to | Start here |
| --- | --- |
| Learn the desktop workflows | [Getting started](thlib/ui/help_articles/getting_started.en.md) · [Handbook](docs/handbook.en.md) |
| Connect Maya or build a connector | [Maya installer](installer/README.md) · [DCC API](docs/dcc_api.md) |
| Write client scripts and tools | [Handler API](docs/handler_api.md) |
| Develop or verify a release | [Documentation index](docs/index.md) · [Release readiness](docs/release_readiness.md) |

Production use requires acceptance against the target server, repositories,
Windows configuration, and DCC host.
The [release checklist](docs/release_acceptance_checklist.md) lists those checks.

[Eclipse Public License 1.0](LICENSE). Bundled components retain their notices.
