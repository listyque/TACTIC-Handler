---
order: 70
---
# System Info

> The legacy diagnostics panel, with its information sections and test actions.

Open the main menu → **System Info** (administrator only). Server, Python and
Client show separate facts; Handler adds its own OS/Python/Qt and Stream shows
browser identity/time zone. Refresh reads facts; Copy copies them. Nothing is
polled while idle. Each test runs only when its button is pressed.

- **Load Balancing / Test load balancing** samples responding workers and ports:
  50 requests with up to eight in flight, even if one worker answers initially.
  Handler uses independent client connections; browsers manage their connection
  pool. Worker IDs distinguish processes sharing one listener. The result is an
  observed sample, not the configured worker count; one worker does not prove
  balancing is disabled.
- **Performance Test / Test performance** performs sequential and parallel reads
  of the Users table definition and up to 20 rows. It uses the CPU count (at most
  256 requests, at most eight in flight) and reports real elapsed request time.
  This replaces the legacy HTML ViewPanel request with the modern table request;
  it includes network/server time, not a client-only render benchmark.
- **Mail Server** shows configuration, editable From and To (comma-separated
  recipients) and **Email Send Test**. Defaults are the administrator's email.
  This sends a real email through the original EmailTriggerTestCmd/TLS settings.
- **Asset Folders** lists repository/handoff paths and server write-access checks.
  **Test client handoff** checks actual client directories in Handler. Browsers
  cannot inspect arbitrary local paths: Stream reports that limit explicitly;
  it never reports a server path as a successful client check. No transfer mode
  is silently changed and access checks create no files.
- **Link Test** offers **Include built-in pages**, **Run link test** and individual
  page buttons. It opens the original configured project definitions in browser
  windows. Permit pop-ups in Stream; blocked windows are counted. Handler opens
  the same Stream addresses in the system browser. Unported page handlers show
  their actual unavailable-handler error; this test does not make them supported.
- **Python Script Test** accepts the path of a saved `config/custom_script` and
  **Run script** calls the original PythonCmd in the current project. The script
  runs with administrator authority and can change data, just as in legacy.

Results and failures appear under their own buttons. Closing or changing the
session invalidates late results; it does not undo an already sent email or a
running server script. Tests never run automatically or retry writes.
