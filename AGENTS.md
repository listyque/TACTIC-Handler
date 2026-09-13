# TACTIC-Handler engineering rules

## Scope and precedence

- This file defines repository-wide engineering rules. A nested `AGENTS.md` may add stricter domain-specific requirements but must not weaken this baseline.
- Follow explicit user requirements first, then the nearest applicable `AGENTS.md`, then established local conventions. When two rules appear to conflict, preserve the more specific safety, data-integrity, or project requirement and document the decision.
- Inspect the current implementation, call sites, tests, configuration, and relevant original workflow before changing code. Conversation history is context, not proof of the current state.
- Never infer behavior from file, module, class, or function names alone. Verify the implementation, call sites, and actual execution flow before drawing conclusions.
- Preserve unrelated user changes in a dirty worktree. Never reset, overwrite, reformat, rename, or clean unrelated files as part of a focused task.

## Change discipline

- Work like a pragmatic lead engineer: understand first, reuse existing paths, extend the narrowest suitable owner, and keep the change coherent and easy to review.
- Make the smallest complete change that solves the requested behavior. Do not mix functional work with broad formatting, renaming, cleanup, or speculative refactoring.
- Do not rewrite stable code merely to reduce line count or impose a preferred style. Refactor when it improves ownership, correctness, testability, reuse, or measured runtime behavior.
- Do not add speculative abstractions, one-use wrappers, unused extension points, parallel workflows, or configuration paths. Prefer explicit domain code over generic machinery.
- When the task intentionally replaces a format, API, control, storage path, or workflow, remove the superseded implementation, fallback, migration, reader, adapter, and dead tests completely. This repository is in closed active development; compatibility is added only when the user explicitly requests it.
- Keep behavior changes, their tests, and their documentation in the same change. Delete documentation and tests that describe a removed path.

## Architecture and ownership

- Give every mutable state and side effect one clear owner. Do not maintain unsynchronized copies of the same state in QML, controllers, caches, and services.
- Dependencies flow inward toward domain behavior and stable interfaces. Presentation code may depend on domain-facing controllers; domain and shared infrastructure must not depend on a feature view.
- Make dependencies explicit through construction, required properties, or narrow method parameters. Do not introduce hidden service lookup or global mutable state when the existing composition root can provide the dependency.
- Keep transport, persistence, presentation, and domain decisions in separate owners. A boundary object should translate between layers, not duplicate business logic.
- Put new behavior in the narrowest existing domain module. Split a module only at a real responsibility or lifecycle boundary; do not create a universal controller, model, helper, or registry.
- Preserve stable public imports, QObject properties, signals, slots, model roles, and launcher contracts unless changing that contract is part of the request.
- Validate data at trust boundaries and maintain invariants inside the owning layer. Reject malformed states early with actionable errors.
- Keep operations idempotent where retries are possible. Deduplicate by stable identity rather than display text or object address.

## Python code

- Follow PEP 8 and the established repository formatting. Prefer descriptive domain names, short cohesive functions, early returns, and direct control flow.
- Code must be simple, concise, and readable on first pass. Prefer domain actions, small named decisions, and sequential state transitions over parallel `canX` flags, dense multi-line boolean expressions, nested callbacks, or duplicated payload dictionaries. Treat those patterns as code smells and replace them with the smallest semantic result, such as a set of allowed actions.
- Use type annotations on new public boundaries and non-obvious data shapes; do not perform unrelated mass typing of legacy code.
- Avoid mutable default arguments, bare `except`, silent exception swallowing, and broad exception handling that hides programmer errors. Catch the narrowest expected exception and retain causal context when re-raising.
- Use context managers for files, locks, temporary resources, and transactions. Define cleanup and cancellation behavior for every long-lived worker, subscription, timer, and external process.
- Comments explain intent, invariants, tradeoffs, and non-obvious constraints. Do not narrate code that can be made self-explanatory through naming and structure.
- Keep import-time work minimal and deterministic. Do not perform network, repository, database, or heavyweight UI initialization as an import side effect.

## Concurrency, lifecycle, and responsiveness

- Never perform TACTIC, network, repository, database, large filesystem, or expensive CPU work on the UI thread.
- Workers return immutable or clearly owned result data. Apply QObject and QML model mutations on the owning Qt thread.
- Give asynchronous requests a generation, request id, or cancellation token when selection, project, page, or controller lifetime can change. Ignore stale completions and disconnect callbacks during teardown.
- Do not replace global TACTIC APIs with stubs to solve a controller lifecycle problem. Fix cancellation, ownership, and teardown in that controller.
- Avoid polling when a signal or event exists. Bound retries, backoff, queues, and caches, and make waiting/cancelled/error states observable.
- Profile before optimizing. Use measurements for startup, memory, frame time, request count, and delegate creation; do not claim a performance fix from static inspection alone.

## TACTIC object API

- Before adding an adapter for a TACTIC object, inspect its native methods and the original workflow that consumes them.
- Use `File` preview, repository, path, size, identity, and preparation methods directly; do not reconstruct their results in the application layer.
- Do not add generic string-based getter wrappers around project objects.
- Keep transport and progress handling in the queue while preserving the source object's path, repository, and identity semantics.
- Treat snapshot metadata size as discovery information. Validate an HTTP transfer against response metadata, as the original download workflow does.
- Project names, Search Type names, pipelines, processes, statuses, groups, roles, contexts, and other server-configured labels are data. Never translate, hardcode, or reinterpret them in application source.

## Handler Server and DCC clients

- Keep TACTIC, repository, and check-in responsibilities in the standalone application. Thin DCC clients execute only application-specific native actions.
- Derive DCC UI actions from the explicitly selected client's application type and registered capabilities. Do not change the standalone process-wide `env_mode` to emulate a remote DCC.
- Route commands to the selected client id when multiple Maya, Blender, or other DCC sessions can be connected.
- Register DCC actions as fixed native methods. Never send generated Python, `eval`, or `exec` payloads to a thin client.
- A scene-save result is preparation data for the standalone check-in workflow; the DCC client must not upload to TACTIC itself.
- Log server lifecycle, registration, routed commands, results, timeouts, disconnects, and tracebacks with request ids and redacted credentials.

## Configuration and persistent state

- Production code uses only `thlib.environment.env_read_config` and `env_write_config`. Do not use `QSettings`, the Windows Registry, a compatibility adapter, or a parallel configuration format.
- Use meaningful `unique_id` and `filename` values and `long_abs_path=True`. Store UI settings under the appropriate `ui_*` location and persistent caches under `cache/*`.
- Independent controllers must not read and rewrite unsynchronized copies of one shared configuration dictionary.
- Isolated and smoke tests redirect `env_mode.current_path`; they never read or mutate production configuration.
- User-facing persistent settings must be represented on the logically matching Configuration page. Internal caches, geometry, transient state, and per-tab or per-window working state are not Configuration options.

## Errors, logging, and security

- Fail explicitly at boundaries and present actionable user errors. Do not turn cancellation, empty results, expected offline states, or DCC-owned failures into unrelated application errors.
- Debug Log events must retain complete messages, details, runtime commands, payloads, script bodies, and tracebacks; do not truncate by length or depth. Control production volume through enabled event levels, not lost diagnostic data.
- Always redact passwords, tickets, tokens, connection secrets, and sensitive fields before logging or serialization. Sanitize untrusted line breaks and delimiters where they could forge log records.
- Mark cyclic Python references explicitly so serialization terminates. Bound log retention and queue growth without silently truncating an individual diagnostic event.
- Never commit credentials, private endpoints, generated session data, or local machine paths unless the repository explicitly defines them as test fixtures.

## Testing and verification

- **Every scrollable view whose content can exceed its viewport must expose the shared scrollbar and reserve breathing room for it; hidden, transient-only, clipped, or content-overlapping scrollbars are defects.**
- Add or update a regression test for every bug fix and behavior change. Whenever practical, prove that the test fails on the broken behavior before relying on it as evidence for the fix.
- Test at the lowest useful layer and at the real integration boundary. Mocks isolate logic but do not replace QML creation, actual model wiring, filesystem, transport, or platform tests when those boundaries caused the bug.
- Keep tests deterministic, independent, and fast. Avoid arbitrary sleeps, order dependence, production configuration, external mutable state, and assertions with side effects.
- For UI work, instantiate the affected QML, exercise the real input path, and inspect layout in relevant narrow and wide geometries. Test mouse, keyboard, touch, focus, scrolling, popup placement, and DPI when the change affects them.
- Run focused tests during development, then the relevant integration and QML smoke suites. A static source assertion alone is never sufficient evidence of runtime or layout correctness.
- Treat warnings, binding loops, invalid contexts, thread-affinity failures, and resource leaks as defects even when the nominal test passes.

## Documentation

- Keep developer documentation in English. Preserve server-defined identifiers, commands, paths, API names, and code examples exactly unless they are obsolete.
- Document why a constraint exists, its owner, and how it is verified. Avoid aspirational documentation that is not enforced by code, tests, or review.
- Update user help, developer docs, and operational notes in the same change as the behavior they describe.
- Follow the canonical [Modern UI QML component contract](docs/ui_component_policy.md) for every new or changed QML interface.

## External engineering baseline

These primary sources inform the general rules above. Project-specific rules in this repository take precedence where they are stricter:

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Qt QML Coding Conventions](https://doc.qt.io/qt-6/qml-codingconventions.html)
- [Qt Quick Performance Considerations](https://doc.qt.io/qt-6/qtquick-performance.html)
- [Qt Test Best Practices](https://doc.qt.io/qt-6/qttest-best-practices.html)
- [Google Engineering Practices: Small Changes](https://google.github.io/eng-practices/review/developer/small-cls.html)
- [Google Engineering Practices: What to Look For](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [Microsoft Architectural Principles](https://learn.microsoft.com/dotnet/architecture/modern-web-apps-azure/architectural-principles)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
