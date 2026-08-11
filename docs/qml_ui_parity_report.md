# Функциональный паритет пользовательских UI

Аудит выполнен по контрактам `docs/qml_ui_contracts`, очереди миграции и
фактической цепочке QML action → Python Slot/model → API/настройки. Наличие
QML-файла без рабочего обработчика не считалось реализацией. `thlib/side`
полностью исключён из анализа.

## Итог

Основной рабочий контур существует: запуск, проекты, поиск, представления
результатов, детали, подготовка и очередь операций, редакторы и сервисные
инструменты связаны с Python API. Статус «готово» присвоен только сценариям,
которые не требуют неподтверждённой серверной мутации или DCC. Для операций с
TACTIC, файловыми хранилищами и внешними процессами сохранён статус ручной
проверки даже при полном наборе обработчиков.

Сокращения в таблице: `static` — проверены обработчики, модели, сигналы и
сохранение; `smoke` — безопасный запуск/импорт без изменения серверных данных.

## Основной интерфейс

| Legacy UI / класс | QML-компонент | Статус | Обязательные сценарии | Автоматическая проверка | Ручная проверка | Известные отличия |
|---|---|---|---|---|---|---|
| Главное окно: `Ui_Main`, `Ui_mainTabs`, `Ui_topBarWidget`, `Ui_projectsChooserWidget` | `Main.qml`, `DockHost.qml`, `NavigationDrawer.qml`, `ProjectChooser.qml` | требует ручной проверки | bootstrap, проекты, разделы, вкладки, state, shutdown | QML smoke; static state handlers | несколько проектов, повторный запуск, активные workers | QML использует dock/workspace-компоновку |
| Авторизация и соединение: `Ui_Main`, `Ui_serverPageWidget` | login/error dialogs в `Main.qml`; connection controller | требует ручной проверки | session, login, неверный пароль, offline, re-login | static signals/retry/dismiss | реальный сервер, смена сервера, истёкший ticket | traceback вынесен в Debug Log |
| Поиск: `Ui_searchWidget`, `Ui_advancedSearchWidget`, `Ui_searchOptionsWidget`, `Ui_processFilterDialog` | `TacticSearchField.qml`, `AdvancedSearchView.qml`, `FilterEditorView.qml` | частично | query, suggestions, filters/groups, tabs, stale-result guard, restore | static Slots/models; filter contract probes | TEL/process filters и сохранённые серверные фильтры | quick chips ещё содержат локальную view-фильтрацию |
| Результаты: `Ui_searchResultsWidget`, `Ui_itemWidget`, `Ui_processItemWidget`, `Ui_snapshotItemWidget`, `Ui_childrenItemWidget`, `Ui_groupItemWidget` | `WorkspaceResultItem.qml`, `WorkspaceCard.qml` | требует ручной проверки | tree/list/cards, expand, select, actions, DnD, lazy preview | QML smoke; role/action inspection | большие выборки, DnD, отсутствующие preview | внешний вид и навигация адаптированы под QML |
| Snapshot/details: `Ui_snapshotBrowserWidget`, `Ui_sobjectInfoWidget` | `SnapshotBrowser.qml`, detail panels в `DockHost.qml` | требует ручной проверки | versions, files, preview, local state, open/download | static model/actions | реальные snapshots/files/repositories | данные представлены QML-safe ролями |
| Database/object info: `Ui_editDBTableWidget`, `Ui_descriptionWidget` | `DatabaseEditorView.qml`, `SObjectFieldEditor.qml` | требует ручной проверки | load, edit, validation, save, refresh | static field model/submit path | права и server validation | schema-driven форма вместо набора QWidget |
| Repository Sync: `Ui_repoSyncDialog`, `Ui_repoSyncQueueWidget` | `RepositorySyncView.qml` | требует ручной проверки | discovery, queue, progress, cancel/retry, shutdown | static controller/model | активная загрузка и закрытие | файловая логика остаётся в Python |
| Debug/error UI: debug widgets и error dialogs | `DebugLogView.qml`, `ErrorDialog.qml` | готово | log sources, sessions, retry/dismiss, stacktrace | QML smoke; static categories/history | визуальная проверка длинных traceback | ошибки файлов выделены отдельной категорией |

## Рабочие подсистемы и редакторы

| Legacy UI / класс | QML-компонент | Статус | Обязательные сценарии | Автоматическая проверка | Ручная проверка | Известные отличия |
|---|---|---|---|---|---|---|
| Configuration: `Ui_configuration_dialogWidget` и page widgets | `ConfigurationView.qml`, `ConfigurationPage.qml`, `ConfigurationSection.qml` | частично | load, Apply/OK/Cancel/Reset, validation, window state | static controller/settings | server/global/project/Maya combinations | Check-in Options и Check-in/Out не полностью равны старым страницам |
| Server Presets: `Ui_serverPresetsEditorWidget` | `ServerPresetsView.qml` | готово | add/edit/delete/default/save, no plaintext secret | static settings/API | визуальная проверка | сохраняются имена/адреса через существующий API |
| Filter Editor: `Ui_filterEditorDialog`, `Ui_filterWidget`, `Ui_processFilterDialog` | `FilterEditorView.qml` | частично | conditions, AND/OR/groups, presets, options, apply | static model/handlers; contract cases | process expression на сервере | формат фильтра общий; не добавлены новые операторы |
| Add/Edit sObject: `Ui_addTacticSobjectWidget`, QTactic field widgets | `SObjectFieldEditor.qml` | требует ручной проверки | schema, defaults, types, validation, create/edit, refresh | static schema model/submit guard | реальные schema/rights/triggers | единый schema-driven editor |
| Link/Unlink: `Ui_linkSobjectsWidget` | `LinkSObjectsView.qml` | требует ручной проверки | search target, link, unlink, cancel, refresh | static async result normalization | реальные relations и permissions | сложные объекты не передаются в QML |
| Columns: `Ui_columnsEditorWidget` | `ColumnsEditorView.qml` | готово | order, visibility, width/label, save/cancel, refresh | static settings/model | визуальная проверка таблиц | настройки отображения, без schema mutation |
| TACTIC Column: `Ui_tacticColumnEditorWidget` | `ColumnsEditorView.qml`, `DatabaseEditorView.qml` | частично | existing value/display options, validation, confirmation | static edit handlers | физическое создание/изменение schema | опасная schema mutation оставлена старому UI |
| Dependency delete/duplicate: `Ui_dependencyExpandWidget`, `Ui_deleteSobjectWidget`, `Ui_duplicateSobjectWidget` | общие confirmation/action dialogs | частично | dependency preview, delete/duplicate options, result | static action routing | зависимости и права на реальном проекте | подробное дерево зависимостей не имеет полного паритета |
| Check-in/Out: `Ui_checkInOutWidget`, `Ui_checkInOutOptionsWidget`, `Ui_checkInOutTabWidget`, `Ui_fastControlsWidget` | `CheckinOutView.qml`, `FilePreparationEditor.qml` | требует ручной проверки | prepare, naming/options, check-in/out, open/import/reference, progress/cancel | static controller/queue callbacks | repository, upload, overwrite, shutdown | DCC actions доступны только через integration API |
| Commit Queue: `Ui_commitQueueWidget`, `Ui_commitItemWidget` | `CommitQueueView.qml` | требует ручной проверки | add/reorder/edit, one/selected/all, progress/retry/cancel/persist | static roles/actions/persistence | реальный commit и закрытие на стадиях | operation objects хранятся в Python |
| Drop Plate: `Ui_dropPlateWidget` | `DropPlateView.qml` | требует ручной проверки | files/folders, async scan, groups/sequences, queue | static handlers/model | большой каталог, DnD, repository mapping | commit выполняется только через очередь |
| Matching Templates: `Ui_matchingTemplateConfigWidget` | `MatchingTemplatesView.qml` | требует ручной проверки | CRUD, order/enable, test, mapping, save/rematch | static model/settings | конфликтующие patterns на реальных файлах | используется существующий формат |
| Repository Editor: `Ui_repositoryEditorWidget` | `RepositoryEditorView.qml` | требует ручной проверки | platform paths, availability, default, mapping, save/cancel | static API/settings | network shares и права | проверка пути нерекурсивна |
| Watch Folders: `Ui_projectWatchFoldersWidget` | `WatchFoldersView.qml` | требует ручной проверки | CRUD, enable, status/error, scan, watcher lifecycle, restore | static controller/settings | filesystem events и restart | auto-commit не добавлен |
| Tasks: `Ui_taskWidget`, `Ui_tasksDockWidget` | `TaskProcessPanel.qml`, `TaskEditor.qml`, `TasksWorkspaceView.qml` | требует ручной проверки | process cards, CRUD, assignee/status/context/dates/progress, user/project scopes, filters, calendar, history, multi-sObject edit | helper tests, syntax, QML window smoke | permissions, triggers, project task/login-group schemas | compact and advanced views share one controller and native task sObjects |
| Notes: `Ui_notesWidget` | `CommunicationView.qml` | частично | create/reply, history, attachments, unread, retry | static model/actions | server history и permissions | выбранный объект объединяет notes/messages в timeline |
| Messages: `Ui_messageWidget`, message widgets | `CommunicationView.qml` | частично | create/reply, history, unread, attachments | static model/signals | адресные сообщения и live updates | отдельного полного addressable-messages API не найдено |
| Rich Edit: `Ui_richeditWidget` | composer в `CommunicationView.qml` | частично | rich/plain fallback, links, attachments, validation | static submit/render | совместимость сложной разметки | отдельный универсальный rich editor не переносился |
| Attachments: attachment widgets | `CommunicationView.qml`, `FilePreparationEditor.qml` | требует ручной проверки | stage, upload/download, preview, progress/cancel/error | static Python file model | реальные загрузки и локальные файлы | файлы не хранятся как сложные QML-объекты |
| Notifications: notify/message widgets | `NotificationStack.qml` | готово | info/warning/error/progress/completion, dedupe, timers | static signals/dedupe/lifecycle | повторное открытие окна | подтверждения остаются модальными |
| Preview Editor: preview/attachment widgets | `ItemPreview.qml`, file preparation/detail actions | требует ручной проверки | select/upload/remove where supported, progress, refresh | static file/check-in path | upload/remove на сервере | отдельной серверной операции удаления в контракте нет |
| Naming Editor: `Ui_namingEditorWidget` | naming preview в `FilePreparationEditor.qml` | намеренно оставлено legacy-only | preview rules, edit/save rules | static preview path | решение о полноценном rules editor | исходный editor фактически являлся диагностическим stub |

## Вспомогательные и изолированные инструменты

| Legacy UI / класс | QML-компонент | Статус | Обязательные сценарии | Автоматическая проверка | Ручная проверка | Известные отличия |
|---|---|---|---|---|---|---|
| Assets Browser: `Ui_assetsBrowserWidget`, `Ui_sobjectWidget` | `AssetsBrowserView.qml`, общие workspace cards/models | готово | search, tabs, selection, open, shared state | static shared controller/model | визуальная проверка большой выдачи | отдельный Search Controller не создан |
| Update/Create Update: `Ui_updateDialog`, `Ui_createUpdateDialog` | `UpdateView.qml` | требует ручной проверки | check/create/apply, progress, cancel/error, restart | static async handlers | архив, rollback, restart | механизм обновления не изменён |
| Maya Import/Open/Reference: option dialogs | `MayaOptionsView.qml` | требует DCC | mode options, persistence, confirm, integration call | standalone disabled-state smoke | Maya import/open/reference | общий QML для опций; Maya не импортируется presentation layer |
| Screenshot Maker: `Ui_screenShotMakerDialog` | `ScreenshotMakerView.qml` | требует ручной проверки | capture/select/save/cancel | static capture API | multi-monitor, DPI, DCC host | используется существующий capture API |
| Script Editor: `Ui_ScriptEditForm` | `ScriptEditorView.qml` | требует ручной проверки | load/save, explicit run confirmation, output/error/cancel | static handlers/no-auto-run | server execution и permissions | traceback направляется в Debug Log |
| TACTIC API Client: `Ui_TacticApiClient` | — | намеренно оставлено legacy-only | original integration listener | — | legacy launcher only | modern supervisor removed; replaced in the menu by Handler Server |
| TACTIC Server: `Ui_TacticServer` | — | намеренно оставлено legacy-only | original runtime/batch launcher | — | legacy launcher only | modern supervisor removed; replaced in the menu by Handler Server |

## Оставшиеся обязательные проверки

1. Серверные mutation-сценарии: Add/Edit/Link, Tasks/Notes, check-in/out,
   commit queue, update и repository sync.
2. Сетевые каталоги, watcher lifecycle, закрытие приложения во время активных
   операций и восстановление очередей/окон после перезапуска.
3. Maya Import/Open/Reference в реальной DCC-среде.
4. Полный process-filter/TEL, адресные Messages, расширенный Rich Edit и
   dependency preview.
5. Решение владельца проекта о переносе редактора naming rules и опасных
   операций физического изменения TACTIC schema.

## Выполненные автоматические проверки

- `python -m compileall -q modern_ui main_qml.py` — успешно.
- `smoke_legacy_compat.py` — успешно.
- Offscreen-запуск `main_qml.py` с автоматическим завершением — успешно,
  QML-компоненты загрузились, процесс завершился штатно.
- Qt сообщил только об отсутствии каталога bundled fonts в установленном
  PySide6; это ограничение окружения, а не ошибка QML-компонента.

## Уточнение действий — этап 41

- Контекстные команды Tasks `Add`, `Edit` и `Delete` подключены к
  `TasksController`; удаление использует существующее подтверждение, а не
  уведомление-заглушку.
- `Refresh` в Assets Browser теперь обновляет текущую вкладку через
  `refresh_current`, не создавая новый поисковый запрос.
- Статическая сверка вызовов всех специализированных QML-контроллеров не
  обнаружила отсутствующих методов/Slot.
- Offscreen bootstrap не выявил QML warnings. Сообщение Qt о каталоге шрифтов
  относится к установке PySide6 и не меняет статус интерфейсов.
- Configuration Check-in Options/Out, process/TEL filters, адресные Messages,
  schema mutation и DCC-сценарии остаются в прежних статусах: их исправление
  требует отдельных подсистем или реальной среды.

## Legacy-регрессия — этап 42

- Старый контракт `OperationWorker.error → worker.retry()` был нарушен после
  перехода pool на `QThreadPool`: `retry()` возвращал `True`, но повторный
  runnable отбрасывался, пока первый ещё числился активным.
- Повторный запуск теперь ставится в ожидание завершения текущего runnable и
  отправляется тем же pool. Публичные сигналы, методы, аргументы и лимит трёх
  попыток сохранены.
- `smoke_legacy_compat.py` проверяет выбор старого launcher, публичные импорты
  Main/Configuration/Search/Check-in/Queue/Add-Link/Tasks/Notes/Messages/
  Repository/Watch/Maya/API tools и реальный цикл failed → retry → result.
- Offscreen созданы и закрыты `Ui_Main`, `Ui_configuration_dialogWidget`,
  `Ui_commitQueueWidget` и `Ui_TacticApiClient`; сетевые операции не запускались.
- Импортная матрица, targeted `py_compile`, расширенный legacy smoke и QML
  bootstrap проходят. Полные server/DCC операции остаются ручными.
- В `ui_editdb_table_classes.py` остаётся старый Python 2 `print`; это
  существовавшая до миграции проблема, не подтверждённая как её регрессия,
  поэтому файл не изменялся.

## Финальная проверка перед merge — этап 45

- Targeted Python compile, legacy import/retry smoke, прямой `main_qml.py` и
  `launch.py --ui qml` прошли из `D:\code`, вне каталога проекта.
- Все зарегистрированные QML-окна открыты и закрыты дважды; binding/property/
  handler warnings отсутствуют, исходное QSettings-состояние восстановлено.
- Проверены resources и пути: QML загружается относительно `main_qml.py`,
  жёстких пользовательских/workspace путей в migration-коде не найдено.
- Проверены background lifecycle, запрет повторного запуска, ожидание pool при
  shutdown и legacy `worker.retry()`; автоматические проверки проходят.
- Из default server preset удалены внутренний адрес, пользователь и ticket.
  Архив `th_codex.zip`, содержавший старый ticket, удалён; session JSONL
  добавлен в `.gitignore` и шаблон ignore.
- Фиктивных данных, debug prints, test endpoints и известных секретов в
  migration-коде/настройках не найдено. `pass` остаются только внутри
  ограниченных обработчиков исключений, не как заглушки.
- Git metadata в предоставленной рабочей папке отсутствует, поэтому состояние
  индекса, tracked logs, полный diff и случайные переименования автоматически
  проверить нельзя.
- Ручной merge gate: login/смена сервера, проекты и поиск на живом TACTIC;
  check-in/out, commit, Drop Plate, watchers/repositories, mutations/tasks/
  communication/update; Maya/DCC и внешние API tools.
