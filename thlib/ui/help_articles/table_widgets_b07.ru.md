---
group: Workflows
icon: table
order: 36
---

# Table View: типизированные ячейки B07

## Группировка и смена родителя

```xml
<element name="parent" title="Parent">
  <display class="tactic.ui.table.ParentGroupTableElementWdg"/>
  <action class="tactic.ui.table.ParentGroupAction"/>
</element>
```

Выберите «Группировать по этой колонке» в меню заголовка. В группе видны превью,
код/имя, тип, описание и количество строк. Группа сохраняется при сворачивании.
«Добавить ещё объект» открывает штатную настроенную форму создания с этим родителем.
Одинаковые коды разных типов не смешиваются. Пропавший родитель явно отмечается.
`disable=true` отключает расширенную группировку. Исторический `label` не имеет
отдельного поведения и в исходной реализации.

Кнопка смены родителя открывает панель у ячейки: тип объекта и буквальный поиск
по коду/имени/заголовку, по 50 результатов. Выберите действующий объект и сохраните.
Отмена/обновление требуют подтверждения потери изменённого выбора. При потере
ответа сначала нажмите «Проверить сохранение». Конфликт требует явного обновления;
retired-цели, циклы и другой проект отклоняются. Expression-ячейка с тем же action
сохраняет вычисленный текст. Перетаскивание одного объекта открывает тот же выбор
с заранее выбранной целью и само связь не записывает.

В этой точке проверяются операции администратора. Права обычного пользователя и
все legacy-итоги/опции групп ещё в работе; произвольный HTML/Mako-редактор не добавлен.
В интерфейс передаются только безопасные поля для отображения родителя.


Общее содержимое выбора родителя и заголовок группы на одинаковых данных,
теме и размере. Растеризация шрифта QML и браузера может отличаться; эти примеры
не подтверждают все исторические опции групп.

![Выбор родителя в Handler](media/frame-table-parent-native-ru.png)
![Выбор родителя в Stream](media/frame-table-parent-stream-ru.png)
![Группа в Handler](media/frame-table-parent-group-native-ru.png)
![Группа в Stream](media/frame-table-parent-group-stream-ru.png)

B07 ещё не завершён. Каталог содержит 72 серверных класса и 174 имени. Здесь описаны добавленные адаптеры значений; поддержка всех исторических опций не заявляется. Неподдерживаемые опции остаются явными ошибками. Сохраните существующий вид и заменяйте только нужный элемент.

## Зависимости снапшота

Добавьте действие зависимостей в таблицу объектов или снапшотов:

```xml
<element name="dependency" width="64">
  <display class="pyasm.widget.DependencyLink"/>
</element>
```

Немодальное окно «Зависимости» показывает файлы, входящие, входные, исходящие и
файловые ссылки. Стрелка показывает загрузку ветки; повторное раскрытие использует
уже загруженные строки. Удалённые/скрытые объекты и циклические ссылки обозначены.
Для объекта один раз выбирается последний снапшот; конкретный снапшот сохраняет
свою версию. «Обновить» начинает новую сессию корня. Если ревизия изменилась,
перед следующей страницей требуется обновление. Закрытие окна или смена проекта
отбрасывает запоздалые ответы.
Снапшот из общей таблицы администрирования открывается в собственном проекте.

Раскройте последовательность, чтобы увидеть имена кадров: по 50 строк с кнопкой
«Показать ещё». Это не скачивает последовательность. Обычный файл открывается
существующим preview/нативным действием файла. Передача последовательностей/UDIM
ещё в работе. Пока просмотрщик требует доступа администратора.
Превью последовательности использует первый кадр. Запоздалый ответ старого
документа не заменяет новое окно и не открывает его после закрытия.

| Зависимости, MD3, тёмная тема | Handler | Stream |
| --- | --- | --- |
| Раскрытое дерево | ![Handler](media/frame-table-dependencies-native-ru.png) | ![Stream](media/frame-table-dependencies-stream-ru.png) |

## Вложения снапшота

`FileAppendLinkTableElement` открывает **Прикрепить файлы** для выбранной версии снапшота. Выберите локальные файлы или вставьте изображение, укажите **Тип файла**, при необходимости сохраните исходные имена и прикрепите файлы. Они добавляются к этой версии; новая версия не создаётся. Versionless-ссылка сначала разрешается в конкретную версию.

```xml
<element name="append" width="64">
  <display class="pyasm.widget.FileAppendLinkTableElement"/>
</element>
```

Исходные файлы клиента остаются нетронутыми. Повторяющиеся/уже существующие имена и изменение снапшота другим клиентом останавливают запись. Отмена предлагает сбросить выбранные файлы. Если результат записи неизвестен, повтор заблокирован: закройте окно и обновите снапшот перед новой попыткой. Поздняя серверная ошибка откатывает зарегистрированные файлы и данные через FileUndo; временная загрузка сервера не является исходным локальным файлом.

Ctrl+V прикрепляет изображение; обычный текст вставляется в поле с фокусом. Выбирайте файлы, а не папки, до 50 за операцию. У каждого черновика своя временная папка загрузки. Сохранение обновляет конкретную версию и исходную строку current/latest.

ТХ открывает обычное отдельное модальное окно, ТС — соответствующий браузерный диалог. Тело формы описано одним Frame-скелетом, включая тип/имя, загрузку, ошибки и отмену. В ТХ загрузка и файловые операции выполняются вне GUI-потока. Эта проверка охватывает административную таблицу; ordinary-user ACL, исполнение на PostgreSQL/исходном сервере и физические телефоны/другие DPI ещё не приняты.

| Tactic Handler | TACTIC Stream |
| --- | --- |
| ![Вложения снапшота ТХ](media/frame-table-append-native-ru.png) | ![Вложения снапшота ТС](media/frame-table-append-stream-ru.png) |

## Получение файлов снапшота

`CheckoutButtonElementWdg` открывает **Получить файлы** для конкретной версии снапшота. Ссылка current/latest сначала разрешается в конкретную версию. Выберите нужный файл и нажмите **Получить файлы**. Проект и версия фиксируются, даже если главная таблица открыта в другом проекте рабочего пространства.

```xml
<element name="checkout" width="64">
  <display class="tactic.ui.table.CheckoutButtonElementWdg">
    <transfer_mode>browser</transfer_mode>
  </display>
</element>
```

ТХ использует настроенный локальный путь файла в репозитории и существующую очередь передач. Если локальный файл отличается от серверного, явно выберите **Перезаписать** либо отмените операцию, чтобы сохранить его. Файл, появившийся во время передачи, стандартная политика сохраняет. ТС скачивает выбранный файл через браузер; папку назначения и подтверждение замены определяет браузер. Режимы `copy` и `client_repo` требуют настольного клиента; браузер сообщает это ограничение.

**Отменить передачу** останавливает текущую загрузку. **Закрыть** также отменяет её и игнорирует запоздавший ответ; снапшот и его версия не изменяются. Вложения личных сообщений остаются в существующем защищённом сценарии скачивания Messages.

Эта контрольная точка поддерживает обычные отдельные файлы в административной таблице. Разворачивание последовательностей/UDIM, другие исторические display options, ordinary-user ACL и проверка исходного сервера/PostgreSQL ещё открыты. Неподдерживаемая группа сообщает ошибку, а не скачивает только один элемент. Общий список файлов использует одно Frame-тело в обоих продуктах, с полосой прокрутки на узкой ширине.

| Tactic Handler | TACTIC Stream |
| --- | --- |
| ![Получение файлов ТХ](media/frame-table-checkout-native-ru.png) | ![Получение файлов ТС](media/frame-table-checkout-stream-ru.png) |

## L02: legacy-ячейки с готовыми панелями

Эти четыре адаптера используют готовые
заметки/Task Inspector, черновики задач и табличные контролы; второй Messages
или Task Manager не создаётся.

```xml
<element name="notes">
  <display class="pyasm.widget.DiscussionWdg">
    <include_submission>false</include_submission>
  </display>
</element>
<element name="tasks">
  <display class="pyasm.widget.SObjectTaskTableElement">
    <width>280</width><supe>true</supe><bid_edit>true</bid_edit>
    <simple_date>true</simple_date>
  </display>
</element>
<!-- Этот элемент применяется в sthpw/task. -->
<element name="context"><display class="pyasm.widget.TaskParentSpacingTableElement"/></element>
<!-- Этот элемент применяется в sthpw/message или sthpw/message_log. -->
<element name="message"><display class="tactic.ui.app.MessageTableElementWdg"/></element>
```

Discussion читает существующие заметки и предлагает процессы из
setting/append_setting, включая пустые ветки. Клик открывает существующую
панель; создание/изменение/удаление заметки сохраняет её проверки прав и ревизий.
В задачах используются готовые компактные карточки, редакторы статуса,
исполнителя и дат с обычными Save/Discard. `supe` включает назначение в ячейке,
`bid_edit` — редактирование дат; эти параметры отображения не выдают серверных
прав. `simple_date` показывает месяц-день вместо полной ISO-даты, когда высоты
строки хватает для дат. Старый HTML CalendarBar не встраивается. Явная ширина
колонки заменяет исходные 250px. TaskParentSpacing показывает контекст до первого
слеша, а полный контекст сохраняет в подсказке.

Сообщения показывают обычный/чатовый текст, изменения заметок/задач/снапшотов,
автора и прогресс. Разметка сообщения отображается как текст. Старое HTML-превью
не воспроизводится. Неверный JSON/нечисловой прогресс дают явную ошибку ячейки.

`include_submission=true` не поддерживается: старый Submission входит в
согласованно исключённый pyasm.prod. Подконтексты со слешем в старых setting
choices и CGI filter state не перенесены; современный Discussion поддерживает
явный context. `scroll=false` — старая HTML-подсказка компоновки; современная
панель сохраняет общую полосу прокрутки. Неизвестные options остаются явными.
В поставляемых XML/CG теперь 54 адаптированных / 20 ожидающих классов. B07 открыт.



### L02: парные примеры ячеек

Свежие снимки настоящих Qt/Vue-компонентов: одинаковые данные, тёмная MD3, язык и ширина колонки 280px. Примеры показывают четыре адаптера ячеек; все исторические HTML options ими не подтверждаются.

| Ячейка | Tactic Handler | TACTIC Stream |
| --- | --- | --- |
| `DiscussionWdg` | ![DiscussionWdg native](media/frame-table-l02-legacy_notes-native-ru.png) | ![DiscussionWdg stream](media/frame-table-l02-legacy_notes-stream-ru.png) |
| `SObjectTaskTableElement` | ![SObjectTaskTableElement native](media/frame-table-l02-legacy_tasks-native-ru.png) | ![SObjectTaskTableElement stream](media/frame-table-l02-legacy_tasks-stream-ru.png) |
| `TaskParentSpacingTableElement` | ![TaskParentSpacingTableElement native](media/frame-table-l02-legacy_context-native-ru.png) | ![TaskParentSpacingTableElement stream](media/frame-table-l02-legacy_context-stream-ru.png) |
| `MessageTableElementWdg` | ![MessageTableElementWdg native](media/frame-table-l02-message_progress-native-ru.png) | ![MessageTableElementWdg stream](media/frame-table-l02-message_progress-stream-ru.png) |

## Блокировка снапшота

Блокировка контекста снапшота; только чтение.

```xml
<element name="locked" width="180">
  <display class="tactic.ui.table.SnapshotLockedElementWdg"></display>
</element>
```

## Файл снапшота

Исходное имя файла, диапазон кадров и безопасная ссылка.

```xml
<element name="file" width="180">
  <display class="tactic.ui.table.SnapshotFileElementWdg"></display>
</element>
```

## Готовность вехи

Для sthpw/milestone; права на процессы сохраняются.

```xml
<element name="completion" width="180">
  <display class="tactic.ui.table.MilestoneCompletionWdg"></display>
</element>
```

## Готовность по группам

Средняя готовность задач каждой группы контекстов.

```xml
<element name="completion" width="180">
  <display class="tactic.ui.table.TaskGroupCompletionWdg"><options>[{"label":"MODEL","context":["model"]}]</options></display>
</element>
```

## Срок задачи

Для задач. Подписи и срочность следуют порогам оригинала.

```xml
<element name="due" width="180">
  <display class="tactic.ui.table.TaskDaysDueElementWdg"><due_date_col>bid_end_date</due_date_col></display>
</element>
```

## Подконтекст

Сохраняет весь текст после первой косой черты контекста.

```xml
<element name="subcontext" width="180">
  <display class="tactic.ui.table.SubContextElementWdg"></display>
</element>
```

## Выбор строки

Отображает существующий выбор строки; это не поле БД.

```xml
<element name="select" width="180">
  <display class="CheckboxColWdg"></display>
</element>
```

## Название Search Type

Показывает штатное название типа из поля search_type.

```xml
<element name="search_type" width="180">
  <display class="SearchTypeElementWdg"></display>
</element>
```

## Компактная сводка задач

Клик открывает конкретную задачу процесса; режим default использует обычные карточки задач.

```xml
<element name="tasks" width="180">
  <display class="tactic.ui.table.TaskSummaryElementWdg"><mode>minimal</mode></display>
</element>
```

## Старая готовность задач

Целочисленный результат и фильтрация старых процессов отличаются от нового виджета.

```xml
<element name="completion" width="180">
  <display class="pyasm.widget.TaskCompletionWdg"></display>
</element>
```

## Обсуждение

Использует существующие счётчики заметок процессов и инспектор. Это отдельный класс от pyasm.widget.DiscussionWdg.

```xml
<element name="notes" width="180">
  <display class="tactic.ui.widget.DiscussionWdg"></display>
</element>
```

## База проекта

Для sthpw/project. Читает наличие и версию БД без её создания.

```xml
<element name="database" width="180">
  <display class="tactic.ui.table.ProjectWdg"></display>
</element>
```

## Наличие таблицы

Для sthpw/search_object. Проверяет наличие физической таблицы.

```xml
<element name="table" width="180">
  <display class="tactic.ui.app.SearchTypeHasTableElementWdg"></display>
</element>
```

## Описание настройки

Для sthpw/pref_list; включает исходные пояснения к настройкам.

```xml
<element name="description" width="180">
  <display class="tactic.ui.table.PreferenceDescriptionWdg"></display>
</element>
```

## Получатели

Для sthpw/notification_log. Читает связанные notification_login. Отправка почты и публичное добавление получателей ещё не перенесены.

```xml
<element name="recipients" width="180">
  <display class="tactic.ui.table.RecipientElementWdg"></display>
</element>
```

## Связанное значение

Замените путь связи и колонку своей схемой. Связанная запись выбирается штатным JOIN.

```xml
<element name="category" width="180">
  <display class="tactic.ui.table.RelatedElementWdg"><template>cg/assets.cg/assets_category</template><column>name</column></display>
</element>
```

## Редактор и ограничения

Одна сцена Frame задаёт текст, многострочный ввод, выбор/пользователя, переключатель, дату/время, цвет и множественные значения. Enter сохраняет строку; в многострочном поле добавляет перенос, а сохраняет кнопка Save. Escape отменяет. Проверки ревизий, прав, откат и проверка неизвестного результата сохранены. Нативные теги используют специализированный редактор. Тридцать шесть упомянутых классов ещё требуют полного переноса: вложенные таблицы, расписания, учёт часов, loader/publish и формы настраиваемых действий.

## Актуальные парные примеры

![table](media/frame-table-table-ru.png)

![fields](media/frame-table-fields-ru.png)

![summary](media/frame-table-summary-ru.png)

![groups](media/frame-table-groups-ru.png)

## Этап 1: служебные ячейки, действия и процессы задач

Stream 0.112.174 / Handler 0.6.0.121 добавляют 16 табличных адаптеров и общий
inline-редактор тегов. Ресурсы продуктов остаются независимыми. B07 и этап 1
не закрыты: часть исходных layouts зависит от вложенных таблиц и файлового ingest.

### Теги и служебные колонки

Двойной клик по Keywords открывает токены и подсказки. Enter добавляет токен;
Save также включает ещё не добавленный текст. Cancel/Escape отменяют черновик.
Клик снаружи ничего не сохраняет. Preferences также требуют явного Save/Cancel:
конфликт ревизии требует перечитать данные, неизвестный результат записи можно
проверить без повторной отправки изменения.

```xml
<!-- Элементы предназначены для соответствующих системных Search Types. -->
<element name="update"><display class="pyasm.widget.UpdateWdg">
  <insert_view>insert</insert_view><edit_view>edit</edit_view>
  <retire>true</retire><delete>false</delete>
</display></element>
<element name="login"><display class="tactic.ui.input.LoginTableElementWdg"/></element>
<element name="security"><display class="tactic.ui.panel.SecurityManagerButtonWdg"/></element>
<element name="value"><display class="tactic.ui.table.PreferenceEditWdg"/></element>
<element name="template"><display class="tactic.ui.table.ProjectTemplateUpdateWdg"/></element>
<element name="summary"><display class="pyasm.widget.MyTacticSummaryWdg"/></element>
<element name="test"><display class="tactic.ui.table.NotificationTriggerElementWdg"/></element>
```

Update использует настроенные insert/edit views и существующий редактор объектов.
Retire/reactivate сверяют ревизию всей записи; Delete работает через текущего
владельца удаления. Login и Security открывают готовую админку с нужной
идентичностью пользователя/группы. Preferences относятся к текущему логину.
Template export вызывает существующую команду шаблона. Summary считает активность
текущего пользователя за час, сегодня и неделю, а также назначенные ему задачи по статусам. Test уведомления вызывает исходный forced
trigger с несохранённой тестовой записью; наличие кнопки не подтверждает настройку
или доставку SMTP/Telegram.

### Исходный JavaScript без браузера внутри Handler

```xml
<element name="action"><display class="tactic.ui.table.ButtonElementWdg">
  <script_path>assets/my_action</script_path>
  <icon>EDIT</icon><hint>Open configured action</hint>
</display></element>
```

По этому пути должен существовать JavaScript custom script. Также поддержаны
исходные `script_code`, `cbjs_action`, `javascript`. Используется оригинальный
SDK. Мост передаёт нажатую строку, view, колонку и зафиксированное выделение;
`bvr.kwargs.search_key`, `spt.table.get_search_key()` и вызовы SDK получают этот
контекст. Переходы Edit/Notes/Tasks/users/groups/schema/workflow/script editor
открывают существующих владельцев. Подтверждение должно предшествовать первому
API-вызову и не переигрывает уже выполненные записи. Смена сессии/проекта отменяет
запуск и отбрасывает запоздалые UI-команды. Тайм-аут — 120 секунд.

В браузере скрипт работает в Worker под CSP приложения, в Handler — в отдельном
процессе QJSEngine: бесконечный цикл не блокирует QML. Это поддержка клиентских
скриптов, а не произвольного DOM/MooTools. Неподдержанные DOM, Promise callbacks
и неизвестные popup-классы дают явную ошибку. Серверные права текущего пользователя
сохраняются. Три поставляемых CG JavaScript действия проверяются с fake SDK,
без изменения пользовательских данных.

### Переносимый CustomLayout

```xml
<element name="script"><display class="tactic.ui.table.CustomLayoutElementWdg">
  <view>episodes/columns/script</view>
</display></element>
```

Слеши в ссылке сопоставляются с точками в сохранённом имени. Настоящий CG layout
сценария показывает текст, ссылку на документ и настроенное редактирование в
обоих клиентах. Поддержаны labels, безопасные ссылки, Thumb previews, вложенные
переносимые CustomLayout и click actions. Внешний документ открывается по ссылке;
HTML/WebEngine в QML не вставляется. Data-only Mako читает переданные данные
записи и форматирует текст; imports, серверные вызовы, запись и файловый/сетевой
I/O отклоняются. Это ограниченное форматирование, не общая совместимость Python/Mako.

Security Summary открывает немодальное окно с выбором группы и одним readonly
редактором исходника её сохранённых правил. Это не вычисленный отчёт эффективных
прав. Кнопка Help ведёт в общую справку.

CG definitions сохранены. `columns/tasks_parent` содержит FastTable и остаётся
зависимостью L01. В `episodes.columns.assets` только `No html`; рабочим виджетом
он не объявляется. Сложные development layouts также не приняты.

### Instance-связи и задачи

```xml
<!-- Для cg/assets: связь с текстурами из поставляемого шаблона CG. -->
<element name="links"><display class="tactic.ui.table.DropElementWdg">
  <instance_type>cg/texture_in_assets</instance_type>
  <accepted_drop_type>cg/texture</accepted_drop_type>
</display></element>
<element name="parallel"><display class="pyasm.widget.ParallelStatusWdg">
  <bar_height>3</bar_height><label_format>abbr</label_format>
</display></element>
<element name="new_task"><display class="pyasm.widget.ParallelStatusEditWdg"/></element>
<element name="tasks"><display class="tactic.ui.table.SObjectTaskStatusElementWdg"/></element>
<!-- Эти три колонки предназначены для таблицы задач. -->
<element name="process"><display class="tactic.ui.table.ProcessElementWdg"/></element>
<element name="status"><display class="tactic.ui.widget.TaskStatusElementWdg">
  <edit_scope>assigned</edit_scope>
</display></element>
<element name="work"><display class="tactic.ui.table.WorkElementWdg">
  <transfer_mode>upload</transfer_mode>
</display></element>
```

Drop принимает ключи объектов настроенного типа, не произвольные файлы.
Link Objects даёт альтернативу клавиатурой/кликом: выбрать, Save или Cancel в
готовом редакторе связей. Полная ревизия instance-записей и все цели проверяются
до удаления; ошибка замены откатывается транзакцией. `path` выбирает связь схемы.
Legacy `folder_drop` с JavaScript/FileIngest остаётся задачей L04 и не подменяется
обычной instance-связью.

Parallel bars сохраняют исходные шаги 33/66/100, цвет просрочки и точную задачу.
Бар или доступная кнопка процесса открывает существующего владельца задач.
Task status использует status pipeline конкретной задачи; assigned scope
проверяется до изменения. Work сохраняет process/context/task identity и открывает
готовый check-in. В браузере доступен upload; local copy/move/inplace остаются
возможностью desktop. Calendar остаётся отдельным доком. Bottom/group totals — L07b.

### Проверка и границы

Примеры воспроизводятся через `tests/test_table_stage_one.py`,
`tests/test_table_services.py`, `tests/test_table_drop_links.py`,
`frontend/tests/table_script_runtime.mjs`. Реальный native input/lifecycle —
`tests.test_frame_table`, `tests.test_table_scripts`,
`tests.test_table_service_workflows` в независимом Handler.
`tools/frame_table/capture.py` и `frontend/tests/frame_table.mjs` сравнивают текущие
Qt/Vue geometry, paint и ввод: три темы, EN/RU, light/dark.

Рабочие business scripts, реальная доставка уведомлений, сервер PostgreSQL,
физический touch и frozen Windows build в этой контрольной точке не проверялись.
Вложенные FastTable/HiddenRow, файловые DOM-actions, произвольный Mako и полные
bottom reports остаются открытыми в L01/L04/L07b/L11.

### Этап 1: парные снимки настоящих ячеек

Одинаковые fixture, ширина, MD3 dark и язык. Снимки ячеек не означают приёмку полного legacy-сценария.

| Cell | Tactic Handler | TACTIC Stream |
| --- | --- | --- |
| `tags` | ![tags native](media/frame-table-stage1-tags-native-ru.png) | ![tags stream](media/frame-table-stage1-tags-stream-ru.png) |
| `service_actions` | ![service_actions native](media/frame-table-stage1-service_actions-native-ru.png) | ![service_actions stream](media/frame-table-stage1-service_actions-stream-ru.png) |
| `parallel_status` | ![parallel_status native](media/frame-table-stage1-parallel_status-native-ru.png) | ![parallel_status stream](media/frame-table-stage1-parallel_status-stream-ru.png) |
| `drop_links` | ![drop_links native](media/frame-table-stage1-drop_links-native-ru.png) | ![drop_links stream](media/frame-table-stage1-drop_links-stream-ru.png) |
| `custom_layout` | ![custom_layout native](media/frame-table-stage1-custom_layout-native-ru.png) | ![custom_layout stream](media/frame-table-stage1-custom_layout-stream-ru.png) |


## Объединённый этап 2: вложенные таблицы и временные ячейки

Старый HTML Custom Layout Editor исключён. Новые переносимые раскладки создаются
через Frame и существующий редактор раскладок. Поддержанные сохранённые CustomLayout
остаются доступными; неподдержанный DOM-виджет явно сообщает об ограничении.

У раскрытой таблицы свои выделение, фильтр и страница. Выбор дочерней строки
не меняет выделение поиска. Обновить применяет её фильтр, Закрыть сворачивает
ветку. Повторное раскрытие сохраняет загруженные строки и выделение в текущем
контексте. Загрузка показывается в иконке раскрытия. Создать/Редактировать вызывают
существующую форму объекта с серверными правами. Сейчас у родительской строки
показывается одна раскрытая поверхность; рекурсивные дочерние поверхности и
оставшиеся виджеты связей/групп ещё не приняты.

```xml
<element name="tasks" title="Tasks">
  <display class="tactic.ui.table.HiddenRowElementWdg">
    <dynamic_class>tactic.ui.panel.FastTableLayoutWdg</dynamic_class>
    <search_type>sthpw/task</search_type>
    <view>table</view>
    <show_insert>false</show_insert>
  </display>
</element>
```

Исходный CG `columns/tasks_parent` открывает таблицу родителя задачи. Его
определение сохранено; перенос не возвращает старый HTML-редактор.
Полоса расписания открывает существующий Gantt таск-менеджера. Дневные часы
открывают существующий Timesheet для задачи/недели; часы всех пользователей
остаются только для чтения. Общая отрисовка не означает приёмку старых
inline/cascade-записей Gantt, всех операций timecard, итогов таблицы или файловых
действий. Объединённый второй этап остаётся открытым.


Сейчас вложенная область использует страницу на 50 записей и высоту 320 пикселей.
Параметры shelf/search/search-limit и выбора скрывают соответствующие controls. `init_load_num` заменён виртуализацией отрисовки и не меняет страницу из 50 записей. Явный `show_gear=true` пока отклоняется: scoped Columns authoring ещё не готов.

Парные примеры этой контрольной точки (одинаковые данные, MD3 dark):

| Поверхность | ТХ | ТС |
| --- | --- | --- |
| `nested` | ![Handler nested](media/frame-table-stage2-nested-th-ru.png) | ![Stream nested](media/frame-table-stage2-nested-ts-ru.png) |
| `schedule` | ![Handler schedule](media/frame-table-stage2-schedule-th-ru.png) | ![Stream schedule](media/frame-table-stage2-schedule-ts-ru.png) |
| `hours` | ![Handler hours](media/frame-table-stage2-hours-th-ru.png) | ![Stream hours](media/frame-table-stage2-hours-ts-ru.png) |


## Связи, вложенные таблицы и сводка

Ячейка связей показывает входящие (`dst`) или исходящие (`src`) объекты,
превью, имена файлов и архивные/удалённые цели. Удаление связи требует
подтверждения и свежей ревизии; оба объекта сохраняются. После неопределённого
ответа список перечитывается перед следующей операцией.

```xml
<element name="connections" width="400">
  <display class="pyasm.widget.SObjectConnectionElement">
    <direction>dst</direction><icon_size>60</icon_size>
  </display>
</element>
<element name="summary" width="200">
  <display class="tactic.ui.table.SObjectSummaryElementWdg"/>
</element>
```

Сводка содержит задачи, check-in, заметки и сумму straight_time без overtime.
Кнопки задач и check-in раскрывают разные настроенные таблицы. Сводка проекта
использует выбранный проект, включая контекст таблиц, редакторов и скриптов.
Вложенные таблицы раскрываются дальше; повтор области предка отклоняется.
Выбор и загруженные строки сохраняются отдельно на каждом уровне: повторное
раскрытие не ждёт нового серверного запроса. Сейчас проверен доступ администратора.
Этап 2/B07 остаётся открытым.


Текущие парные примеры (MD3, тёмная тема, тестовые данные):

| Ячейка | Handler | Stream |
| --- | --- | --- |
| Сводка | ![Handler](media/frame-table-object_summary-native-ru.png) | ![Stream](media/frame-table-object_summary-stream-ru.png) |
| Связи | ![Handler](media/frame-table-object_connections-native-ru.png) | ![Stream](media/frame-table-object_connections-stream-ru.png) |


## Настроенная публикация

`PublishTableElement` открывает форму `publish` текущей записи. `GeneralPublishElementWdg` также принимает настроенный `view` и `preview=false`. Общий Frame задаёт ячейку, ограниченное превью, заголовок и кнопку публикации; ТХ и ТС поставляют независимые копии. Повторный клик не затирает несохранённую, занятую, пакетную форму или неизвестный результат записи; чистая форма может переключиться на другой объект.

```xml
<element name="publish" width="100">
  <display class="tactic.ui.table.GeneralPublishElementWdg">
    <view>review_publish</view><preview>true</preview>
  </display>
</element>
```

В `review_publish` нужно явно настроить действия полей, например:

```xml
<review_publish>
  <element name="attachment">
    <display class="tactic.ui.widget.SimpleUploadWdg"><context>publish/reference</context></display>
    <action class="pyasm.command.UploadAction"/>
  </element>
</review_publish>
```

Опция `multi_publish=true` у `PublishTableElement` добавляет кнопку заголовка, открывающую явно настроенный view `multi_publish`. Это не общий режим пакетного создания. UploadAction создаёт настроенный снапшот; NullAction остаётся неработающей настройкой загрузки и явно диагностируется. Исключённый production Publish Browser и произвольные DOM callbacks не переносятся. Полная приёмка прав обычных пользователей и legacy-опций остаётся во втором этапе.

| Ячейка | ТХ | ТС |
| --- | --- | --- |
| Публикация | ![ТХ](media/frame-table-publish-native-ru.png) | ![ТС](media/frame-table-publish-stream-ru.png) |

Настроенная публикация ТХ принимает текст, многострочный текст, select, checkbox, превью (`ThumbInputWdg`) и многофайловую загрузку (`UploadWdg`, `SimpleUploadWdg` с `UploadAction`). Неперенесённые сочетания input/action явно блокируют форму. Сохранение идёт через настроенный EditCmd; обычные формы ТХ сохраняют прежний способ записи. Выбор файла — переиспользуемый базовый контролл в обоих клиентах с одним описанием Frame.

## Приёмка этапа 1.5: итоги, вложенный редактор колонок, ACL и ревизии форм

- **Итоги групп и низа таблицы**: `FormatElementWdg` (`total_summary` = `count` | `total` | `average`), `ExpressionElementWdg` (`bottom` / `group_bottom`), `WorkHoursElementWdg` и `WeekTableElement` выводят строки итогов по группам и общий итог внизу таблицы в обоих движках.
- **Редактор колонок во вложенной таблице (`show_gear`)**: вложенные таблицы `HiddenRowElementWdg` / `CustomLayoutElementWdg` показывают кнопку настройки колонок (`nestedColumns`) администраторам, если `show_gear` не отключён.
- **Права обычного пользователя (ACL) и средства администратора**: чтение таблиц, inline-правки, формы и автономные табличные процедуры (`read_nested_scope`, `read_dependency_node`, `read_connection_cells`, `remove_connection`, `edit_parent_group`, `read_parent_cells`, `append_snapshot_files`, `read_snapshot_files`, `edit_drop_links`, `read_summary_cell`) проверяют права проекта, `search_type` и `element` для авторизованных пользователей, оставляя `read_group_summary`, `read_custom_layout` и `ColumnsEditor` доступными только администраторам.
- **Ревизии форм, защита retired-записей и проверка сохранения**: `read_form` и `EditCmd` / `EditMultipleCmd` проверяют `expected_revision` перед записью, запрещают редактирование архивных (`retired`) записей и поддерживают `action='check'` («Проверить сохранение») при сетевом сбое с неизвестным результатом.
- **Оставшиеся явные ограничения**: отклоняются только отсутствующие в шаблонах исторические ссылки `CustomLayout` (`asset_panel_wdg`, `asset_cost_breakdown`, `inline_add_item`, пустой `custom_col`) и `include_submission=true`.


## Файлы в истории версий

Ячейка Files в истории раскрывает таблицу файлов, зарегистрированных именно в выбранном снапшоте: ссылка на файл, каталог репозитория, тип, диапазон кадров, размер и время. Фильтр и страницы ограничены этим снапшотом; у пустой версии список пуст. Ссылки на обычные файлы используют настроенный URL репозитория. Для последовательностей сохраняются маска имени и диапазон; ссылка не скачивает всю последовательность. Пакеты каталогов отображаются как зарегистрированные файловые записи, без рекурсивного раскрытия диска. Действия Maya/applet исключены.


В Checkin Log столбец Code показывает имя и код связанного объекта, как в легаси TACTIC. Для отсутствующего или исключённого владельца выводится n/a. Files открывает файлы конкретной версии. Старая команда RenderSubmission относится к исключённой production-подсистеме и убрана из штатного журнала.
