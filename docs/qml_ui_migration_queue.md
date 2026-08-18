# Очередь оставшихся UI

Очередь актуализирована по фактическим action handlers, Python-моделям,
сигналам и сохранению результата. Наличие QML-компонента само по себе не
считалось готовностью. `thlib/side` исключён из анализа. Полная матрица классов,
компонентов и проверок находится в
[отчёте о паритете](qml_ui_parity_report.md).

## Сводка

| Всего | Готово | Частично | Ручная проверка | Требует DCC | Legacy-only |
|---:|---:|---:|---:|---:|---:|
| 27 | 4 | 6 | 15 | 1 | 1 |

## 1. Уже начатые, но незавершённые UI

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 1 | Configuration | частично | Завершить паритет Check-in Options и Check-in/Out страниц |
| 2 | Filter Editor | частично | Подтвердить process/TEL filters; убрать расхождение локальных quick filters |
| 3 | Notes | частично | Проверить history/permissions и различия общей timeline |
| 4 | Messages | частично | Определить и подключить адресные сообщения и live updates |
| 5 | Rich Edit | частично | Проверить сложную разметку; отдельный editor нужен только при подтверждённом сценарии |
| 6 | Tactic Column Editor | частично | Решить перенос schema mutation с прежним confirmation и правами |

## 2. Основной рабочий процесс

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 7 | Check-in / Check-out | требует ручной проверки | Серверный check-in/out, overwrite, cancel и закрытие во время операции |
| 8 | Commit Queue | требует ручной проверки | Реальный commit, retry/cancel и восстановление после закрытия |
| 9 | Drop Plate | требует ручной проверки | Большие каталоги, DnD, sequences и передача в реальную очередь |
| 10 | Matching Templates | требует ручной проверки | Конфликтующие patterns и rematch на реальных файлах |
| 11 | Tasks | требует ручной проверки | Права, server validation/triggers и точечное обновление моделей |
| 12 | Attachments | требует ручной проверки | Upload/download/preview, cancel и локальные состояния |
| 13 | Watch Folders | требует ручной проверки | Реальные filesystem events, lifecycle и restart |
| 14 | Repository Editor | требует ручной проверки | Network shares, platform mapping и права |

## 3. Редакторы объектов

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 15 | Add / Edit / Link sObject | требует ручной проверки | Schema/rights/relations и server validation |
| 16 | Columns Editor | готово | Только регрессионная визуальная проверка |
| 17 | Preview Editor | требует ручной проверки | Реальный upload/remove и обновление выбранного объекта |
| 18 | Naming Editor | намеренно оставлено legacy-only | Отдельное решение о полноценном rules editor |

## 4. Коммуникация

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 19 | Уведомления | готово | Регрессионная проверка повторного открытия окна |

## 5. Вспомогательные инструменты

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 20 | Server Presets | готово | Регрессионная проверка без сохранения секретов |
| 21 | Assets Browser | готово | Визуальная проверка большой выдачи |
| 22 | Update dialogs | требует ручной проверки | Архив, cancel/error, rollback и restart |
| 23 | Script Editor | требует ручной проверки | Выполнение на сервере, permissions и cancel |
| 24 | Screenshot Maker | требует ручной проверки | Multi-monitor, DPI и DCC host |
| 25 | TACTIC API Client | намеренно оставлено legacy-only | Modern supervisor removed; Handler Server is the current integration path |
| 26 | TACTIC Server | намеренно оставлено legacy-only | Modern supervisor removed; original launcher remains unchanged |

## 6. Изолированные интеграции

| Приоритет | Область | Статус | Оставшаяся работа |
|---:|---|---|---|
| 27 | Maya Import / Open / Reference | требует DCC | Полный прогон import/open/reference в Maya |

## Проверка перед merge

Автоматический контур миграции готов к объединению: Python syntax, прямой и
унифицированный QML launchers, запуск из другой рабочей директории, двукратное
открытие всех зарегистрированных окон, legacy smoke, worker retry/shutdown и
QSettings window-state прошли. Статусы очереди выше не повышены без реального
TACTIC/DCC прогона. Перед merge вручную проверить login, серверные mutation и
file/repository операции, Maya и внешние API tools.

## Release and cutover gate

- `launch.py` теперь запускает modern QML по умолчанию; legacy сохраняется как
  явный `--ui legacy`/`TACTIC_HANDLER_UI=legacy` и regression oracle.
- Единый `tests/run_release_gate.py` проверяет чистое дерево и whitespace, Python
  syntax, все изолированные тесты, legacy compatibility и оба modern entry point
  из другой рабочей директории.
- Живые mutation/repository/DCC/Windows/visual проверки не выданы за автоматику и
  перечислены как обязательный environment-dependent допуск в
  `tests/contracts/release_acceptance.json`.
- Чистое окружение проверяется `tests/run_clean_environment_smoke.py`; совместимость
  generated server procedures — `tests/run_live_server_procedure_smoke.py`.
- Clean-environment smoke пройден на Python 3.14.6/PySide6 6.11.1; live TACTIC,
  repository, Windows lifecycle и Maya проверки остаются environment-dependent.
- Результаты допуска записываются через `tests/record_release_acceptance.py` и
  проверяются строгим режимом `tests/run_release_gate.py --require-manual`.
- Статусы интерфейсов выше намеренно не повышены только по факту зелёного QML
  smoke; production release остаётся закрыт до ручного допуска.
