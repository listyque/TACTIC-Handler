# TACTIC Handler

### От первого ассета до опубликованной сцены

Нативное рабочее пространство для студии: объекты, задачи, файлы и инструменты Maya связаны одним производственным контекстом. Python · Qt Quick · TACTIC / TACTIC Stream.

[English](README.md) · [Обзор возможностей](docs/presentations/product-tour.ru.md) · [Maya и shelf](docs/presentations/maya.ru.md) · [Начать работу](#start)

![Рабочее место ревьюера: визуальные ассеты и крупное превью публикации](docs/assets/product-tour/docks-review.png)

> **Прототип в активной разработке.** Perforce-like File Workspace также остаётся прототипом.

<a id="workspace"></a>
## Весь объект — перед глазами

**Обычный Item View** раскрывает ассет в непрерывное дерево: связанные объекты, процессы, задачи, snapshots и версии файлов. Превью, статусы и обсуждения находятся рядом с работой. Для других задач есть карточки, компактные строки, таблица и отдельная область версий.

![Обычный Item View: объект, процессы и раскрытая история версий](docs/assets/product-tour/item-view-standard.png)

[Поиск, представления и работа с объектом →](docs/presentations/product-tour.ru.md#workspace)

<a id="maya"></a>
## Maya входит в рабочий процесс

Откройте опубликованную сцену, импортируйте файл или создайте reference в выбранной Maya. Подготовьте текущую сцену к check-in; Handler продолжит работу с naming, версиями и очередью публикации. Плагин добавляет подключение к Handler и нативную полку запуска.

![Нативная полка Maya 2023, созданная коннектором Handler: запуск TH и проектные инструменты](docs/assets/product-tour/maya-shelf-strip.png)

[Maya-плагин: возможности, установка и работа со сценой →](docs/presentations/maya.ru.md)

<a id="scripting"></a>
## Инструменты студии — на shelf

Сохранённый скрипт становится кнопкой с собственной иконкой, подписью и подсказкой. Соберите личную или общую полку, назначьте отдельный набор вкладке проекта. **Ту же полку можно создать или обновить в подключённой Maya.** Script Editor помогает разрабатывать инструменты и выбирать среду исполнения.

![Редактор shelf: настоящие скрипты демопроекта, подписи, иконки и порядок действий](docs/assets/product-tour/shelf-editor.png)

[Shelf и перенос в Maya →](docs/presentations/maya.ru.md#shelf) · [Script Editor и автоматизация →](docs/presentations/product-tour.ru.md#scripting)

<a id="docks"></a>
<a id="sidebar"></a>
## Соберите свой интерфейс

Доки превращают одно приложение в рабочее место ревьюера, художника или координатора. Разделяйте области, собирайте вкладки, выносите панели на другой монитор. Пресеты, Sidebar Editor и редакторы представлений связывают компоновку с работой отдела.

![Объекты, задачи и опубликованные файлы в одной компоновке](docs/assets/product-tour/docks-planning.png)

[Доки и пресеты →](docs/presentations/product-tour.ru.md#docks) · [Sidebar Editor →](docs/presentations/product-tour.ru.md#sidebar)

<a id="planning"></a>
<a id="workflow"></a>
## От процесса — к плану команды

Workflow задаёт маршрут объекта. Task Manager и Gantt связывают этапы с исполнителями, сроками и прогрессом. Заметки сохраняют решения ревью, а Messages поддерживает разговор команды между проектами.

![Gantt: производственные задачи, исполнители и сроки](docs/assets/product-tour/gantt.png)

[Workflow →](docs/presentations/product-tour.ru.md#workflow) · [Задачи и Gantt →](docs/presentations/product-tour.ru.md#planning) · [Messages →](docs/presentations/product-tour.ru.md#communication)

<a id="files"></a>
## Публикация с понятным результатом

Drop Plate готовит файлы, Commit Queue показывает будущую публикацию, Naming Editor определяет имена и пути. Snapshot Browser возвращает к нужной версии. Repository Sync доставляет выбранные файлы в локальный репозиторий.

![Commit Queue: подготовленная публикация, версия и разрешённый путь](docs/assets/product-tour/commit-queue.png)

[Check-in, check-out, naming и Repository Sync →](docs/presentations/product-tour.ru.md#files)

<a id="assistant"></a>
<a id="dashboards"></a>
## Ещё два способа работать с проектом

| Ассистент проекта | Собственные дашборды |
| --- | --- |
| ![Ассистент анализирует задачи и опубликованные версии](docs/assets/product-tour/assistant.png) | ![Производственный обзор с живыми метриками и объектами](docs/assets/product-tour/dashboard-overview.png) |
| Задайте вопрос по выбранному объекту, изучите ответ и операции, на которых он основан. **[Презентация чат-бота →](docs/presentations/assistant.ru.md)** | Соберите страницу из метрик, диаграмм, Item View и действий. **[Презентация дашбордов →](docs/presentations/dashboards.ru.md)** |

<a id="administration"></a>
<a id="people"></a>
<a id="history"></a>
<a id="object-overview"></a>
<a id="configuration"></a>
<a id="frame"></a>
## Настраивается под вашу студию

[Схема и администрирование](docs/presentations/product-tour.ru.md#administration) · [Пользователи и права](docs/presentations/product-tour.ru.md#people) · [Обзор объекта](docs/presentations/product-tour.ru.md#object-overview) · [История сервера](docs/presentations/product-tour.ru.md#history) · [Tactic Frame](docs/presentations/product-tour.ru.md#frame) · [Конфигурация](docs/presentations/product-tour.ru.md#configuration)

<a id="start"></a>
## Начать работу

[Установка и первое подключение](docs/presentations/product-tour.ru.md#start) · [Maya-плагин](docs/presentations/maya.ru.md#setup) · [Python API](docs/handler_api.md) · [Вся документация](docs/index.md)

Показанные современные инструменты работают с TACTIC Stream. Для исходного TACTIC смотрите [карту совместимости](docs/tactic_compatibility/README.md). Снимки сделаны в текущих приложениях на изолированном Orbit Studio; данные и иллюстрации демонстрационные.

[Eclipse Public License 1.0](LICENSE) · Основано на экосистеме [Southpaw TACTIC](https://github.com/Southpaw-TACTIC/TACTIC).
