# Контракт Add/Edit/Link sObject

## Область и источники

- Legacy Add/Edit реализован программно классами `Ui_addTacticSobjectWidget` и `QtTacticEditWidget`; Link/Unlink — `Ui_linkSobjectsWidget`. Отдельных `.ui`-форм у этих окон нет.
- Серверное описание формы получает `Ui_addTacticSobjectWidget.get_widgets()` через существующий `env_inst.server_pool`: `execute_procedure_serverside(query_EditWdg, kwargs, project=...)`.
- `query_EditWdg` создаёт серверный `tactic.ui.panel.EditWdg`, вызывает `explicit_display()` и возвращает JSON с `EditWdg` и `InputWidgets`. В описании есть порядок, имена, заголовки и описания элементов, режим, security flag, class name, action options, значения и widget-specific metadata.
- Схема отношений для создания и связывания берётся отдельно из `stype.get_schema()`: insert определяет `relationship=instance` и `instance_type`, Link/Unlink получает `path` через `get_parent_instance`.
- Текущая QML-поверхность — `WindowContent.qml::sobjectEditForm` и floating windows `add_sobject`/`link_sobjects`. Она использует только общий `searchTypeModel`, поля Name/Description и кнопки; schema/model/API редактора полей отсутствуют.

## Legacy Add/Edit

### Контекст формы

| Контекст | Контракт |
|---|---|
| Создание | `view="insert"`, `input_prefix="insert"`, `search_type`, `parent_key`; проект берётся из parent stype либо stype |
| Редактирование | `view="edit"`, `input_prefix="edit"`, `search_key`, `parent_key`; допустим иной серверный `view` с edit prefix |
| Объект и родитель | Передаются как Python-объекты только внутренним legacy-адаптерам; серверный payload использует search keys |
| Поля | Порядок и тип определяет серверный EditWdg/config view, а не локальный список колонок |
| Права | `security_denied` приходит в описании EditWdg, но legacy-оболочка явно его не обрабатывает |

`Ui_addTacticSobjectWidget` сопоставляет серверный `class_name` через `tactic_widgets.get_widget_name`, создаёт нейтральный `Tactic*Wdg`, затем соответствующий QWidget `QTactic*Wdg`. Неизвестный класс ошибочно подменяется `TacticCurrentCheckboxWdg`, поэтому это нельзя переносить как допустимый общий fallback.

### Поддерживаемые поля

| Семантика | Legacy widget / источник | Поведение и ограничения |
|---|---|---|
| Text | `TextWdg` → `QTacticTextWdg` | `QLineEdit`; default/current value; `kwargs.read_only` отключает поле |
| Rich text | `TextAreaWdg` → `QTacticTextAreaWdg` | Многострочный **plain text** через `toPlainText`; HTML/rich-text контракт не подтверждён |
| Numeric | Отдельного numeric widget нет | Числовая колонка приходит как Text/Select согласно server view; локального parsing/range validation нет |
| Boolean | `CheckboxWdg`, `CurrentCheckboxWdg` | Возвращает `0/1`; initial value берётся из display values |
| Date/time | `CalendarInputWdg` | `yyyy-MM-dd HH:mm:ss`, calendar popup; пустое значение не моделируется явно |
| Enum | `SelectWdg` | Labels отделены от values; column может переопределяться `action_options.column`; editable combo допускает ввод, но возвращается value текущего индекса |
| User | `ProcessGroupSelectWdg` | Список логинов ограничивается assigned login group процесса либо всеми login objects из environment |
| Project | `ProjectSelectWdg` | Выбор из server-provided labels/values; отдельного QML project-field API нет |
| Process | `ProcessInputWdg`, `SubContextInputWdg`, `TaskStatusSelectWdg`, `PipelineInputWdg` | Значения зависят от parent pipeline, process info, task pipeline и `info_dict.process` |
| Relation / parent | `TaskSObjectInputWdg`, Select с `action_options.column` | Родитель отображается label и возвращает server-provided key/value; произвольного relation picker внутри Add/Edit нет |
| File / preview upload | `SimpleUploadWdg` | Выбор/drag-and-drop изображений, screenshot, preview editor; после insert/update выполняется отдельный icon check-in |
| Existing preview | `ThumbInputWdg` | Только отображает `Ui_iconWidget`; не возвращает значение поля |
| Password | `PasswordWdg` | Не показывает прежнее значение, возвращает только непустой новый текст; поддерживает read-only |

Не подтверждены отдельные field contracts для generic file, arbitrary relation picker, rich HTML, integer/decimal spin controls и standalone preview value. Их нельзя выводить только из типа DB-колонки: фактический редактор задаётся TACTIC view/widget class.

### Defaults, обязательность и read-only

- Default/current value приходит преимущественно в `__display_values__`, `values`, `kwargs.default` и widget-specific metadata. Select сначала применяет default, затем пытается заполниться из parent/current sObject; Pipeline использует current label при edit.
- `required` извлекается нейтральными Select/ProcessGroup/Project/Pipeline wrappers, но QWidget-слой не блокирует commit пустого значения и не показывает единой ошибки required.
- Read-only реально применяется только Text и Password. Для остальных типов общий read-only контракт не реализован.
- Неизменённые Text/TextArea/SubContext/Password возвращают `None` и не входят в update payload. Checkbox/date/select обычно возвращают значение независимо от факта изменения.
- Поля `preview` и `parent` исключаются из обычного data payload; preview обрабатывается отдельным check-in после commit.

### Validation, commit и результат

- Единственная явная client validation — проверка совпадающего `name`; пользователь может подтвердить дубликат. Required, numeric, enum membership, date range и межполевые зависимости общей проверкой не покрыты.
- Insert вызывает `tc.insert_sobjects(search_type, project, data, parent_key, instance_type)`. Update вызывает `server_start(project).update(search_key, data)`.
- После успеха Add открывает search tab для созданного объекта либо refresh текущих результатов; Edit refresh’ит результаты. При необходимости отдельно создаётся directory structure.
- Возвращённый sObject остаётся внутренним значением commit workflow. Диалог не вызывает `accept()`, не имеет собственного result signal и закрывается после side effects; вызывающий код не получает стабильного typed result.
- Загрузка схемы асинхронна и направляет ошибку в `gf.error_handle`. Commit защищён `gf.catch_error`, но выполняется синхронно в GUI-потоке; полный контракт ошибки определяется legacy decorator. Preview check-in и directory traversal также входят в legacy side effects.

## Legacy Link/Unlink

- Link показывает две существующие search-поверхности: доступные sObjects и уже связанные. Фильтрация по имени использует `("name", "EQI", query)`, связанная выборка — `("_expression", "in", related_expr)`.
- Перемещение между списками изменяет `include_set` и `exclude_set`; `current_set` предотвращает повторную вставку исходной связи. Порядок не является частью результата.
- Save вызывает `tc.edit_multiple_instance_sobjects(project, insert_search_keys, exclude_search_keys, parent_key, instance_type, path)` и закрывает окно.
- Unlink использует тот же API только с `exclude_search_keys`. В текущем QML реальный Unlink уже вызывается из `ApplicationController`, после чего выполняется refresh.
- Legacy Link не имеет отдельного unlink dialog, validation summary, result signal или `accept/reject`: результат — серверный side effect и refresh при закрытии. Save выполняется синхронно и не имеет локального error handler.

## Состояние QML

| Сценарий | Статус | Разница |
|---|---|---|
| Открыть Add/Link window | Частично | Floating window существует и сохраняет геометрию |
| Schema-driven поля | Отсутствует | Нет запроса EditWdg, модели descriptors и type delegates |
| Create/Edit | Отсутствует | Confirm не вызывает Python; edit выбранного объекта использует legacy QWidget только для snapshot file info |
| Link | Отсутствует | Нет двух выборок, include/exclude state и вызова `edit_multiple_instance_sobjects` |
| Unlink | Частично | Реальный API есть, но sync server call выполняется из GUI thread и ошибка сводится к короткому notification |
| Validation/errors/result | Отсутствует | QML поля не валидируются, нет busy/error state и результата операции |
| File/preview | Отсутствует | QML Add/Edit не подключён к существующему preview/check-in workflow |

Текущие Name/Description не являются безопасным минимальным редактором: они могут не входить в server view, пропускают обязательные поля и не сохраняются. QML Link визуально повторно использует Add form, хотя legacy-контракты этих окон различны.

## Общий schema-driven QML editor

Общий редактор сделать можно и это безопаснее прямого переноса каждого `QTactic*Wdg`, если Python остаётся владельцем схемы и commit:

1. Специализированный QObject запрашивает существующий `query_EditWdg` через server pool и преобразует JSON в QML-safe field descriptors: stable id, column, title, kind, value/default, required, read-only, options и validation state.
2. `QAbstractListModel` хранит draft и точечно сообщает изменения. QML выбирает небольшой набор delegates по нормализованному `kind`, не знает TACTIC class paths и не получает sObject/stype.
3. Python сохраняет исходные `class_name`, `action_options` и widget metadata для точного legacy-compatible payload, выполняет validation и вызывает существующие `TacticEditWdg.commit`/TACTIC API.
4. Text, textarea, boolean, datetime и select можно перенести общими delegates. User/project/process/pipeline/parent требуют field adapters, поскольку значения зависят от environment, workflow и родителя.
5. Upload/preview должен остаться отдельным адаптером существующего check-in workflow. Link требует отдельной модели available/linked и не должен маскироваться generic field editor.

До реализации необходимо формально определить fallback неизвестного widget class, required/read-only для всех типов и QML-safe operation result (`created/updated/linked/unlinked`, search key, message). Автоматическая подмена неизвестного типа checkbox несовместима с таким контрактом.

## Рекомендуемые этапы

1. Python schema adapter + field model, read-only загрузка реальной insert/edit view и явная ошибка unsupported widget.
2. Базовые delegates и единая validation: text, textarea, boolean, datetime, select; затем user/project/process/pipeline/parent adapters.
3. Async create/update с operation result и refresh, без переноса legacy QWidget side effects в QML.
4. Отдельный Link model с available/linked selection и общей async link/unlink командой.
5. Preview/upload adapter поверх существующего check-in API; ручная проверка прав, instance relations, parent path, task/process views и серверных ошибок.

## Реализация Add/Edit

- `SObjectEditorController` и `SObjectFieldModel` являются отдельной QML-facing границей; `ApplicationController` хранит только текущий operation context и существующий refresh callback.
- Insert/edit schema загружается асинхронно тем же `query_EditWdg`. Для edit передаются исходный `search_key` и view `edit`, а текущие значения уточняются по `SObject.get_info()`.
- Создание и изменение выполняет существующий `TacticEditWdg.commit` через `env_inst.server_pool`. QML не вызывает `insert`, `update` и не получает stype, SObject или schema objects.
- Related Add передаёт parent sObject и parent search key в Python. Instance type и relation path остаются ответственностью существующих schema/commit API.
- Поддержаны базовые типы предыдущего этапа, а также server-configured user, project, process/pipeline, task status и read-only parent. File, preview и Link намеренно не подключены.
- Required и базовая type validation выполняются до отправки. Серверная validation остаётся окончательной; её ошибка возвращается в форму, снимает loading и допускает осознанный повтор.
- Во время schema load и commit поля и кнопки блокируются. Повторный submit игнорируется, successful result закрывает окно и вызывает обычный `refresh_current`.
- Cancel до отправки закрывает окно без side effects. Повторное открытие создаёт новую schema session и отбрасывает запоздалый schema result по request id.

### Проверка

| Сценарий | Статус |
|---|---|
| Новый объект активного search type | Реализован; требует ручной проверки прав и server defaults |
| Новый related object | Реализован через parent context; instance relation требует ручной проверки |
| Редактирование выбранного sObject | Реализовано из context menu |
| Required/type validation | Реализована до server call |
| Server validation/error/retry | Реализованы как error state без автоматического повторного submit |
| Cancel/reopen/loading guard | Реализованы |
| Обновление результатов | Обычный async `refresh_current` после успеха |
| Link, file, preview | Не входят в этот этап |

## Реализация Link и специальных полей

- `SObjectLinkController` загружает available и linked sObjects через существующие `get_sobjects`/`get_related_sobjects` в server pool. QML получает только search key, title и subtitle.
- Поиск повторяет legacy `name EQI` semantics, ограничен 100 результатами и имеет stale-result guard. Пустой available/linked список является отдельным нормальным состоянием.
- Add/remove в окне меняют локальный набор связей. Save вычисляет только разницу с исходным набором и вызывает `edit_multiple_instance_sobjects` с исходными `instance_type`, parent key и schema path.
- Unlink из context menu переведён на тот же worker pool; после успеха выполняется `refresh_current`, поэтому обновляются карточки, дерево и детали активного объекта.
- Cancel закрывает Link без server mutation. Ошибка загрузки или save остаётся в окне и допускает повторное действие; повторное открытие заново получает обе выборки.
- Relation-поля server EditWdg остаются обычными enum adapters; `TaskSObjectInputWdg` представлен read-only parent, а user/project/process/pipeline/task status — специализированными option descriptors без передачи объектов в QML.
- `SimpleUploadWdg` представлен одним preview file picker. Путь нормализуется на
  Python-стороне, но отправка preview отложена до подключения repository и
  общего check-in API.
- `ThumbInputWdg` остаётся read-only thumbnail surface. Механически переносить screenshot maker и preview editor в field delegate не требуется.
- Отдельный generic file-column widget в проверенном legacy EditWdg отсутствует, поэтому QML-only file field не вводился. File attachment/check-in остаётся отдельным существующим workflow.

### Итоговая проверка

| Сценарий | Статус |
|---|---|
| Загрузка/поиск available и linked | Реализованы асинхронно |
| Создание и удаление instance links | Реализованы; реальные права/схема требуют ручной проверки |
| Cancel, empty, server error, reopen | Реализованы |
| Refresh карточек/дерева/деталей | `refresh_current` после успешной mutation |
| Preview selection и queue | Реализованы через существующий legacy check-in adapter |
| Generic file/relation QWidget clones | Намеренно не переносятся |
