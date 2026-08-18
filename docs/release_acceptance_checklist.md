# Release acceptance checklist

Этот checklist проверяет только поведение, которое нельзя честно подтвердить
offline smoke-тестом. Все изменения выполняются в изолированном проекте `th_test_*`
и тестовом репозитории. Production-проекты не используются.

Результат каждой группы записывается через `tests/record_release_acceptance.py` с
именем проверяющего, временем UTC и конкретным evidence: логом, снимком экрана,
кодами созданных объектов или описанием окружения.

## Session and navigation

- Войти с действующим ticket и повторно войти после logout.
- Переключить server preset и убедиться, что старый ticket не используется.
- Открыть проект, выполнить поиск и перейти по `skey` с `code`.
- Проверить существующую filtered search tab и fallback в новую подходящую вкладку.
- Имитировать потерю соединения и убедиться, что UI восстанавливается без сброса
  пользовательских настроек.

## Server procedure compatibility

- Запустить `tests/run_live_server_procedure_smoke.py` на поддерживаемом сервере.
- Подтвердить выполнение task workspace, conversations, user activity и batched
  server updates без server-side `SyntaxError`, `Undefined` и различий API.
- Сохранить версию TACTIC и серверного Python в evidence.

## Server mutations

- Создать, изменить, связать и удалить тестовый sObject штатным API.
- Создать и изменить task, milestone, work hour и note.
- Отправить, изменить, удалить и прочитать chat message; проверить reply, pin,
  reaction и attachment metadata.
- Изменить тестового пользователя и его группы с разрешённой учётной записью.
- Повторить запрещённое действие обычным пользователем и проверить понятную ошибку.
- После каждой операции обновить представление и подтвердить сохранённое значение с
  сервера, а не только optimistic state.

## Files, repository and check-in

- Проверить platform mapping и создание отсутствующих каталогов репозитория.
- Скачать HTTP preview/file, проверить размер ответа и повторное использование
  локального файла.
- Выполнить Check-in, Check-out, Commit Queue и Drop Plate для одного файла,
  последовательности и групповой операции.
- Проверить screenshot, clipboard preview, generated preview и naming result.
- Прервать передачу, повторить её и закрыть окно во время активной операции.
- Убедиться, что retry не создаёт дубликат snapshot/path, а completed queue entries
  очищаются согласно Auto-clean.

## Windows lifecycle

- Открыть, закрыть и повторно открыть крупные окна минимум два раза.
- Проверить minimum sizes, dock resize/stack/float/reset и восстановление geometry.
- Закрыть главное окно с подключённым DCC-клиентом, восстановить его из tray.
- Закрыть приложение во время server poll, repository sync и worker operation.
- Перезапустить и проверить сохранённые настройки без изменения unrelated keys.

## Clean environment

- На чистом поддерживаемом Python запустить
  `tests/run_clean_environment_smoke.py`.
- Подтвердить установку только из `requirements-modern.txt` или контролируемого
  wheelhouse.
- Запустить modern и explicit legacy entry points из другой рабочей директории.
- Сохранить версии Python, PySide6 и Windows в evidence.

## Maya thin client

- Запустить standalone без ручного ввода endpoint, затем один и несколько Maya
  clients.
- Проверить discovery, active-client switching, capabilities и disconnect/reconnect.
- Выполнить open, import, reference, save, current scene и playblast preparation.
- Убедиться, что TACTIC upload остаётся в standalone, а Maya получает только
  фиксированные native actions.
- Проверить timeout, structured error и request id в общем Debug Log.

## Visual and localization

- Проверить dark/light themes и English/Russian UI.
- Убедиться, что server/project/search type/process/status names не переводятся как
  статические строки приложения.
- Проверить wide, ordinary и minimum widths без перекрытий и недоступных действий.
- Проверить указатель руки у active controls и text cursor у полей ввода.
- Запустить QML с чистым log и убедиться в отсутствии binding/property/handler
  warnings.

## Release candidate command

```powershell
python tests/run_release_gate.py --require-manual `
  --manual-results .release/acceptance.json
```

Непройденная группа не означает плохую архитектуру. Она означает только отсутствие
доказательства для конкретного окружения или подтверждённый дефект этого сценария.
