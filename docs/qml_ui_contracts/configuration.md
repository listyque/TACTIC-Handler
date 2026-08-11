# Контракт Configuration UI

## Область проверки

Контракт зафиксирован по `ui_conf_classes.py`, формам из `thlib/ui/conf`, непосредственно используемому `Ui_serverPresetsEditorWidget`, текущему `WindowContent.qml`, `ApplicationController` и моделям `WorkspaceState`. Внешние Qt-обёртки не рассматривались.

## Сводное сравнение

| Страница | Legacy | QML | Итог |
|---|---|---|---|
| Main | Управляет страницами, dirty state, Apply/Reset/Close и перезапуском | Самостоятельное окно с внутренней навигацией, dirty state, Apply, Save/OK, Cancel, Reset и подтверждением закрытия | Готово как оболочка |
| Server | Полный preset/server/site/proxy/ticket/ping workflow | Загружает, проверяет и сохраняет server/user/site/proxy через существующий environment; ping асинхронный | Готово, кроме legacy preset editor и ticket dialog |
| Project | Показывает проекты и переключает открытые project docks | Показывает `projectModel` и передаёт выбранный code общей команде `select_project` | Реализовано, семантика отличается |
| Global | Форма существует, но страница отключена в legacy Main | Рабочие настройки кэша вкладок и общей темы; активный config root отображается без небезопасной смены bootstrap path | Готово в пределах действующего runtime |
| Check-in Options | Полный набор search/check-in/drop/repository параметров | `optionModel` не заполняется, поэтому основной список пуст | Только каркас |
| Check-in/Out | Per-project search types, видимость и порядок control tabs | Показывает search types как всегда включённые; control tabs model пуст | Только отображается |
| Maya Scene | Форма существует, но страница отключена в legacy Main | Загружает и сохраняет настройки через `cfg_controls.get_maya_scene/set_maya_scene` | Реализовано |

Оболочка, Server, Global и Maya Scene имеют рабочий save contract. Project использует общий runtime-переход без отдельного набора настроек. Check-in Options и Check-in/Out остаются частичными: их legacy-контракт связан с repository/check-in runtime и не заменён фиктивной QML persistence.

## Main

### Legacy-контракт

- **Настройки:** выбранная страница toolbox, позиция, размер и maximized state диалога; наличие несохранённых изменений на активной странице.
- **Источники:** `env_read_config(filename="ui_settings", unique_id="ui_conf")`; страницы создаются `Ui_configuration_mainWidget`.
- **Значения по умолчанию:** страница `0`, `windowState=false`, позиция `[150, 150]`, размер `[600, 540]`; offline разрешает только Server.
- **Валидация:** Main делегирует её страницам; сам отслеживает изменения через `eventFilter`.
- **Сигналы:** `Close → close`, `Reset → undo_changes`, `Apply → perform_save`; mouse/key/focus/enabled events помечают страницу как changed.
- **Apply / Save:** сохраняется только текущая страница; Server, Check-in Options и Check-in/Out имеют маршруты `perform_save`.
- **Cancel / Close:** при закрытии вызывается сравнение изменений и диалог Yes / Undo / Close without save / Cancel.
- **Reset:** заявлен для текущей страницы, но реализация неполная. Для Check-in Options условие использует другое имя страницы и обращается к отсутствующему `checkoutPageWidget`.
- **Зависимости:** доступность страниц зависит от online/offline; Global и Environment отключены и не создаются.
- **Работающий UI:** Server save может сменить соединение; Check-in страницы вызывают restart всего legacy main window.
- **Перезапуск:** Server после проверки; Check-in Options и Check-in/Out — всегда после Apply.
- **Ошибки:** confirmation dialogs есть; общей транзакции или отката нескольких страниц нет.

### QML-состояние

- `ConfigurationView.qml` показывает шесть страниц внутри одного самостоятельного floating window; `ConfigurationPage.qml` содержит ранее существовавшие page surfaces.
- `ConfigurationController` хранит активную страницу и dirty state, делегирует Server Apply существующему `ApplicationController.apply_server_configuration` и не дублирует server bootstrap.
- **Apply** применяет текущую изменённую Server, Global или Maya page; **Save / OK** применяет все изменённые поддержанные страницы и закрывает окно; **Cancel** и системная кнопка Close используют один close guard.
- При несохранённых изменениях доступны Save, Discard и Cancel. Закрытие не выполняет скрытого сохранения.
- **Reset** доступен только для legacy-resettable страниц и восстанавливает session snapshot текущей страницы.
- Последняя страница хранится рядом с другими QML presentation preferences; геометрия и размер уже восстанавливаются `FloatingWindowModel`.
- Page contents, не имеющие рабочего Python save contract, не помечаются как сохраняемые оболочкой и остаются в статусе, описанном ниже.

## Server

### Legacy-контракт

- **Настройки:** server preset, TACTIC URL, user, portal site enabled/name, proxy enabled/login/password/server; environment paths присутствуют в форме, но группа отключена.
- **Источники:** `env_server.get_server_presets`, `get_server`, `get_user`, `get_site`, `get_proxy`; page controls также сохраняются через `cfg_controls.get_server`.
- **Значения по умолчанию:** текущий либо первый preset; proxy выключен; остальные значения приходят из активного server preset/defaults.
- **Валидация:** асинхронный `server_fast_ping_predefined`; ticket создаётся через `generate_new_ticket` и `server_auth`. Формат URL отдельно не проверяется.
- **Сигналы:** Connect, Generate Ticket, Edit Presets, изменение preset; worker `result/error`; cancel progress dialog.
- **Apply / Save:** записывает page controls, server/user/site/proxy/ticket/defaults, затем проверяет соединение.
- **Cancel:** общий Main confirmation; server preset editor отменяет несохранённый список повторной загрузкой defaults.
- **Reset:** `collect_defaults(undo_changes=True)`.
- **Зависимые поля:** portal checkbox включает site; proxy group определяет использование proxy; preset немедленно перезагружает все поля.
- **Работающий UI:** смена preset вызывает `env_server.reload`; успешная проверка меняет online/offline и ticket status.
- **Перезапуск:** после Save и завершения проверки выполняется restart main UI.
- **Ошибки:** ping/auth ошибки передаются в `gf.error_handle`; доступен retry ticket; отмена останавливает worker signals.
- **PySide6 compatibility:** сгенерированные Configuration forms используют `QFont.Bold` вместо несовместимого `setWeight(75)`; публичные классы и формы не изменены.

### QML-состояние

- **Загрузка:** URL, active preset, user, site и proxy берутся из `env_server`; preset model заполняется при создании `WorkspaceState`, независимо от загрузки проекта.
- **Редактирование:** URL, preset, user, portal site и proxy routing. Сохранённый proxy password не передаётся в QML и остаётся неизменным; новый открытый пароль страница не сохраняет.
- **Валидация:** проверяются URL scheme/host, preset, user и обязательные зависимые site/proxy поля. Некорректные данные блокируют Apply/Save.
- **Проверка:** Test запускает legacy `server_fast_ping_predefined` через `env_inst.server_pool`; busy/success/error отображаются отдельно, GUI-поток не блокируется.
- **Apply / Save:** сохраняют через существующий `env_server`, сбрасывают ticket и делегируют bootstrap прежнему `ApplicationController.apply_server_configuration`.
- **Cancel / Reset:** используют session snapshot специализированного `ConfigurationController`; несохранённые поля не попадают в environment.
- **Ошибки:** недоступность и timeout отображаются коротким сообщением, исходная worker error сохраняется через Python logging/debug log.
- **Не переносится здесь:** legacy preset editor и генерация ticket остаются в существующем authorization workflow.

## Project

### Legacy-контракт

- **Настройки:** список всех проектов, category/type/status/template, открытые project docks; действие Toggle this Project.
- **Источники:** `env_inst.projects` и `env_inst.ui_main_tabs`; `cfg_controls.get_project()` читается, но не применяется к форме.
- **Значения по умолчанию:** все доступные проекты сгруппированы по category; templates disabled; уже открытые отмечены.
- **Валидация:** разрешено действие только для дочернего project item; серверная доступность и права предполагаются уже проверенными bootstrap.
- **Сигналы:** custom context menu → `activate_current_project`.
- **Apply / Save:** toggle немедленно вызывает `create_project_dock`; `perform_save` для Project закомментирован, а `save_config` использует неинициализированные `current_project/current_namespace`.
- **Cancel / Reset:** функционального отката toggle нет.
- **Зависимые поля:** визуальный checked state зависит от открытых вкладок main UI.
- **Работающий UI:** меняется набор project docks сразу, до Apply.
- **Перезапуск:** не выполняется.
- **Ошибки:** отдельной обработки нет.

### QML-состояние

- `projectModel` реально отображает title/code/category/status.
- Выбранные code/title/status сохраняются в состоянии страницы до её закрытия; Current Project связан с общим состоянием приложения.
- Двойной клик и **Activate selected project** вызывают реальный `appController.select_project(projectCode)`.
- Отдельная команда Create Project удалена как подтверждённая неработавшая заглушка.
- В отличие от legacy toggle project docks, QML переключает активный проект тем же путём, что основной Project Chooser; отдельного Apply/Reset для этого немедленного действия нет.

## Global

### Legacy-контракт

- **Настройки:** cache process tabs, Flush Tabs Cache, путь configuration files.
- **Источники:** только значения формы; отдельный `cfg_controls` contract для Global не реализован.
- **Значения по умолчанию:** cache checkbox выключен, config path пуст.
- **Валидация:** отсутствует.
- **Сигналы:** в `Ui_globalPageWidget` не подключены.
- **Apply / Save / Cancel / Reset:** отсутствуют.
- **Зависимые поля:** не реализованы.
- **Работающий UI:** отсутствует — `create_global_config_page` не вызывается, toolbox page disabled.
- **Перезапуск:** не определён.
- **Ошибки:** не обрабатываются.

### QML-состояние

- **Загрузка:** показывает фактическое состояние `workspace/cacheProcessTabs`, общую `appearance/darkTheme` и текущий `env_mode.get_current_path()`.
- **Редактирование:** cache process tabs и общая тема участвуют в dirty state; Apply/Save записывают существующий QML settings store и немедленно обновляют тему.
- **Cache:** выключение запрещает сохранение и восстановление search tab cache; Flush удаляет только ключи `search/treeCacheV1/*`.
- **Cancel / Reset:** восстанавливают session snapshot без скрытого сохранения.
- **Configuration path:** отображается read-only. Legacy bootstrap не умеет безопасно сохранять и применять смену корня, поэтому фиктивный выбор пути не реализован.
- **Перезапуск:** для поддержанных параметров не требуется.

## Check-in Options

### Legacy-контракт

- **Настройки отображения:** раздельные versions, позиция versions, snapshot description limit `20..50000`, result limit `20..500`, double-click save/open, builtin processes, preview over HTTP.
- **Настройки snapshot/check-in:** active repository, update versionless, naming template, sequence padding `1..9`, playblast, save/revision confirmations, Maya dirs, preview generation, check-in и checkout methods.
- **Drop Plate:** minimum frame padding `1..9`, clear/uncheck after check-in, single-frame/UDIM detection, sync between tabs.
- **Repositories:** base/sandbox/local/client/handoff path, name, enabled state, colors; custom repository name/path/list/visibility.
- **Источники:** `cfg_controls.get_checkin`, `env_tactic.get_base_dirs`, `get_custom_dir`, `get_all_base_dirs`.
- **Значения по умолчанию формы:** description limit `80`; versions right; update versionless, playblast, confirm save/revision, preview generation включены; sequence padding `3`; Drop Plate flags включены; base/local repositories включены. Persisted values заменяют defaults через `collect_defaults`.
- **Валидация:** только диапазоны spinbox, valid color и непустые name/path при добавлении custom repo; существование/доступность путей и naming template не проверяются.
- **Сигналы:** add/save/edit/delete custom repo, tree visibility, четыре color dialogs; sliders синхронизированы со spinboxes.
- **Apply / Save:** пишет `cfg_controls.set_checkin`, базовые repository records и `env_tactic.save_base_dirs`; custom dirs помечены TODO и полностью не сохраняются.
- **Cancel / Reset:** общий confirmation; intended reset через collected defaults, но Main reset route для этой страницы сломан.
- **Зависимые поля:** active repositories формируют repository combo; enabled flags влияют на runtime repository selection; spinbox/slider пары синхронны.
- **Работающий UI:** параметры читаются рабочими search/card/file/check-in сценариями; repository paths меняют разрешение локальных путей.
- **Перезапуск:** после Apply выполняется restart legacy main UI.
- **Ошибки:** нет проверки путей/коллизий; некоторые операции с пустым custom list могут завершиться ошибкой.

### QML-состояние

- `checkinPreferencesForm` отображает только `optionModel`, но модель создаётся пустой и нигде не заполняется из `cfg_controls.get_checkin`.
- Даже при ручном наполнении toggle меняет только запись `RecordListModel`; сохранения в `cfg_controls` нет.
- Все legacy параметры, repository paths/colors/custom dirs, methods, limits и dependencies не загружаются и не отображаются.
- Собственных Apply/Save/Cancel/Reset и обработки ошибок нет.
- Отдельные runtime-компоненты QML читают несколько legacy flags напрямую (`doubleClick*`, checkout method, builtin processes), поэтому рабочая логика использует старые значения, но Configuration не умеет их менять.

## Check-in/Out

### Legacy-контракт

- **Настройки:** process/search-type filter по проекту; видимость, имя и порядок control tabs; global/per-project mode; Apply current to all; Last opened Tab Layout to all Tabs.
- **Источники:** `cfg_controls.get_checkin_out`, `get_checkin_out_projects`, `env_inst.projects`, project stypes и открытые main tabs.
- **Значения по умолчанию:** filters group boxes выключены; global mode включён; last-view выключен; tabs `Checkin / Checkout`, `My Tactic`, `Assets Browser` включены; project stypes initially unset.
- **Валидация:** отсутствует; при первом открытии project config строится из текущего списка проектов и stypes.
- **Сигналы:** project click, process/control item changes, global/per-project toggle, Apply-to-all, item rename, move up/down.
- **Apply / Save:** пишет `cfg_controls.set_checkin_out` и `set_checkin_out_projects`.
- **Cancel / Reset:** `compare_changes` не проверяет эту страницу; отдельный reset route отсутствует.
- **Зависимые поля:** per-project mode включает Apply-to-all; выбранный project меняет process и tabs trees; parent process checkbox массово меняет children.
- **Работающий UI:** настройки определяют открываемые search types/control tabs и восстановление tab layout.
- **Перезапуск:** после Apply выполняется restart legacy main UI.
- **Ошибки:** отдельной обработки нет; загрузка stypes вызывается синхронно из страницы, если cache пуст.

### QML-состояние

- `processTabsModel` заполняется всеми stypes текущего проекта, но не читает saved `stypes_list`; каждый delegate статически checked.
- `controlsTabsModel` создаётся пустой и не загружается из `checkin_out_projects`.
- Last view статически checked, хотя legacy default — false, и не связан с `lastViewOnAllTabscheckBox`.
- Нет global/per-project выбора, project selector, порядка/rename tabs, Apply-to-all и сохранения.
- Сигналы checkbox отсутствуют, поэтому даже presentation model не меняется.

## Maya Scene

### Legacy-контракт

- **Настройки:** current workdir, create Maya dirs, create playblast, Maya save format.
- **Источники:** форма; `cfg_controls.get_maya_scene/set_maya_scene` существуют, но `Ui_mayaScenePageWidget` их не использует.
- **Значения по умолчанию:** workdir пуст; Maya dirs и playblast включены; format combo без заданного form default.
- **Валидация:** отсутствует.
- **Сигналы:** не подключены.
- **Apply / Save / Cancel / Reset:** отсутствуют.
- **Зависимые поля:** предполагаются только для Maya mode, но логика не реализована.
- **Работающий UI:** отсутствует — page creation закомментирован, toolbox page disabled.
- **Перезапуск:** не определён.
- **Ошибки:** не обрабатываются.

### QML-состояние

- **Загрузка:** `currentWorkdir`, оба checkbox и format читаются через `cfg_controls.get_maya_scene`; при отсутствии файла используются defaults формы: пустой workdir, оба checkbox=true, `mayaAscii`.
- **Редактирование:** workdir остаётся read-only как в `.ui`; доступны Maya dirs, playblast и два реально поддержанных формата `mayaAscii/mayaBinary`.
- **Apply / Save:** сохраняют legacy-compatible control dictionary через `cfg_controls.set_maya_scene`.
- **Cancel / Reset:** используют session snapshot и не вызывают DCC API.
- **Валидация:** неподдерживаемый или пустой format блокирует сохранение с коротким сообщением.
- **Влияние:** Configuration только предоставляет настройки существующему API; Maya integration, scene operations и DCC imports не изменены.
- **Перезапуск:** не требуется самим Configuration; фактическое потребление настроек Maya требует ручной проверки внутри DCC.

## Несовместимые или отдельные настройки

- QML использует `QSettings("TACTIC-Handler", "modern-qml")` для geometry, theme, last project и других presentation preferences; legacy Configuration сохраняет geometry/page в `ui_settings/ui_conf`.
- Такое разделение корректно для чисто QML geometry/theme, но `server/currentProject` является дополнительным QML recovery key рядом с legacy current-project state.
- Второго набора Server, Maya или check-in business settings не создано. Maya использует `cfg_controls`; неподключённые Check-in controls не притворяются сохраняемыми.

## Финальный функциональный паритет

| Сценарий | Статус | Результат |
|---|---|---|
| Открытие | реализован | Самостоятельное floating window; QML runtime-проход всех шести страниц без ошибок |
| Загрузка значений | реализован | Server, Global и Maya читают действующие API; Project читает общую model |
| Переключение проекта | требует ручной проверки | Команда общая с QML Project Chooser; несколько реальных проектов и legacy docks нужно сравнить вручную |
| Apply | реализован | Server, Global и Maya; Project действует немедленно; Check-in pages частичны |
| Save / OK | реализован | Применяет все dirty pages с рабочим contract и закрывает окно |
| Cancel | реализован | Discard не пишет pending values; подтверждение доступно при dirty state |
| Reset | реализован | Server, Global и Maya восстанавливают session snapshot; Check-in pages частичны |
| Закрытие с изменениями | реализован | Save / Discard / Cancel; системная кнопка использует тот же guard |
| Ошибки | реализован | Validation блокирует save; server worker errors остаются в debug log |
| Значения по умолчанию | реализован | Server environment, Global runtime state, Maya defaults из `.ui` |
| Зависимые поля | реализован | Server site/proxy; Maya format ограничен поддержанными значениями |
| Положение и размер | реализован | Сохраняет и восстанавливает `FloatingWindowModel` |
| Повторное открытие | реализован | Начинает новую session snapshot без старого dirty state |
| Legacy UI | реализован | Offline/online создание и compatibility smoke проходят на PySide6 |
| Maya внутри DCC | требует ручной проверки | Нужен запуск Maya; DCC-логику этап не изменяет |
| Check-in Options / Check-in-Out | требует отдельного этапа | Legacy repository/tab persistence остаётся частично представленной |
