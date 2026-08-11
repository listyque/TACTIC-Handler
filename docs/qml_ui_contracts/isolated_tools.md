# Изолированные инструменты: контракт миграции

Аудит ограничен перечисленными интерфейсами, их текущими QML-представлениями
и непосредственно используемыми API. `thlib/side` не анализировался.

## Сводка

| Инструмент | Standalone UI | DCC | Открывается без интеграции | Текущий QML | Объём |
|---|---:|---:|---:|---|---|
| Assets Browser | да | нет | да | частично | средний |
| Update | да | нет | да | визуальная оболочка | средний/высокий |
| Create Update | решение продукта | нет | технически да | визуальная оболочка | средний |
| Maya Import Options | нет | да | только декоративно | фиктивная общая форма | малый UI, средняя интеграция |
| Maya Open Options | частично | условно | да, но DCC-опции неприменимы | фиктивная общая форма | малый |
| Maya Reference Options | нет | да | только декоративно | фиктивная общая форма | малый UI, средняя интеграция |
| TACTIC API Client | отдельный режим | нет | да | отсутствует | высокий |
| TACTIC Server | отдельный служебный режим | Maya batch/окружение | только при установленном runtime | отсутствует | высокий |

## 1. Assets Browser

- **Назначение:** пользовательский standalone browser объектов проекта; DCC не
  требуется.
- **Открытие:** допустимо в обычном приложении после выбора проекта и search
  type.
- **Python API:** `env_inst.get_current_stypes()`, `tactic_classes.get_sobjects()`,
  `group_sobject_by()` и методы полученных sObject; детали уже доступны через
  workspace selection/detail state.
- **Текущее состояние:** `AssetsBrowserView` использует активный search section,
  `workspaceModel`, `WorkspaceCard`/`WorkspaceResultItem`, общий selection,
  paging и detail actions без второго search controller.
- **Объём переноса:** средний. Отдельный серверный client не нужен; безопаснее
  переиспользовать search tabs, result model и detail controller.
- **Паритет:** реальные stypes; search/filter; limit/paging; card flow и zoom;
  preview; выбор и двойной клик; открытие объекта; loading/error/empty; отсутствие
  повторного запроса при одном изменении масштаба.

## 2. Update и Create Update

- **Назначение:** Update полезен standalone-пользователю. Create Update является
  release/admin-инструментом; его доступность в обычной сборке требует отдельного
  решения, но он не исключён из очереди.
- **DCC:** отсутствует; оба окна можно открыть без интеграции.
- **Python API:** `update_functions.get_current_version()`,
  `get_info_from_updates_folder()`, `get_update_archive_from_server()`,
  `update_from_archive()`, `save_current_version()`, `create_updates_list()` и
  `create_update_archive()`; перезапуск — существующий
  `env_inst.ui_main.restart_for_update_ui_main()`.
- **Текущее состояние:** QML читает реальную локальную историю, асинхронно
  вызывает существующий remote refresh и restart-to-update. Create Update
  формирует metadata, JSON, список версий и ZIP через исходный API.
- **Объём переноса:** средний для просмотра/create, высокий для безопасного
  применения из-за записи поверх приложения, progress, rollback и restart.
- **Паритет Update:** текущая/последняя версия; реальная история; выбор версии;
  download; подтверждение; progress/error; проверка архива; применение только
  после явного действия; restart; корректное состояние после сбоя.
- **Паритет Create Update:** версия/date/changes/misc; валидация; JSON;
  `versions.json`; архив с исходными правилами исключения; progress/error;
  запрет случайного повторного создания.

## 3. Maya Import Options

- **Назначение:** только DCC workflow; в standalone не нужен как самостоятельный
  инструмент.
- **Открытие без Maya:** окно технически можно показать, но операция должна быть
  disabled с объяснением.
- **Python API:** выбранные file object/nested item из Check-in/Out и
  `maya_functions.import_scene(file_object)` после существующего download/sync.
- **QML:** общий `MayaOptionsView` с mode `import`, сохранённым count,
  подтверждением, progress/cancel из Check-in/Out и disabled state вне Maya.
- **Исходные параметры:** Import count (slider/spinbox) и переход к расширенным
  importing options; текущий класс сам действие не подключает.
- **Паритет:** выбранный snapshot/file; доступность только в Maya; count;
  download при отсутствии local file; последовательный import; progress/error;
  cancel до запуска; обновление UI без импорта Maya-модулей в presentation layer.

## 4. Maya Open Options

- **Назначение:** Open остаётся полезным standalone для ассоциированного
  приложения, но Maya-specific setup workdir должен включаться только в Maya.
- **Открытие без Maya:** допустимо для обычного open; недоступные DCC options
  должны быть выключены.
- **Python API:** общий open/download workflow Check-in/Out; в Maya —
  `maya_functions.open_scene(file_object)`.
- **QML:** общий `MayaOptionsView` с mode `open`; standalone open разрешён,
  выполнение начинается только после подтверждения.
- **Исходные параметры:** Setup working directory, Save и расширенные opening
  options; текущий класс не подключает кнопки.
- **Паритет:** корректный выбранный файл; local-state/overwrite; download;
  setup-workdir; save-current-scene confirmation; open; progress/error; понятная
  причина недоступности DCC-функции.

## 5. Maya Reference Options

- **Назначение:** только Maya/DCC; в обычном standalone UI не требуется.
- **Открытие без Maya:** только read-only/disabled состояние, если вызов пришёл
  из сохранённого UI state.
- **Python API:** download/sync Check-in/Out и
  `maya_functions.reference_scene(file_object)`.
- **QML:** общий `MayaOptionsView` с mode `reference`, сохранённым count,
  подтверждением и явной Maya capability check.
- **Исходные параметры:** Reference count (slider/spinbox) и расширенные
  referencing options; исходный dialog сам операцию не выполняет.
- **Паритет:** выбранный snapshot/file; Maya capability check; count; получение
  local file; reference через integration API; progress/error; отсутствие
  Maya-import в общем QML/Python presentation layer.

## 6. TACTIC API Client

- **Назначение:** отдельный локальный listener для внешних клиентов, а не
  обязательное окно обычного standalone UI. Пользовательская ценность есть у
  integrations и automation; включение в дистрибутив — отдельное решение.
- **DCC:** не зависит. Запускается отдельной точкой `tactic_api_server.py`.
- **Python API:** `env_api.spawn_api_server()`, `execute_method()`,
  `get_results()`, `close_server()` и диспетчеризация разрешённых методов
  `tactic_classes`; текущий UI также создаёт notification/debug/script окна.
- **QML:** `ServiceToolView` запускает неизменённый `tactic_api_server.py` в
  отдельном процессе, показывает lifecycle/history/output и подтверждает stop.
- **Объём переноса:** высокий: отдельный bootstrap, listener lifecycle,
  single-instance, status, errors, shutdown и проверка совместимости протокола.
- **Паритет:** тот же localhost endpoint/port и wire format; запуск/остановка;
  обработка одного и нескольких клиентов; возврат результата/исключения;
  Debug Log; корректное закрытие; отсутствие расширения доступных методов и
  security model.

## 7. TACTIC Server

- **Назначение:** служебный process/batch launcher, не основной standalone UI.
  Возможная пользовательская ценность — контроль локального server/batch
  процесса; перенос требует отдельного решения.
- **DCC/runtime:** жёстко зависит от установленного TACTIC runtime и исторически
  запускает batch через platform-specific Python path; часть сценария связана с
  Maya batch окружением.
- **Открытие без интеграции:** окно возможно, но запуск процесса должен быть
  disabled, пока runtime/path не валидирован.
- **Python API:** отдельный launcher `thlib/tactic_server.py`,
  `mayaBatchClass`/`QProcess`, merged output, process errors, `env_api`,
  Debug Log и Script Editor.
- **QML:** тот же `ServiceToolView` запускает исходный launcher отдельным
  процессом, поддерживает state/PID/output/error и подтверждённый stop.
- **Объём переноса:** высокий; это отдельный режим приложения, а не ещё один dock.
- **Паритет:** обнаружение runtime; явный start/stop; один процесс; state/PID;
  stdout/stderr без блокировки; progress/log; process error/exit code; безопасное
  закрытие; отсутствие захардкоженного Windows path; сохранение текущего
  поведения server launcher.

## Рекомендуемый порядок

1. Assets Browser — завершить на уже существующих search/detail моделях.
2. Maya Open Options — разделить общий open и Maya capability.
3. Maya Import и Reference Options — одним typed options controller в DCC-этапе.
4. Read-only Update/history, затем отдельно подтверждаемое применение.
5. Create Update — только после решения о доступности release-инструмента.
6. TACTIC API Client — отдельный launcher после стабилизации обычного UI.
7. TACTIC Server — последним, как отдельный runtime/process-control проект.
