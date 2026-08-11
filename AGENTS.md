# TACTIC-Handler QML UI rules

## TACTIC object API

- Before adding an adapter for a TACTIC object, inspect its native methods and the original workflow that consumes them.
- Use `File` preview, repository, path, size, identity, and preparation methods directly; do not reconstruct their results in the modern layer.
- Do not add generic string-based getter wrappers around project objects.
- Keep transport and progress handling in the queue, but preserve the source object's path and repository semantics.
- Treat snapshot metadata size as discovery information; validate an HTTP transfer against the response metadata, as the original download workflow does.

## Handler Server and DCC clients

- Keep TACTIC, repository, and check-in responsibilities in the standalone application; thin DCC clients execute only application-specific actions.
- Derive DCC UI actions from the explicitly selected client's application type and registered capabilities. Do not change the standalone process-wide `env_mode` to emulate a remote DCC.
- Route commands to the selected client id when the user can have multiple Maya, Blender, or other DCC sessions.
- Register DCC actions as fixed native adapter methods. Never send generated Python, `eval`, or `exec` payloads to a thin client.
- A scene save result is preparation data for the standalone check-in workflow; the DCC client must not upload to TACTIC itself.
- Write Handler Server lifecycle, client registration, routed commands, results, timeouts, disconnects, and tracebacks to the shared session Debug Log with request ids and redacted credentials.

## Icons

- Choose an icon that directly describes the action, entity, or state when the UI element is introduced.
- Verify every icon name resolves through the shared `MaterialIcon` mapping; extend that mapping centrally for project vocabulary.
- Never use `o`, `circle`, `category`, or another generic glyph as a placeholder for an unresolved icon.
- Use the three-dot overflow icon for compact menus that collect secondary actions or view options; reserve settings and tune icons for actions that open an actual settings editor.
- Center a lone icon horizontally and vertically in every icon-only button; compacting a labeled button must preserve that centering.

## Shared control and icon reuse gate

- Reuse an existing shared control before writing any local button, popup, field, menu, or indicator implementation.
- Reuse the existing semantic icon for an action; the same action must not use different glyphs in different interfaces.
- Search neighboring QML and `modern_ui/qml/controls` before adding or changing any visual control.
- If a matching visual exists only inline, extract it into `modern_ui/qml/controls` and replace both call sites with that shared control.
- Do not accept a QML change until its shared control, semantic icon, radius, size, states, and animation match the existing interface.

## Project-defined names and localization

- Treat project names, Search Type names, pipeline and process names, statuses, groups, roles, contexts, and other server-configured labels as project data, not application source text.
- Never hardcode one project's labels in QML, Python UI code, or translation catalogs.
- Never pass a complete phrase containing project data to `qsTr` and never call `qsTr` on the project-defined value itself.
- Translate only the surrounding interface template and insert the server value unchanged; for example, render `qsTr("All") + " " + searchTypeName`, so Russian displays `Все Textures` rather than a hardcoded project translation.
- If a project needs localized data labels, they must come from explicit project/server configuration rather than the application translation catalog.

## Resizable QML panels

- Calculate pointer deltas in stable parent, scene, or window coordinates.
- Never measure a resize drag in the local coordinates of the handle or panel whose position changes during that drag; it creates feedback, jitter, and pointer detachment.
- Persist the final size when the drag finishes, not on every pointer movement.
- Define minimum usable width and height for every resizable window and dock through the shared sizing policy.
- The minimum size must keep primary controls visible; secondary content should scroll or reflow instead of overflowing beyond the window.
- Clamp restored geometry to the current minimum so an obsolete saved size cannot reopen a broken layout.

Для любых новых и изменяемых QML-интерфейсов:

- исходные пользовательские строки modern UI писать на английском языке,
  независимо от языка запроса; русский и другие языки поддерживать через механизм
  локализации, не добавляя переведённые строки напрямую в QML/Python;
- соблюдать существующий визуальный язык `modern_ui` и Material Design 3;
- использовать только палитру из действующей темы проекта, без локальных цветов;
- переиспользовать существующие проектные контролы, меню, диалоги, подсказки, тени и индикаторы;
- использовать принятые в проекте состояния hover, pressed, selected, disabled, loading и error;
- анимации брать из существующих компонентов и применять с теми же duration/easing;
- не создавать новый вариант контрола или анимации, пока не найден и не проверен существующий аналог;
- новые визуальные решения сначала сверять с соседними QML-компонентами;
- не смешивать стандартный стиль Qt Quick Controls с проектным MD3-оформлением;
- сохранять единый стиль во всех представлениях одной функции: cards, items, docks, menus и dialogs.

Функциональные требования этапа не дают разрешения менять общий дизайн. Если
существующего компонента недостаточно, расширять его минимально и так, чтобы
остальные интерфейсы могли сохранить единый внешний вид.

## Покрытие Configuration

- Любая новая пользовательская настройка, которая загружается или сохраняется
  в постоянной конфигурации, должна иметь соответствующий элемент в окне
  Configuration.
- Размещать настройку на логически подходящей существующей странице или секции;
  новую секцию создавать только при отсутствии подходящего места.
- Окно Configuration должно использовать тот же API и те же ключи, что и
  функциональный интерфейс, без отдельного QML-only хранилища.
- Не дублировать в Configuration служебное состояние: кэши, временное состояние,
  геометрию и индивидуальные параметры пользовательских вкладок и окон.
