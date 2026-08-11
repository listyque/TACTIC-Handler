# Temporary modern UI catalog

Open the catalog through `…` → **Tools and Test Windows**. This is a diagnostic
catalog, not the final information architecture. Every available entry uses the existing
`FloatingWindowModel` or `DockPanelModel`; opening it again raises the same instance.
The current registry has no multi-instance windows. Opening a view never confirms or
starts check-in, update, DCC, script, or service operations.

| Menu entry | QML component | Controller/model | Instance | Status |
|---|---|---|---|---|
| **Core** |||||
| Configuration | `ConfigurationView.qml` | `ConfigurationController` | singleton window | Available |
| Filter Editor | `FilterEditorView.qml` | `FilterEditorController` | singleton window | Available |
| Check-in / Check-out | `CheckinOutView.qml` | `CheckinOutController` | singleton dock | Available; operations are destructive |
| Commit Queue | `CommitQueueView.qml` | `CommitQueueController` | singleton dock | Available; commit is destructive |
| Drop Plate | `DropPlateView.qml` | `DropPlateController` | singleton dock | Available |
| Watch Folders | `WatchFoldersView.qml` | `WatchFoldersController` | singleton dock | Available; opening does not start the watcher |
| Repository Editor | `RepositoryEditorView.qml` | `RepositoryEditorController` | singleton window | Available |
| Repository Sync | `RepositorySyncView.qml` | `RepositorySyncController` | singleton window | Available; opening does not start sync |
| Database Editor | `DatabaseBatchEditorView.qml` | `ApplicationController` | singleton dock | Available; Save is destructive |
| SObject Info | `SObjectInfoView.qml` | workspace state | singleton window | Experimental |
| Add sObject | `SObjectFieldEditor.qml` | `SObjectEditorController` | singleton window | Available; Submit is destructive |
| Edit selected sObject | `SObjectFieldEditor.qml` | `SObjectEditorController` | singleton window | Requires a selection; Submit is destructive |
| Link sObjects | `LinkSObjectsView.qml` | `SObjectLinkController` | singleton window | Requires a relation selection |
| Tasks | `TaskEditor.qml` / Tasks dock | `TasksController` | singleton dock | Available; Save/Delete are destructive |
| Notes | `CommunicationView.qml` | `CommunicationController` | singleton dock | Available; Send/Delete are destructive |
| Messages | `MessagesView.qml` | `MessagesController` | singleton window | Experimental: existing TACTIC chat subscriptions |
| **User and Communication** |||||
| User Profile | `UserProfileView.qml` | `UserController` | singleton window | Available |
| Users | `UserProfileView.qml` | `UserController` | alias of singleton `user_profile` | Available |
| Notifications | `NotificationsView.qml` | `NotificationController` | singleton window plus global overlay | Current-client session history |
| Activity Feed | `ActivityFeedView.qml` | `ActivityFeedController` | singleton window | Experimental; server-dependent |
| Chat / Messages | `MessagesView.qml` | `MessagesController` | alias of singleton `messages` | Experimental |
| Attachments | `FilePreparationEditor.qml` | `CheckinOutController` | alias of singleton `attachments_editor` | Experimental |
| **Editors** |||||
| Columns Editor | `ColumnsEditorView.qml` | `ColumnsEditorController` | singleton window | Available |
| TACTIC Column Editor | — | — | — | Not implemented; disabled |
| Naming Editor | `FilePreparationEditor.qml` | `CheckinOutController` | singleton window | Experimental naming preview |
| Preview Editor | `FilePreparationEditor.qml` | `CheckinOutController` | singleton window | Experimental; check-in requires a click |
| Attachments Editor | `FilePreparationEditor.qml` | `CheckinOutController` | singleton window | Experimental; check-in requires a click |
| Matching Templates | `MatchingTemplatesView.qml` | `MatchingTemplatesController` | singleton window | Available |
| Script Editor | `ScriptEditorView.qml` | `ScriptEditorController` | singleton window | Available; Run requires confirmation |
| Server Presets | `ServerPresetsView.qml` | `ServerPresetsController` | singleton window | Experimental |
| **Integrations and Service Tools** |||||
| Assets Browser | `AssetsBrowserView.qml` | shared workspace models | singleton window | Experimental |
| Screenshot Maker | `ScreenshotMakerView.qml` | `ScreenshotController` | singleton window | Available; capture requires a click |
| Update | `UpdateView.qml` | `UpdateController` | singleton window | Experimental; update requires confirmation |
| Create Update | `UpdateView.qml` | `UpdateController` | singleton window | Experimental; creation requires a click |
| Maya Import Options | `MayaOptionsView.qml` | `MayaOptionsController` | singleton window | Available; disabled outside Maya |
| Maya Open Options | `MayaOptionsView.qml` | `MayaOptionsController` | singleton window | Available; disabled outside Maya |
| Maya Reference Options | `MayaOptionsView.qml` | `MayaOptionsController` | singleton window | Available; disabled outside Maya |
| TACTIC Handler Server | `HandlerServerView.qml` | `HandlerServerController` | singleton window | Available; current localhost command router |
| Thin Client Demo | `HandlerServerView.qml` | `HandlerServerController` | alias of singleton `handler_server` | Experimental; demo subprocess |
| Debug Log | `DebugLogView.qml` | `DebugLogController` | singleton window | Available |

Python routing errors are caught, reported with a short notification, and written to
Debug Log with a stack trace. QML runtime warnings are already captured by the shared
Qt message bridge.
