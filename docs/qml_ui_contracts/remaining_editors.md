# Контракт оставшихся редакторов

Проверены только непосредственно связанные классы, точки открытия, QML-окна и
API восьми редакторов. `thlib/side` не анализировался. Большинство QWidget
редакторов строятся программно и не имеют собственной `.ui`-формы.

## 1. Preview Editor

- **Класс:** `Ui_previewsEditorDialog`; элементы создаёт
  `Ui_previewItemWidget` через `global_functions.add_preview_item()`.
- **Форма:** собственной формы нет; элемент использует
  `thlib/ui/items/ui_preview_item.ui`.
- **Открытие:** кнопка Edit previews в `commitWidget` и preview-поле
  `QTacticPreviewWidget`; окно модальное.
- **Вход:** сгруппированные file objects и список `QPixmap` screenshots.
- **Результат:** только просмотр текущего набора; диалог не возвращает изменённую
  коллекцию и не содержит подключённых действий редактирования.
- **QML:** отдельный Preview Editor использует общую Python-модель файлов,
  naming preview и асинхронный check-in с progress/cancel/retry.
- **Зависимости:** Check-in/Commit Queue, file objects, preview classification,
  repository paths.
- **Ограничение:** удаление убирает подготовленный файл; серверное удаление
  preview не добавлено, поскольку его нет в контракте исходного окна.

## 2. Attachments Editor

- **Класс:** `Ui_attachmentsEditorWidget`; элементы создаёт
  `Ui_attachmentItemWidget`.
- **Форма:** собственной формы нет.
- **Открытие:** разворачиваемая область `Ui_notesWidget` после выбора файлов,
  drop или screenshot.
- **Вход:** сгруппированные file objects и screenshots.
- **Результат:** визуальный список; исходные коллекции принадлежат Notes editor.
- **QML:** Attachments Editor хранит staging в общей Python-модели, принимает
  выбор/drop файлов и передаёт подготовленную операцию в check-in/Commit Queue.
- **Зависимости:** Notes, MatchTemplate, Check-in/Commit Queue, Screenshot Maker,
  attachment snapshots, Repository Sync.
- **Интеграция:** кнопка вложения в Communication открывает редактор без второго
  upload workflow.

## 3. Columns Editor

- **Класс:** `Ui_columnsEditorWidget`.
- **Форма:** нет; toolbar, definitions и tabs создаются программно.
- **Открытие:** скрытый dock `columns_viewer_dock` внутри Check-in/Out; selection
  search tree передаёт один item либо выбранные items.
- **Вход:** project, stype, search item(s), definition (`edit`/`table`).
- **Результат:** single commit через sObject `set_value()/commit()` или
  `update_multiple(..., triggers=True)` для нескольких объектов.
- **QML:** `columns_editor` зарегистрирован как floating window, но показывает
  только `columnsModel`; Move/Apply не подключены к API.
- **Зависимости:** stype definitions, schema columns, выбранные sObject/snapshot,
  Tactic Column Editor, multi-update.
- **Рекомендация:** создать Python model definitions/columns и переиспользовать
  schema-driven field delegates; отдельно сохранить multiple-edit semantics.

## 4. Tactic Column Editor

- **Класс:** `Ui_tacticColumnEditorWidget`.
- **Форма:** нет.
- **Открытие:** создаётся вкладкой `Ui_columnsEditorWidget` для каждой колонки.
- **Вход:** sObject, column, stype, `multiple_mode`.
- **Результат:** `get_changed_data()`; сохранение выполняет родительский Columns
  Editor. В самом классе реально поддержаны только `text` и `varchar`.
- **QML:** прямого аналога нет; `SObjectFieldEditor` уже имеет более полный набор
  schema-driven delegates, но не подключён к Columns Editor.
- **Зависимости:** column info, definitions, rich edit; локальные lock/edit
  состояния QWidget не являются серверным контрактом.
- **Рекомендация:** не переносить класс механически; адаптировать существующую
  QML field model к single/multiple column editing.

## 5. Server Presets Editor

- **Класс:** `Ui_serverPresetsEditorWidget`.
- **Форма:** нет.
- **Открытие:** кнопка Edit Server Presets страницы Server Configuration.
- **Вход:** `env_server.get_server_presets()` и preset names.
- **Результат:** add/remove, защита `default`, Save через
  `save_server_presets_defaults()`; Cancel перечитывает сохранённые presets.
- **QML:** отдельный MD3 editor поддерживает add/remove, защиту `default`,
  Save/Cancel и обновляет общий список presets без хранения credentials.
- **Зависимости:** `env_server`, Configuration controller, server bootstrap;
  изменение активного сервера требует существующего restart/reconnect сценария.
- **Реализация:** использует методы `env_server` и существующий preset format;
  активное подключение меняется только через Configuration.

## 6. Screenshot Maker

- **Класс:** `Ui_screenShotMakerDialog`.
- **Форма:** нет.
- **Открытие:** camera action в Commit Queue и preview field; временно скрывает
  главное/DCC/queue окна.
- **Вход:** выбранная пользователем область desktop.
- **Результат:** `screenshot_pixmap`, затем preview/check-in коллекция.
- **QML:** maker позволяет выбрать область, использует Qt desktop capture API и
  передаёт PNG в общую Python-модель подготовки preview.
- **Зависимости:** desktop capture, multi-screen/DPI, window visibility,
  QPixmap→file object, Commit Queue; текущий `grabWindow()` устарел для Qt 6.
- **Проверка:** Windows scaling, несколько экранов и DCC host требуют ручной
  проверки.

## 7. Script Editor

- **Класс:** `Ui_ScriptEditForm`.
- **Форма:** нет; editor/output/tree собираются программно.
- **Открытие:** Main menu, tray/float notify, TACTIC Server и API Server startup;
  глобальная ссылка `env_inst.ui_script_editor`.
- **Вход:** source, language, local/server execution mode, project scripts
  `config/custom_script`, script path.
- **Результат:** stdout/stderr, выполнение local/server code, создание и
  сохранение server scripts, сохранённое состояние окна.
- **QML:** реализованы загрузка/создание/сохранение, исходные языки и local/server
  Run с обязательным подтверждением и output.
- **Зависимости:** console/stream, server execution, permissions, current project,
  `tactic_classes.execute_procedure_serverside`, script storage.
- **Ошибки:** краткое состояние остаётся в редакторе, полный traceback пишется
  в Debug Log; автоматического выполнения нет.

## 8. Naming Editor

- **Класс:** `Ui_namingEditorWidget`.
- **Форма:** нет.
- **Открытие:** код кнопки в Check-in/Out закомментирован.
- **Вход/результат:** отсутствуют; конструктор только печатает сообщение.
- **QML:** Naming Preview выделен в самостоятельное окно; пути рассчитывает
  `CheckinOutController` через `get_virtual_snapshot()`.
- **Зависимости:** naming definitions, virtual snapshot и repository mapping.
- **Ограничение:** editing naming rules не добавлен: исходный класс его не
  реализует и отдельного контракта правил пока нет.

## Columns и Tactic Column Editor

Columns Editor реализован отдельными `ColumnsEditorController` и
`ColumnsEditorView`. Для колонок текущего search type поддержаны порядок,
видимость, display label и ширина. Настройки валидируются, сохраняются по
project/search type через QSettings, поддерживают Apply, Cancel и Reset.

После Apply обновляются общая columns model, представление результатов и Database
Editor. Database Editor фильтрует и сортирует поля по применённым настройкам;
формирование серверного search query не изменяется.

Tactic Column pane редактирует значение существующей schema-колонки выбранного
sObject. Типы integer/float валидируются до отправки, системные колонки read-only,
а сохранение использует существующий `update_selected_item_fields()` и
`update_multiple(..., triggers=True)`.

Создание или alter физической DB-колонки намеренно недоступны: проверенный код не
содержит принятой schema-mutation обёртки и обязательного подтверждения. Добавление
колонки в display выполняется включением скрытой колонки действующей схемы.
