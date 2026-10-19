---
group: Workflows
icon: table
order: 36
---

# Table View: типизированные ячейки B07

B07 ещё не завершён. Каталог содержит 41 серверный класс и 98 имён. Здесь описаны добавленные адаптеры значений; поддержка всех исторических опций не заявляется. Неподдерживаемые опции остаются явными ошибками. Сохраните существующий вид и заменяйте только нужный элемент.

## L02: legacy-ячейки с готовыми панелями

В каталоге теперь 41 класс / 98 имён. Эти четыре адаптера используют готовые
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
В поставляемых XML/CG теперь 38 адаптированных / 36 ожидающих классов. B07 открыт.



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
