# Контракт Check-in/Check-out

## Область аудита

Legacy-подсистема сосредоточена в `Ui_checkInOutTabWidget`, `Ui_checkInOutWidget`,
`Ui_checkInOutOptionsWidget`, `Ui_fastControlsWidget`, `Ui_commitQueueWidget` и
`commitWidget`. Используются формы:

- `ui_checkin_out_options_dialog.ui` — контейнер параметров текущей вкладки;
- `ui_fast_controls.ui` — context, process, mode и explicit filename;
- `ui_commit_queue.ui` — очередь, редактор операции и общий progress;
- `ui_drop_plate.ui` и `ui_drop_plate_config.ui` — выбор файлов и настройки Drop Plate.

Основная legacy-форма рабочего пространства создаётся программно. Текущая
QML-поверхность находится в `DockHost.qml` (Drop Plate, Check-in Options, Fast
Controls, Commit Queue), `SnapshotBrowser.qml`, `RepositorySyncView.qml` и
контекстных действиях `ApplicationController`.

Статусы в таблице означают фактическую работоспособность, а не наличие визуального
компонента.

## Сценарии

| Сценарий | Legacy-контракт и Python API | Текущий QML | Статус / недостающее |
|---|---|---|---|
| Оболочка | `Ui_checkInOutTabWidget` создаёт проектную оболочку; `Ui_checkInOutWidget` объединяет search, docks и общие инстансы через `env_inst` | Главное workspace и dock host существуют, выбранные панели сохраняются общей моделью доков | **Частично**: QML-оболочка не связана с legacy check-in runtime и проектной commit queue |
| Вкладки | Левая панель stype, пользовательские sidebar views, создание/закрытие/восстановление вкладок; состояние в существующем config/QSettings API | Поисковые вкладки и выбор stype реализованы собственной QML-facing моделью | **Частично**: нет полного соответствия sidebar views и привязки каждой вкладки к отдельному check-in context |
| Выбранный объект | Search item передаёт `SObject`, snapshot и item widget в операции; после commit вызывается `refresh_results()` нужной вкладки | Controller хранит выбранный node и его Python source; карточки, детали и snapshots обновляются | **Частично**: выбор есть, но QML commit queue не получает безопасный идентификатор и не обновляет модель после commit |
| Context | Берётся из выбранного элемента (`get_context_options()`), разрешает ручной override/freeze в fast controls | `fastControlModel` визуально показывает значения и choices | **Отсутствует функционально**: ComboBox не записывает изменения в Python и не формирует операцию |
| Process | Список строится из `get_full_process_list()`; есть publish/icon/attachment и фильтр встроенных процессов | Process присутствует в node/drop records | **Частично**: выбранный process виден, но fast controls и queue не синхронизированы |
| Naming | `tc.get_dirs_with_naming()`, `tc.get_virtual_snapshot()`, server naming, explicit filename, keep filename, context-as-filename, versionless | В Drop Plate/queue показываются имя и repository | **Отсутствует**: naming preview, server-derived target paths и редактирование имени в QML не подключены; старый Naming Editor также отключён в legacy-классе |
| File selection | `Ui_dropPlateWidget` собирает `File` objects, группы, последовательности, каталоги и metadata | Drag-and-drop вызывает `queue_dropped_files()` и создаёт простые записи path/size/process | **Частично**: нет legacy file grouping, sequence/directory semantics, matching templates и выбора файлов через рабочую кнопку |
| Check-in options | `Ui_checkInOutOptionsWidget` переиспользует `Ui_checkinOptionsPageWidget`, config defaults и per-tab values | `optionModel` и Check-in Options dock отображаются | **Отсутствует функционально**: toggle меняет только QML-модель; значения не загружаются/сохраняются через legacy config и не влияют на commit |
| Подготовка операции | `save_file()` объединяет selection, context, description, revision, repo, mode, filenames и Drop Plate; `tc.checkin_file()` формирует queue item | Save/Save Revision/Paste лишь открывают docks; preview открывает Drop Plate | **Отсутствует**: нет validation, virtual snapshot, revision confirmation и реального добавления в commit queue |
| Commit queue | `Ui_commitQueueWidget` содержит очередь `commitWidget`, редактирование description/preview/repo/options, commit current/all, удаление и обновление результатов | `commitModel` и визуальный dock существуют | **Отсутствует функционально**: Commit All, Commit Selected, Edit Previews и context menu вызывают только уведомления; `commitModel` не содержит реальных операций |
| Check-in | `tc.checkin_file()` → virtual snapshot → `tc.inplace_checkin()`/upload path; поддержаны standalone и Maya | Реального общего QML check-in API нет; preview из schema editor может отдельно делегироваться legacy adapter | **Отсутствует** для workspace: нельзя считать изолированный preview check-in полноценным сценарием |
| Checkout | Метод определяется `cfg_controls.get_checkin()['checkoutMethodComboBox']`: local либо HTTP download через repository queue | Snapshot/file action использует текущий checkout method и repository sync controller | **Частично/готово для файлов**: загрузка и открытие snapshots работают; отдельной операции checkout с legacy-семантикой рабочего файла нет |
| Open | Legacy выбирает main/maya/обычный файл, открывает локальный либо после download; standalone вызывает `File.open_file()` | Snapshot Browser вызывает реальное open/local-or-sync действие | **Готово для поддержанных snapshot files**; выбор при нескольких неоднозначных файлах требует ручной проверки |
| Import | Только Maya: local `maya_functions.import_scene()`, HTTP — после repository download | Окно Maya Import присутствует как визуальная surface | **Отсутствует функционально**: execute не связан с Maya API |
| Reference | Только Maya: local `maya_functions.reference_scene()`, HTTP — после download | Окно Maya Reference присутствует как визуальная surface | **Отсутствует функционально**: execute не связан с Maya API |
| Progress | Commit workers передают progress в `commitWidget` и общий status bar; repository sync имеет discovery/download phases | Repository Sync показывает queued/downloading/completed/failed/cancelled, bytes/speed; QML commit queue показывает только текстовое поле status | **Готово для download, отсутствует для check-in** |
| Cancel | Legacy `stop_progress()` вызывает `interrupt_commit()`, который отключает worker signals | Repository sync имеет реальный cancel flag и отмену строк | **Частично**: download отменяется; legacy check-in «cancel» не прерывает серверную операцию и не гарантирует rollback, QML commit cancel отсутствует |
| Errors | Entry points используют `gf.catch_error`; workers подключают `error` к `gf.error_handle`; server/file exceptions сохраняются legacy logging | Repository sync публикует failed state, error и stacktrace; общая QML error surface получает server/API ошибки | **Частично**: download ошибки обработаны; у визуальной QML commit queue нет error/retry state |

## Где находится бизнес-логика

- Оркестрация операции находится в `Ui_checkInOutWidget.save_file()`,
  `checkin_file_objects()` и `checkin_from_maya()`. Это legacy UI orchestration,
  поэтому QML нужен тонкий нейтральный controller, а не вызов QWidget из QML.
- Серверная и файловая логика остаётся в `tactic_classes`: `checkin_file()`,
  `get_virtual_snapshot()`, `inplace_checkin()`, `SObject`/`Snapshot`/`File`,
  repository/naming helpers.
- Очередь и последовательность стадий находятся в `commitWidget` и
  `Ui_commitQueueWidget`; конфигурация берётся из `cfg_controls`, окружение и pools
  — из `env_inst`.
- Локальное открытие реализует `File.open_file()`. HTTP checkout/open/import/reference
  использует repository sync, а DCC-действие выполняется только после сигнала
  успешной загрузки.

QML-контроллер не должен повторять insert snapshot, preallocation, naming,
копирование/перемещение файлов или upload. Безопасная граница — immutable описание
операции (search key, context/process, paths, options) и QML-facing модель её
состояния.

## Асинхронность и потоки

- Virtual snapshot, inplace/upload check-in и server snapshot creation запускаются
  через `env_inst.commit_pool`; результаты, progress и ошибки приходят сигналами.
- Repository discovery запускается через существующий `env_inst.server_pool`.
- QML repository downloads выполняются в `QThreadPool`; изменения модели
  возвращаются queued signals в поток controller.
- Локальное добавление пути в QML Drop Plate синхронно вызывает только `stat()`.
  Полноценный scan последовательностей/каталогов и вычисление итогового размера
  нельзя переносить в GUI-поток.
- Legacy `interrupt_commit()` отключает сигналы worker, но не является
  подтверждённой отменой серверного запроса. Его нельзя отображать в QML как
  гарантированное «операция отменена».

## Объекты, запрещённые на QML-границе

Нельзя передавать в QML делегаты raw `SObject`, `Snapshot`, `File`, stype/schema,
legacy search/item widgets, `commitWidget`, worker, project/repository objects,
virtual snapshot dictionaries с Python-объектами и Maya scene objects. В
`commitWidget.args_dict` сейчас также хранятся callbacks, screenshots,
`item_widget`, `files_objects` и result snapshot — это внутреннее Python-состояние.

Для QML достаточны search key/token, project/stype, context/process, нормализованные
пути, примитивные options, display name, repository code, progress/status/error и
безопасные списки файлов. Разрешение токенов в legacy-объекты должно выполняться
внутри Python controller на момент операции.

## Подключённые и неподключённые QML-действия

Реально подключены: выбор объекта; drag-and-drop путей в простую Drop Plate модель;
просмотр snapshots/files; local open; repository discovery/download; retry/cancel
download; открытие папки и копирование путей, где доступно.

Только визуальны или заменены `notice()`:

- Add files, Matching Templates, Open check-in queue;
- Drop Plate context actions;
- все изменения Fast Controls;
- все Check-in Options;
- Commit All, Commit Selected, Edit Previews и commit context actions;
- Save, Save Revision и Paste после открытия панелей;
- Maya Open/Import/Reference options как исполняемые DCC-команды.

`paste_from_clipboard()` содержит пустую реализацию и в legacy-классе, поэтому это
не QML-регрессия, а существующий неподтверждённый сценарий.

## DCC-зависимости

- `checkin_from_maya()`, fast save Maya scene, save/export selected, playblast и
  selected-objects check-in зависят от `maya_functions`.
- Import и Reference доступны только в Maya. Open использует Maya scene API в Maya
  и `File.open_file()` в standalone.
- Maya option dialogs и текущая scene format/selection не должны становиться частью
  общего QML check-in controller; их следует подключать отдельным DCC adapter,
  доступным только при соответствующем `env_mode`.
- Preallocation, naming, repository resolution, commit queue и standalone check-in
  DCC-независимы и могут быть вынесены в общий QObject API без изменения Maya
  интеграции.

## Рекомендуемое разбиение переноса

Preview из редактора объекта не отправляется в очередь до появления общего
QML-facing API, который учитывает naming, repository selection, file grouping,
virtual snapshot и полный жизненный цикл операции.

1. Ввести QML-safe описание подготовленной операции и controller, переиспользующий
   `tc.checkin_file()`/существующую commit queue, без передачи QWidget и TACTIC
   objects.
2. Связать выбранный объект, context/process, реальные check-in options и Drop
   Plate file grouping; добавить validation и virtual naming preview.
3. Подключить commit queue model: prepare, commit current/all, progress, error,
   retry и честную семантику cancel.
4. Завершить standalone check-in/checkout/open и обновление workspace models после
   результата.
5. Отдельно подключить Maya open/import/reference/save/export через DCC adapter;
   не включать эти команды в standalone.

## Ручные проверки

- file, multi-file, sequence, directory и workarea modes с каждым разрешённым
  repository и naming rule;
- versionless/revision/keep filename/explicit filename и group check-in;
- local и HTTP checkout, существующий локальный файл, несколько файлов snapshot;
- закрытие приложения во время virtual snapshot, upload и download;
- отсутствие обновления уничтоженной вкладки после позднего результата;
- Maya scene, selected objects, playblast, open/import/reference и восстановление
  UI после screenshot maker.

## Этап 15: оболочка и выбранный объект

- **Реализовано:** отдельный dock `Check-in / Check-out`, рабочие вкладки объектов,
  выбранный объект Workspace, переключение check-in/check-out, process, context
  и сохранение вкладок/режима через существующий `QSettings`.
- **Реализовано:** QML получает только строки, списки и словари; исходный sObject
  остаётся внутри `CheckinOutController`. Список process берётся через нативный
  `SObject.get_all_processes()`.
- **Отличается:** восстановленная вкладка без объекта в текущей модели доступна
  для навигации, но её операции недоступны до повторного выбора объекта.
- **Намеренно недоступно:** подготовка файлов, check-in, checkout, open, import,
  reference и commit queue. Кнопка выполнения явно disabled.
- **Требует ручной проверки:** context у объектов с пользовательскими process,
  восстановление вкладок после смены проекта и отображение QWidget-интерфейса.

## Этап 16: подготовка check-in

- **Реализовано:** выбор и drag-and-drop отдельных файлов, QML-safe файловая
  модель, удаление, размер, расширение и тип через существующий `file_format`.
- **Реализовано:** process/context, description, version/revision, keep filename,
  update versionless и generate previews. Значения по умолчанию берутся из
  `cfg_controls.get_checkin()`, repository — из `env_tactic.get_current_repo()`.
- **Реализовано:** naming preview вызывается асинхронно через
  `tc.get_virtual_snapshot()` и `env_inst.server_pool`; поздний ответ предыдущего
  запроса игнорируется.
- **Реализовано:** валидированный QML-safe payload доступен без выполнения
  операции. При `TACTIC_QML_DEBUG=1` его JSON показывается без ticket, паролей и
  repository paths.
- **Отличается:** каталоги и автоматическая группировка sequences пока явно
  отклоняются, чтобы не запускать обход файловой системы в GUI-потоке.
- **Намеренно недоступно:** создание snapshot, commit queue и перенос файлов.
- **Требует ручной проверки:** серверные naming rules, каждый активный repository,
  revision/version и preview-файлы на рабочем сервере.

## Этап 17: выполнение check-in

- **Реализовано:** последовательные стадии queued/preparing, copying, upload или
  snapshot и completed/failed. Повторный запуск блокируется до завершения.
- **Реализовано:** выполнение использует `env_inst.commit_pool`,
  `tc.get_virtual_snapshot()`, `tc.inplace_checkin()` и `tc.checkin_snapshot()`;
  файловый и серверный движок не дублируются.
- **Реализовано:** QML показывает стадию, текущий файл, progress и ошибку.
  Worker-сигналы возвращают изменения в QObject через queued Qt connections.
- **Реализовано:** traceback сохраняется в Debug Log. После ошибки payload и
  файлы остаются доступными для полного повторного запуска.
- **Реализовано:** после успеха вызывается точечное обновление Snapshot Browser
  выбранного объекта.
- **Отличается:** QWidget commit queue не создаётся; одна подготовленная операция
  живёт в контроллере со стадией `queued`, затем выполняется тем же core API.
- **Ограничение:** запущенные copy/upload/server calls не имеют подтверждённой
  безопасной отмены. Закрытие использует общий shutdown worker pools и ожидает
  завершения активной операции.
- **Намеренно отсутствует:** checkout, import и reference.
- **Требует ручной проверки:** inplace/preallocate/upload, большой файл,
  разрыв сети, retry и закрытие приложения во время каждой стадии.

## Этап 18: Check-out, Open, Import и Reference

- **Реализовано:** выбор snapshot/version и конкретного файла использует модели
  Snapshot Browser; `Snapshot` и `File` не передаются в QML.
- **Реализовано:** Get/download выполняется существующим Repository Sync с
  progress, retry, `.part`, проверкой размера, cancel и обновлением локального
  состояния.
- **Реализовано:** несовпадающий локальный файл требует явного Overwrite, Skip
  или Cancel. Совпадающий файл не загружается повторно.
- **Реализовано:** Open после download вызывает `File.open_file()` в standalone.
  В Maya Open/Import/Reference вызывают существующие функции интеграции.
- **Реализовано:** Import/Reference вне Maya недоступны, а UI показывает причину;
  Maya-модули импортируются только условно внутри DCC boundary.
- **Реализовано:** download и DCC ошибки сохраняются в Debug Log; после
  завершения обновляются Snapshot Browser и локальный статус файла.
- **Намеренно отсутствует:** реализация Import/Reference для DCC, у которых нет
  соответствующего API в проекте.
- **Требует ручной проверки:** HTTP Get, overwrite/skip/cancel, несколько файлов
  snapshot, Maya open/import/reference и закрытие во время download.
