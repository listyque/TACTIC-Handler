# Контракт Watch Folders и Repository Editor

## Граница и компоненты

`Ui_projectWatchFoldersWidget` использует форму
`thlib/ui/misc/ui_watch_folders.ui`: таблицу Status/SType/SObject/Repositories и
неактивный общий checkbox `Watch Folders Enabled`.
`Ui_repositoryEditorWidget` собирается программно в
`ui_watch_folder_classes.py`; отдельной `.ui`-формы у него нет.

QML Watch Folders находится inline в `DockHost.qml` и использует
`WorkspaceState.watch_model`. QML `repository_editor` — общий визуальный
`editorListForm` в `WindowContent.qml` с пустым `repositoryModel`.
`RepositorySyncView` и `RepositorySyncController` — отдельная рабочая подсистема
discovery/download и не редактируют repository mapping или Watch Folders.

## Формат сохранённых данных

Настройки сохраняются через `env_read_config`/`env_write_config` в
`ui_watch_folder`, ключ
`ui_main/<project type>/<project code>/watch_folders_dict`.
Формат — параллельные списки:

- `assets_codes`, `assets_names`, `assets_stypes`, `assets_skeys`;
- `assets_pipelines`, `paths`, `repos`, `statuses`.

`paths` содержит относительный watch path, `repos` — список repository codes,
`statuses` — enable flag. Process, context, matching template, scan interval и
последняя ошибка в формате не сохраняются.

## Контракт сценариев

| Сценарий | QWidget / Python API | Текущий QML | Статус QML |
|---|---|---|---|
| Список Watch Folders | `fill_watch_folders_tree_widget()` показывает status, stype, object и repository titles | Загружает title/path/pipeline/status из того же config | Частично: repository, project и реальное состояние watcher не показаны |
| Enable/disable | Item button вызывает `edit_watch_to_watch_folders_dict()`, затем добавляет/удаляет watch и стартует/останавливает observer | Switch меняет только `statuses` в config и роль модели | Частично: живой watcher не обновляется |
| Общий enable | Checkbox существует, но принудительно disabled; observer работает, пока есть `watched_items` | Отсутствует | Намеренно отсутствует до рабочего lifecycle |
| Путь | Относительный путь из naming `watch_folder`; editor разрешает ручное изменение | Только отображается | Частично |
| Repository | Editor выбирает один/несколько активных `env_tactic.get_all_base_dirs()` и сохраняет их codes | Generic editor показывает пустую presentation model | Отсутствует |
| Project | Один `Ui_projectWatchFoldersWidget` на project хранится в `env_inst.watch_folders[project_code]` | Модель перезагружается при `load_project()` | Частично |
| Process | Сохраняется `asset_pipeline`, а не process; при событии pipeline используется для определения check-in mode | Роль `process` фактически содержит pipeline code | Отличается / требует переименования роли |
| Context | Вычисляется во время события: `publish` для корня watch path, иначе имя непосредственного каталога | Отсутствует | Отсутствует |
| Matching template | Для созданного файла жёстко используется `$FILENAME.$EXT` | Отсутствует | Отсутствует |
| Scan interval | `FSObserver(timeout=1)` использует watchdog event queue; периодического directory scan нет | Отсутствует | Не применимо как scan interval; event timeout не настраивается |
| Recursive | Каждый watch регистрируется с `recursive=True` | Отсутствует | Отсутствует |
| Watcher state | `Watching`, если запись enabled и соответствующий item загружен; `Waiting`, если item/folder ещё не подключён; `Stopped`, если disabled | Показывает только bool enabled | Отсутствует фактическое состояние |
| Ошибки | Недоступные каталоги дают `dl.warning`; операции с папками обёрнуты `gf.catch_error`; row error не хранится | Ошибка toggle подавляется, UI не получает сообщение | Частично / недостаточно |
| Добавление | Item action открывает `Ui_repositoryEditorWidget`; после Save создаются root и process directories | Add создаёт фиктивную строку через `append_named()` | Отсутствует функционально |
| Редактирование | Editor загружает path и выбранные repositories, пересоздаёт недостающие directories | Settings вызывает только `notice()` | Отсутствует |
| Удаление | Диалог Remove/Keep/Cancel; может удалить запись либо запись вместе со всеми каталогами и файлами | Context action вызывает только `notice()` | Отсутствует |
| Repository mapping | Относительный path разворачивается через каждый выбранный repository root; editor поддерживает Add/Remove/All Repos | Пустая модель без Apply/Cancel | Отсутствует |
| Проверка пути | Перед запуском watch проверяется существование пути во всех выбранных активных repositories; отсутствующий path исключает item из watcher | При Open проверяется active repository, но editor validation отсутствует | Частично |

## Watcher lifecycle

`gf.FSObserver` расширяет watchdog `Observer`, хранит watches по search key и
передаёт событие вместе с repository/pipeline metadata. Watch создаётся для
каждого repository path рекурсивно. Observer стартует, когда `watched_items` не
пуст, и останавливается иначе.

На created event:

1. context определяется по каталогу созданного файла;
2. файл группируется фиксированным `$FILENAME.$EXT`;
3. pipeline/context используются для поиска check-in mode;
4. `checkin_file_objects()` добавляет операцию в проектную Commit Queue.

Событие не использует новый Matching Templates catalog. Дублирование,
debounce/stability проверки ещё записываемого файла и retry в watcher-классе не
обнаружены. Это требует отдельной проверки до подключения QML watcher.

## Repository API и доступность

`env_tactic.get_all_base_dirs()` возвращает base/client/local/sandbox с path,
title, color, code и active flag. `get_base_dir()` разворачивает code для
текущей платформы; `set_base_dir()` и `save_base_dirs()` изменяют общую
repository configuration.

Watch Folder Repository Editor выбирает только уже настроенные активные
repositories и не должен менять их корневые пути. Общий QML Repository Editor
не подключён к этому API. Repository Sync использует готовые local/web paths,
проверяет существующий файл, создаёт parent directory в worker, скачивает через
временный `.part`, поддерживает progress/retry/cancel и атомарную замену.

## Подтверждённые проблемы

- QML toggle сохраняет flag, но не вызывает `FSObserver.append_watch()` или
  `remove_watch()`.
- QML Add создаёт фиктивную запись, не связанную с project/sObject/config.
- QWidget context menu Enable/Disable/Edit/Delete содержит неподключённые
  actions; рабочие операции доступны через item actions.
- Глобальный checkbox watcher отключён и не управляет observer.
- Repository Editor не проверяет пустой path, абсолютный path, `..`, права
  записи и пересечение нескольких watch folders.
- `create_watch_folders()` и destructive directory removal выполняют обход и
  filesystem mutations синхронно из UI-вызова.
- Created event может обработать файл до окончания записи; watcher state не
  содержит processing/error/retry.
- Сохранённый pipeline ошибочно отображается в QML как `process`.

## Рекомендуемые этапы

1. Создать Python model/controller поверх существующего
   `watch_folders_dict`: полноценные роли, CRUD, validation и реальный
   enable/disable lifecycle без QWidget item dependency.
2. Реализовать отдельный Repository Mapping editor для Watch Folder:
   относительный path, multi-repository selection, asynchronous availability
   check, Save/Cancel и безопасное создание каталогов.
3. Подключить watcher events к Matching Templates и существующей Commit Queue;
   добавить file-stability/debounce, processing/error state и корректный
   shutdown.

## Ручные проверки

- включение/выключение нескольких watches в разных проектах;
- отсутствующий, read-only, сетевой и отключённый repository;
- одинаковый relative path в нескольких repositories;
- created/moved sequence files и файл, который долго дописывается;
- переключение проекта и повторное создание `env_inst.watch_folders`;
- закрытие приложения при активном observer и обрабатываемом событии;
- Delete с Keep и Remove без удаления пути за пределами repository root.
## Repository Editor

QML Repository Editor заменён отдельными `RepositoryEditorView` и
`RepositoryEditorController`. Рабочая копия строится из
`env_tactic.get_base_dirs()`; отдельного хранилища QML нет. Поддержаны
base/client/local/sandbox и handoff, Windows/Linux paths, active/default,
Save/Cancel и mapping текущего проекта по Watch Folders.

Проверка активных путей выполняется через local worker pool и проверяет только
directory/read/write без рекурсивного обхода. Save использует
`env_tactic.save_base_dirs()`, default — существующий key
`repositoryComboBox` в `cfg_controls`. После сохранения Check-in/Out повторно
читает repository и пересчитывает naming preview. Недоступный активный путь
блокирует сохранение и остаётся видимым в UI.

Требуют ручной проверки сетевые shares, Linux paths с Windows-хоста, QWidget
Repository Editor и активные Repository Sync операции.
## Watch Folders

QML Watch Folders использует отдельные `WatchFoldersController` и
`WatchFoldersView`, существующий `FSObserver`, repository API, Matching
Templates и Drop Plate. Поддержаны список, add/edit/remove выбранного sObject,
enable/disable, несколько repositories, relative path, project, pipeline,
process/context, matching template, Watching/Waiting/Stopped/Error, последняя
проверка и текст ошибки.

Настройки сохраняются в прежний `ui_watch_folder` project key. Для новых полей
в тот же `watch_folders_dict` добавлены параллельные списки `processes`,
`contexts`, `matching_templates`, `last_checks`, `errors`; старые ключи и
сигнатуры сохранены. При старте проекта записи восстанавливаются, доступные
enabled folders снова подключаются к watcher.

Создание каталогов и ручной recursive scan выполняются через local worker pool.
Созданные watcher files и результаты ручного scan передаются в Drop Plate,
где применяются Matching Templates; commit автоматически не запускается.
При закрытии QML watcher снимает watches и останавливает принадлежащий ему
observer до завершения общих worker pools.
