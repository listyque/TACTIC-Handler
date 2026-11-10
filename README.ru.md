# ![TACTIC Handler](docs/assets/readme/wordmark.svg)

**Настольный клиент для TACTIC и TACTIC Stream.**

[English](README.md) · **[Начать работу](#установка-и-подключение)** · [Обзор возможностей](docs/presentations/product-tour.ru.md) · [Maya-плагин](docs/presentations/maya.ru.md) · [Документация](docs/index.md)

В Handler можно найти ассет, посмотреть его задачи и замечания, открыть опубликованную сцену в Maya и сдать новую версию. Приложение работает с локальными файлами и репозиторием, а записи проекта хранит сервер. Поддерживаются TACTIC Stream и совместимые установки оригинального TACTIC.

![Обычный Item View: Survey Drone, производственные процессы и опубликованные версии](docs/assets/product-tour/item-view-standard.png)

> **Прототип в разработке**, в том числе Perforce-like File Workspace.

## Item View

Основное представление Handler — Item View. Объект раскрывается в дерево процессов, задач и публикаций: версии файлов видны прямо в результатах поиска. Для визуального просмотра есть карточки, для массовой правки полей — таблица.

Рядом с результатами можно разместить задачи, заметки и превью файлов. Раскладки сохраняются, а скрипты проекта доступны с личной или общей полки.

## Установка и подключение

Для запуска исходников на Windows нужны Python 3.14 и работающий сервер TACTIC Stream или совместимый TACTIC:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

Откройте **Configuration → Server**, подключитесь и войдите в систему. Выберите проект и настройте пути репозитория перед работой с файлами.

[Установка и первое подключение](docs/handbook.ru.md) · [Подключение Maya](docs/presentations/maya.ru.md) · [Совместимость с оригинальным TACTIC](docs/tactic_compatibility/README.md)

## Работа в Handler

### Доки и рабочие раскладки

Доки делят окно на панели, которые можно переставлять, объединять во вкладки и выносить на второй монитор. Раскладку для ревью или планирования можно сохранить и назначить пункту sidebar. Вместе с поиском и выбранным представлением она задаёт рабочее место отдела.

![Рабочее пространство из доков: объекты, задачи и опубликованные файлы](docs/assets/product-tour/docks-planning.png)

[Доки и сохранённые раскладки →](docs/presentations/product-tour.ru.md#доки-и-раскладки) · [Sidebar Editor →](docs/presentations/product-tour.ru.md#sidebar-editor)

### Задачи и расписание

Task Manager показывает личные задачи, работу отдела или весь проект. В Gantt редактируются сроки и прогресс, видны пересечения назначений. Замечания к объекту хранятся в Notes, переписка команды — в Messages. Переходы между производственными этапами задаёт Workflow.

![Gantt: этапы производства, исполнители и сроки](docs/assets/product-tour/gantt.png)

[Задачи и Gantt →](docs/presentations/product-tour.ru.md#планирование) · [Workflow →](docs/presentations/product-tour.ru.md#workflow-граф-и-исполнение) · [Notes и Messages →](docs/presentations/product-tour.ru.md#messages-и-notes)

### Чекин, версии и синхронизация

Файлы добавляются через Drop Plate и попадают в Commit Queue. Перед отправкой видны версия, описание и рассчитанный путь. Публикация сохраняется у объекта в виде snapshot; Repository Sync скачивает выбранные версии в локальный репозиторий. Имена и каталоги задаются правилами Naming Editor.

![Commit Queue: подготовленная публикация, версия и рассчитанный путь](docs/assets/product-tour/commit-queue.png)

[Чекин, чекаут, нейминг и Repository Sync →](docs/presentations/product-tour.ru.md#чекин-и-чекаут)

### Maya и полки скриптов

Плагин открывает, импортирует или подключает reference в выбранной сессии Maya. Для сдачи Maya сохраняет сцену, затем Handler выполняет чекин: передаёт файлы и регистрирует публикацию на сервере.

![Нативная полка Maya, созданная коннектором Handler](docs/assets/product-tour/maya-shelf-strip.png)

На Script Shelf размещаются сохранённые скрипты с подписями, иконками и подсказками. Полка может быть личной, общей или привязанной к вкладке проекта. Из редактора её можно перенести в Maya и обновлять там по мере изменения инструментов.

![Редактор Script Shelf: инструменты проекта, иконки и порядок кнопок](docs/assets/product-tour/shelf-editor.png)

[Maya-плагин, полки и работа со сценами →](docs/presentations/maya.ru.md)

### Помощник проекта

Помощнику можно поручить разбор выбранного ассета: прочитать задачи, замечания и публикации, затем составить отчёт. На снимке — такой запрос по Survey Drone. Моделинг отмечен завершённым, но файла модели среди публикаций нет; помощник отметил это в ответе.

![Помощник проекта работает с ассетами, задачами и опубликованными версиями](docs/assets/product-tour/assistant.png)

[Чат-бот: провайдеры, инструменты и возможности →](docs/presentations/assistant.ru.md)

### Собственные дашборды

В Dashboard Editor собираются страницы с показателями, диаграммами, Item View и действиями над объектами. Ниже — обзор загрузки и статусов проекта. Страницу можно открыть из sidebar и настроить под нужный отдел.

![Кастомный дашборд: показатели проекта, загрузка команды и ассеты](docs/assets/product-tour/dashboard-overview.png)

[Дашборды и визуальное редактирование →](docs/presentations/dashboards.ru.md)

### Справка и база знаний

В базе знаний хранятся инструкции студии: требования к сдаче, вводные для новых сотрудников, технические заметки. Статьи связываются с ассетами и шотами, содержат вложения и доступны через поиск. Есть Visual / Markdown, черновики и история редакций.

![База знаний: инструкция по сдаче, связанная с Survey Drone](docs/assets/product-tour/knowledge-base.png)

[База знаний: чтение, редактор и публикация →](docs/presentations/knowledge-base.ru.md)

Встроенная справка открывается из рабочих окон и главного меню. В ней описаны команды, настройки и процедуры; статьи доступны на русском и английском. Поиск работает по тексту, текущую статью можно сохранить в Markdown.

![Встроенная справка: каталог с поиском и контекстная статья](docs/assets/product-tour/help.png)

[Презентация встроенной справки →](docs/presentations/help.ru.md)

## Настройка и API

| Область | Подробнее |
| --- | --- |
| **Устройство проекта** | [Схема и администрирование](docs/presentations/product-tour.ru.md#администрирование-проекта), [пользователи и права](docs/presentations/product-tour.ru.md#пользователи-и-права), [конфигурация](docs/presentations/product-tour.ru.md#configuration). |
| **Контекст и события** | [Обзор объекта](docs/presentations/product-tour.ru.md#обзор-объекта) и [история работы на сервере](docs/presentations/product-tour.ru.md#activity-feed-и-история-проекта). |
| **Автоматизация** | [Script Editor и среды выполнения](docs/presentations/product-tour.ru.md#script-editor-и-автоматизация), [Python API](docs/handler_api.md), [DCC API](docs/dcc_api.md). |
| **Разработка интерфейса** | [Tactic Frame](docs/presentations/product-tour.ru.md#tactic-frame): общие описания для нативного Qt Quick и Vue. |

**[Полный обзор продукта →](docs/presentations/product-tour.ru.md)** · [Вся документация](docs/index.md)

Редакторы проекта, дашборды и помощник в этой презентации показаны с сервером TACTIC Stream. Для оригинального TACTIC доступна карта совместимости. Скриншоты сделаны в текущем приложении на демонстрационном проекте Orbit Studio.

Проект основан на экосистеме [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC). [Eclipse Public License 1.0](LICENSE).
