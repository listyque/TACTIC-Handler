# Назначение и фактическое поведение modern UI

## Границы и статусы

Отчёт составлен по цепочкам QML action → Python Slot/model → API/настройки. Наличие
QML-файла само по себе не считается работающим интерфейсом. `thlib/side` исключён из
анализа. Под «безопасно тестировать» ниже понимается проверка, не меняющая TACTIC,
репозитории, локальные файлы или запущенные процессы.

- `ORIGINAL_PARITY` — назначение и основная цепочка действий соответствуют оригиналу.
- `USEFUL_EXTENSION` — осмысленное дополнение нового клиента, которого не было в таком виде.
- `EXPERIMENT` — рабочая идея, но её пользовательский контракт ещё не устоялся.
- `UNCLEAR_BEHAVIOR` — интерфейс доступен, однако действие или результат неоднозначны.
- `VISUAL_ONLY` — представление существует, но существенный сценарий не подключён.
- `NOT_REACHABLE` — компонент зарегистрирован, но штатного пути открытия не найдено.
- `DANGEROUS` — доступны реальные серверные, файловые или процессные изменения; нужен тестовый контур.

Один статус отражает главный риск, а не полноту реализации. Поэтому, например,
работающая очередь имеет статус `DANGEROUS`, хотя большая часть её функций подключена.

## Карта открытия

- Постоянная оболочка: `Main.qml` → `DockHost.qml`; результаты поиска нельзя закрыть.
- Панели открываются из меню Workspace Panels, контекстных команд и кнопок карточек.
- Отдельные окна создаёт общий реестр `FloatingWindowModel`; содержимое выбирает
  `WindowContent.qml`. Регистрация окна не означает, что в меню есть путь к нему.
- Configuration открывается из меню главного окна; из неё доступны Repository Editor,
  Server Presets, Script Editor, Debug Log, Repository Sync, TACTIC API Client и TACTIC Server.
- Контекст результата открывает Add/Edit/Link/Delete/Duplicate, Check-in/Out, Queue,
  Database Editor и связанные панели.

## Основной клиент

### Главное окно, проекты, навигация и workspace — `ORIGINAL_PARITY`

- **Открытие и задача:** `main_qml.py`/QML launcher; выбор проекта и search type, вкладки
  поиска, карточки/список/дерево и dock workspace. Аналоги: `Ui_Main`, main tabs,
  project chooser, search/check-in shell.
- **Реально:** bootstrap/login, проекты, поиск и suggestions, вкладки, навигация,
  сохранение раскладки, открытие команд, details, cards/items, refresh и shutdown.
- **Добавлено:** карточная навигация «внутрь», быстрые фильтры, облако тегов,
  перестраиваемые/открепляемые панели. Это полезные функции нового клиента.
- **Данные и фон:** читает/меняет состояние сессии и QSettings; поиск и details идут
  через серверный pool. Выбор объекта запускает загрузку details и меняет target Check-in/Out.
- **Тест:** навигация и локальная раскладка безопасны; реальные поиски читают сервер.

### Поиск, Advanced Search и Filter Editor — `ORIGINAL_PARITY`

- **Открытие:** строка поиска, панель Advanced Search и команда Filter Presets.
  Аналоги: `Ui_searchWidget`, `Ui_advancedSearchWidget`, `Ui_filterEditorDialog`,
  process filter и search options.
- **Реально:** серверный поиск, отмена устаревшего результата, conditions/groups,
  AND/OR, операторы, presets CRUD, process/search options и возврат фильтра во вкладку.
- **Добавлено:** quick-filter badges и tag cloud. Они должны формировать слой общего
  search contract; отдельная локальная фильтрация результатов остаётся неоднозначной.
- **Данные и фон:** меняются параметры/история вкладок и сохранённые фильтры; запросы
  асинхронны. Apply запускает новый серверный поиск.
- **Тест:** редактор без Apply безопасен; Apply обращается к серверу, но не мутирует объекты.

### Результаты, Snapshot Browser, Description и Database Editor — `DANGEROUS`

- **Открытие:** центральные results и правые/контекстные панели. Аналоги: search result
  items, snapshot browser, description и edit DB table.
- **Реально:** выбор/раскрытие, lazy preview, версии/snapshots/files, download/open,
  редактирование description и полей, refresh точечных моделей.
- **Странно:** один selection одновременно является target для нескольких независимых
  панелей, включая Check-in/Out; это не всегда очевидно визуально.
- **Данные и фон:** detail/download идут в pools; Save меняет sObject, download пишет в
  репозиторий. Просмотр безопасен, Save/Download/Open — только на тестовых данных.

### Assets Browser — `NOT_REACHABLE`

- **Открытие:** окно `asset_browser` зарегистрировано, штатной кнопки/команды его
  открытия не найдено. Аналог: `Ui_assetsBrowserWidget`.
- **Реально:** поиск, refresh, cards/items и selection подключены к общим navigation,
  application и workspace models.
- **Неоднозначность:** это не изолированный browser — смена раздела/выбора меняет
  состояние главного workspace. Самостоятельного Search Controller нет, что правильно,
  но независимость окна лишь визуальная.
- **Данные и фон:** только чтение/поиск через общий pool; локально меняет активную вкладку.
  Ручное открытие безопасно для данных. Как отдельное окно имеет смысл только после
  определения маршрута и ожидаемого разделения состояния.

## Check-in, файлы и очереди

### Check-in / Check-out — `DANGEROUS`

- **Открытие и задача:** dock из Workspace Panels/контекста объекта. Аналоги:
  `Ui_checkInOutWidget`, `Ui_checkInOutTabWidget`, fast controls и options. Готовит и
  выполняет check-in, checkout/get, open/import/reference.
- **Реально:** target, object tabs, process/context, выбор и DnD файлов, naming preview,
  version/description/options, payload, Add to queue, прямой Check-in, progress,
  retry/cancel, snapshot/file refresh, checkout/download и DCC actions через integration API.
- **Только визуально/ограниченно:** отмена не гарантирует прерывание уже необратимой
  серверной стадии; DCC actions отключены вне подходящего host. Naming Editor показывает
  расчёт, но не является полноценным редактором naming rules.
- **Данные и фон:** серверный/local pools выполняют naming, копирование, snapshot/check-in
  и загрузку. Меняются TACTIC, repository, snapshots и QSettings вкладок. Просмотр target
  безопасен; Check-in/Download/Open/Import/Reference — нет.
- **Расширение:** отдельная история object tabs в Check-in/Out создана для QML; в
  оригинальном окне текущий выбранный tree item просто питал общие check-in panels.

#### Почему обычное выделение что-либо показывает

1. `ApplicationController.select_result_node()` меняет selection и испускает
   `selected_node_changed`.
2. `CheckinOutController` постоянно подписан на этот сигнал. Его `_selection_changed()`
   принимает sObject/process/snapshot, создаёт или активирует объектную вкладку,
   сохраняет её в `checkinOut/tabs`, загружает process/context и запускает naming preview.
3. В оригинальном `Ui_searchWidget.selection_changed()` selection обновлял versions,
   preview и текущий item связанных check-in panels. Создание отдельной истории вкладок
   на каждый выбранный объект и сохранение её между запусками явно не предусматривалось.
4. **Обычное выделение не добавляет Commit Queue item и не отправляет check-in.** Запись
   очереди появляется только после `queue_current_operation()`, команды Drop Plate
   `add_selected_to_queue()` либо восстанавливается из `commitQueue/pending`.
5. Риск всё же есть: уже добавленные в форму файлы остаются staged при смене обычного
   selection, а naming пересчитывается для нового target. Последующее невнимательное
   нажатие Add to queue/Check-in может подготовить операцию не для того объекта.
6. Ожидаемый сценарий: явно выбрать target → открыть Check-in/Out → добавить файлы →
   выбрать process/context/options → проверить naming/repository → отдельно нажать
   Add to queue или Check-in. Object tabs должны обозначать только target/history, а не очередь.

### Commit Queue — `DANGEROUS`

- **Открытие:** Workspace Panels, контекстные команды и Check-in/Drop Plate. Аналоги:
  `Ui_commitQueueWidget`, `Ui_commitItemWidget`.
- **Реально:** Python-owned payload, add/remove/reorder/select, редактирование разрешённых
  параметров, commit one/selected/all, последовательное выполнение, stages/progress,
  retry/cancel и сохранение незавершённых записей в QSettings.
- **Странно:** восстановленная после прошлого запуска запись может восприниматься как
  результат свежего selection. Clear удаляет неактивные записи; изменённый payload
  помечается для повторной проверки, но его корректность окончательно выясняется при run.
- **Данные и фон:** вызывает тот же Check-in executor, меняет server/repository и обновляет
  snapshots/files. Осмотр безопасен; изменение/удаление меняет сохранённую очередь,
  Commit — только на тестовом проекте.
- **Смысл:** полноценная рабочая часть клиента, не самостоятельный второй engine.

### Drop Plate — `DANGEROUS`

- **Открытие:** Workspace Panels. Аналоги: `Ui_dropPlateWidget` и matching workflow.
- **Реально:** DnD/выбор файлов и каталогов, асинхронный рекурсивный сбор, grouping,
  sequences, matching status, process/context, remove/clear и явная передача выбранного
  в Commit Queue. Сам Drop Plate commit не выполняет.
- **Странно:** process/context берутся из общего Check-in target, поэтому обычная смена
  selection может изменить смысл подготовленных элементов.
- **Данные и фон:** local pool читает каталоги; queue action создаёт сохраняемые payloads.
  На копии каталога сбор безопасен, но большие деревья дают нагрузку; передача в очередь
  меняет persistent state. Имеет смысл как основная входная точка пакетного check-in.

### Matching Templates Editor — `ORIGINAL_PARITY`

- **Открытие:** из Drop Plate и Configuration. Аналог: `Ui_matchingTemplateConfigWidget`.
- **Реально:** CRUD, duplicate, enable, priority/order, pattern, process/context mapping,
  example test, Save/Cancel. Использует существующий формат.
- **Побочный эффект:** сохранение меняет templates; открытый Drop Plate повторно сопоставляет
  уже собранные пути. Тест pattern безопасен, Save лучше проверять на копии настроек.

### Preview, Attachments, Naming и Screenshot — `DANGEROUS`

- **Открытие:** кнопки Check-in/Out; Screenshot Maker также зарегистрирован отдельным окном.
  Аналоги: preview/attachment widgets, naming preview и `Ui_screenShotMakerDialog`.
- **Реально:** Preview/Attachments используют общую file preparation и выполняют check-in;
  Naming только пересчитывает preview; Screenshot захватывает экран во временный PNG,
  добавляет его в staged files и открывает Preview.
- **Придумано:** один `FilePreparationEditor` переиспользуется как три «редактора» и при
  активации меняет mode/process/context общей Check-in формы. Названия обещают большую
  независимость, чем реально есть.
- **Данные и фон:** capture пишет temp-файл; upload/check-in меняет server/repository.
  Naming preview безопасен, capture оставляет локальный файл, Save/Check-in опасен.

### Repository Editor и Repository Sync — `DANGEROUS`

- **Открытие:** Configuration, signed-out экран и service menu; Sync также отдельное окно.
  Аналоги: repository editor и repo sync queue.
- **Реально:** platform paths, availability/default/mapping, Save/Cancel; discovery,
  download queue, progress, retry/cancel, overwrite и local-state refresh.
- **Данные и фон:** Save меняет общие repository settings/env и зависимые UI; Sync пишет
  файлы через существующий downloader. Проверка доступности не рекурсивна. Безопасны
  просмотр и Cancel; Save/Download проверять только на тестовом mapping.

### Watch Folders — `DANGEROUS`

- **Открытие:** Workspace Panels. Аналог: `Ui_projectWatchFoldersWidget`.
- **Реально:** CRUD, enable, repository/path/project/process/context/template, status,
  last scan/error, manual scan и start/stop существующего watcher.
- **Данные и фон:** сохраняет настройки, может создавать/наблюдать каталоги; найденные
  файлы передаются в подготовительный workflow, не commit автоматически. Тестировать
  только на временном каталоге. Полезен как расширение пакетной работы.

## Объекты и настройки

### Configuration — `ORIGINAL_PARITY`

- **Открытие:** меню `…` главного окна и signed-out экран. Аналог:
  `Ui_configuration_dialogWidget` со страницами Main/Server/Project/Global/Check-in/Maya.
- **Реально:** загрузка, validation, server test/login, Apply/OK/Cancel/Reset, unsaved
  confirmation, repositories, search/check-in defaults и window state.
- **Данные и фон:** изменяет существующие config keys, env/server/repository/theme;
  test/login асинхронны и могут заменить session/ticket. Cancel безопасен; Apply/OK
  влияет на текущий клиент, часть параметров требует повторной инициализации.
- **Отдельные page windows:** `server`, `project`, `checkin_preferences`,
  `checkinout_preferences`, `global_preferences`, `maya_preferences` зарегистрированы,
  но штатно используются как страницы Configuration, а не самостоятельные окна.

### Server Presets — `UNCLEAR_BEHAVIOR`

- **Открытие:** Server page Configuration. Аналог — preset selector/configuration workflow;
  отдельного равного оригинального редактора в основной цепочке не установлено.
- **Реально:** список имён, add/rename/delete/default и Save через `env_server`; секреты
  не показываются. Серверные поля редактируются на соседней Server page.
- **Странно:** создание имени ещё не гарантирует наличие полного server definition;
  окно выглядит как редактор presets, но фактически управляет преимущественно индексом
  имён. Save меняет постоянную server config и выбор default. Cancel безопасен.
- **Смысл:** полезен только после явного объединения с полями адреса/proxy/auth.

### Add/Edit sObject — `DANGEROUS`

- **Открытие:** Add в results/context; Edit Info использует тот же schema-driven editor.
  Аналоги: `Ui_addTacticSobjectWidget` и QTactic field workflow.
- **Реально:** schema/default/current values, базовые/relation/user/file/preview fields,
  validation, create/update, loading guard, error и refresh моделей.
- **Данные и фон:** server pool читает schema и выполняет insert/update/file preparation.
  Открытие/Cancel безопасны; Submit создаёт или изменяет sObject.
- **Добавлено:** единая schema-driven форма вместо класса QWidget на каждый field type;
  это осмысленная архитектура нового клиента.

### Link/Unlink, Delete и Duplicate sObject — `DANGEROUS`

- **Открытие:** контекст объекта. Аналоги: link/delete/duplicate dialogs.
- **Реально:** async поиск relation target, link/unlink, confirmations, delete/duplicate
  и refresh затронутых моделей. Dependency preview не равен полному дереву оригинала.
- **Тест:** только Cancel безопасен; все подтверждения мутируют TACTIC.

### Columns Editor — `USEFUL_EXTENSION`

- **Открытие:** context/Database Editor. Аналог: columns/display editor.
- **Реально:** порядок, visibility, width/label/display options, save/cancel и обновление
  зависимых моделей. Меняет пользовательскую конфигурацию представления, не schema.
- **Странно:** полноценного TACTIC Column Editor для физической schema mutation нет;
  его функции нельзя считать реализованными этим окном. Тест с Cancel безопасен.

### TACTIC Column Editor — `VISUAL_ONLY`

- Отдельного доступного QML-интерфейса безопасного добавления/изменения server columns
  с оригинальным confirmation/permissions не найдено. Database Editor меняет значения,
  Columns Editor — отображение; ни один из них не заменяет schema editor.

### Maya Open/Import/Reference Options — `DANGEROUS`

- **Открытие:** из checkout actions; общий `MayaOptionsView` получает mode. Аналоги:
  Maya open/import/reference option dialogs.
- **Реально:** общие и mode-specific options, persist, confirmation и вызов существующего
  integration API; вне Maya controls disabled с причиной.
- **Данные и фон:** в DCC открывает/импортирует/reference scene и меняет Maya session.
  В standalone безопасно проверить disabled state; операцию — только в тестовой Maya scene.

## Коммуникация

### Tasks — `DANGEROUS`

- **Открытие:** Tasks dock и кнопки карточек/items. Аналоги: `Ui_tasksDockWidget`, task widgets.
- **Реально:** список, refresh, create/edit/delete, assignee, status, process, dates,
  progress, description, validation и точечное обновление текущего object model.
- **Данные и фон:** server pool читает и мутирует task sObjects; selection меняет контекст.
  Просмотр безопасен, Save/Delete/статусы — только на тестовой задаче.

### Notes — `DANGEROUS`

- **Открытие:** Notes dock и кнопки Notes на карточках/items. Аналог: notes timeline.
- **Реально:** history по выбранному объекту/process, create/reply, delete собственного
  сообщения, retry, attachment candidates и download/open attachment.
- **Данные и фон:** `CommunicationController` вызывает note API и snapshot/download paths.
  Просмотр безопасен; Send/Delete/Download имеют серверный или файловый эффект.

### Messages — `UNCLEAR_BEHAVIOR`

- **Открытие:** bell и user menu открывают floating window `messages`.
- **Реально:** окно использует тот же `CommunicationView` и тот же selected-object notes
  controller, поэтому показывает timeline текущего sObject, а не адресную переписку.
- **Не подключено:** users/subscriptions/conversations оригинального `Ui_messagesWidget`,
  отдельный recipient и полноценное unread/history сообщений не обнаружены.
- **Странно:** заголовок MESSAGES обещает глобальные сообщения, но selection главного
  workspace определяет содержимое. Отправка создаёт note на объекте. Для записи тест
  небезопасен. Как расширение клиента в текущем виде смысла не имеет без переименования
  в Notes или подключения настоящего message workflow.

### Rich Edit — `VISUAL_ONLY`

- Composer поддерживает plain text, безопасное отображение и ссылки, но отдельный
  универсальный rich editor и полный формат/toolbar оригинала не перенесены. Attachments
  уходят через общий preparation/check-in workflow. Это часть Notes, не самостоятельный UI.

### User UI — `VISUAL_ONLY`

- **Открытие:** avatar в верхней панели. Аналог: user icon/menu.
- **Реально:** показывает initials/name и открывает Messages; полноценные profile/account,
  session actions, subscriptions или user settings не подключены.
- **Данные/эффекты:** само меню read-only. Имеет смысл как будущая точка account actions,
  но сейчас визуально обещает больше, чем выполняет.

### Notifications — `USEFUL_EXTENSION`

- **Открытие:** глобальный `NotificationStack`, автоматически от app/check-in/download/
  tasks/communication/error signals. Аналоги — notify widgets и status messages.
- **Реально:** info/warning/error/progress/completion, максимум одновременно видимых,
  dedupe повторяющихся ошибок и корректные timers. Полный traceback остаётся в Debug Log.
- **Не является:** историей подписок, inbox или заменой modal confirmation. Toast не меняет
  данные и безопасен. Это полезная общая функция нового клиента.

### Feed — `NOT_REACHABLE`

- Самостоятельного QML Feed, controller/model и маршрута открытия не найдено. Notes timeline,
  Notifications и окно с названием Messages не образуют feed: у них нет агрегированного
  источника событий, подписок и собственной истории. Пользователь тестировать его не может.

## Обслуживание и специальные инструменты

### Update UI — `UNCLEAR_BEHAVIOR`

- **Открытие:** окна `update` и `create_update` зарегистрированы, но штатной команды в
  обычных меню не найдено. Аналоги: update/create-update dialogs.
- **Реально:** local history, async remote refresh, selection, restart-to-update; Create
  Update формирует metadata/archive через существующий update API.
- **Странно:** cancel remote refresh инвалидирует результат в UI, но не обязательно
  останавливает worker; выбранная строка визуально хранится, а restart вызывает общий
  update restart без явной передачи выбранной версии. Связь выбора с применяемым архивом
  требует подтверждения.
- **Данные и фон:** remote read, файловые metadata/archive и restart процесса. Окно истории
  безопасно, Create/Update and restart — опасны. До появления штатного route и проверки
  выбора это не следует считать готовым пользовательским updater.

### Screenshot Maker — `DANGEROUS`

- **Открытие:** из Check-in/Out; отдельное окно зарегистрировано. Аналог:
  `Ui_screenShotMakerDialog`.
- **Реально:** capture существующим API, preview/accept/cancel; Accept создаёт temp image,
  добавляет его в staged files и открывает Preview Editor.
- **Эффекты:** локальный temp-файл и изменение общей Check-in формы; server upload происходит
  только после последующего подтверждения. Capture можно тестировать, затем Cancel и удалить temp.

### Script Editor — `DANGEROUS`

- **Открытие:** Configuration service menu. Аналог: `Ui_ScriptEditForm`.
- **Реально:** load/save source, history/output/errors, confirmation перед Run, local run
  в worker и попытка server run; traceback идёт в Debug Log, автоматического запуска нет.
- **Странно:** server path передаёт source как аргумент процедуры с пустой callable;
  соответствие реальному server script execution по коду не доказано. Cancel не может
  гарантированно остановить произвольный Python code.
- **Эффекты:** local script имеет права приложения, server script потенциально имеет права
  пользователя TACTIC. Безопасны открытие/редактирование несохранённой копии; Run/Save
  нельзя тестировать вне изолированного контура.

### TACTIC API Client — `EXPERIMENT`

- **Открытие:** Configuration service menu. Аналог: `Ui_TacticApiClient`.
- **Реально:** QML `ServiceToolView` запускает/останавливает отдельный процесс
  `tactic_api_server.py`, показывает state/output/errors и скрывает секреты.
- **Не перенесено:** это supervisor, а не QML-копия полного API Client UI; дочерний процесс
  по-прежнему содержит собственное пользовательское окно/workflow.
- **Эффекты:** создаёт listener/process, способный обслуживать внешние DCC-клиенты.
  Просмотр безопасен; Start/Stop проверять при отсутствии рабочих клиентов. Полезность есть
  как service control, но название должно ясно сообщать, что запускается локальный bridge.

### TACTIC Server — `DANGEROUS`

- **Открытие:** Configuration service menu. Аналог: `Ui_TacticServer`.
- **Реально:** тот же supervisor запускает/останавливает `thlib/tactic_server.py`, собирает
  stdout/state/errors и просит подтверждение остановки.
- **Не является:** UI удалённого web-сервера TACTIC и не даёт административных функций.
  Название неоднозначно: это локальный Handler listener/process.
- **Эффекты:** влияет на локальные/внешние интеграции и незавершённые запросы. Только status
  безопасен; Start/Stop — на машине без рабочих клиентов. Как service monitor полезен,
  но как «TACTIC Server UI» вводит в заблуждение.

### Debug Log и Error/Login dialogs — `USEFUL_EXTENSION`

- **Открытие:** Configuration menu и автоматически при ошибке/auth bootstrap.
- **Реально:** категории Python/QML/server/missing files, session files/history/import,
  filters, Show stack trace, retry/dismiss/config/login; Login обновляет session/ticket.
- **Данные и фон:** Debug Log read-only; Retry повторяет исходную операцию, Login делает
  auth request. Просмотр логов безопасен, повтор сетевой mutation зависит от исходной команды.

## Сводка остальных зарегистрированных UI

| Интерфейс | Статус | Реальное назначение и тестовый риск |
|---|---|---|
| Project chooser | `ORIGINAL_PARITY` | Выбор/загрузка проекта; серверное чтение, безопасно |
| Login/server gate | `ORIGINAL_PARITY` | Bootstrap, ticket и server path; меняет session/config |
| Repository availability gate | `USEFUL_EXTENSION` | Не пускает в workspace без repository mapping |
| Check-in Options/Fast Controls | `ORIGINAL_PARITY` | Общие process/context/options Check-in; меняют staged payload |
| SObject Info | `NOT_REACHABLE` | Окно зарегистрировано; данные дублируют details/editor |
| Filter Presets window | `ORIGINAL_PARITY` | См. Filter Editor; меняет сохранённые filters |
| Database Batch Editor | `DANGEROUS` | Пакетные server field updates; только тестовый проект |
| File preparation editors | `UNCLEAR_BEHAVIOR` | Режимы общего Check-in workflow, не независимые редакторы |
| Create Update | `DANGEROUS` | Пишет version metadata/archive; route не найден |
| Repository Editor | `DANGEROUS` | Меняет mapping всех файловых операций |
| Maya options | `DANGEROUS` | Реальные DCC actions только после подтверждения |
| Delete/Duplicate confirmations | `DANGEROUS` | Реальные server mutations |
| Dock/floating window manager | `USEFUL_EXTENSION` | Layout, dock/float/detach и QSettings; безопасно |

`ActionMenu`, `WorkspaceCard`, `WorkspaceResultItem`, preview/delegates, MD3 controls,
dialogs, tooltips, shadows и indicators — presentation components, а не самостоятельные
пользовательские UI. Их actions учтены у интерфейсов, которые ими владеют.

## Главные выводы перед ручным тестированием

1. Selection не отправляет check-in и не создаёт queue item, но меняет target и naming
   уже открытой Check-in формы; это главный скрытый риск рабочего процесса.
2. Messages фактически является вторым входом в Notes текущего объекта; Feed отсутствует,
   User UI почти визуален.
3. Assets Browser и Update зарегистрированы, но штатно недостижимы; самостоятельность
   Assets Browser от главного workspace отсутствует.
4. Preview/Attachments/Naming — режимы одной Check-in формы, а не независимые редакторы.
5. API Client и TACTIC Server — supervisors локальных процессов, не полные QML-порты и
   не администрирование удалённого TACTIC.
6. Без тестового TACTIC безопасно проверять layout, фильтры до Apply, naming preview,
   Debug Log, notifications и Cancel. Check-in/queue, object/task/note edits, repository,
   watcher, update, scripts и service start/stop требуют изолированного контура.
