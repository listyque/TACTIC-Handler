# Контракт Drop Plate и Matching Templates

## Граница и компоненты

QWidget-реализация состоит из `Ui_dropPlateWidget` и
`Ui_matchingTemplateConfigWidget`. Формы `ui_drop_plate.ui` и
`ui_drop_plate_config.ui` задают дерево файлов, quick config, progress и таблицу
шаблонов. Drop Plate встраивается как проектный dock в `Ui_checkInOutWidget`;
process/context и запуск Check-in находятся снаружи, в выбранном объекте и fast
controls.

Текущий QML Drop Plate — встроенный `dropPlateContent` в `DockHost.qml` с
`WorkspaceState.drop_model`. DnD с `WorkspaceCard` и `WorkspaceResultItem`
попадает в `ApplicationController.queue_dropped_files()`. Отдельное окно
Matching Templates использует общий `editorListForm` и пустой `templateModel`.

## Контракт сценариев

| Сценарий | QWidget / Python API | Текущий QML | Статус |
|---|---|---|---|
| Drag-and-drop | Принимает URL, преобразует через `toLocalFile()` и запускает `get_files_objects()` в `env_inst.local_pool` | DnD на карточку/item добавляет локальные пути в `drop_model`; сам dock не имеет DropArea | Частично |
| Добавление файлов | Ненативный multi-file dialog и вставка путей из clipboard | Add file, folder и context actions вызывают только `notice()`; toolbar `add` создаёт фиктивную строку | Отсутствует функционально |
| Каталоги | Каталог принимается через DnD | Путь каталога добавляется как обычная строка | Частично визуально |
| Рекурсивный сбор | `includeSubfoldersCheckBox`; `os.walk()` выполняется внутри `local_pool` | Отсутствует | Отсутствует |
| Список файлов | Дерево: pretty name, sequence info, pretty/base type, path; хранит Python `FileObject` отдельно от отображения | Плоские роли title/path/size/process/checked/status | Частично |
| Grouping | `MatchTemplate.get_files_objects()` группирует совпавшие пути в `FileObject`; `Group Checkin` передаёт группу одной операцией, иначе создаёт операцию на объект | Группировки и Group Checkin нет | Отсутствует |
| Sequences | FRAME, UV, UDIM, LAYER и комбинации; `FileObject` отдаёт frame ranges, tiles, layer, metadata и полный список файлов | Каждый путь независим; sequence metadata отсутствует | Отсутствует |
| Matching templates | 19 встроенных выражений; первые два обязательны, восемь включены по умолчанию; padding фактически всегда 3 | Пустая presentation-модель | Отсутствует функционально |
| Preview шаблона | `MatchTemplate.get_preview_string()` и `get_type_string()` заполняют Preview/Type | Отсутствует | Отсутствует |
| Preview результата | После grouping дерево показывает имя группы, frames/tiles/layer и тип | Показывает только имя, размер и process | Частично |
| Process/context | Берутся из выбранного item и fast controls; Drop Plate хранит только файлы и keep filename | DnD записывает process/context-target в роль `process`; смены process/context в dock нет | Частично |
| Ошибки | Ошибка worker идёт в `gf.error_handle`; отдельного row error нет | `stat()` игнорирует ошибку размера; ошибок grouping/scan нет, потому что сами операции отсутствуют | Частично |
| Удаление | Clear all и удаление выбранных; после удаления индексы `tree_items` не пересчитываются, поэтому повторное multi-remove требует ручной проверки | Clear работает; удаления одной строки и рабочих context actions нет | Частично |
| Commit Queue | `save_file()` берёт выбранные `FileObject`, group/keep filename, process/context и создаёт одну или несколько подготовленных операций | Кнопка лишь уведомляет; `drop_model` не передаётся в `CheckinOutController`/`CommitQueueController` | Отсутствует |
| Сохранение | Drop Plate сохраняет include subfolders, keep filename и group check-in через настройки Check-in/Out; config dialog сохраняет только geometry | `drop_model` и template state не сохраняются | Отсутствует |

## Matching и naming API

`gf.MatchTemplate` является рабочим API распознавания и должен остаться
Python-ответственностью. Он сортирует пути, применяет шаблоны от наиболее
специфичных типов к простым, объединяет совпадения и создаёт `FileObject`.
`FileObject` предоставляет полный список файлов, тип, extension, metadata,
frame ranges, UV/UDIM tiles, layer и pretty name. Эти объекты нельзя передавать
в QML; модель должна публиковать безопасные роли, сохраняя объект по внутреннему
ID на Python-стороне.

Naming выполняется позже через уже используемые
`tc.get_virtual_snapshot()`, repository и payload `CheckinOutController`.
Drop Plate не должен рассчитывать repository target paths самостоятельно.

## Подтверждённые ограничения QWidget UI

- `templatesTreeWidget.itemChanged` не подключён: изменение checkbox не
  обновляет `current_templates_list`.
- Add new и Edit из формы не подключены; delete отсутствует.
- `get_min_padding()` жёстко возвращает 3, хотя Check-in Options содержит
  `minFramesPaddingSpinBox`.
- config dialog сохраняет только положение и размер, но не выбранные шаблоны.
- Filter by Extension/Filename визуально включается, но фильтрация списка не
  реализована в классе.
- Paste from clipboard работает только для текста с путями; clipboard files и
  неверные строки не получают отдельного статуса ошибки.

## Безопасная граница QML

Нужен специализированный Python controller/model, который асинхронно принимает
файлы и каталоги, выполняет recursive scan и `MatchTemplate`, хранит
`FileObject` по ID и отдаёт роли: display name, source paths/count, type,
extension, frame range, tiles, layer, size, process, checked и error.
Подготовка операции должна идти через `CheckinOutController`, затем в уже
существующий `CommitQueueController`; отдельную очередь создавать нельзя.

## Рекомендуемые этапы

1. Реализовать Python model/controller Drop Plate: file dialog, DnD, directory
   scan, grouping, sequences, remove/clear и состояния loading/error.
2. Реализовать рабочую модель Matching Templates с preview/type, обязательными
   default patterns, padding и сохранением через существующие Check-in Options.
3. Добавить выбор process/context и preview подготовленного payload, затем
   передать отмеченные группы в Check-in preparation и Commit Queue.

## Ручные проверки

- большие и вложенные каталоги, symlink/reparse points и недоступные пути;
- смешанные одиночные файлы, sequence, layer, UV и UDIM с padding 1–9;
- конфликт нескольких включённых шаблонов и одинаковые файлы из разных DnD;
- group/individual check-in, keep filename и очистка после успешного commit;
- повторное удаление после удаления нескольких строк;
- восстановление шаблонов и Drop Plate options после перезапуска.

## Этап 23 — Drop Plate

Реализован отдельный `DropPlateController` с role-based моделью. File dialog,
Folder dialog и DropArea передают только локальные URL; сбор каталогов и
`MatchTemplate.get_files_objects()` выполняются в существующем
`env_inst.local_pool`. QML не обходит файловую систему и не содержит matching
выражений.

Модель хранит безопасные роли группы: display/path, file count, total size,
matching type, frame/tiles/layer summary, process, context, checked, status и
error. `FileObject` остаётся в Python по внутреннему `groupId`. Реализованы
добавление, рекурсивный сбор, deduplication, удаление, clear, grouping и
sequence/UV/UDIM/layer status.

Process/context используют выбранный объект и API `CheckinOutController`.
Каждая отмеченная группа преобразуется в сериализуемый preparation payload с
исходными путями, template и metadata и добавляется в существующий
`CommitQueueController`. Commit из Drop Plate не запускается.

Matching Templates Editor намеренно не реализован: на этом этапе применяется
зафиксированный набор включённых шаблонов QWidget Drop Plate с padding 3.

Автоматически проверены рекурсивный сбор, распознавание sequence, сериализация
payload, Python syntax и QML offscreen loading. Вручную проверить file/folder
dialogs, DnD каталогов, UV/UDIM/layer группы и реальный check-in sequence через
Commit Queue.

## Этап 24 — Matching Templates Editor

Реализован `MatchingTemplatesController` с отдельной role-based моделью и
`MatchingTemplatesView`. Поддержаны создание, изменение pattern, duplication,
удаление, enable/disable, изменение priority, process/context mapping и
проверка выражения на имени файла. Обязательные `$FILENAME` и
`$FILENAME.$EXT` нельзя удалить или отключить.

Pattern хранится в исходном формате `MatchTemplate`; mapping является
Python-side метаданными выбора применимых patterns и не меняет синтаксис
выражения. Сохраняется упорядоченный список в существующем QSettings namespace.
Save публикует `templatesChanged`, Cancel восстанавливает последнюю сохранённую
версию.

Drop Plate получает активные patterns с учётом process/context. После Save
открытые группы повторно распознаются в `local_pool` по исходным путям; QML не
выполняет matching. Редактор подключён к существующему окну
`matching_templates` и открывается из toolbar Drop Plate.

Подтверждён и исправлен дефект priority: `MatchTemplate` преобразовывал входной
список в `set` и терял порядок. Ordered deduplication сохраняет configured
priority, не меняя regex, классификацию типов и matching pipeline.

Автоматически проверены create/edit/validation/duplicate-order, mapping,
pattern test, save/cancel, сохранение priority, Python syntax и QML loading.
Вручную проверить rematch большого открытого Drop Plate и конфликт нескольких
patterns одного matching type.
