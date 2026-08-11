# Original vs modern: аудит изменений

Дата сравнения: 2026-08-01. Эталон: `D:\code\TACTIC-Handler-stable`.

## Границы проверки

Из сравнения полностью исключены `thlib/side`, `tools`, `settings`,
`prject_templates`, `project_templates`, `log`, `installer`, `docs` и
`custom_scripts`. Файлы в этих каталогах не учитывались при выводах и не
изменялись.

В общей части проектов найдено 126 побайтово отличающихся файлов:

- 117 после нормализации кодировки и окончаний строк совпадают полностью;
- 7 Python-файлов содержат реальные изменения поведения;
- `.gitignore` и `default.gitignore` дополнены маской журналов modern UI;
- в текущий проект добавлен один общий модуль `thlib/search_helpers.py`;
- 35 файлов `screenshots/` есть только в оригинале; один из них используется
  ссылкой из корневого `README.md`, но на выполнение приложения это не влияет.

Неизменённые по смыслу 117 файлов распределены так: 69 `thlib/ui`, 34
`thlib/ui_classes`, 3 тестовых файла и 11 прочих файлов `thlib`. Это шум от
окончаний строк/кодировки, а не изменение API или поведения.

`main_standalone.py`, `main_standalone.pyw` и `main_maya.py` побайтово совпадают
с оригиналом. Новые `launch.py` и `main_qml.py` не заменяют старые точки входа.

## KEEP

| Файл | Зачем и кто использует | Влияние на QWidget UI | Можно вынести |
|---|---|---|---|
| `thlib/global_functions.py` | `MatchTemplate` сохраняет порядок шаблонов и удаляет дубликаты без неустойчивого порядка `set`. Используется Drop Plate, Commit Queue, Notes, items, Watch Folders и modern check-in/matching. | Поведение становится детерминированным; публичный API и тип входных данных сохранены. | Нет: это общая naming/matching-логика. |
| `thlib/tactic_query.py` | Защищает расчёт `include_progress` от отсутствующих pipeline/process/workflow/task mapping и всегда создаёт результат для каждого sObject. Используется обоими Search UI через `tactic_classes.get_sobjects`. | Убирает подтверждённые падения на неполной серверной схеме; корректный результат — пустой progress. | Нет: проверка относится к серверному запросу. |
| `.gitignore`, `default.gitignore` | Исключают `log/modern_session_*.jsonl`. | Нет. | Не требуется. |

## FIX_COMPATIBILITY

| Файл | Зачем и кто использует | Влияние на QWidget UI | Решение |
|---|---|---|---|
| `thlib/pool.py` | Общие `server_pool`, `commit_pool` и `local_pool` переведены на ограниченный `QThreadPool`; добавлены рабочий retry (не более трёх попыток), освобождение worker и ожидание операций при shutdown. Используется всеми UI. | Сохранены `start`, `exit`, `add_task`, worker signals, `start`, `retry`, result data. В проекте нет вызовов QThread-only методов старого `ThreadsPool`. Импортный smoke и retry проходят. | Сохранять как общую реализацию. Перед merge вручную проверить несколько одновременных commit/download и закрытие во время зависшего сетевого вызова. |

Тип `ThreadsPool` изменён с `QThread` на `QObject`. Это допустимо для найденных
внутренних вызовов, но является единственным существенным риском для внешнего
плагина, если он ошибочно использовал недокументированные `QThread.wait()`,
`quit()` или `isRunning()` непосредственно на пуле.

## MOVE_TO_CORE

| Файл | Состояние | Причина |
|---|---|---|
| `thlib/search_helpers.py` | Уже выполнено корректно. | `get_suggestion_filter` вынесен из `ui_search_classes.py` без изменения формата фильтра. Его импортируют QWidget Search и modern Search, поэтому QML не зависит от QWidget-модуля ради общей функции. |
| `thlib/ui_classes/ui_search_classes.py` | Оставить совместимый импорт функции. | Старый публичный импорт `ui_search_classes.get_suggestion_filter` продолжает работать. |

Модули `thlib.tactic_classes` и `thlib.global_functions` существовали в
оригинале уже с импортами QtWidgets. Modern UI использует их бизнес-API и
поэтому транзитивно загружает QtWidgets. Чистые операции можно позднее выносить
в нейтральные модули только по фактической необходимости; массовое разделение
в рамках этого аудита не оправдано.

## MOVE_TO_MODERN

| Файл | Проблема | Рекомендуемая граница |
|---|---|---|
| `modern_ui/controllers/snapshot_actions.py` | Действие `edit` напрямую импортирует и показывает `Ui_addTacticSobjectWidget`. Это единственная найденная прямая зависимость modern UI от старого окна. | Открывать существующий schema-driven QML editor через controller/window registry. Серверный save API оставлять общим. |

`main_qml.py` использует `QApplication`, а не `QGuiApplication`. Это намеренное
совместимое основание процесса и само по себе не создаёт старые окна. Адаптеры,
записанные в `env_inst.ui_repo_sync_queue` и `env_inst.ui_debuglog`, реализуют
существующие callable API и также не создают QWidget.

## REVERT

Подтверждённых изменений, которые следует откатить, не найдено. Массовый откат
117 файлов с отличающимися окончаниями строк не нужен и создаст новый шум.

## GENERATED_FILE

Вручную изменены только три сгенерированных файла:

- `thlib/ui/conf/ui_checkinOptionsPage.py`;
- `thlib/ui/conf/ui_checkinOutPage.py`;
- `thlib/ui/conf/ui_serverPage.py`.

Во всех случаях `QFont.setWeight(75)` заменён на
`QFont.setWeight(QFont.Bold)`. Связанные `.ui`-формы по нормализованному тексту
совпадают с оригиналом. Проверка оригинального `ui_serverPage.py` под текущим
PySide6 воспроизводит `TypeError`, а текущий старый Configuration открывается.
Правки нужны для Qt-совместимости и не должны быть откачены. Отдельное решение:
закрепить эту конверсию в используемом процессе генерации или безопасном
compatibility layer, иначе следующая регенерация их сотрёт.

## UNCLEAR

- Полный behavioural parity нового `QThreadPool` с внешними плагинами нельзя
  доказать без списка их недокументированных вызовов; код не изменялся.
- Online-запуск через реальный server ping/auth требует ручной проверки:
  ограниченный автоматический прогон ожидал сетевой worker дольше окна теста.
  Legacy launcher, `server_ping` и форма входа относительно оригинала не
  менялись, поэтому это не подтверждённая регрессия.
- Отсутствующие `screenshots/` оставлены без изменений. Это не runtime-ресурс,
  но ссылка в корневом README сейчас не отображается.

## Зависимости слоёв

- Импортов `modern_ui` из `thlib` вне исключённой области нет.
- QML-файлы не импортируют и не создают QWidget.
- Python presentation layer имеет одну прямую зависимость от старого окна —
  snapshot file edit, указанную в `MOVE_TO_MODERN`.
- Остальные обращения modern UI к `thlib` направлены на environment, worker
  pools, TACTIC API, file/repository, naming и update API.

## Проверки и изменения этого аудита

- `py_compile` изменённых semantic Python-файлов, launchers и smoke-check: OK;
- `smoke_legacy_compat.py`: OK;
- старый `Ui_Main` в offline-режиме создан, показан и штатно закрыт: OK;
- старый Configuration создан и показан: OK;
- оригинальный generated Server page под PySide6: подтверждён `TypeError`;
- функциональный код не менялся: подтверждённых регрессий, требующих точечного
  исправления на этом этапе, не найдено.
