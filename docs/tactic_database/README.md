# TACTIC 5.0 Database Reference for Codex

Справочник собран из консолидированных PostgreSQL-схем ветки Southpaw TACTIC `5.0` и реестра `sthpw/search_object`. Дата извлечения: 2026-08-06.

## Что покрыто

- 6 bootstrap-таблиц;
- 50 таблиц основной `sthpw`-схемы;
- 15 project-local таблиц `config/*` (`spt_*`);
- логические search types, физические имена, зарегистрированные классы и поля;
- правила безопасной записи и список подсистем-владельцев;
- связи между workflow, DAM, messaging, security и audit;
- SQL для сравнения с живой установленной базой.

## Важное ограничение

TACTIC допускает произвольные project search types. Их физические таблицы создаются пользователем/шаблоном и регистрируются в `sthpw/search_object`; поэтому исходники не могут содержать конечный список таблиц конкретной студии. Этот комплект документирует **ядро платформы**, а `tools/live_schema_inventory.sql` должен дополнить его таблицами вашего сервера.

## Порядок чтения для Codex

1. `01_DATABASE_RULES.md` — модель данных и обязательные правила.
2. `02_CORE_TABLE_CATALOG.md` — все `sthpw/bootstrap` таблицы.
3. `03_CONFIG_TABLE_CATALOG.md` — все project-local `config/*` таблицы.
4. `04_RELATIONSHIPS_AND_FLOWS.md` — типовые цепочки записи.
5. `05_WRITE_POLICY_MATRIX.md` — короткая матрица «куда и как писать».
6. `06_LIVE_DATABASE_CHECK.md` — как не доверять слепо старой SQL-схеме.
7. `07_EVIDENCE_AND_LIMITATIONS.md` — границы доказанности и confidence.
8. `machine/` — JSON/CSV для автоматического поиска.

## Главная установка

Не проектировать новую таблицу, пока не проверены:

- `sthpw/search_object`;
- таблицы и классы в этом каталоге;
- существующие методы server stub и серверные классы;
- `sthpw/schema`, `sthpw/connection`, `sthpw/note`, `sthpw/task`, `sthpw/snapshot`, `sthpw/message*`, `config/*`;
- фактическая схема живой БД.

## Первичные источники

- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/bootstrap_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/sthpw_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/config_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/search.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/transaction.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/security/security.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/security/access_manager.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/task.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/note.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/snapshot.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/file.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/pipeline.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/subscription.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/tactic/ui/app/message_wdg.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/command/workflow.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/naming.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/checkin/file_checkin.py
