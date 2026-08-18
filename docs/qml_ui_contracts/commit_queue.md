# Контракт Commit Queue

## Граница аудита

Очередь состоит из `Ui_commitQueueWidget`, редактора `commitWidget` и строки
`Ui_commitItemWidget`. Формы: `ui_commit_queue.ui` задаёт splitter со списком,
редактором, Clear/Commit All/Close и status bar; `ui_commit_item.ui` задаёт
preview 64×64, имя, описание и progress overlay.

Текущий QML dock находится в `DockHost.qml` и использует `commitModel`.
Выполнение Check-in этапов находится отдельно в `CheckinOutController`.

## Структура элемента

`Ui_commitItemWidget` хранит `args_dict`, ссылку на исходный item widget,
`commitWidget`, preview, title, description, progress и флаг `commited`.
`args_dict` содержит search key, context, description, version/revision,
versionless flags, file paths/types/metadata, repository, mode, DCC options,
callbacks, `File` objects и подготовленный `files_dict`.

`commitWidget` добавляет редактируемые context, explicit filename, repository,
description, keep filename, update/only versionless, previews и server-derived
versioned/versionless naming. При множественном выборе часть значений применяется
сразу ко всем выбранным элементам.

QML `commitModel` содержит только `title`, `context`, `repository`, `status` и
`checked`. Он не хранит подготовленный payload, progress, error, result snapshot
или Python-side file objects.

## Сценарии

| Сценарий | QWidget-контракт | Текущий QML | Статус QML |
|---|---|---|---|
| Добавление | `add_item_to_queue()` создаёт item/editor; одинаковые `file_paths` предлагают Update/Add New/Ignore | `CheckinOutController` выполняет одну подготовленную операцию напрямую; `commitModel` не заполняется | Отсутствует |
| Удаление | Current item либо Clear Queue; удаляются item, editor и tree row | Clear очищает только визуальную модель | Частично визуально |
| Reorder | API и drag reorder отсутствуют | Отсутствует | Намеренно отсутствует до появления семантики |
| Редактирование | Context, repo, filename, description, versionless, previews; multi-edit поддерживает общий набор полей | Параметры редактируются до запуска в Check-in dock, но queued item не редактируется | Частично |
| Commit одного | Context menu вызывает `commit_current_item()` при свободном pool | Кнопка/контекстное действие не подключены | Отсутствует |
| Commit всех | Последовательный запуск первого незавершённого элемента; следующий стартует после `checkin_done()` | Кнопка показывает уведомление | Отсутствует |
| Dependencies | `run_before_checkin`, `run_after_checkin`, item refresh, repository, mode, DCC state, `env_inst.commit_pool` | Check-in controller использует core API/pool, но не queue dependencies | Частично |
| Progress | Progress одновременно обновляет строку и общий status bar; показывает count/status text | Check-in dock показывает progress одной операции; queue row не обновляется | Частично |
| Ошибки | Worker errors идут в `gf.error_handle`; traceback сохраняется общим обработчиком, но item не всегда переводится в failed | Check-in dock хранит failed/retry; queue error role отсутствует | Частично вне queue |
| Retry | Явной команды queue/item нет; возможен retry конкретного worker через общую error surface | Полный retry есть только в Check-in dock | Отсутствует в queue |
| Cancel | `stop_progress()` вызывает `interrupt_commit()`, но worker-поля не присваиваются, а текущий `OperationWorker` не имеет `disable_signals()` | Безопасная отмена check-in не заявлена | Не работает подтверждённо |
| Сохранение | Сериализации queue нет | Сериализации queue нет | Отсутствует |
| Восстановление | Только пока жив тот же `Ui_commitQueueWidget` в `env_inst`; после процесса очередь потеряна | Отсутствует | Отсутствует |
| Завершённые элементы | Single commit удаляет item; Commit All собирает result snapshots, refresh-ит результаты и очищает/закрывает queue | Check-in dock сохраняет completed state до следующего запуска | Отличается |
| Закрытие | Close доступен при idle; собственного `closeEvent` нет. Закрытие окна не сериализует и не очищает queue. Во время Commit All кнопка Close disabled, но системное закрытие отдельно не блокируется | Dock можно закрыть, controller продолжает жить; операция завершается через общий pool shutdown | Частично |

## Фактическая последовательность QWidget queue

1. `tc.checkin_file()` формирует `args_dict` и добавляет элемент в проектную либо
   global queue.
2. `commitWidget` повторно получает virtual snapshot после изменения параметров.
3. `tc.inplace_checkin()` подготавливает/копирует файлы в repository.
4. `tc.checkin_snapshot()` выполняет upload при необходимости и создаёт snapshot.
5. `checkin_done()` сохраняет result, запускает следующий item либо обновляет
   результаты и очищает очередь.

## Архитектурные проблемы

- QML dock выглядит рабочим, но Commit All, Commit Selected, Edit Previews и
  context actions не выполняют операции.
- `commitModel` и `CheckinOutController` представляют две независимые очереди:
  пустую визуальную и реально выполняемую одиночную операцию.
- QWidget cancel с текущим `OperationWorker` не соответствует фактическому API;
  отключение сигналов также не гарантировало бы остановку copy/upload/server call.
- После ошибки последовательный Commit All не имеет явного состояния failed и
  команды retry/skip, поэтому продолжение очереди неоднозначно.
- Очередь содержит несериализуемые QObject/File/item/callback ссылки; сохранять
  её напрямую в QSettings нельзя.

## Контракт следующего этапа

Нужна одна Python-side модель prepared operations, использующая уже реализованные
этапы `CheckinOutController`, с безопасными ролями для QML. Она должна поддержать
add/remove, редактирование до запуска, commit one/all, failed/retry/skip,
completed history и честную отмену только на стадиях, где core её поддерживает.

Для восстановления следует сохранять только примитивный preparation payload и
повторно валидировать объект, repository и файлы. Python objects, callbacks,
worker и virtual snapshot сохранять нельзя. Reorder нужен только до запуска;
running item должен оставаться фиксированным.

## Ручные проверки

- duplicate Update/Add New/Ignore и multi-edit;
- последовательность нескольких inplace/upload операций и callbacks;
- ошибка naming/copy/upload/snapshot в середине Commit All;
- закрытие окна и приложения при idle/running;
- фактическое поведение общей error surface при retry worker;
- refresh нескольких исходных вкладок после Commit All.

## Модель и представление

Реализована единая Python-side очередь подготовленных операций:
`CommitQueueController` хранит полный preparation payload, а
`CommitQueueModel` отдаёт в QML только примитивные роли и `operationId`.
Очередь наполняется из готового payload `CheckinOutController`; отдельной
QML-копии операции и самостоятельной процедуры подготовки больше нет.

QML dock поддерживает пустое состояние, выбор, удаление, очистку, изменение
порядка и просмотр параметров. Разрешено редактировать description, context,
version и опции versionless/filename/preview. Изменение naming-параметров
переводит элемент в `Needs validation`, чтобы будущий запуск не использовал
устаревшие рассчитанные пути.

Повторное добавление той же комбинации объекта и файлов обновляет существующий
элемент. Выполнение, progress, retry, завершённые элементы и сохранение между
запусками намеренно остаются за следующими этапами. QWidget Commit Queue не
изменялся.

Требуют ручной проверки: добавление реальной подготовленной операции из
Check-in dock, редактирование всех разрешённых параметров и удобство двух
панелей при минимальной ширине dock.

## Выполнение

Очередь использует тот же `CheckinOutController` и `env_inst.commit_pool`, что
и одиночный Check-in. Добавлена последовательная обработка одного, отмеченных
или всех незавершённых элементов. Активный ID блокирует повторный запуск;
ошибка останавливает batch и оставляет failed item для Retry.

Модель получает `progress`, `stage`, `error`, `checked` и блокирует изменение
активного элемента. Завершённые операции остаются видимыми до явного
`Remove completed`. После успеха обновляются snapshots/files только если
соответствующая объектная панель сейчас отображается; полная search model не
перезагружается.

Незавершённые payload сохраняются в существующем QSettings namespace без
Python objects, workers и рассчитанного virtual snapshot. При восстановлении
они возвращаются в Prepared и полностью валидируются при новом запуске.
Shutdown прекращает продолжение batch, сохраняет очередь, затем общий lifecycle
дожидается worker pool.

Cancel снимает ожидающий batch и останавливает активную операцию на ближайшей
безопасной границе между prepare/copy/snapshot. Уже выполняющийся серверный
вызов принудительно не завершается: pool не поддерживает безопасный abort.

Автоматически проверены последовательность, защита от двойного запуска,
failed/retry, удаление завершённых и восстановление. Вручную проверить:
реальный copy/upload/snapshot, закрытие во время каждой стадии и обновление
открытой вложенной snapshot/file панели.
