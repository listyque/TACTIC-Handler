# TACTIC Database Rules

## 1. Search type важнее физической таблицы

Код должен работать с логическим именем вроде `sthpw/task`, `config/process` или `my_project/asset`, а не с голым именем таблицы. `sthpw/search_object` определяет DB, физическую таблицу и Python-класс. Для `config/*` физические таблицы называются `spt_*` и находятся в каждой project DB.

## 2. Прямой SQL — не штатный способ записи

Штатная цепочка: `SearchType.create()`/специализированный factory → `SObject.set_value()` → `commit()` или команда/ServerStub API. Это сохраняет security, triggers, transaction log, change timestamps и кэши. Прямой SQL допустим только для миграций и диагностического ремонта.

## 3. Не создавать вручную производные записи

- `snapshot` и `file` создаются check-in системой;
- `status_log`, `transaction_log`, `sobject_log`, `change_timestamp`, notification logs создаются системой;
- `message_log` создаётся messaging API;
- `process_state` создаётся workflow engine;
- `login`/`ticket` изменяются security API.

## 4. Полиморфная привязка

Многие таблицы используют `search_type + search_id`, а новые участки также `search_code`. Не добавлять собственный FK к каждой project table. Передавать search key/SObject в нативный API и позволять TACTIC заполнить связь.

## 5. Retire вместо удаления

Для пользовательских/config SObjects обычно использовать retire (`s_status`) и нативный retire API. Hard delete оставлять системному cleanup/uninstall, иначе теряются audit, dependencies и references.

## 6. `project_code` и область данных

`sthpw/*` — глобальные таблицы, но многие строки принадлежат проекту через `project_code`. `config/*` — физически находятся в project DB. Не смешивать global и project-scoped определения.

## 7. XML/JSON — контракт подсистемы

Поля `pipeline`, `schema`, `config`, `snapshot`, `access_rules`, `manifest`, `status`, `data`, `metadata` не являются свободными текстовыми корзинами. Сохранять неизвестные ключи, использовать owning parser/manager и не переписывать payload частично без merge.

## 8. Кэш и reload

Изменения `config/naming`, `config/widget_config`, triggers, security groups, pipeline/process и settings могут кэшироваться. После административной записи использовать штатный manager/command, который инвалидирует или перезагружает кэш.

## 9. Security всегда серверная

Скрытие кнопки клиентом — только UX. Любая mutation должна выполняться под пользовательским ticket и проверяться серверным `AccessManager`.

## 10. Источник истины — живая база плюс код

Консолидированный SQL описывает ветку 5.0, но установленный сервер мог пройти дополнительные upgrades или иметь плагины. Перед новым модулем запускать live inventory и сравнивать registry/columns.
