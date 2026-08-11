# Контракт Tasks, Notes, Messages и уведомлений

## Граница аудита

Проверены `ui_tasks_classes.py`, `ui_notes_classes.py`,
`ui_richedit_classes.py`, непосредственно связанные формы и текущие
QML-модели, контроллеры и представления коммуникации. Активные QWidget Tasks
и Notes собираются программно; собственной `.ui`-формы у них нет.

Связанные формы:

- `thlib/ui/misc/ui_richedit.ui` — панель форматирования;
- `thlib/ui/misc/ui_messages.ui` и `ui_message.ui` — старые макеты списка
  пользователей, разговора и reply editor, но активного controller-класса в
  проверенных модулях нет;
- `thlib/ui/tasks/ui_float_notify.ui` — макет View/Skip/Previous/Next/Hide,
  но активной реализации уведомлений в проверенных классах нет.

## Используемые классы и Python API

### Tasks

`Ui_tasksDockWidget` управляет выбранным одним или несколькими sObject,
асинхронно получает задачи и создаёт по процессам `Ui_taskWidget`.
`Ui_taskWidget` поддерживает несколько task sObject одного процесса, add/edit
через `Ui_addTacticSobjectWidget`, delete через `delete_sobject()`, а также
commit изменённых `status`, `assigned`, `description`, `bid_start_date` и
`bid_end_date`. Допустимые статусы берутся из task pipeline, пользователи — из
назначенной login group либо общего списка logins. Есть single/multiple save,
process filter, expand/collapse и переход к Notes.

QML получает задачи через `SnapshotDetailsController`, хранит исходные task
objects в `WorkspaceState._task_sobjects` и выдаёт безопасные роли
`process/status/user/due/color/notes`. Реальная операция сейчас одна:
`set_task_status()` вызывает `task.set_value("status")` и `task.commit()` в
server worker. Кнопка Add изменяет только presentation model, а context actions
не подключены к операциям.

### Notes и история

`Ui_notesBaseWidget` асинхронно вызывает `get_tasks_and_notes()` для выбранного
sObject/process. `Ui_notesWidget` может отдельно запросить notes, объединяет их
со status log текущей задачи, сортирует по timestamp и отображает входящие и
исходящие записи через `Ui_messageWidget`/`Ui_statusWidget`.

Reply вызывает `tactic_classes.add_note(search_key, process, context, note,
login, attachments)`. Текстовые URL преобразуются в ссылки. Удаление note
работает через `delete_sobject()`; пункт Edit присутствует, но
`edit_message()` содержит только диагностический `print` и функционально не
реализован.

QML загружает notes вместе с выбранным объектом и показывает роли
`author/time/body/status/attachments`. `workspaceState.add_note()` реально
добавляет plain-text note через server worker, но всегда использует
`process=context=publish`. После успеха запись добавляется в модель локально.
Status log задачи, отдельное обновление истории и server-generated note data
после создания не загружаются.

### Rich Edit

Форма `ui_richedit.ui` содержит bold, italic, underline, strike, alignment,
lists, sub/superscript, caps, font/color, links, images, folders и clipboard
actions. В `Ui_richeditWidget` реально подключён только italic; lightweight
режим скрывает большую часть расширенных кнопок. Notes используют plain-text
reply editor, а rich display создаётся только при показе URL как HTML.

QML использует обычные `TextField`, `TextArea` и `Label`. Форматированное
редактирование, HTML document model и безопасная обработка rich text
отсутствуют.

### Attachments

`Ui_notesWidget` принимает локальные файлы через dialog и drag-and-drop,
изображения через clipboard, показывает attachment editor и счётчик. Файлы
группируются существующим `MatchTemplate`, публикуются через Check-in/Commit
Queue в `attachment/<process>/<filename>`, после чего snapshots передаются в
`add_note()`. `Ui_messageWidget` получает attachment process/contexts и
показывает snapshot widgets.

QML attachment button показывает только уведомление. Модель выставляет
`attachments=0`, drag/paste/file selection, upload queue, attachment snapshots
и открытие вложений не подключены.

### Messages и notifications

QML `messagesForm` показывает `userModel`, но история и Send используют тот же
`noteModel` и `workspaceState.add_note()` выбранного sObject. Выбор пользователя
не меняет адресата или историю. Это визуальная оболочка, а не самостоятельный
Messages API.

`ApplicationController.notification_changed` показывает временный QML toast и
пишет событие в Debug Log. Кнопка notifications открывает `messagesForm`.
Модели unread, истории уведомлений, acknowledge/skip/view и счётчика на кнопке
нет. Макет `ui_float_notify.ui` к рабочему Python API в проверенной области не
подключён.

## Матрица функционального паритета

| Функция | QWidget | QML | Статус | Основной разрыв |
|---|---|---|---|---|
| Task: создание | Реальный Add sObject dialog | Add создаёт локальную строку | отсутствует | Нет schema/API submit и refresh |
| Task: редактирование | Status, assigned, description, dates | Только status | частично | Нет user, description, dates |
| Task: удаление | `delete_sobject()` | Context action без операции | отсутствует | Нет confirmation/API/refresh |
| Task: назначение пользователя | Login group или все logins | Только отображение user | отсутствует | Нет допустимой user model и commit |
| Task: status | Pipeline statuses с цветами | Commit текущего status работает | частично | QML список строится лишь из уже встреченных статусов |
| Task: process | Process widgets/filter и несколько tasks | Process только отображается | частично | Нет filter, add for process, task switch |
| Task: даты | Start/end edit и commit | Только due label | отсутствует | Нет date editor и сохранения |
| Notes: создание/reply | Plain reply, Ctrl+Enter, process/context | Plain reply работает для publish | частично | Контекст жёстко задан, нет Ctrl+Enter parity |
| Notes: редактирование | Пункт есть, реализация отсутствует | Отсутствует | отсутствует | Нет рабочего эталонного сценария |
| Notes: удаление | `delete_sobject()` | Context action без операции | отсутствует | Нет delete API и обновления модели |
| Rich text | UI богатый, реально подключён только italic | Plain text | отсутствует | Нужен согласованный минимальный формат |
| Attachments | File/drop/paste, editor, Check-in Queue, snapshots | Кнопка без действия | отсутствует | Нет подготовки, upload и отображения |
| Загрузка истории | Notes + task status log, timestamp sort | Notes текущей selection load | частично | Нет status log, reload, pagination |
| Messages | Формы есть, активного controller в области нет | Notes под видом conversation | отсутствует | Нет адресата, dialog model и Messages API |
| Unread | Не найдено | Не найдено | отсутствует | Нет server contract и модели состояния |
| Notifications | Форма есть без активного controller | Toast работает | частично | Нет history, unread и действий |
| Ошибки | Worker error через `gf.error_handle` | Общий notice/Debug Log | частично | Нет inline error/retry для Tasks/Notes |

## Состояния и обновление

- Первичная загрузка Tasks/Notes QML выполняется асинхронно через существующий
  server pool при выборе объекта.
- Защита от устаревшего detail request существует в общем selection controller,
  но отдельного request identity для ручного refresh Tasks/Notes нет.
- Task status и add note выполняются вне GUI thread и обновляют только
  затронутую строку/модель после success.
- Empty state, loading state и error state в самих Tasks/Notes docks явно не
  представлены; ошибка остаётся в общем toast и Debug Log.
- QML не хранит note/task identifiers в ролях, поэтому edit/delete/reply-to
  невозможно подключить безопасно без расширения модели.
- Attachment count сейчас фиктивно равен нулю, хотя исходные note objects могут
  содержать attachment snapshots.

## Рекомендуемый порядок переноса

1. Расширить Tasks model безопасными идентификаторами, pipeline statuses,
   допустимыми users и полями description/start/end; подключить add/edit/delete.
2. Добавить Notes controller с note identifiers, process/context, refresh,
   delete и объединённой timeline notes/status log.
3. Подключить attachments через существующие Check-in/Commit Queue и snapshot
   API, не передавая file objects в QML.
4. Определить минимальный реально поддерживаемый rich-text contract; не
   переносить неработающие кнопки формы механически.
5. Реализовывать Messages только после определения отдельного server API,
   адресата, conversation identity, history и unread semantics.
6. Поверх общей communication model добавить notification history, unread
   counter и View/Skip actions; временный toast оставить для кратких событий.

## Этап 29 — Tasks

QML Tasks использует отдельный `TasksController` и исходные task sObject, которые
остаются в `WorkspaceState`. Создание выполняется через `insert_sobjects()` с
`parent_key`, редактирование — через `set_value()`/`commit(triggers=True)`, удаление —
через `delete_sobject(include_dependencies=True)`. Все операции и повторная загрузка
задач выполняются в существующем server pool.

Реализованы создание, редактирование, подтверждённое удаление, process, pipeline
status, назначение пользователя, start/end, description, validation, loading,
inline error и повторная загрузка модели после успешной операции. Progress
сохраняется только при наличии колонки `progress` или `completion` в действующей
схеме `sthpw/task`; при её отсутствии поле отключено, серверная модель не меняется.
Существующий список Tasks сохранён, добавлены реальные Add/Edit/Refresh и быстрый
commit статуса. Полный traceback серверной ошибки остаётся в Debug Log.

Ручная проверка: ограничения login group конкретного проекта, серверные triggers
при create/edit/delete и фактическое имя progress-колонки в установленной схеме.
Notes, Messages, Rich Edit, attachments и notifications этим этапом не изменялись.

## Этап 30 — Notes, Messages и Rich Edit

Notes dock и Messages window используют единый `CommunicationController` и одну
timeline-модель выбранного sObject. Реализованы асинхронная загрузка и retry,
создание/reply с выбранным process, подтверждённое удаление, inline error,
локальное unread-состояние и обновление строк модели по search key без reset.

Текст сохраняется исходным plain text через существующий `add_note()`. Для показа
используется экранированное rich-text представление с кликабельными HTTP/HTTPS
ссылками; новый серверный HTML-формат не вводился. Редактирование сообщения
намеренно отсутствует: `Ui_messageWidget.edit_message()` не реализует операцию.

Вложения существующих notes загружаются из attachment snapshots, показывают
preview для локальных изображений и скачиваются через Repository Sync. К новому
сообщению можно привязать выбранные snapshots; новые файлы подготавливаются через
существующий Check-in/Out, после создания snapshot он становится доступен для
выбора. Передача файлов и сетевые операции не выполняются в GUI-потоке.

Отдельного рабочего адресного Messages API в проверенной реализации нет, поэтому
Messages остаётся альтернативным представлением истории выбранного sObject, без
фиктивных conversations. Требуют ручной проверки server permissions удаления,
связь note↔snapshot и preview/download на настроенных repositories.

## Этап 31 — уведомления

QML использует ограниченную очередь из трёх MD3-уведомлений поверх существующего
`notification_changed`, `loading_changed`, Repository Sync и Check-in signals.
Поддержаны info, warning, error, progress и completion; progress обновляет одну
карточку вместо создания потока сообщений.

Одинаковое активное уведомление не добавляется повторно, а повтор после закрытия
ограничен временным окном. Ошибки Tasks и Communication показываются только при
изменении текста. Полный traceback по-прежнему записывается исходным controller в
Debug Log; notification layer его не перехватывает и не сокращает.

Info/completion закрываются автоматически, warning/error живут дольше и могут
быть закрыты вручную. Таймеры имеют QObject-parent, останавливаются при удалении
уведомления и при shutdown. Модальные подтверждения остаются отдельными диалогами.

## Расширенный Tasks UI

Tasks теперь имеют два представления над одним `TasksController` и исходными
`sthpw/task` sObject. Компактный dock строится по процессам pipeline и показывает
также процессы без созданной задачи. Несколько задач одного процесса переключаются
внутри process card. Статусы, цвета и допустимые исполнители берутся из workflow.

`TasksWorkspaceView` поддерживает текущий объект, прямой `skey`, несколько
выделенных sObject, задачи пользователя и всего проекта. Поиск, фильтры, сортировка,
grouping и календарь работают локально над одной загруженной выборкой. Из User
Profile workspace открывается сразу в scope выбранного пользователя.

Пакетное изменение использует один server-side procedure: существующие задачи
общего процесса обновляются через `update_multiple`, отсутствующие создаются с
правильным `parent_key`. История статусов загружается лениво только для выбранной
задачи. QML получает безопасные роли; task/sObject instances остаются в Python.

Автоматически проверены helpers, Python syntax, QML loading и повторное открытие
окон. Вручную проверить permissions супервайзера, task pipelines/login groups,
server triggers и bulk edit на тестовом проекте.

## Tasks Workspace Stage 0 baseline (2026-08-04)

### Current quick editor behavior

- The process model contains every non-special process from the selected
  sObject pipeline, including processes that do not yet have a task.
- Special workflow nodes `action`, `condition`, `dependency` and `progress` are
  excluded from the quick task list.
- A missing task can stage status and assignee values before explicit Save. Save
  creates the task with the selected sObject as `parent_key`.
- Multiple tasks on one process remain separate by `task.code`. The quick editor
  exposes a task selector and remembers the preferred task code for the process.
- Preferred-task fallback is the remembered code, then the task associated with
  the current login when available, then the first task returned by the server.
- Process status choices come from that process's task pipeline. They are not a
  project-wide common status list.
- Assignee choices use the process login-group restriction and fall back to all
  loaded logins when the workflow provides no group.
- Cards and compact rows are two presentations of the same process model.

### Current detailed workspace scopes and query baseline

| Scope | Task query baseline | Parent query baseline |
|---|---:|---:|
| Current object with valid workspace data | 0 | 0 |
| Explicit object refresh | 1 native `get_tasks_sobjects` | 0 |
| Multiple selected sObjects | 1 `get_multiple_tasks_sobjects` | 0 |
| Project | 1 `sthpw/task` query | 1 batched query per distinct parent search type |
| User | 1 filtered `sthpw/task` query | 1 batched query per distinct parent search type |

The current project/user query has a hard limit of 500 tasks. Parent objects are
already batched by search type and code rather than loaded once per task. Local
search, grouping, sorting and calendar generation operate on the loaded records
and make no server request.

### Task identity and pipelines

- Detailed rows are identified by task code/search key, not by process.
- Two tasks with the same parent and process must remain two rows through every
  grouping mode.
- Status validation must remain per process/task pipeline. Tests now use separate
  model and publish task pipelines to prevent a common-status regression.

### Notes and multiple tasks

- Original and current note creation stores parent sObject, process and context;
  it does not store a task code.
- Ordinary notes are therefore a shared process thread.
- The original Notes widget displayed status history for its currently selected
  task. `CommunicationController` now selects one exact task by `task.code` and
  includes status events only from that task.
- Multiple tasks for the same process are selectable in the fixed Task Inspector.
  Switching tasks reuses loaded task and note records, so the shared Notes thread
  stays visible and no server request is issued.
- Preferred selection is the remembered code, the task assigned to the current
  login, then the first available task. The selected code remains stable while
  the dock is hidden and reopened.

### Confirmed task columns used by the current UI

`code`, `search_type`, `search_code`, `project_code`, `process`, `context`,
`status`, `assigned`, `description`, `bid_start_date`, `bid_end_date`,
`pipeline_code` and `timestamp` are consumed by current task workflows.

Progress is optional and is enabled only when the authenticated server schema
contains `progress` or `completion`. Priority exists only in inactive/commented
original UI code and is not confirmed as a current portable column. Direct task
attachment, dependency and latest-version columns are also unconfirmed; they
must not be added to the first table without checking the active project schema.

### Automated Stage 0 coverage

- no-task process rows;
- one task plus an empty process;
- multiple selectable tasks on one process;
- task-code identity across every grouping mode;
- different status pipelines for different processes;
- one native object query;
- one batched multi-object query;
- one project/user task query and batched parent queries by search type;
- quick Tasks and Notes QML component loading.

## Tasks Workspace Stage 1 store (2026-08-04)

The detailed Tasks Workspace now has one Python-owned `TaskWorkspaceStore`.
It owns source task objects, parent indexes, flat records, paging and worker
request generation. The existing `TasksController` remains the QML-facing
facade, so the quick editor and current QML bindings keep their public API.

Implemented scope/query rules:

- current object: reuse already loaded workspace tasks;
- selected objects: one existing multiple-task query;
- user, team or project: one `sthpw/task` query per page;
- parent data: one lightweight batch per parent search type;
- pipeline statuses and assignable users: loaded pipeline/login catalogs only;
- stale results: rejected after a scope change by request generation;
- duplicate task codes: replace the object in place and retain one row.

Each flat record now has stable task/parent identity, pipeline/status/user
catalogs, due state, notes, preview/version data when already present in the
loaded parent source, and
selection/edit/loading/error/conflict roles. Full attachment and history payloads
remain lazy. Automated coverage verifies parent-code collisions, page deduping,
total/has-more semantics, team filters and stale result rejection.

Live server permissions, triggers, exact optional columns and representative
large-project timings remain manual checks because they depend on the configured
TACTIC installation and project schema.

## Tasks Workspace Stage 2 browser (2026-08-04)

`TasksWorkspaceView` now presents real tasks through a separate
`TaskBrowserTable`. Rows show parent identity/preview, task process, pipeline
status, assignee, start/deadline, progress, latest version when already known,
notes and an overflow menu. Narrow layouts progressively hide secondary columns
while retaining object, process and status controls.

Single-click active selection is separate from checkbox selection. Ctrl-click
toggles a checked row and Shift-click checks a visible range. Double-click opens
the parent object. Sorting, grouping, selection and filters remain local and do
not query the server.

Inline status and assignee edits are staged in Python records. Save submits the
changed task objects through the existing server worker pool; Discard restores
the loaded values. Worker results reach the model through queued signals and
row errors remain visible for retry. The table uses reusable delegates without
scroll-triggered entrance animations.
