# Modern QML baseline

Дата фиксации: 2026-08-11.

## Назначение

Этот baseline фиксирует первое воспроизводимое Git-состояние modern QML ветки до
дальнейшей стабилизации архитектуры. Рабочее дерево восстановлено поверх
канонической истории TACTIC-Handler, без массового отката текущих файлов.

- Канонический upstream: `https://github.com/listyque/TACTIC-Handler.git`.
- Базовый legacy commit: `25d3c262ad424f334342263032a73225550380f6` (`upstream/stable`).
- Modern branch: `modern-main`.
- Legacy branch: `legacy-stable` (tracking `upstream/stable`).
- Legacy tag: `legacy-stable-baseline`.
- Modern tag: `modern-baseline-2026-08-11`.
- Неизменённая копия `D:\code\TACTIC-Handler-stable` совпадает с базовым
  commit после нормализации окончаний строк; единственное дополнительное
  содержимое копии — локальный `__pycache__`.

## Состав baseline

- 507 Python-файлов, 149557 строк.
- 152 QML-файла, 41821 строка.
- Полный SHA-256 manifest: [modern_baseline_files.txt](modern_baseline_files.txt).
- Утверждённый визуальный reference Task Workspace:
  [tasks_workspace_approved_mockup.png](assets/tasks_workspace_approved_mockup.png).
- Снимок текущего Task Workspace:
  [tasks_workspace_current_ui_reference.png](assets/tasks_workspace_current_ui_reference.png).
- Legacy screenshots остаются доступны в `legacy-stable-baseline`; отсутствие
  папки `screenshots` в modern worktree является частью текущего состояния.

## Исключённые локальные данные

В baseline намеренно не входят:

- `settings/` — пользовательские настройки, server presets и tickets;
- `log/` — session/debug logs, команды и диагностические payload;
- `custom_scripts/` — локальные production-скрипты, среди которых обнаружены
  присваивания token-подобных значений;
- Python/Qt caches, временные transfer-файлы и editor backups.

Эти пути исключены одновременно в `.gitignore` и `default.gitignore`. Секреты
не переносятся в документацию или Git history.

## Автоматические проверки

| Проверка | Результат |
|---|---|
| `compileall` для `modern_ui`, `handler_server`, `tactic_handler_dcc`, `tests` | PASS |
| `py_compile` для `main_qml.py`, `launch.py`, `smoke_legacy_compat.py` | PASS |
| `smoke_legacy_compat.py` с `QT_QPA_PLATFORM=offscreen` | PASS |
| 33 test-модуля, запущенные изолированно | 31 PASS, 2 ERROR; всего 357 tests |
| QML warning scan последней session JSONL | 0 binding/property/handler warning lines |
| Полный `unittest discover` одним процессом | FAIL: один test error, затем native Qt process crash |

Известные test errors:

1. `tests.test_drop_plate.DropPlateTest.test_item_target_uses_clicked_process` —
   тестовый `Operations` создаётся без `workspace_state`.
2. `tests.test_script_editor.ScriptEditorTests.test_script_run_suppresses_dialog_from_worker_and_gui_paths` —
   Windows не удаляет временный JSONL/log, потому что handler остаётся открыт;
   также зафиксирован `ResourceWarning` для двух файлов.

Изолированный запуск предотвращает взаимное загрязнение Qt/runtime состояния;
все остальные 355 tests проходят. Эти два дефекта и native crash являются
зафиксированным долгом baseline, а не скрытым зелёным результатом.

## Runtime baseline

Последняя доступная session trace: `modern_session_11_08_2026_20_13_28.jsonl`
(сам файл игнорируется Git). За всю записанную сессию:

- 304 диагностических события;
- 156 TACTIC API calls;
- 4.900 s суммарного server-call времени;
- 2888.9 KB ответов;
- 1 exception: истёкший login ticket;
- 0 warning events.

В первые 30 секунд trace зафиксировано 68 API calls, 2.545 s server-call
времени и 1825.2 KB ответов. Наиболее заметны `get_sobjects` (18 calls за всю
сессию), search-type catalog (921.2 KB), snapshot updates (812.9 KB) и server
updates (5 calls). Метрики зависят от открытых dock/tab и живых данных сервера;
после каждого изменения batching/cache их следует переснимать тем же способом.

## Ручной verification gate

Перед merge или release требуется повторить на действующем TACTIC и реальных
репозиториях:

1. login, смену server preset, истёкший ticket и повторный login;
2. project/search tabs, selection, previews и восстановление layout;
3. Add/Edit/Link, Tasks, Notes, Messages, Activity Feed и права доступа;
4. Check-in/Out, Commit Queue, Drop Plate, repository sync и Watch Folders;
5. закрытие приложения во время активных workers/transfers;
6. Maya/DCC open, import, reference, save scene и reconnect через thin client;
7. standalone QML launcher и legacy launcher из другой рабочей директории.

Подробный статус функционального паритета находится в
[qml_ui_parity_report.md](qml_ui_parity_report.md). Наличие QML-файла само по
себе не считается подтверждением готовности.

## Воспроизведение и сравнение

```text
git switch modern-main
git status
git diff legacy-stable-baseline..modern-baseline-2026-08-11
```

Для просмотра исходного legacy состояния используется `legacy-stable` или tag
`legacy-stable-baseline`. Baseline создан локально; push в remote не выполнялся.
