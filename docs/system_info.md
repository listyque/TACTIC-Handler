# System Info

`SystemInfoController` registers `show_system_info`, opens the existing native
`FloatingWindow`/`WindowHost` and reads server facts using the authenticated
SDK's `execute_class_method` on a server-pool worker. It calls
`tactic.ui.app.system_info_wdg.SystemInfoWdg.get_info`, which requires a Stream
administrator. It never imports Stream modules or probes the server locally.
Local Handler version, operating system, Python and Qt are a separate section.

The shared Frame description renders separate Server/Python/Client sections,
load-balancing/performance tests, editable email sender/recipients, asset/handoff
paths and test, project-page load test with built-in checkbox, saved-script path
and Run. Plain values are not a report editor.
The bounded body uses the shared scrollbar; clipboard copying is a toolbar action.

There is no polling or persistent report cache. Close, authentication changes
and shutdown cancel pending work and invalidate its generation. Stale replies
cannot republish facts; already issued server writes are not undone by closing.
The server pool owns all requests/local path checks. Parallel probes use separate
SDK clients/transports with the captured session, up to eight concurrently.
The SDK forwards `execute_class_method(class_name, method, kwargs=None)` with
its current ticket and project through either XML-RPC or JSON. Parallel clients
copy the server address from `get_server_name()`, never the transport proxy
returned by `get_server()`. Server-side execution and administrator checks remain
authoritative; remote faults propagate through the existing error presentation.
Load balancing always samples 50 requests with at most eight independent clients
in flight. It does not stop after repeated replies from one worker. The result
is explicitly a sample, not the configured worker count. Browser pooling or
upstream affinity may still route all requests to one worker.
The page test opens the same Stream addresses in the system browser, without
passing tickets in URLs. Navigation refresh remains with its normal owner;
System Info does not clear an unused legacy filesystem cache.

`tests/test_system_info.py` exercises all test buttons and fields with actual
QML mouse/keyboard input, copy, narrow/wide geometry, local folder access,
failed reads, access denial and a completion after close. SMTP/script/page actions
are mocked at the remote boundary; no live email or working script is invoked.
The server projection, independent API/security tests and legacy exclusions are
documented in Stream's `docs/SYSTEM_INFO.md`; user-facing scope is in the local
EN/RU `system_info` Help topic.

`tests/test_system_info_transport.py` exercises the shipped SDK over loopback
HTTP in both protocols, including facts, load-balancing samples, independent
parallel clients, method arguments, and remote permission denial. Only the
remote diagnostic implementation is a fixture; the SDK and transport are real.
