// Shared Frame labels from the existing Handler/Stream EN/RU catalogs.
const russian = {
    'A view with this name already exists':
        'Представление с таким именем уже существует',
    'Actions on hover': 'Действия при наведении',
    'Applies to every process with this name in the project, including other pipelines.':
        'Действует для всех процессов с этим именем в проекте, включая другие pipeline.',
    'Apply or discard the pending text before continuing':
        'Примените или сбросьте введённый текст перед продолжением',
    'Attributes must be a JSON object with string values':
        'Атрибуты должны быть объектом JSON со строковыми значениями',
    'Checking objects and dependencies…': 'Проверка объектов и зависимостей…',
    'Choose which actual task date to set.':
        'Выберите, какую фактическую дату задачи изменить.',
    'Conditions are checked as XML before saving.':
        'Перед сохранением проверяется XML условий.',
    'Database table unavailable': 'Таблица базы данных недоступна',
    'Enter a whole number within the allowed range':
        'Введите целое число в допустимом диапазоне',
    'Explain why this rule is needed.': 'Объясните назначение этого правила.',
    'Filter the source task status, or listen to any status.':
        'Выберите исходный статус задачи или отслеживайте любой статус.',
    'Invalid JSON. Check quotes, commas and braces.':
        'Некорректный JSON. Проверьте кавычки, запятые и скобки.',
    'Invalid layout template': 'Некорректный шаблон компоновки',
    'Invalid view name': 'Некорректное имя представления',
    'Mobile actions': 'Мобильные действия',
    'Native action parameters. TACTIC expressions are supported by notifications.':
        'Штатные параметры действия. В уведомлениях поддерживаются выражения TACTIC.',
    'No Search Objects': 'Нет Search Objects',
    'Node positions must be finite':
        'Координаты узлов должны быть конечными числами',
    'Notification message with optional TACTIC expressions.':
        'Текст уведомления; можно использовать выражения TACTIC.',
    'Object information': 'Сведения об объекте',
    'Process settings must be a JSON object':
        'Параметры процесса должны быть объектом JSON',
    'Related and child objects': 'Связанные и дочерние объекты',
    'Save or discard changes before continuing':
        'Сохраните или сбросьте изменения перед продолжением',
    'Save the workflow before editing process dependencies':
        'Сохраните рабочий процесс перед редактированием зависимостей',
    'Schema changed on the server. Reload before deleting a Search Type.':
        'Схема изменилась на сервере. Обновите её перед удалением Search Type.',
    'Select a SObject layout configuration':
        'Выберите конфигурацию компоновки SObject',
    'Source status': 'Исходный статус',
    'Tasks and notes': 'Задачи и заметки',
    'The database table is absent. No table is created by reading columns.':
        'Таблица базы данных отсутствует. Чтение колонок не создаёт таблицу.',
    'The deletion result is unknown. Close this review and reload the schema before trying again.':
        'Результат удаления неизвестен. Закройте это окно и обновите схему перед повторной попыткой.',
    'The native event template replaces the subject and body when saved.':
        'При сохранении штатный шаблон события заменит тему и текст.',
    'The native event that starts this rule.':
        'Штатное событие, запускающее это правило.',
    'The native notification handler may include a login ticket.':
        'Штатный обработчик уведомлений может включать тикет входа.',
    'The readable name of this rule.': 'Понятное имя этого правила.',
    'This process is referenced by a connection. Add the missing process or remove its connections before saving.':
        'На этот процесс ссылается связь. Добавьте отсутствующий процесс или удалите его связи перед сохранением.',
    'Use a lowercase table name with letters, digits and underscores':
        'Используйте строчные латинские буквы, цифры и подчёркивания в имени таблицы',
    'Use inherited': 'Наследовать',
    Assignment: 'Назначение',
    Body: 'Текст',
    Depth: 'Глубина',
    Editor: 'Редактор',
    Select: 'Выбрать',
    'Invalid column move': 'Некорректное перемещение колонки',
    'The column cannot be moved further.': 'Колонку нельзя переместить дальше.',
    Guide: 'Руководство',
    Reference: 'Справочник',
    'Help topics': 'Разделы справки',
    'Search help': 'Поиск по справке',
    'Close help topics': 'Закрыть разделы справки',
    'Reload help articles': 'Перезагрузить статьи справки',
    'Open article file': 'Открыть файл статьи',
    'Download article': 'Скачать статью',
    'No help topics match your search': 'Подходящие разделы справки не найдены',
    Display: 'Вид',
    Enabled: 'Включено',
    'Start date': 'Дата начала',
    'Assigned to': 'Исполнитель',
    Actions: 'Действия',
    Loading: 'Загрузка',
    Size: 'Размер',
    Assets: 'Ассеты',

    Thumbnail: 'Миниатюра',
    'Delete the selected sidebar item?':
        'Удалить выбранный элемент бокового меню?',
    '%1 nodes selected': 'Выделено нод: %1',
    '1. Choose a starting point · 2. Arrange elements · 3. Check and save':
        '1. Выбери заготовку · 2. Размести элементы · 3. Проверь и сохрани',
    'A deadline or another date with a time.':
        'Срок сдачи или другая дата со временем.',
    'A field stores one attribute of each Search Object. Define its name and type here; fill in actual values when editing the objects.':
        'Поле хранит один параметр каждого серч-объекта. Здесь задаются имя и тип поля, а сами значения заполняются при редактировании объектов.',
    'A flag with two values, stored as true or false.':
        'Признак с двумя значениями, в базе хранится как true или false.',
    'A new preview is ready to be queued':
        'Новое превью готово к добавлению в очередь',
    'A read-only view of this Search Type and only its direct schema relationships.':
        'Схема выбранного серч-тайпа и только его прямых связей — без редактирования.',
    'A recognizable name for users.': 'Понятное название для пользователей.',
    'A technical name: lowercase Latin letters, numbers and underscores. For example, duration_minutes. No spaces; start with a letter.':
        'Техническое имя: строчные латинские буквы, цифры и подчёркивания. Например, duration_minutes. Без пробелов, первая — буква.',
    'APPLY XML': 'ПРИМЕНИТЬ XML',
    'Accent color': 'Цвет',
    'Access level': 'Уровень доступа',
    'Access rules': 'Правила доступа',
    'Access: %1': 'Доступ: %1',
    Action: 'Действие',
    'Action and condition nodes use a native process|action trigger. Script changes are saved, not executed by this editor.':
        'Узлы action и condition используют триггер process|action. Редактор сохраняет скрипты, но не запускает их.',
    Active: 'Активные',
    'Actual date': 'Фактическая дата',
    Add: 'Добавить',
    'Add a field': 'Добавить поле',
    'Add an image, text or button to begin.':
        'Для начала добавь картинку, текст или кнопку.',
    'Add link': 'Добавить ссылку',
    'Add node': 'Добавить узел',
    'Add process': 'Добавить процесс',
    'Add rule': 'Добавить правило',
    'Add section': 'Добавить раздел',
    'Add separator': 'Добавить разделитель',
    'Add to canvas': 'Добавить на схему',
    'Add to draft': 'Добавить в черновик',
    'Add widget': 'Добавить виджет',
    'Additional conditions (native rules XML)':
        'Дополнительные условия (XML правил TACTIC)',
    'Additional fields': 'Дополнительные поля',
    'Additional fields to create (%1)': 'Дополнительные поля к созданию (%1)',
    Administration: 'Администрирование',
    'Advanced JSON': 'Расширенный JSON',
    'Advanced XML': 'Расширенный XML',
    'Advanced access to native data, including parameters of installed custom nodes. Standard settings are available in Parameters.':
        'Расширенные данные TACTIC, включая параметры установленных пользовательских нод. Обычные настройки доступны в разделе «Параметры».',
    'Advanced fields': 'Дополнительные поля',
    'Advanced layout settings and XML':
        'Дополнительные настройки компоновки и XML',
    'Advanced rule pages': 'Разделы расширенных правил',
    'Advanced rules': 'Расширенные правила',
    'Affect related objects only, or all objects of this Search Type.':
        'Работать только со связанными объектами или со всеми объектами серч-тайпа.',
    All: 'Все',
    'All Search Types': 'Все Search Type',
    'All data in these columns will be lost. This editor cannot restore it after saving. Check any scripts, naming rules and saved searches that use these fields.':
        'Все данные в этих столбцах будут потеряны. После сохранения этот редактор не сможет их восстановить. Проверьте скрипты, правила нейминга и сохранённые поиски, использующие эти поля.',
    'All group rules': 'Все правила группы',
    'All groups': 'Все группы',
    'All matching processes': 'Все одноимённые процессы',
    'All objects': 'Все объекты',
    'All targets': 'Все объекты',
    'Allow processes and tasks for this Search Type.':
        'Разрешить процессы и задачи для этого серч-тайпа.',
    'Already on schema': 'Уже на схеме',
    'Any status': 'Любой статус',
    Appearance: 'Внешний вид',
    'Applies only to this process in this pipeline.':
        'Применяется только к этому процессу в этом пайплайне.',
    'Applies to every process named %1 in this project, including other pipelines.':
        'Применяется ко всем процессам с именем %1 в проекте, в том числе в других пайплайнах.',
    Apply: 'Применить',
    'Apply administrative changes?': 'Применить изменения на сервере?',
    'Apply attributes': 'Применить атрибуты',
    'Apply settings': 'Применить параметры',
    'Apply to draft': 'В черновик',
    'Apply to draft, then save the table.':
        'Примените к черновику, затем сохраните таблицу.',
    'Apply updates the draft. Save sends it to the server.':
        '«Применить» обновляет черновик. «Сохранить» отправляет его на сервер.',
    Approval: 'Согласование',
    Archive: 'Архивировать',
    'Arrange nodes': 'Расставить ноды',
    'Arrange processes on the canvas, connect their ports and select a process to configure it.':
        'Разместите процессы на графе, соедините порты и выберите процесс для настройки.',
    'Assigned group': 'Группа исполнителей',
    'Assigned user': 'Исполнитель',
    'Assignment choices and default estimates for this process.':
        'Исполнители и плановые значения задач этого процесса.',
    'Attributes (JSON)': 'Атрибуты (JSON)',
    'Automatic layout': 'Автоматическая раскладка',
    'Available targets': 'Доступные объекты',
    Back: 'Назад',
    'Back to rules': 'К правилам',
    'Behave as': 'Соответствует статусу',
    'Build your own view': 'Собери свой вид',
    'Built-in system schema · read-only':
        'Встроенная системная схема · только чтение',
    Cancel: 'Отмена',
    'Cannot be empty in the database': 'В базе не может быть пустым',
    'Card width': 'Ширина карточки',
    'Cell editor': 'Редактор ячейки',
    'Change parent status': 'Изменить статус родителя',
    'Change process': 'Изменить процесс',
    'Change task statuses': 'Изменить статусы задач',
    'Checked = allowed. The lock marks a grant controlled by another rule. Other group memberships can also grant access.':
        'Галочка — доступ разрешён. Замок — доступ задан другим правилом. Членство в других группах тоже может давать доступ.',
    'Checking the table and its dependencies…':
        'Проверяем таблицу и её зависимости…',
    'Child key column': 'Ключевое поле дочернего объекта',
    'Choose Search Type preview': 'Выбрать превью серч-тайпа',
    'Choose a registered Search Type to add to the schema.':
        'Выберите серч-тайп, который нужно добавить на схему.',
    'Choose a server target or enter its identifier. An asterisk matches all targets.':
        'Выберите объект сервера или введите его код. Звёздочка означает все объекты.',
    'Choose an existing user to receive approval tasks.':
        'Выберите пользователя, которому назначаются задачи согласования.',
    'Choose an input port. Esc cancels the connection.':
        'Выберите входной порт. Esc отменяет создание связи.',
    'Choose an output port. Esc cancels the connection.':
        'Выберите выходной порт. Esc отменяет создание связи.',
    "Choose existing columns below, or enter a new key column name. New columns are created on schema save, using the opposite key's type.":
        'Выберите столбцы из списков или введите имя нового. Новые столбцы создаются при сохранении схемы с типом ключа на другой стороне связи.',
    'Choose the native behavior of this process.':
        'Выберите поведение процесса в TACTIC.',
    'Choose the pipeline this hierarchy process opens.':
        'Выберите пайплайн, который открывает этот процесс hierarchy.',
    'Choose which objects and processes this node signals or tracks.':
        'Укажите, каким объектам и процессам нода отправляет события или за какими следит.',
    'Click a part of the preview, or select it in Elements.':
        'Нажми на часть примера или выбери её в списке элементов.',
    Close: 'Закрыть',
    'Close details': 'Закрыть карточку',
    'Close process dependencies': 'Закрыть зависимости процесса',
    'Close workflow editor': 'Закрыть редактор workflow',
    'Collapse navigation': 'Свернуть навигацию',
    'Collection layout': 'Размещение объектов',
    Color: 'Цвет',
    Column: 'Колонка',
    Columns: 'Колонки',
    'Columns Editor': 'Редактор колонок',
    'Columns of system and config Search Types cannot be deleted here.':
        'Столбцы системных серч-тайпов и config здесь удалять нельзя.',
    'Completion level represented by this process or status.':
        'Процент готовности, которому соответствует процесс или статус.',
    'Completion, %': 'Готовность, %',
    'Configuration changes': 'Изменения конфигурации',
    'Configuration source': 'Источник конфигурации',
    'Configuration view': 'Представление конфигурации',
    'Confirm table name': 'Подтверждение имени таблицы',
    Connect: 'Соединить',
    'Connect Search Types to describe how Search Objects relate to each other.':
        'Соедините серч-тайпы, чтобы задать связи между серч-объектами.',
    'Connect processes': 'Соединить процессы',
    Connection: 'Подключение',
    'Connection {from} to {to}': 'Связь {from} → {to}',
    'Connections refer to missing processes: %1. Add the missing processes or remove their connections before saving.':
        'Связи ссылаются на отсутствующие процессы: %1. Перед сохранением добавьте эти процессы или удалите лишние связи.',
    Content: 'Содержимое',
    'Copy recipients': 'Копия письма',
    'Counts or durations in whole units, without a fractional part.':
        'Количество или длительность в целых единицах, без дробной части.',
    Create: 'Создать',
    'Create a Search Object before evaluating this rule.':
        'Для проверки правила сначала создайте объект.',
    'Create a table and add its node to the project schema. Your current connections and canvas edits will be kept.':
        'Создайте таблицу и добавьте её ноду на схему проекта. Текущие связи и изменения канваса сохранятся в черновике.',
    'Create a task when a workflow event reaches this process.':
        'Создавать задачу, когда в процесс поступает событие воркфлоу.',
    'Create a trigger or notification using the plus button.':
        'Создайте триггер или уведомление кнопкой «+».',
    'Create a user group in Groups before editing its permissions. The admin group has full access and is not editable here.':
        'Сначала создайте группу в разделе «Группы». Группа admin имеет полный доступ и здесь не редактируется.',
    'Create a workflow from a saved Search Type.':
        'Создайте воркфлоу из сохранённого серч-тайпа.',
    'Create custom view': 'Создать свой вид',
    'Create group': 'Создать группу',
    'Create missing columns': 'Создать недостающие столбцы',
    'Create naming rule': 'Создать правило именования',
    'Create output tasks': 'Создать задачи следующих процессов',
    'Create parent task and subtasks': 'Создавать задачу и подзадачи',
    'Create parent task only': 'Создавать только родительскую задачу',
    'Create subtasks only': 'Создавать только подзадачи',
    'Create task status workflow': 'Создать workflow статусов задач',
    'Create tasks': 'Создавать задачи',
    'Create tasks automatically': 'Создавать задачи автоматически',
    'Create workflow': 'Создать воркфлоу',
    'Create workflow for': 'Создать workflow для',
    'Create workflow for %1': 'Создать воркфлоу для %1',
    'Create workflow for {type}': 'Создать воркфлоу для {type}',
    'Created on save': 'Будет создан при сохранении',
    'Current Search Type preview': 'Текущее превью серч-тайпа',
    'Custom access level: %1. Edit it in Advanced rules.':
        'Особый уровень доступа: %1. Его можно изменить в расширенных правилах.',
    'Custom access level: {level}. Edit it in Advanced rules.':
        'Особый уровень доступа: {level}. Измените его в расширенных правилах.',
    'Custom attributes (JSON)': 'Произвольные атрибуты (JSON)',
    'Custom event': 'Другое событие',
    'Custom scopes': 'Дополнительные категории',
    'Custom views and SObject item layouts':
        'Пользовательские виды и компоновки SObject',
    DISCARD: 'НЕ СОХРАНЯТЬ',
    'DROP TABLE': 'DROP TABLE',
    'Data location': 'Где хранятся данные',
    Database: 'База данных',
    'Database table': 'Таблица базы данных',
    'Database type: %1': 'Тип в базе: %1',
    'Database type: {type}': 'Тип в базе данных: {type}',
    'Database: %1': 'База данных: %1',
    'Date and time': 'Дата и время',
    'Decimal number': 'Дробное число',
    Default: 'По умолчанию',
    'Default duration, days': 'Длительность по умолчанию, дни',
    'Default fields': 'Стандартные поля',
    'Default planned effort for a new task.':
        'Плановая трудоёмкость новой задачи.',
    'Default reviewer for approval tasks.':
        'Исполнитель задач согласования по умолчанию.',
    'Defines statuses only for tasks of this process, not stages of the parent Search Object workflow.':
        'Задаёт статусы только для задач этого процесса, а не этапы воркфлоу родительского серч-объекта.',
    Delete: 'Удалить',
    'Delete Search Type from project': 'Удалить SearchType из проекта',
    'Delete Search Type from project?': 'Удалить серч-тайп из проекта?',
    'Delete Search Type…': 'Удалить серч-тайп…',
    'Delete columns from %1 (%2):': 'Удалить столбцы из %1 (%2):',
    'Delete field': 'Удалить поле',
    'Delete fields from {type}: {fields}? All values in these columns will be lost. Check scripts, naming rules and saved searches before saving.':
        'Удалить поля из {type}: {fields}? Все значения этих колонок будут потеряны. Перед сохранением проверьте скрипты, правила нейминга и сохранённые поиски.',
    'Delete from project': 'Удалить из проекта',
    'Delete marks a field for removal. Undo cancels the mark. Confirming Save deletes the column and its values; field types are not changed here.':
        'Удаление помечает поле, а отмена снимает пометку. Подтверждённое сохранение удаляет колонку и её значения; типы полей здесь не меняются.',
    'Delete marks a field for removal. You can undo the mark before saving. Confirming Save deletes the column and all its values; field types are not changed here.':
        'Кнопка удаления помечает поле. До сохранения пометку можно отменить. После подтверждения сохранения столбец и все его значения будут удалены; типы полей здесь не меняются.',
    'Delete row': 'Удалить строку',
    'Deleting Search Type…': 'Удаляем серч-тайп…',
    'Deletion is blocked. Remove Search Objects and dependencies first, or only remove the node from the canvas.':
        'Удаление заблокировано. Сначала удалите серч-объекты и зависимости либо только уберите ноду со схемы.',
    Deny: 'Запрет',
    'Dependency sections': 'Разделы зависимостей',
    'Describe the scene and what needs to be done.':
        'Опишите сцену и что нужно сделать.',
    Description: 'Описание',
    'Descriptions and notes spanning several lines.':
        'Описания и заметки из нескольких строк.',
    Destination: 'Назначение',
    'Destination status': 'Целевой статус',
    'Destination tasks': 'Задачи для изменения',
    Details: 'Параметры',
    'Direct table editing and CSV export':
        'Прямое редактирование таблиц и экспорт CSV',
    'Directory naming': 'Именование папок',
    Discard: 'Не сохранять',
    'Discard changes': 'Отменить изменения',
    'Discard naming changes': 'Отменить изменения нейминга',
    'Discard unapplied JSON changes?': 'Отменить неприменённые изменения JSON?',
    'Discard unsaved access changes?': 'Отменить несохранённые изменения прав?',
    'Discard unsaved changes?': 'Отменить несохранённые изменения?',
    'Discard unsaved definition changes?':
        'Отменить несохранённые изменения определения?',
    'Discard unsaved naming changes?':
        'Отменить несохраненные изменения именования?',
    'Discard unsaved raw table changes?':
        'Отменить несохранённые изменения таблицы?',
    'Discard unsaved sidebar changes and reload from the server?':
        'Отменить несохранённые изменения сайдбара и загрузить конфигурацию с сервера?',
    'Display label': 'Отображаемое название',
    'Do not create tasks': 'Не создавать задачи',
    Draft: 'Черновик',
    'Draft · not saved yet': 'Черновик · ещё не сохранён',
    'Drag a selected node to move the group · Delete: remove selection · F: center selection · Home: reset view · Ctrl+S: save':
        'Потяните выделенную ноду, чтобы переместить группу · Delete — убрать выделенное · F — центрировать · Home — сбросить вид · Ctrl+S — сохранить',
    'Drag an element onto a cell, or use the move buttons.':
        'Перетащите элемент на ячейку или используйте кнопки перемещения.',
    'Duplicate selected rule': 'Дублировать выбранное правило',
    'Each Search Object selects its pipeline through the pipeline_code field.':
        'Пайплайн каждого серч-объекта задаётся в поле pipeline_code.',
    'Each process uses its own task status workflow.':
        'У каждого процесса свой воркфлоу статусов задач.',
    Edit: 'Редактировать',
    'Edit generated workflow triggers in the node parameters':
        'Меняйте сгенерированные триггеры в параметрах узла',
    'Edit one native TACTIC element at a time. Custom options remain unchanged in XML.':
        'Редактируйте по одному нативному элементу TACTIC. Пользовательские параметры в XML останутся без изменений.',
    'Edit pipelines': 'Редактировать пайплайны',
    'Edit rule': 'Изменить правило',
    'Edit task status workflow': 'Редактировать статусы задач',
    'Edit the title and description without changing the Search Type identity.':
        'Изменение названия и описания сохраняет идентификатор типа объектов.',
    Elements: 'Элементы',
    'Enter %1 to confirm': 'Для подтверждения введите %1',
    'Enter {type} to confirm': 'Введите {type} для подтверждения',
    'Entities and fields': 'Серч-тайпы и их поля',
    'Estimated work, hours': 'Плановая работа, часы',
    'Evaluate the draft on a real object with the native TACTIC engine. Preview does not check in a file.':
        'Проверка черновика на реальном объекте штатным движком TACTIC. Файл не сдаётся в репозиторий.',
    Event: 'Событие',
    'Exact status name understood by the target process.':
        'Точное имя статуса, который поддерживает целевой процесс.',
    'Example description': 'Пример описания',
    'Example object': 'Пример объекта',
    'Example value: %1': 'Пример значения: %1',
    'Example value: {value}': 'Пример значения: {value}',
    'Example: %1 = %2': 'Пример: %1 = %2',
    'Example: {name} = {value}': 'Пример: {name} = {value}',
    'Execution mode': 'Режим выполнения',
    'Existing fields (%1)': 'Поля на сервере (%1)',
    'Existing fields ({count})': 'Существующие поля ({count})',
    'Existing files already use this path: {count}':
        'Этот путь уже используют файлы: {count}',
    'Expand navigation': 'Развернуть навигацию',
    'Explain what happens at this stage of the workflow.':
        'Опишите, что происходит на этом этапе.',
    'Explain what these Search Objects represent.':
        'Опишите, что представляют собой эти серч-объекты.',
    'Explain what this pipeline is used for.':
        'Опишите назначение этого пайплайна.',
    'Explicit permission for this group.': 'Право явно задано для этой группы.',
    'Export CSV': 'Экспорт CSV',
    Field: 'Поле',
    'Field access': 'Доступ к полям',
    'Field name': 'Имя поля',
    'Field type': 'Тип данных',
    Fields: 'Поля',
    'Fields to create (%1)': 'Будут созданы поля (%1)',
    'Fields to create ({count})': 'Поля для создания ({count})',
    'File checked in': 'Файл опубликован',
    'File naming': 'Именование файлов',
    'File type': 'Тип файла',
    'Filter by Search Type': 'Фильтр по Search Type',
    'Filter saved views': 'Фильтр сохранённых представлений',
    'Filter tables': 'Фильтр таблиц',
    'Find a Search Type': 'Найти серч-тайп',
    'Find a field': 'Поиск поля',
    'Find a group': 'Найти группу',
    'Find a permission': 'Найти право доступа',
    'Find a pipeline': 'Найти пайплайн',
    'Find a server target': 'Найти объект на сервере',
    'Find a target or rule': 'Найти объект или правило',
    'Find the permission row and the group column, then tick to allow access. Changes across groups are saved together.':
        'Найдите строку права и столбец группы, затем поставьте галочку, чтобы разрешить доступ. Изменения всех групп сохраняются вместе.',
    Firetruck: 'Пожарная машина',
    'From (child)': 'От (дочерний)',
    'Full access': 'Полный доступ',
    'Generate a temporary login ticket': 'Создавать временный тикет для входа',
    'Generated workflow rule': 'Сгенерированное правило workflow',
    'Global permissions': 'Общие права',
    'Granted by defaults, subgroups or an All rule. Change the granting rule first.':
        'Доступ задан настройками группы, подгруппами или правилом «Все». Сначала измените правило, выдающее доступ.',
    Group: 'Группа',
    'Group defaults': 'Базовые правила группы',
    'Group project (empty = global)': 'Проект группы (пусто — общая)',
    Groups: 'Группы',
    'Groups and members': 'Группы и участники',
    Help: 'Справка',
    'Hide config types': 'Скрыть типы config',
    'Hide properties': 'Скрыть свойства',
    'Hide workflow list': 'Скрыть список воркфлоу',
    'Hierarchy: child → parent.': 'Иерархия: дочерний → родительский объект.',
    'How many tasks to create for this process.':
        'Сколько задач создавать для этого процесса.',
    'How this Search Type appears in navigation and Search Object lists.':
        'Как серч-тайп выглядит в навигации и списках серч-объектов.',
    'How this item appears in project navigation. Its color comes from the Search Type; selection follows your theme.':
        'Как пункт выглядит в навигации проекта. Цвет берётся из типа объектов, а выделение — из выбранной темы.',
    Identifier: 'Идентификатор',
    'Image sent to Commit Queue; track upload progress there':
        'Изображение передано в очередь отправки; следите за загрузкой там',
    'In process': 'В текущем процессе',
    'Include this process when generating tasks.':
        'Включать процесс при создании задач.',
    'Inherited access-level defaults (server)':
        'Базовые права уровня группы (сервер)',
    'Inherited defaults still apply. Add a rule to override them for a target.':
        'Базовые права продолжают действовать. Добавьте правило, чтобы изменить их для нужного объекта.',
    'Inherited. Click to set an explicit permission.':
        'Правило наследуется. Нажмите, чтобы задать право явно.',
    "Initial interval between a task's start and end dates.":
        'Начальный интервал между датами начала и окончания задачи.',
    'Input name': 'Имя входа',
    'Input process': 'Входной процесс',
    Inspector: 'Свойства',
    'Installed Python class': 'Установленный класс Python',
    'Instance table name': 'Имя связующей таблицы',
    'Item preview': 'Предпросмотр строки',
    'Its description, action and native settings will appear here.':
        'Здесь появятся его описание, действие и параметры TACTIC.',
    'Its details appear here.':
        'Здесь отображаются сведения о выбранном элементе.',
    'Its details appear here. Use Add node to extend the canvas.':
        'Здесь появятся его параметры. Для нового узла откройте «Добавить узел».',
    'Keep editing': 'Продолжить',
    'Key fields: %1 → %2': 'Поля связи: %1 → %2',
    'Key fields: {from} → {to}': 'Ключевые поля: {from} → {to}',
    'Layout Editor': 'Редактор компоновки',
    'Layout: ': 'Компоновка: ',
    'Limits the available assignees to members of this group.':
        'Исполнителей можно будет выбирать из участников этой группы.',
    'Limits the available supervisors to members of this group.':
        'Супервайзеров можно будет выбирать из участников этой группы.',
    'Link table · M:N': 'Связующая таблица · M:N',
    'Link table: %1': 'Связующая таблица: %1',
    'Link table: {name}': 'Таблица связи: {name}',
    'Linked workflows': 'Связанные workflows',
    'Loading columns…': 'Загрузка столбцов…',
    'Loading data…': 'Загружаем данные…',
    'Loading interface…': 'Загружаем интерфейс…',
    'Loading sidebar configuration...':
        'Загрузка конфигурации боковой панели...',
    'Loading…': 'Загрузка…',
    'Long text': 'Длинный текст',
    'Manage groups and members': 'Управление группами и участниками',
    'Managed by node parameters': 'Задаётся параметрами ноды',
    'Many-to-many (M:N): each side can be linked to several objects on the other side.':
        'Многие ко многим (M:N): каждый объект может быть связан с несколькими объектами другой стороны.',
    'Many-to-many · M:N': 'Многие ко многим · M:N',
    'Many-to-many · new Search Type': 'Многие ко многим · новый серч-тайп',
    'Map this status to a native behavior, or explicitly change a connected process.':
        'Задайте стандартное поведение статуса или изменение связанного процесса.',
    'Marked for deletion. The column and its data will be deleted when you save.':
        'Помечено на удаление. Столбец и его данные будут удалены при сохранении.',
    'Measurements that need a fractional part.':
        'Измерения, для которых нужна дробная часть.',
    'Members and group management': 'Группы и их участники',
    'Menu action': 'Действие меню',
    'Menu actions': 'Действия меню',
    'Missing process: %1': 'Процесс отсутствует: %1',
    Modify: 'Изменение',
    'More element settings': 'Дополнительные настройки элемента',
    Name: 'Имя',
    'Name the process and choose its native type.':
        'Задайте имя процесса и выберите его тип в TACTIC.',
    'Names and short labels, up to 256 characters.':
        'Названия и короткие подписи, до 256 символов.',
    Naming: 'Нейминг',
    'Naming actions': 'Действия нейминга',
    'Naming conventions': 'Правила нейминга',
    'Naming editor': 'Редактор нейминга',
    'Naming preview': 'Превью именования',
    'Naming result': 'Результат нейминга',
    'Naming rules': 'Правила именования',
    'Native XML': 'XML TACTIC',
    'Native access rules': 'Правила доступа TACTIC',
    'Native access value: %1. It is kept until you choose a different level.':
        'Значение доступа TACTIC: %1. Оно сохранится, пока вы не выберете другой уровень.',
    'Native check-in ignores config/naming rules in admin and sthpw. Preview evaluates the expression only.':
        'Штатная сдача файлов не использует config/naming в admin и sthpw. Предпросмотр только вычисляет выражение.',
    'Native command class': 'Класс команды TACTIC',
    'Native event identifier': 'Идентификатор события TACTIC',
    'Native process settings': 'Параметры процесса TACTIC',
    'Native task status behavior.':
        'Стандартное поведение статуса задачи в TACTIC.',
    'New Search Type': 'Новый серч-тайп',
    'New naming rule': 'Новое правило нейминга',
    'New override': 'Новое переопределение',
    'New pipeline': 'Новый пайплайн',
    'New row': 'Новая строка',
    'New rule': 'Новое правило',
    Next: 'Далее',
    'No Search Type': 'Без серч-тайпа',
    'No Search Type is linked. Create a workflow from the Search Type editor.':
        'Серч-тайп не привязан. Создайте воркфлоу из редактора серч-тайпа.',
    'No Search Types found': 'Серч-тайпы не найдены',
    'No additional fields': 'Нет дополнительных полей',
    'No description': 'Без описания',
    'No explicit relationships for this type in the loaded schemas.':
        'В загруженных схемах нет явно заданных связей для этого серч-тайпа.',
    'No explicit rules in this category': 'В этой категории пока нет правил',
    'No fields found': 'Поля не найдены',
    'No login groups were loaded from the server.':
        'С сервера не загружены группы пользователей.',
    'No matching permissions or groups':
        'Подходящие права или группы не найдены',
    'No matching rules': 'Подходящих правил нет',
    'No matching targets. You can enter an identifier above.':
        'Ничего не найдено. Можно ввести код вручную выше.',
    'No naming conventions for this process.':
        'У процесса нет правил нейминга.',
    'No pipelines are linked to this Search Type':
        'У серч-тайпа нет связанных пайплайнов',
    'No rows': 'Нет записей',
    'No rule selected': 'Правило не выбрано',
    'No rules configured. Use Add rule to create one.':
        'Правил нет. Нажмите «Добавить правило».',
    'No rules for this search type': 'Для этого типа поиска нет правил',
    'No saved definitions match the filter':
        'Нет определений, подходящих под фильтр',
    'No types found': 'Типы не найдены',
    'No workflows linked to this Search Type.':
        'У типа объектов нет связанных workflows.',
    'Node type': 'Тип узла',
    'Node type: %1': 'Тип узла: %1',
    'Nodes and connections': 'Узлы и связи',
    None: 'Нет доступа',
    'Not set': 'Не задано',
    'Note created': 'Создана заметка',
    'Note created or modified': 'Заметка создана или изменена',
    'Notification content': 'Содержание уведомления',
    Notifications: 'Уведомления',
    'Number of tasks': 'Количество задач',
    'Object details': 'Карточка объекта',
    'Object identifier. This field cannot be deleted.':
        'Идентификатор объекта. Это поле нельзя удалить.',
    'Objects (including retired)': 'Объекты (включая архивные)',
    'Objects use a pipeline': 'Серч-объекты используют пайплайн',
    'Objects using this pipeline': 'Объекты с этим пайплайном',
    'One level per rule. Higher levels include lower ones; this is not a set of independent permissions.':
        'У каждого правила один уровень доступа. Более высокий уровень включает предыдущие.',
    'Only a connection to this process exists in the XML. Use Add node to recreate it with the same name, or select and remove the connection.':
        'В XML есть только ссылка на этот процесс. Добавьте ноду с таким же именем или выделите и удалите лишнюю связь.',
    'Only connected output processes are available. Add connections on the canvas first.':
        'Доступны только процессы с исходящими связями от этой ноды. Сначала добавьте связи на схеме.',
    'Only current project': 'Только текущий проект',
    'Only pipelines of the selected Search Type are listed.':
        'В списке только пайплайны выбранного серч-тайпа.',
    'Only the selected connection will be removed when you save. Its nodes and their data will not be deleted.':
        'При сохранении будет убрана только выбранная связь. Ноды и их данные не удаляются.',
    'Only the selected node and its connections will be removed from this schema when you save. The Search Type, its table, objects and pipelines will not be deleted.':
        'При сохранении из этой схемы будет убрана только выбранная нода и её связи. Серч-тайп, таблица, объекты и пайплайны не удаляются.',
    'Open a cell to edit its value. Text needs no quotes. Choose NULL or Database default explicitly in the cell editor.':
        'Откройте ячейку для редактирования. Текст вводится без кавычек. NULL и значение БД по умолчанию выбираются явно в редакторе ячейки.',
    'Open process dependencies': 'Открыть зависимости процесса',
    'Open workflow': 'Открыть воркфлоу',
    Operator: 'Оператор',
    'Optional TACTIC search expression; it replaces selection by Search Type.':
        'Необязательное выражение поиска TACTIC. Заменяет выбор по серч-тайпу.',
    'Other registrations for this table': 'Другие регистрации этой таблицы',
    'Other schemas using this type': 'Другие схемы, использующие этот тип',
    'Output condition': 'Условие выхода',
    'Output process': 'Выходной процесс',
    'Output processes': 'Следующие процессы',
    'Parent key column': 'Ключевое поле родительского объекта',
    'Permanently delete this table and all its rows? Type its full name to confirm.':
        'Безвозвратно удалить таблицу со всеми записями? Для подтверждения введите полное имя.',
    Permission: 'Разрешение',
    'Permission / Group': 'Право / Группа',
    'Permission matrix': 'Матрица прав',
    'Permission scopes': 'Области доступа',
    Pipeline: 'Пайплайн',
    'Pipeline details': 'Параметры пайплайна',
    'Pipeline settings': 'Настройки пайплайна',
    Pipelines: 'Пайплайны',
    'Pipelines and workflow': 'Пайплайны и воркфлоу',
    'Pipelines linked to this Search Type, including shared workflows.':
        'Pipelines этого типа объектов, включая общие workflows.',
    'Pipelines with processes': 'Pipeline с процессами',
    'Pipelines: %1': 'Пайплайны: %1',
    'Place on the grid': 'Разместить на сетке',
    Position: 'Позиция',
    'Positions follow shared item styles. Choose Grid in the parent container for placement by rows and columns.':
        'Позиции задаются стилями исходного item. Для размещения по строкам и столбцам выберите сетку в родительском контейнере.',
    'Preview as group': 'Предпросмотр от лица группы',
    'Preview data could not be loaded':
        'Не удалось загрузить данные для предпросмотра',
    'Preview is optional': 'Превью — по желанию',
    Previous: 'Назад',
    Priority: 'Приоритет',
    Process: 'Процесс',
    'Process action': 'Действие процесса',
    'Process dependencies': 'Зависимости процесса',
    'Process name': 'Имя процесса',
    Processes: 'Процессы',
    'Processes and connections': 'Процессы и связи',
    'Processes and tasks are enabled': 'Процессы и задачи включены',
    'Processes, dependencies and scripts': 'Процессы, зависимости и скрипты',
    'Processes: %1': 'Процессов: %1',
    'Profiles and accounts': 'Профили и учётные записи',
    Project: 'Проект',
    'Project navigation': 'Навигация проекта',
    'Project navigation and sidebar items':
        'Навигация проекта и элементы боковой панели',
    'Project schema': 'Схема проекта',
    'Project-specific rules are preserved. Select a rule to edit its native attributes.':
        'Правила для отдельных проектов сохраняются. Выберите правило для настройки его атрибутов.',
    'Project: %1 · Table: %2': 'Проект: %1 · Таблица: %2',
    Projects: 'Проекты',
    'Projects, entities, processes and interface':
        'Проекты, серч-объекты и интерфейс',
    Queued: 'В очереди',
    'Raw SQL bypasses object validation, triggers and undo history. Changes can break the application.':
        'Прямой SQL обходит проверки объектов, триггеры и историю отмены. Изменения могут нарушить работу приложения.',
    'Raw database': 'Raw-редактор базы',
    'Raw table rows': 'Строки таблицы базы данных',
    Read: 'Чтение',
    'Read-only': 'Только чтение',
    'Read-only preview. Changes have not been saved.':
        'Предпросмотр без редактирования. Изменения ещё не сохранены.',
    'Ready to create': 'Всё готово к созданию',
    Recipients: 'Получатели',
    'Refreshing server metadata…': 'Обновляю данные проекта…',
    'Registered Search Types': 'Зарегистрированные типы объектов',
    'Related object expression': 'Выражение поиска связанных объектов',
    'Related objects': 'Связанные объекты',
    'Related pipeline': 'Связанный пайплайн',
    'Related process': 'Связанный процесс',
    'Related workflow': 'Связанный воркфлоу',
    Relationship: 'Связь',
    'Relationship in schema: %1': 'Тип связи в схеме: %1',
    'Relationship in schema: {kind}': 'Тип связи в схеме: {kind}',
    'Relationship map': 'Карта связей',
    'Relationship map for {name}': 'Карта связей для {name}',
    'Relationship type': 'Тип связи',
    'Relationships between entities': 'Связи между серч-тайпами',
    "Relationships come from this project's schema and inherited schemas, not from table names.":
        'Связи взяты из схемы проекта и унаследованных схем, а не определены по именам таблиц.',
    Reload: 'Обновить',
    'Reload columns from server': 'Обновить столбцы с сервера',
    'Reload from server': 'Обновить с сервера',
    'Reload naming rules': 'Обновить правила нейминга',
    'Reload sidebar': 'Обновить боковую панель',
    Remove: 'Удалить',
    'Remove draft field {name}': 'Убрать поле {name} из черновика',
    'Remove from canvas': 'Убрать со схемы',
    'Remove from canvas?': 'Убрать со схемы?',
    'Remove rule': 'Удалить правило',
    'Remove staged field': 'Убрать новое поле',
    'Remove the selection from the schema draft? Search Types, tables and data will be kept.':
        'Удалить выбранное из черновика схемы? Типы, таблицы и данные сохранятся.',
    'Remove the selection from this workflow draft?':
        'Удалить выбранные элементы из черновика workflow?',
    'Remove this element and its children?':
        'Удалить этот элемент вместе с дочерними?',
    'Remove this rule from the draft?': 'Удалить правило из черновика?',
    'Remove this rule?': 'Удалить правило?',
    'Required by TACTIC. This field cannot be deleted.':
        'Служебное поле TACTIC. Это поле нельзя удалить.',
    'Reset canvas view': 'Сбросить вид схемы',
    'Reset color': 'Сбросить цвет',
    'Resolve the native TACTIC view again':
        'Заново разрешить нативное представление TACTIC',
    'Resolved preview': 'Предпросмотр итоговой компоновки',
    'Restore direct connection': 'Вернуть прямую связь',
    'Restore row': 'Восстановить строку',
    'Restrictions change which Search Objects are returned. They do not grant access.':
        'Ограничивают результаты поиска, но сами по себе не дают доступа.',
    Retired: 'Архивные',
    Retry: 'Повторить',
    'Reverse connection': 'Развернуть связь',
    Row: 'Строка',
    'Row {row}, column {column}': 'Строка {row}, столбец {column}',
    'Rule details': 'Параметры правила',
    'Rule project': 'Проект правила',
    "Rules whose context starts with this process. Edit naming in the Search Type's existing Naming Editor.":
        'Правила, контекст которых начинается с имени этого процесса. Настроить нейминг можно в редакторе серч-тайпа.',
    'Run custom naming code? This uses the normal server environment, not an isolated sandbox. Scripts and classes can change data or files.':
        'Запустить пользовательский код нейминга? Он выполняется в обычной серверной среде, без изоляции. Скрипты и классы могут изменять данные и файлы.',
    SAVE: 'СОХРАНИТЬ',
    'Same transaction': 'В той же транзакции',
    'Sandbox directory naming': 'Именование папки sandbox',
    Save: 'Сохранить',
    'Save naming rule': 'Сохранить правило нейминга',
    'Save process rules on the server? Global rules also affect same-name processes in other pipelines. Removed rules will be deleted; their scripts are kept. Actions and notifications are not executed by Save.':
        'Сохранить правила процесса на сервере? Общие правила затронут одноимённые процессы в других пайплайнах. Удалённые из списка правила будут удалены с сервера, но их скрипты сохранятся. Сохранение не запускает действия и не отправляет уведомления.',
    'Save process rules? Global rules affect matching processes in other pipelines. Removed rules are deleted; their scripts are kept. Actions are not executed by Save.':
        'Сохранить правила? Глобальные правила влияют на подходящие процессы других pipelines. Удалённые правила будут стёрты, их скрипты сохранятся. Действия при сохранении не запускаются.',
    'Save rules': 'Сохранить правила',
    'Save sidebar changes before opening this search and its quick filters.':
        'Сначала сохраните изменения сайдбара, затем откройте поиск или его быстрые фильтры.',
    'Save the schema and create its new instance tables and missing key columns? Existing columns and values will be kept.':
        'Сохранить схему и создать новые таблицы связей и недостающие ключевые колонки? Существующие колонки и значения будут сохранены.',
    'Save to server': 'Сохранить на сервер',
    'Saved definitions': 'Сохранённые определения',
    'Saving configures the trigger. It does not run the action.':
        'Сохранение настраивает триггер, но не запускает действие.',
    'Saving creates the registry entry, database table and default views in the selected project.':
        'Сохранение создаёт запись реестра, таблицу базы данных и стандартные представления в выбранном проекте.',
    'Saving...': 'Сохранение...',
    'Schema relationships': 'Связи в схеме',
    'Schema relationships: %1': 'Связей в схеме: %1',
    'Schema relationships: {count}': 'Связей в схеме: {count}',
    'Schema: %1': 'Схема: %1',
    'Schema: {name}': 'Схема: {name}',
    Scope: 'Область действия',
    'Script body': 'Код скрипта',
    'Script language': 'Язык скрипта',
    'Script path (optional)': 'Путь скрипта (необязательно)',
    'Search Object or operation': 'Серч-объект или операция',
    'Search Objects': 'Серч-объекты',
    'Search Objects (including retired): %1':
        'Серч-объектов (включая retired): %1',
    'Search Objects without a workflow': 'Серч-объекты без воркфлоу',
    'Search Type': 'Серч-тайп',
    'Search Type identifier': 'Идентификатор серч-тайпа',
    'Search Type image': 'Превью серч-тайпа',
    'Search Type saved, but its preview could not be queued: {error}':
        'SearchType сохранён, но изображение не удалось отправить в очередь: {error}',
    'Search Type sections': 'Разделы типа объектов',
    'Search Type: %1': 'Серч-тайп: %1',
    'Search Types': 'Серч-тайпы',
    'Search Types catalog': 'Каталог типов объектов',
    'Search and quick filters': 'Поиск и быстрые фильтры',
    'Search restrictions': 'Ограничения поиска',
    'Select Search Type': 'Выберите Search Type',
    'Select a Search Type or create one.':
        'Выберите тип объектов или создайте новый.',
    'Select a Search Type to edit its appearance and fields. Changes stay in your draft until you save.':
        'Выберите серч-тайп для настройки вида и полей. До сохранения изменения остаются в черновике.',
    'Select a Search Type to edit its properties and fields. Changes stay in your draft until you save.':
        'Выберите тип объектов для настройки свойств и полей. Правки остаются в черновике до сохранения.',
    'Select a connection to choose its relationship type and key columns. Many-to-many creates an instance node in the draft.':
        'Выберите соединение для настройки типа связи и ключевых столбцов. Many-to-many добавляет связующую ноду в черновик.',
    'Select a definition': 'Выберите определение',
    'Select a node or a connection': 'Выберите узел или связь',
    'Select a process on the canvas': 'Выберите процесс на графе',
    'Select a project': 'Выберите проект',
    'Select a project to edit layouts.':
        'Выбери проект для настройки компоновок.',
    'Select a rule': 'Выберите правило',
    'Select a rule or create a new one.':
        'Выберите правило или создайте новое.',
    'Select a sidebar element first': 'Сначала выберите элемент боковой панели',
    'Select an element or add a new widget.':
        'Выбери элемент или добавь новый виджет.',
    'Select an element to edit it. Groups hold other elements.':
        'Выбери элемент для настройки. Группы содержат другие элементы.',
    'Select an existing server script. Its source remains in the Script Editor.':
        'Выберите существующий серверный скрипт. Его код редактируется в редакторе скриптов.',
    'Select an item in the preview to edit it, or add a new link or section.':
        'Выберите элемент в предпросмотре или добавьте новую ссылку либо раздел.',
    'Select any rule to edit its native attributes, including custom scopes.':
        'Выберите правило для изменения атрибутов, в том числе пользовательской области.',
    'Select multiple nodes': 'Выбрать несколько узлов',
    'Select multiple processes': 'Выбрать несколько процессов',
    'Select the login groups allowed to see this sidebar item. The group preview uses these draft permissions immediately.':
        'Выберите группы, которым разрешено видеть этот пункт. Предпросмотр для группы сразу учитывает эти права из черновика.',
    'Selected document': 'Выбранный документ',
    'Selected element': 'Выбранный элемент',
    'Selected element XML': 'XML выбранного элемента',
    Selection: 'Выбранное',
    'Separate process, background': 'Отдельный процесс, в фоне',
    'Separate process, blocking': 'Отдельно, с ожиданием',
    'Separate process, non-blocking': 'Отдельно, без ожидания',
    'Separate process, wait': 'Отдельный процесс, с ожиданием',
    Separator: 'Разделитель',
    'Server command class': 'Класс серверной команды',
    'Server script': 'Серверный скрипт',
    'Set actual task date': 'Задать фактическую дату задачи',
    'Shared TACTIC login groups and their members':
        'Общие группы пользователей TACTIC и их участники',
    'Shared data outside the selected project':
        'Общие данные вне выбранного проекта',
    'Shared pipeline: read-only. Create a project-owned pipeline to make project-specific changes.':
        'Общий пайплайн: только чтение. Для настроек отдельного проекта создайте его собственный пайплайн.',
    'Shared · read-only': 'Общий · только чтение',
    'Short text': 'Короткий текст',
    'Show on canvas': 'Показать на схеме',
    'Show properties': 'Показать свойства',
    'Show workflow list': 'Показать список воркфлоу',
    'Shown on the canvas without changing the process name.':
        'Название на схеме без изменения имени процесса.',
    'Sidebar Editor': 'Редактор боковой панели',
    'Sidebar has unsaved changes':
        'В боковой панели есть несохранённые изменения',
    'Sidebar is up to date': 'Боковая панель актуальна',
    'Sidebar items': 'Пункты сайдбара',
    'Sidebar link': 'Ссылка сайдбара',
    'Sidebar links': 'Ссылки сайдбара',
    Signal: 'Событие',
    'Some connections refer to missing processes. Add the processes or remove those connections before saving.':
        'Некоторые связи ссылаются на отсутствующие процессы. Добавьте процессы или удалите связи перед сохранением.',
    Source: 'Исходник',
    'Source XML': 'Исходный XML',
    'Standard fields': 'Стандартные поля',
    'Start from a template or copy this view. Give your view a unique name.':
        'Выбери заготовку или скопируй текущий вид. Задай новому виду уникальное имя.',
    'Status behavior': 'Поведение статуса',
    'Stored in the selected project': 'Данные хранятся в выбранном проекте',
    'Subgroups, separated by |': 'Подгруппы через |',
    Subject: 'Тема',
    Submenu: 'Подменю',
    Subpipeline: 'Вложенный пайплайн',
    Summary: 'Сводка',
    'Supervisor group': 'Группа супервайзеров',
    'TACTIC creates these columns automatically when you save the new Search Type. Do not add them again below; the draft list is only for extra fields.':
        'TACTIC создаст эти столбцы автоматически при сохранении нового серч-тайпа. Повторно добавлять их ниже не нужно: список черновика предназначен только для дополнительных полей.',
    'TACTIC creates these fields automatically. Add only extra fields below.':
        'TACTIC создаёт эти поля автоматически. Ниже добавляйте только дополнительные поля.',
    'TACTIC expressions are supported in recipients, subject and body. Saving does not send a notification.':
        'В получателях, теме и тексте поддерживаются выражения TACTIC. При сохранении уведомление не отправляется.',
    'TACTIC identifiers and widget options. For normal setup, use Item.':
        'Идентификаторы TACTIC и параметры виджетов. Для обычной настройки используйте вкладку «Пункт».',
    'TACTIC sidebar': 'Сайдбар TACTIC',
    'TACTIC will create the Search Type, its table and a schema node on the server. Other unsaved canvas changes remain in your draft; save the schema separately to apply them.':
        'TACTIC создаст серч-тайп, его таблицу и ноду схемы на сервере. Остальные изменения канваса останутся в черновике — для их применения сохраните схему отдельно.',
    'TACTIC-HANDLER  ·  ADMIN': 'TACTIC-HANDLER  ·  АДМИНКА',
    'TH sidebar': 'Сайдбар TH',
    Table: 'Таблица',
    'Table %1.%2 is missing. This Search Type is still referenced by the schema. Check the table on the server or correct the connection, then reload columns. No table is created automatically.':
        'Таблица %1.%2 отсутствует, но схема всё ещё ссылается на этот серч-тайп. Проверьте таблицу на сервере или исправьте связь, затем обновите столбцы. Таблица не создаётся автоматически.',
    'Table views and columns': 'Варианты таблицы и колонки',
    Target: 'Объект',
    'Target status': 'Целевой статус',
    'Task assignee changed': 'Изменён исполнитель задачи',
    'Task settings': 'Настройки задач',
    'Task status changed': 'Изменён статус задачи',
    'Task status workflow': 'Воркфлоу статусов задач',
    'Task status workflows': 'Статусы задач',
    'Task statuses': 'Статусы задач',
    'Technical settings': 'Технические настройки',
    'The built-in system schema is read-only':
        'Встроенная системная схема доступна только для чтения',
    'The change is staged until Save. Processes used by tasks, snapshots or triggers cannot be removed on the server.':
        'Изменение применится после сохранения. Нельзя удалить процесс, который используется задачами, снапшотами или триггерами.',
    'The code is stored with this process. Applying the draft does not run it.':
        'Код сохраняется с процессом. Применение черновика не запускает скрипт.',
    'The color of the entire pipeline, independent of its process colors.':
        'Цвет всего пайплайна, независимо от цветов отдельных процессов.',
    'The database table for {type} is absent. No table is created by reading columns.':
        'Таблица базы данных для {type} отсутствует. Чтение списка колонок не создаёт таблицу.',
    'The database table is missing. Check the server schema before editing.':
        'Таблица базы данных отсутствует. Проверьте схему сервера перед редактированием.',
    'The image belongs to the Search Type itself, not to one of its Search Objects. Saving adds the replacement to Commit Queue.':
        'Изображение относится к самому серч-тайпу, а не к одному из его объектов. При сохранении новое превью добавится в очередь отправки.',
    'The image belongs to the Search Type itself. Saving sends the replacement through Commit Queue.':
        'Изображение относится к самому SearchType. При сохранении замена отправляется через очередь сдачи файлов.',
    'The installed Python command that handles this action.':
        'Установленная на сервере Python-команда, которая выполняет это действие.',
    'The language used by the native server handler.':
        'Язык, который использует серверный обработчик TACTIC.',
    'The layout editor could not be loaded. Connect to TACTIC Stream and try again.':
        'Не удалось загрузить редактор. Подключись к TACTIC Stream и повтори попытку.',
    'The native document for this canvas. Unknown elements and attributes are preserved.':
        'Документ графа в формате TACTIC. Дополнительные элементы и атрибуты сохраняются.',
    'The native workflow signal sent to the related process.':
        'Событие воркфлоу TACTIC, отправляемое в связанный процесс.',
    'The pipeline name shown to other users.':
        'Название пайплайна, которое видят другие пользователи.',
    'The process to signal or listen to; leave empty to use the native default.':
        'Процесс для отправки или отслеживания событий. Пустое значение использует правило TACTIC по умолчанию.',
    'The related objects affected by this node.':
        'Тип связанных объектов, с которыми работает нода.',
    'The rule will be removed from the server when you save. The script itself is not deleted.':
        'Правило удалится с сервера после сохранения. Сам скрипт удалён не будет.',
    'The saved search defines the starting query. Quick filters refine it in the same search tab and use this item’s own defaults.':
        'Сохранённый поиск задаёт исходный запрос. Быстрые фильтры уточняют его в той же вкладке и используют настройки этого пункта.',
    'The selected nodes and their connections will be removed from the canvas when you save. Server data is not deleted.':
        'При сохранении выделенные ноды и их связи будут убраны с канваса. Серверные данные не удаляются.',
    'The selected preview will be added through Commit Queue after creation.':
        'После создания выбранное превью будет добавлено через очередь отправки.',
    'The shared Search Type registration is kept for other projects, as in TACTIC.':
        'Общая регистрация серч-тайпа сохранится для других проектов, как в TACTIC.',
    'The shared Search Type registration is retained for other projects.':
        'Общая регистрация SearchType сохраняется для других проектов.',
    'These changes will be saved on the server and will affect other users of the project.':
        'Изменения сохранятся на сервере и затронут других пользователей проекта.',
    'These fields exist only in your draft. Save creates them; removing a draft field does not change the database.':
        'Эти поля существуют только в черновике. Сохранение создаст их; удаление поля из черновика не меняет базу.',
    'These fields exist only in your draft. Save to server creates them; removing a draft field does not change the database.':
        'Эти поля пока только в черновике. Они появятся в базе после сохранения на сервер. Удаление поля из черновика не меняет базу.',
    'These native group settings participate in every access check, together with explicit rules and other memberships.':
        'TACTIC учитывает эти параметры при каждой проверке доступа, вместе с правилами и участием в других группах.',
    'These pipelines are linked to this Search Type on the server. Open one to edit its processes, task settings, groups, dependencies and scripts.':
        'Эти пайплайны связаны с серч-тайпом на сервере. Откройте нужный, чтобы настроить процессы, параметры задач, группы, зависимости и скрипты.',
    'These settings belong to the whole pipeline. Select a node on the canvas to configure its process and task statuses.':
        'Эти настройки относятся ко всему пайплайну. Выберите ноду на холсте для настройки процесса и статусов задач.',
    'These settings belong to the whole pipeline. Select a node on the canvas to configure that process and its task statuses.':
        'Настройки всего пайплайна. Выберите ноду на канвасе, чтобы настроить процесс и статусы его задач.',
    'This Search Type has no pipeline_code field. A pipeline association alone does not add it.':
        'У серч-тайпа нет поля pipeline_code. Привязка пайплайна сама по себе его не создаёт.',
    'This Search Type is in use. Remove its objects and dependencies before deleting it.':
        'SearchType используется. Перед удалением удалите его объекты и зависимости.',
    'This Search Type is registered, but its database table (%1.%2) is absent. Fields and Search Objects cannot be loaded. Editing is disabled; no table will be created automatically.':
        'Этот серч-тайп зарегистрирован, но его таблица в базе (%1.%2) отсутствует. Поля и серч-объекты загрузить нельзя. Редактирование отключено; таблица не будет создана автоматически.',
    'This count is for the pipeline, not the number of tasks in this process.':
        'Показаны объекты пайплайна, а не количество задач этого процесса.',
    'This deletes the empty table, empty pipelines and the node with its connections in this project. This editor cannot undo the deletion. Check scripts, naming rules and saved searches that refer to this type.':
        'Будут удалены пустая таблица, пустые пайплайны и нода с её связями в этом проекте. Отменить удаление в редакторе нельзя. Проверьте скрипты, правила нейминга и сохранённые поиски, ссылающиеся на этот тип.',
    'This draft is not selected for these parameters by native naming lookup.':
        'Штатный поиск нейминга не выбирает этот черновик при заданных параметрах.',
    'This endpoint is inherited or implicit. Add the registered Search Type to this canvas to position it locally.':
        'Этот узел унаследован или задан неявно. Добавьте зарегистрированный тип на схему, чтобы задать его положение в этом проекте.',
    'This group has no sidebar items': 'Для этой группы в сайдбаре нет пунктов',
    'This is a draft. The instance table and its key columns will be created only when you save the schema.':
        'Это черновик. Связующая таблица и её ключевые столбцы появятся на сервере только после сохранения схемы.',
    'This is a link table for a many-to-many relationship, not a separate object category.':
        'Это связующая таблица для связи «многие ко многим», а не отдельная категория объектов.',
    'This is how the new Search Type will appear. Nothing has been created on the server yet.':
        'Так будет выглядеть новый серч-тайп. На сервере пока ничего не создано.',
    'This pipeline': 'Этот пайплайн',
    'This process': 'Этот процесс',
    'This process is referenced by a connection but is missing from the pipeline.':
        'Связь ссылается на процесс, которого нет в pipeline.',
    'This sidebar has no items': 'В боковой панели нет элементов',
    'This trigger is generated by the workflow engine. Edit its action or progress listener in the node parameters, not in a second copy here.':
        'Этот триггер создан движком воркфлоу. Его действие или отслеживание прогресса настраивается в параметрах ноды — здесь показана та же запись, а не отдельная копия.',
    'This type has no pipeline_code field. Add it in Fields to assign workflows to its objects.':
        'У типа нет поля pipeline_code. Добавьте его в «Поля», чтобы назначать workflow объектам.',
    'This type is referenced by a connection. Add its registered node to the canvas to move it.':
        'На этот тип ссылается связь. Добавьте зарегистрированный узел на схему, чтобы перемещать его.',
    Title: 'Заголовок',
    'To (parent)': 'К (родительский)',
    'Today, 14:30': 'Сегодня, 14:30',
    'Totals include retired Search Objects. Shared system types are counted in their own database. Reload to update the summary.':
        'В подсчёт входят архивные серч-объекты. Общие системные типы считаются в своей базе данных. Обновите данные, чтобы актуализировать сводку.',
    'Trigger execution mode': 'Режим выполнения триггера',
    Triggers: 'Триггеры',
    'Triggers, notifications, naming conventions and objects using this pipeline. Save node changes before editing dependencies.':
        'Триггеры, уведомления, нейминг и объекты пайплайна. Перед настройкой зависимостей сохраните изменения ноды.',
    "Types stored in the selected project's database, regardless of their namespace. Turn off to include shared system types.":
        'Серч-тайпы, данные которых хранятся в базе выбранного проекта, независимо от префикса. Снимите галочку, чтобы видеть и общие системные типы.',
    'Undo field deletion': 'Отменить удаление поля',
    'Unsaved changes': 'Несохранённые изменения',
    Unspecified: 'Не указано',
    'Up to %1 characters': 'До %1 символов',
    'Up to {count} characters': 'До {count} символов',
    'Update project naming rule? This changes future check-ins in the current project. Existing files are kept.':
        'Обновить правило нейминга проекта? Изменится нейминг будущих сдач файлов в этом проекте. Существующие файлы сохраняются.',
    'Use Create workflow above. The new pipeline will already be linked to this Search Type.':
        'Нажмите «Создать воркфлоу» выше. В новом пайплайне уже будет выбран этот серч-тайп.',
    'Use Source XML or create a view from a layout template.':
        'Используйте исходный XML или создайте вид из заготовки.',
    'Use TACTIC default': 'По умолчанию в TACTIC',
    'Use a script or an installed server command class.':
        'Используйте скрипт или класс команды, установленной на сервере.',
    'Use an existing server script, or provide a script body below.':
        'Укажите существующий серверный скрипт или введите его код ниже.',
    'Use inherited rule': 'Наследовать правило',
    'Use the execution mode supported by the installed server handler.':
        'Укажите режим выполнения, который поддерживает установленный серверный обработчик.',
    'Use the native event template on save':
        'При сохранении взять шаблон события из TACTIC',
    'Use these settings for shared item styles, nested widgets or direct XML editing.':
        'Здесь настраиваются стили исходного item, вложенные виджеты и XML.',
    'Used by a schema relationship. Change the relationship before deleting this field.':
        'Поле используется в связи схемы. Сначала измените связь, затем удаляйте поле.',
    'Used for this process on the canvas and in task views.':
        'Цвет процесса на схеме и в списках задач.',
    'Used in lists and the project schema. Reset to use the theme color.':
        'Цвет в списках и на схеме проекта. Сброс возвращает цвет темы.',
    'Used when no status mapping is selected.':
        'Используется, если соответствие статусу не выбрано.',
    'User directory': 'Все пользователи',
    Users: 'Пользователи',
    Value: 'Значение',
    Version: 'Версия',
    Versionless: 'Без номера версии',
    'View root': 'Корень вида',
    'Visible in navigation': 'Показывать в навигации',
    'Wait for a completion signal instead of completing this node immediately.':
        'Дождаться события завершения, а не завершать ноду сразу.',
    'Wait for completion': 'Ожидать завершения',
    'Wheel: zoom · Middle-button drag: pan':
        'Колесо — масштаб · Зажатая средняя кнопка — панорама',
    'Wheel: zoom. Middle-button drag: pan. Shift/Ctrl-click or drag a frame to select nodes.':
        'Колесо — масштаб. Зажатая средняя кнопка — панорама. Shift/Ctrl-клик или рамка — выделение нод.',
    'Who can see this item': 'Кому доступен пункт',
    'Whole number': 'Целое число',
    Width: 'Ширина',
    Workflow: 'Воркфлоу',
    'Workflow catalog tools': 'Инструменты списка воркфлоу',
    'Workflow editor': 'Редактор воркфлоу',
    Workflows: 'Рабочие процессы',
    'Working on the server…': 'Выполняется на сервере…',
    XML: 'XML',
    'Yes / No': 'Да / Нет',
    'You can choose an image now. After the Search Type is created, its preview will be sent through Commit Queue.':
        'Можно выбрать картинку сразу. После создания серч-тайпа превью загрузится через очередь отправки.',
    'Zoom in': 'Увеличить',
    'Zoom level': 'Масштаб',
    'Zoom out': 'Уменьшить',
    'pipeline_code will also be created: pipeline support is enabled.':
        'Также будет создано поле pipeline_code: поддержка пайплайна включена.',
    'pipeline_code will not be created: pipeline support is disabled.':
        'Поле pipeline_code не будет создано: поддержка пайплайна выключена.',
    '{count} processes': 'Процессов: {count}',
    'Enter a valid value for the column type.':
        'Введите допустимое значение для типа колонки.',
    'Access rules saved on server': 'Правила доступа сохранены на сервере',
    'No rules match the search': 'Подходящих правил нет',
    'Select a rule to edit': 'Выберите правило',
    'Find a target': 'Найти объект',
    'Selected rule JSON': 'Атрибуты правила JSON',
    'Inherited rules': 'Наследуемые правила',
    'Discard text': 'Сбросить текст',
    Subgroups: 'Подгруппы',
    'The save result is unknown. Reload access rules before trying again.':
        'Результат сохранения неизвестен. Загрузите правила доступа заново перед повторной попыткой.',
    'Changes apply to the draft. Save to server to publish them.':
        'Изменения остаются в черновике. Сохраните на сервер, чтобы применить их.',
    'Value mode': 'Режим значения',
    'Database default': 'Значение БД по умолчанию',
    'Cell value': 'Значение ячейки',
    'Delete item': 'Удалить элемент',
    'Sidebar Editor help': 'Справка редактора сайдбара',
    'Sidebar preview width': 'Ширина предпросмотра сайдбара',
    'Preview group': 'Предпросмотр для группы',
    'Move up': 'Переместить вверх',
    'Move down': 'Переместить вниз',
    'Apply XML': 'Применить XML',
    'Item type': 'Тип элемента',
    'A link opens a search, a section groups links, and a separator divides the list.':
        'Ссылка открывает поиск, раздел объединяет ссылки, разделитель отделяет пункты списка.',
    'Internal name': 'Внутреннее имя',
    'The stable identifier for this sidebar item and its quick-filter defaults. Change the title for a visual rename.':
        'Постоянный идентификатор пункта и его быстрых фильтров. Для изменения видимой подписи меняйте заголовок.',
    'Child view': 'Дочерний вид',
    "The SideBarWdg view containing this section's links.":
        'Представление SideBarWdg, в котором хранятся ссылки раздела.',
    'Icon name': 'Имя иконки',
    'The server icon identifier. You can also choose an icon on the Item page.':
        'Идентификатор иконки на сервере. Выбрать иконку из библиотеки можно на странице «Пункт».',
    'Widget Type': 'Тип виджета',
    'The TACTIC web widget used by this link.':
        'Веб-виджет TACTIC, используемый этой ссылкой.',
    'Class Path': 'Путь к классу',
    'The Python class registered for this TACTIC widget.':
        'Класс Python, зарегистрированный для этого виджета TACTIC.',
    'The server view used to render the selected TACTIC widget.':
        'Представление сервера для отображения выбранного виджета TACTIC.',
    'A short, recognizable name in the sidebar.':
        'Короткое и понятное название в сайдбаре.',
    'Click the icon to choose from the searchable library.':
        'Нажмите на иконку, чтобы выбрать другую. В библиотеке есть поиск.',
    'Hide this item without deleting its settings.':
        'Скрыть пункт, не удаляя его настройки.',
    "The saved search defines the starting query. Quick filters refine it in the same search tab and use this item's own defaults.":
        'Преднастроенный поиск задаёт исходный запрос. Быстрые фильтры уточняют его в той же вкладке и используют отдельные настройки этого пункта.',
    'Which project objects this item opens.':
        'Какие объекты проекта открывает этот пункт.',
    'Predefined search': 'Преднастроенный поиск',
    'Choose a saved query or leave the list unfiltered.':
        'Выберите сохранённый запрос или оставьте список без фильтрации.',
    'No predefined search': 'Без преднастроенного поиска',
    'Configure search': 'Настроить поиск',
    'Default item view': 'Представление элементов по умолчанию',
    'The initial presentation when this search tab is opened.':
        'В каком виде показывать объекты при открытии вкладки.',
    'Workspace layout': 'Компоновка рабочего пространства',
    'Apply a saved dock arrangement when this sidebar item opens.':
        'Применять сохранённое расположение доков при открытии этого пункта сайдбара.',
    'Do not change workspace layout':
        'Не менять компоновку рабочего пространства',
    'Script shelf': 'Шелф скриптов',
    'Show this shared shelf when the sidebar tab is active.':
        'Показывать этот общий шелф, когда активен данный таб сайдбара.',
    'Project default shelf': 'Общий шелф проекта',
    'Collapse section': 'Свернуть раздел',
    'Expand section': 'Развернуть раздел',
    'Saved definitions panel width': 'Ширина списка определений',
    'Definition XML': 'XML определения',
    'Columns list height': 'Высота списка колонок',
    'Native field identifier.': 'Нативный идентификатор поля.',
    'The column heading shown to users.':
        'Заголовок колонки, который видят пользователи.',
    'Show in table': 'Показывать в таблице',
    'Keep the column in this saved view.':
        'Оставить колонку в этом сохранённом представлении.',
    'Default width in the table view.':
        'Ширина по умолчанию в табличном представлении.',
    'Display widget': 'Виджет отображения',
    'Choose a supported TACTIC table widget.':
        'Выберите поддерживаемый табличный виджет TACTIC.',
    'This TACTIC view has no columns. Add elements in XML mode.':
        'В этом представлении TACTIC нет колонок. Добавьте элементы в режиме XML.',
    'This definition does not use a native TACTIC table layout. Open XML to edit its exact structure.':
        'Это определение не использует нативную табличную компоновку TACTIC. Откройте XML для редактирования точной структуры.',
    'Open XML': 'Открыть XML',
    'Server error': 'Ошибка сервера',
    'Discard unsaved sidebar changes?':
        'Отменить несохранённые изменения бокового меню?',
    'Columns list width': 'Ширина списка колонок',
    '*': '*',
    '1. Details': '1. Параметры',
    '2. Fields': '2. Поля',
    '3. Ready': '3. Подтверждение',
    'A column with this name already exists':
        'Поле с таким именем уже существует',
    'A login is required': 'Укажите логин',
    'A native TACTIC expression evaluated on the object and snapshot.':
        'Штатное выражение TACTIC, вычисляемое для объекта и снимка.',
    'A technical name: lowercase Latin letters, numbers and underscores. No spaces; start with a letter.':
        'Техническое имя: строчные латинские буквы, цифры и подчёркивания. Без пробелов; начинается с буквы.',
    'A user with this login already exists':
        'Пользователь с таким логином уже существует',
    Access: 'Доступ',
    Account: 'Аккаунт',
    'Add field': 'Добавить поле',
    Address: 'Адрес',
    'An existing login cannot be changed':
        'Логин существующего аккаунта нельзя изменить',
    Auto: 'Авто',
    'Base directory alias': 'Псевдоним базовой папки',
    Button: 'Кнопка',
    Changes: 'Изменения',
    'Check the people who belong to this group':
        'Отметьте участников этой группы',
    'Check-in type': 'Тип Check-in',
    'Choose image': 'Выбрать изображение',
    'Class name': 'Имя класса',
    'Column names must be unique lowercase SQL identifiers':
        'Имена полей должны быть уникальными SQL-идентификаторами в нижнем регистре.',
    Condition: 'Условие',
    'Confirm save': 'Подтвердить сохранение',
    'Create user': 'Создать пользователя',
    'Current versionless': 'Текущий versionless',
    'Decrease width': 'Уменьшить ширину',
    'Default group': 'Группа по умолчанию',
    Department: 'Отдел',
    'Discard unsaved group changes?':
        'Отменить несохранённые изменения группы?',
    'Discard unsaved user changes?':
        'Отменить несохранённые изменения пользователя?',
    'Display name': 'Отображаемое имя',
    'Edit group membership': 'Изменить группы',
    Email: 'Электронная почта',
    'Empty matches any snapshot type.':
        'Пустое поле соответствует любому типу снимка.',
    'Enter a Search Type title': 'Введите название типа объектов.',
    'Enter a group identifier': 'Введите идентификатор группы',
    'Enter a login without spaces or slashes':
        'Введите логин без пробелов и слешей',
    'Evaluate naming': 'Проверить нейминг',
    'Evaluate with custom code': 'Проверить с пользовательским кодом',
    'Example file': 'Пример файла',
    'Existing server script overriding directory and file naming.':
        'Существующий серверный скрипт, заменяющий нейминг каталога и файла.',
    'First name': 'Имя',
    Grid: 'Сетка',
    'Group details': 'Параметры группы',
    'Group details changed. Reload before saving.':
        'Настройки группы изменились. Обновите данные перед сохранением.',
    'Group identifier': 'Идентификатор группы',
    "Group membership changes affect this user's permissions.":
        'Изменение групп влияет на права пользователя.',
    'Group saved on server': 'Группа сохранена на сервере',
    Heading: 'Заголовок',
    'Hourly wage': 'Ставка в час',
    'Hourly wage must be a non-negative number':
        'Почасовая ставка должна быть неотрицательным числом',
    Icon: 'Иконка',
    'Increase width': 'Увеличить ширину',
    'Ingest rule code': 'Код правила импорта',
    'Input — connect here': 'Вход — подключить сюда',
    'Installed naming class implementing get_dir and get_file.':
        'Установленный класс нейминга с методами get_dir и get_file.',
    'Invalid account status': 'Некорректный статус учётной записи',
    'Invalid password or user groups': 'Некорректный пароль или список групп',
    'Invalid user document': 'Некорректные данные пользователя',
    'Invalid user profile field': 'Некорректное поле профиля пользователя',
    Item: 'Пункт',
    Label: 'Подпись',
    'Last name': 'Фамилия',
    'Latest versionless': 'Последний versionless',
    'Leave empty to keep the current password':
        'Оставьте пустым, чтобы сохранить текущий пароль',
    'License type': 'Тип лицензии',
    Link: 'Ссылка',
    'Local rule simulation': 'Локальный предпросмотр',
    Login: 'Логин',
    'Manual version': 'Версия вручную',
    Members: 'Участники',
    'Members: {count}': 'Участников: {count}',
    'Membership changes apply on the server. Sidebar visibility rules are configured separately for each sidebar item.':
        'Состав групп сохраняется на сервере. Права видимости настраиваются отдельно для каждого пункта сайдбара.',
    'Missing process': 'Процесс отсутствует',
    NULL: 'NULL',
    'Name, login or email': 'Имя, логин или почта',
    Namespace: 'Пространство имён',
    'Naming rule': 'Правило нейминга',
    'New group': 'Новая группа',
    'New user': 'Новый пользователь',
    'New · many-to-many': 'Новый · многие ко многим',
    'No pipeline': 'Без пайплайна',
    'No user groups yet': 'Групп пользователей пока нет',
    'No users match the search': 'Пользователи не найдены',
    Number: 'Номер',
    'Open Commit Queue': 'Открыть очередь сдачи файлов',
    'Optional ingest rule associated with this naming rule.':
        'Необязательное правило импорта, связанное с правилом нейминга.',
    'Output — connect here': 'Выход — соединить здесь',
    Password: 'Пароль',
    'Phone number': 'Номер телефона',
    Preview: 'Превью',
    'Preview context': 'Контекст превью',
    Profile: 'Профиль',
    'Project code': 'Код проекта',
    'Project: {project}': 'Проект: {project}',
    'Repository alias used by native check-in.':
        'Алиас репозитория для штатной сдачи файлов.',
    'Retired user': 'Архивный · retired',
    "Retiring keeps this user's history. Clear this option to reactivate the account, then save.":
        'При переносе в архив история пользователя сохраняется. Снимите отметку и сохраните, чтобы вернуть учётную запись из архива.',
    'Rule context (empty means any)': 'Контекст правила (пусто — любой)',
    'Sandbox directory alias': 'Псевдоним папки sandbox',
    'Sandbox repository alias used by native check-in.':
        'Алиас рабочего репозитория для штатной сдачи файлов.',
    'Save or discard user changes before leaving.':
        'Сохраните или отмените изменения пользователя перед выходом.',
    'Script path': 'Путь скрипта',
    Scroll: 'Прокрутка',
    'Search Object': 'Объект',
    'Search users': 'Поиск пользователей',
    Section: 'Раздел',
    'Select a group or create a new one': 'Выберите группу или создайте новую',
    'Select a user or create a new account':
        'Выберите пользователя или создайте учётную запись',
    'Show retired users': 'Показывать retired',
    Simple: 'Простой',
    'Snapshot type': 'Тип снапшота',
    Status: 'Статус',
    Strict: 'Строгий',
    TACTIC: 'TACTIC',
    TH: 'ТХ',
    Technical: 'Технические',
    'The identifier is used in access rules and cannot be changed after creation.':
        'Идентификатор используется в правилах доступа. После создания изменить его нельзя.',
    'The sandbox path expression; empty uses Directory naming.':
        'Выражение рабочего пути. Пустое поле использует нейминг каталога.',
    'The save result is unknown. Reload groups before trying again.':
        'Результат сохранения неизвестен. Обновите группы перед повторной попыткой.',
    'The save result is unknown. Reload users before trying again.':
        'Результат сохранения неизвестен. Перезагрузите пользователей перед повторной попыткой.',
    'The selected user group no longer exists. Refresh the list.':
        'Выбранная группа больше не существует. Обновите список.',
    'The selected user no longer exists. Refresh the list.':
        'Выбранный пользователь больше не существует. Обновите список.',
    'These details are shown in profiles, messages and user pickers.':
        'Эти данные видны в профиле, сообщениях и списках выбора пользователей.',
    UPN: 'UPN',
    'Unique identifier': 'Уникальный идентификатор',
    'Unique login, without spaces': 'Уникальный логин без пробелов',
    'Unsupported column type': 'Неподдерживаемый тип поля.',
    'Use a color in #RRGGBB format or leave it empty':
        'Введите цвет в формате #RRGGBB или оставьте пустым.',
    'Use a context or a native wildcard such as publish/*.':
        'Укажите контекст или штатный шаблон, например publish/*.',
    'User details or memberships changed. Reload before saving.':
        'Данные пользователя или членство в группах изменились. Перезагрузите их перед сохранением.',
    'User saved on server': 'Пользователь сохранён на сервере',
    View: 'Вид',
    'What is this group responsible for?': 'За что отвечает эта группа?',
    Wizard: 'Мастер',
    'You cannot remove your own administrator membership':
        'Нельзя удалить собственное членство в группе администраторов',
    'You cannot retire the account you are signed in with':
        'Нельзя отключить учётную запись, под которой вы вошли',
    builtin: 'встроенная функция',
    center: 'во вкладки',
    code: 'code',
    column: 'Столбец',
    columns: 'Столбцы контейнера',
    create: 'Создать объект',
    delete: 'Удалён',
    description: 'Описание',
    error: 'Failed',
    file: 'Файл',
    group: 'Группа',
    height: 'Высота картинки',
    icon: 'Иконка',
    image: 'Картинка',
    left: 'слева',
    link: 'Ссылка',
    preview: 'Предпросмотр',
    process: 'Процесс',
    ready: 'Готов к публикации',
    rows: 'Высота в строках',
    selected: 'выбрано',
    table: 'Таблица',
    tasks: 'задачи',
    text: 'Текст',
    title: 'Заголовок',
    value: 'значение',
    view: 'Вложенный вид',
    'Search Types panel width': 'Ширина панели типов объектов',
    'Naming rules panel width': 'Ширина списка правил именования',
    'Discard unsaved Search Type changes?':
        'Отменить несохранённые изменения типа объектов?',
    'Existing files already use this path:':
        'Этот путь уже используется файлами:',
    'Version must be between 1 and 9999': 'Версия должна быть от 1 до 9999',
    'Undo image change': 'Отменить выбор изображения',
    'Center selection': 'Центрировать выделение',
    'Drag: move · Ctrl/Shift: select · F: center':
        'Перенос: мышью · Ctrl/Shift: выделение · F: центрировать',
    'Create Search Type': 'Создать тип объектов',
    'Existing files': 'Существующие файлы',
    'Select a Search Type': 'Выберите тип объектов',
    'Undo deletion': 'Отменить удаление',
    'Wheel: zoom · Middle button: pan':
        'Колесо: масштаб · Средняя кнопка: перемещение',
    'Naming sections': 'Разделы нейминга',
    'New rule is local until Save is pressed.':
        'Новое правило останется локальным до сохранения.',
    'Close administration': 'Закрыть администрирование',
    'Administration project': 'Проект администрирования',
    'Administration section': 'Раздел администрирования',
    'Administration sections': 'Разделы администрирования',
    'TACTIC · ADMIN': 'TACTIC · ADMIN',
    'Duplicated rule is local until Save is pressed.':
        'Копия правила останется локальной до сохранения.',
    Design: 'Конструктор',
    Configuration: 'Конфигурация',
    'Current state': 'Текущее состояние',
    'Blank view': 'Пустое представление',
    Cards: 'Карточки',
    'Cards example': 'Пример карточек',
    'Table example': 'Пример таблицы',
    'Tree example': 'Пример дерева',
    'Continuous Tree': 'Непрерывное дерево',
    'Table View': 'Табличный вид',
    'Copy current view': 'Копия текущего представления',
    'Check and preview': 'Проверить и показать',
    'Check and preview the draft before saving.':
        'Перед сохранением проверьте черновик и посмотрите результат.',
    'Column tracks': 'Размеры колонок',
    'Container layout': 'Компоновка контейнера',
    Container: 'Контейнер',
    'Child layout': 'Компоновка дочерних элементов',
    'Element settings': 'Параметры элемента',
    'Element settings width': 'Ширина панели параметров',
    'Elements panel width': 'Ширина списка элементов',
    'Fixed text': 'Заданный текст',
    'Layout guide': 'Справка по компоновке',
    'Layout template': 'Шаблон компоновки',
    List: 'Список',
    'Move element earlier': 'Переместить элемент раньше',
    'Move element later': 'Переместить элемент позже',
    'Optional sizes such as 128px 1fr auto':
        'Необязательные размеры, например 128px 1fr auto',
    'Preview item type': 'Тип элемента для предпросмотра',
    'Remove element': 'Удалить элемент',
    'Reusable view': 'Переиспользуемое представление',
    'Shared item layout': 'Общая компоновка элемента',
    'View name': 'Имя представления',
    Visible: 'Видимый',
    Widget: 'Виджет',
    Alignment: 'Выравнивание',
    'All items': 'Все элементы',
    'Badge binding': 'Источник счётчика',
    'Branch summary': 'Сводка ветки',
    Center: 'По центру',
    'Child object': 'Дочерний объект',
    'Choose a number to show on the button':
        'Выберите числовое значение для счётчика на кнопке',
    'Choose which object value to display':
        'Выберите значение объекта для отображения',
    'Code editor help': 'Справка по редактору кода',
    'Column span': 'Колонок по ширине',
    'Create related object': 'Создать связанный объект',
    'Custom data binding': 'Произвольная привязка данных',
    'Data binding': 'Источник данных',
    'Display conditions': 'Условия отображения',
    'Edit history': 'История изменений',
    End: 'В конце',
    'Extra large': 'Очень крупный',
    'File Offline': 'Файл недоступен локально',
    'File preview': 'Предпросмотр файла',
    'File size': 'Размер файла',
    'Fill the cell': 'Заполнить ячейку',
    'Fill the image area': 'Заполнить область изображения',
    'Grid columns': 'Колонок в сетке',
    'Higher layers appear in front. Use the same grid cells to place text or buttons over an image.':
        'Более высокие слои отображаются поверх остальных. Совместите ячейки сетки, чтобы разместить текст или кнопки поверх изображения.',
    'Image URL': 'Адрес изображения',
    'Image fit': 'Размещение изображения',
    'Image height': 'Высота изображения',
    'Invalid configuration XML': 'Некорректный XML конфигурации',
    'Invalid layout size': 'Некорректный размер компоновки',
    'Invalid or cyclic layout container':
        'Некорректная или циклическая вложенность контейнеров',
    'Invalid or duplicate layout element name':
        'Некорректное или повторяющееся имя элемента',
    'Item actions': 'Действия с элементом',
    'Item variant': 'Вариант элемента',
    'Knowledge Base': 'База знаний',
    Large: 'Крупный',
    Layer: 'Слой',
    'Layout supports at most 128 elements':
        'Компоновка поддерживает не более 128 элементов',
    'Limit the element to desktop, mobile or particular items':
        'Ограничьте отображение настольным, мобильным режимом или отдельными элементами',
    'Link URL': 'Адрес ссылки',
    'Link URL binding': 'Источник адреса ссылки',
    'Main object': 'Основной объект',
    'Markup tag': 'Тег разметки',
    Medium: 'Средний',
    Metadata: 'Метаданные',
    'Move left': 'Переместить влево',
    'Move right': 'Переместить вправо',
    Muted: 'Приглушённый',
    'No badge': 'Без счётчика',
    Normal: 'Обычный',
    'Number of children': 'Число дочерних элементов',
    'Number of notes': 'Число заметок',
    'Object actions': 'Действия с объектом',
    'Object description': 'Описание объекта',
    'Object preview': 'Превью объекта',
    'Object title': 'Название объекта',
    'Open view': 'Открыть представление',
    'Open view in browser': 'Открыть представление в браузере',
    Relation: 'Связь',
    'Relationship actions': 'Действия со связями',
    'Row span': 'Строк по высоте',
    'Show the whole image': 'Показать изображение целиком',
    Small: 'Мелкий',
    'Snapshot actions': 'Действия со снапшотом',
    'Snapshot author': 'Автор снапшота',
    'Snapshot details': 'Сведения о снапшоте',
    'Snapshot summary': 'Сводка снапшота',
    'Snapshot version': 'Версия снапшота',
    Start: 'В начале',
    Strong: 'Выделенный',
    'Style role': 'Роль оформления',
    'Text size': 'Размер текста',
    'Text style': 'Оформление текста',
    Versions: 'Версии',
    Copy: 'Копировать',
    Cut: 'Вырезать',
    Paste: 'Вставить',
    Find: 'Найти',
    Replace: 'Заменить',
    Undo: 'Отменить',
    Redo: 'Повторить',
    'Add files': 'Добавить файлы',
    File: 'Файл',
    Image: 'Изображение',
    Text: 'Текст',
    Tasks: 'Задачи',
    Notes: 'Заметки',
    Kind: 'Вид',
    Snapshot: 'Снапшот',
    'Alphabetical grid': 'Сетка по алфавиту',
    Canvas: 'Полотно',
    'Choose a column': 'Выберите колонку',
    'Command class': 'Класс команды',
    'Connections refer to missing processes':
        'Связи ссылаются на отсутствующие процессы',
    'Destination key column': 'Ключевая колонка назначения',
    'Directed flow': 'Направленный граф',
    'Enter a unique node name': 'Введите уникальное имя узла',
    'Enter the Search Type identifier to confirm':
        'Для подтверждения введите идентификатор типа',
    'Existing columns': 'Существующие колонки',
    'Find a workflow': 'Найти рабочий процесс',
    'Horizontal position': 'Положение по горизонтали',
    'Layout container depth exceeds 8':
        'Глубина вложенности контейнеров превышает 8',
    'Many-to-many creates a separate instance Search Type with two key connections.':
        'Для связи многие-ко-многим создаётся отдельный тип экземпляров с двумя ключевыми связями.',
    'Missing processes': 'Отсутствующие процессы',
    'Move this node without dragging.':
        'Измените положение узла без перетаскивания.',
    'Native connection attributes.': 'Нативные атрибуты связи.',
    'Network clusters': 'Сетевые кластеры',
    'New workflow': 'Новый рабочий процесс',
    'Node name': 'Имя узла',
    'Optional native path used to distinguish multiple relationships.':
        'Необязательный нативный путь для различения нескольких связей.',
    Parameters: 'Параметры',
    Pending: 'Ожидает обработки',
    Properties: 'Свойства',
    'Properties panel width': 'Ширина панели свойств',
    'Relationship path': 'Путь связи',
    'Review again': 'Проверить снова',
    'Rule list width': 'Ширина списка правил',
    Script: 'Скрипт',
    'Select a workflow or create a new one.':
        'Выберите рабочий процесс или создайте новый.',
    'Source key column': 'Исходная ключевая колонка',
    'Vertical position': 'Положение по вертикали',
    'Workflow list width': 'Ширина списка рабочих процессов'
};

export function translate(text, language, values) {
    let result =
        language === 'ru' && russian[text] ? russian[text] : String(text || '');
    for (const key of Object.keys(values || {}))
        result = result.split('{' + key + '}').join(String(values[key]));
    return result;
}
