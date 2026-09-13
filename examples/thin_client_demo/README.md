# Simulated Maya thin client

Start the TACTIC-Handler application. Its local Handler Server starts in the
background automatically. Then run as many demo clients as needed:

```powershell
python examples/thin_client_demo/demo_client.py
```

The client discovers the current per-user localhost session and generates a unique
client id. It does not need a server address, port, or token. A second invocation
creates another independent simulated Maya client and both appear in the main UI.

For standalone transport testing, `python -m handler_server.launcher` also generates
its own random token and publishes the same discovery record. Manual
`--host/--port/--token` client arguments are retained only for diagnostics.

The demo opens a small MD3 client window and registers itself as `maya`. Its action
list can inspect, validate, prepare, and save a simulated Maya scene. The
`Prepare scene check-in` action returns both the saved `.ma` file and a generated
playblast image, matching the normalized payload used by the standalone queue. The main
TACTIC-Handler header displays the active DCC and allows switching between connected
clients. Item context menus expose only actions registered by that selected client.

The adapter has no Maya or TACTIC dependency and never evaluates received code.
Files written by the simulated save action live in the operating system's temporary
directory. The production Maya example uses the same command registry contract.
