---
group: Рабочие процессы
icon: bolt
order: 41
---
# Триггеры скриптов

> Триггеры запускают сохранённые скрипты непосредственно до или после выбранных действий Handler и
> DCC.

## Основные элементы

Откройте «Триггеры скриптов» из редактора скриптов. Выберите действие, запуск до или после него и
сохранённый скрипт.

Необязательные фильтры по Search Type, search key, процессу и контексту ограничивают условия
запуска. Несколько подходящих скриптов выполняются сверху вниз.

## Как пользоваться

- Каждый триггер получает TACTIC_SCRIPT_KWARGS.
- Общие ключи: event, phase, operation_id, project_code, source, client_id, targets, search_key,
  process и context.
- Данные конкретного действия — например values, file, snapshot или result_search_key — добавляются,
  когда доступны.
- Во время тестирования выведите словарь через print, чтобы увидеть точный payload.
- Перехваченные stdout и stderr скриптов Handler и DCC записываются в панель «Вывод» редактора
  скриптов и в Debug Log, если включены события LOG; если скрипт триггера уже открыт во вкладке,
  вывод остаётся в этой вкладке.
- Server-скрипты показывают там возвращённый RESULT; stdout их процесса остаётся в журнале сервера
  TACTIC.
- Исключение в скрипте «До действия» блокирует действие.
- Исключение в скрипте «После действия» записывается в журнал, но не может отменить уже завершённое
  действие и не останавливает следующие скрипты после действия.

## Примеры

### Получить настоящие SObject из payload

`targets`, `target` и `snapshot` внутри `TACTIC_SCRIPT_KWARGS` — обычные словари с данными
действия. Для чтения полей, связей, задач и снапшотов получите публичные объекты API по их
`search_key`. Пример подходит для Local Python; DCC Python использует тот же API через подключённый
Handler.

```python
from tactic_handler_api import get_api

data = TACTIC_SCRIPT_KWARGS
th = get_api()

search_keys = [
    target['search_key']
    for target in data.get('targets', [])
    if target.get('search_key')
]
for name in ('search_key', 'result_search_key'):
    if data.get(name):
        search_keys.append(data[name])
search_keys.extend(data.get('result_search_keys') or [])

sobjects = [
    th.sobject(search_key)
    for search_key in dict.fromkeys(search_keys)
]

for sobject in sobjects:
    print('Object:', sobject.get_search_key())
    print('Values:', dict(sobject.get_info()))

RESULT = [dict(sobject.get_info()) for sobject in sobjects]
```

До создания объекта `search_key` может отсутствовать — настоящего объекта на сервере ещё нет.
После пакетного создания новые ключи приходят в `result_search_keys`.

### Получить Snapshot и его File-объекты

При открытии опубликованного файла ключ снапшота находится в `snapshot.search_key`. По нему можно
получить `Snapshot`, а затем родные File-объекты с репозиторными путями и метаданными.

```python
from tactic_handler_api import get_api

data = TACTIC_SCRIPT_KWARGS
th = get_api()
snapshot_key = (data.get('snapshot') or {}).get('search_key')

if snapshot_key:
    snapshot = th.snapshot(snapshot_key)
    print('Snapshot:', dict(snapshot.get_info()))

    for file_object in snapshot.get_files_objects():
        print('File:', file_object.get_full_abs_path())
        print('Metadata:', file_object.get_metadata())
```

### До действия: проверить контекст и при необходимости заблокировать действие

```python
data = TACTIC_SCRIPT_KWARGS

if data['phase'] != 'before':
    raise RuntimeError('This script must run before the action')

targets = data.get('targets', [])
if not targets:
    raise RuntimeError('Select an object first')

print('Starting:', data['event'])
print('Target:', targets[0]['search_key'])
RESULT = {'allowed': True}
```

### После действия: обработать завершённое действие

```python
data = TACTIC_SCRIPT_KWARGS

print('Completed:', data['event'])
print('Project:', data['project_code'])
for target in data.get('targets', []):
    print('Target:', target['search_key'])

RESULT = data.get('result_search_key')
```
