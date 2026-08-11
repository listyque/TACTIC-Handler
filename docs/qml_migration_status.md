# Статус миграции на PySide6/QML

## Итоговая функциональная матрица

| Функция | Legacy UI | QML UI | Статус | Различия | Критичность |
|---|---|---|---|---|---|
| Запуск | `main_standalone.py/.pyw`, host launchers | `main_qml.py`, `launch.py`, `TACTIC_HANDLER_UI=qml` | готово | После Block F общий selector запускает QML по умолчанию; legacy доступен явно через `--ui legacy`/`TACTIC_HANDLER_UI=legacy`; используется один `QApplication` | низкая |
| Login | Полный legacy login/bootstrap | Диалог login, ticket bootstrap, cancel/retry | требует ручной проверки | Пароль не сохраняется; неверный пароль и повторная авторизация требуют проверки на живом сервере | высокая |
| Server connection | `env_server`, ticket, server pool | Те же `env_server`, ticket и pool через нативные API проекта | требует ручной проверки | Есть ping, понятная ошибка и ограничение повторов; смена сервера требует ручной проверки | высокая |
| Проекты | Legacy project chooser/cache | `ProjectModel`, асинхронная загрузка и выбор | требует ручной проверки | Серверный источник общий; права доступа и несколько проектов проверить вручную | высокая |
| Главное окно и навигация | QWidget main window, sidebar, docks | QML shell, drawer, sections, dock/floating layout | готово | Presentation state отдельный, бизнес-данные общие | средняя |
| Поиск | Полный legacy search/filter pipeline | Асинхронный search, suggestions, paging/infinite mode, stale-result guard | требует ручной проверки | Основные фильтры переиспользуются; сложные комбинации фильтров нужно сравнить вручную | высокая |
| Search/workspace tabs | Legacy tabs и сохранение состояния | Постоянные модели вкладок, восстановление проекта/раздела/поиска | готово | QML presentation state хранится в modern QSettings | средняя |
| Дерево результатов | Полный legacy tree | Иерархия SObject/Process/Relation/Snapshot/File, lazy expansion | частично | Drag/drop и редкие relation-сценарии не покрыты полностью | высокая |
| Карточки | Legacy tile/card presentation | SObject/Process/Relation/Snapshot cards, drill-down, breadcrumbs | частично | Relation count известен только после загрузки; визуальное соответствие требует ручной проверки | средняя |
| Версии | Полный legacy versions tree | Асинхронная модель версий и отдельная панель | частично | Не все legacy context/version actions перенесены | высокая |
| Snapshots | Полный snapshot item/browser | Snapshot browser, версии, extension/file presentation | частично | Multi-file, versionless и missing repository требуют ручной проверки | высокая |
| Preview | Legacy local/web preview/cache | Lazy QML Image, web-first URL, локальный fallback | частично | Серверные 404 показывают fallback; repository path correctness зависит от конфигурации | средняя |
| Файлы и локальные пути | Полные File-object действия | Список файлов, путь, размер, exists/open/sync состояния | частично | Некоторые edit-info и специализированные file actions остаются legacy | высокая |
| Repository sync | Полный legacy queue/dialog | Discovery, queue, progress, speed, cancel, retry, completed/failed states | частично | Discovery/preset traversal частично повторяет legacy алгоритм; active-close требует ручной проверки | высокая |
| Tasks | Полный просмотр и редактирование | Реальная загрузка, отдельный Tasks dock, статусы и счётчики | частично | Часть команд меню пока только уведомляет и не выполняет mutation | высокая |
| Notes | Полный просмотр, ответы и вложения | Реальная загрузка, отдельный Notes dock и счётчики | частично | Добавление заметки/ответа и часть команд ещё не подключены к legacy mutation API | высокая |
| Вложения и drop | Legacy attachment/check-in workflow | Drop zones, очередь и attachment target | частично | Кнопка добавления attachment и часть queue actions не завершены | высокая |
| Контекстные команды | Полный набор по типу элемента | Реестр команд, реальные open/sync/watch/relations и часть mutation actions | частично | Редкие editors и некоторые меню остаются presentation-only | высокая |
| Check-in/check-out | Полный legacy workflow | Drop/commit/check-in panels и вызовы существующей логики | частично | Полный набор commit options и DCC-сценариев не перенесён | высокая |
| Watch folders | Полный legacy dialog/workflow | Модель, состояния и dock presentation | частично | Изменение сложной конфигурации требует legacy UI/ручной проверки | средняя |
| Настройки | Полный legacy configuration | Server/repository/appearance и набор QML configuration pages | частично | Часть страниц отображает данные, но не все операции редактирования подключены | высокая |
| Логирование | `dl.*`, terminal и legacy log | `dl.*`, Python logging, Qt/QML, API, traceback и debug model | готово | Большие server script payload усечены, полный traceback сохраняется | средняя |
| Ошибки | Legacy exception dialogs/log | Классификация, понятное сообщение, traceback, retry/cancel, deduplication | требует ручной проверки | Timeout, auth failure и HTTP 500 нужно воспроизвести вручную | высокая |
| Восстановление состояния | Legacy configs/QSettings | Геометрия, docks, tabs, проект, раздел, поиск и view mode | частично | Восстановление повреждённых/старых search filters требует дополнительных сценариев | средняя |
| Закрытие приложения | Legacy `closeEvent` и `exit_pools` | Idempotent shutdown, repository pool stop, `env_inst.exit_pools` | требует ручной проверки | Автоматический startup/close проходит; закрытие во время download проверить вручную | высокая |
| Legacy UI | Полный QWidget интерфейс и integrations | Не импортируется QML-слоем | требует ручной проверки | Import/launcher smoke проходит; полный Maya/Nuke/3ds Max запуск только в соответствующих host | высокая |
| DCC/host dialogs и script editor | Нативные legacy реализации | Открываются legacy или представлены частично | намеренно не переносится | Специализированные Maya/Nuke/3ds Max и rich editors остаются QWidget | низкая |

## Что полностью готово

- Безопасный выбор UI с legacy режимом по умолчанию и отдельным QML launcher.
- QML bootstrap, регистрация context properties, диагностика ошибки загрузки и idempotent shutdown.
- Каркас главного окна, навигация, вкладки и сохранение основного presentation state.
- Асинхронная инфраструктура запросов через существующий server pool без нового TACTIC client.
- Структурированный debug log с legacy/Python/Qt/API событиями и полным traceback.
- Архитектурная граница: QML не создаёт QWidget и не обращается напрямую к TACTIC API или файловой системе.

## Что осталось

- Завершить mutation-команды Tasks/Notes/attachments и проверить их legacy-семантику.
- Довести file/check-in/commit options, сложные context actions и multi-file snapshots.
- Свести repository-sync discovery к нейтральной общей операции вместо частичного повторения traversal.
- Завершить редактирование server/repository/configuration pages, которые сейчас только частично функциональны.
- Проверить сложные search filters, relation paths, versionless snapshots и повреждённое сохранённое состояние.

## Сценарии для ручной проверки

1. Успешный login, неверный пароль, cancel, повторная авторизация и сохранённая сессия.
2. Недоступный сервер, timeout, HTTP 500, смена server preset и восстановление соединения.
3. Переключение нескольких проектов, прав доступа, разделов и сохранённых search tabs.
4. Legacy/QML сравнение suggestions, сложных фильтров, paging и запоздалых результатов.
5. Глубокие Process/Relation деревья, карточный drill-down и возврат по breadcrumb.
6. Versionless/multiple snapshots, отсутствующий repository, preview 404 и локальный fallback.
7. Repository sync: exists, cancel, retry, failure и закрытие приложения во время download.
8. Tasks/Notes/attachments mutations, check-in/out и DCC-specific операции.
9. Полный legacy standalone и host integrations в Maya, Nuke и 3ds Max.

## Известные ограничения

- Некоторые Tasks/Notes/attachments/context menu actions пока presentation-only.
- Relation count нельзя получить до загрузки relation без отдельного тяжёлого серверного запроса.
- Preview зависит от корректных web/repository paths; серверный 404 приводит к fallback без падения UI.
- `ApplicationController` и `WorkspaceState` остаются крупными зонами сцепления; механическое разделение не выполнялось.
- QML получает много отдельных context models; публичные имена уже являются compatibility-контрактом.
- Modern QSettings хранит только QML presentation preferences; сервер, ticket и проекты остаются в `env_*`.

## Изменения legacy-кода и причины

- Legacy launcher не заменён: `launch.py` выбирает UI до импорта Qt stack и сохраняет legacy по умолчанию.
- Fixed-pitch editor font нормализован с `Fixedsys` на `Consolas` для совместимости с Qt 6 DirectWrite.
- Серверная, search, authorization, File-object и repository логика не переносилась из `thlib`.
- Защита от бесконечных повторов, stale search results и ошибочного сохранённого поиска добавлена в modern controller, не в legacy widgets.
- Modern repository queue получил минимальные QWidget-подобные visibility methods только для существующего `env_inst.ui_repo_sync_queue` контракта.

## Сохранённые публичные интерфейсы

- `main_standalone.startup`, старые `.py/.pyw` и host launchers.
- `thlib.environment.env_inst`, `env_mode`, `env_server`, `server_pool`, `local_pool` и `exit_pools`.
- Публичные функции `thlib.tactic_classes`, включая `server_query`, и legacy search helpers.
- Старые QWidget-классы, сигналы/callbacks, File objects и repository path API.
- Контракт repository queue: `schedule_file_object`, `is_all_downloads_done`, `isHidden`, `setHidden`, `show`, `hide`.

## Результаты автоматических проверок

- Legacy compatibility smoke: пройден.
- Компиляция всех 28 QML-компонентов: пройдена.
- QML offscreen startup и автоматическое закрытие: пройдены без зависшего процесса.
- Во время startup сервер вернул 404 для одного preview; ошибка обработана, но путь требует ручной проверки конфигурации.
