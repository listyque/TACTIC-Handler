---
group: Workflows
icon: bolt
order: 41
---
# Script triggers

> Script triggers run saved scripts immediately before or after selected Handler and DCC actions.

## Main controls

Open Script Triggers from Script Editor. Choose an action, Before or After, and a saved script.

Optional Search Type, search key, process, and context filters restrict when it runs. Multiple
matching scripts run from top to bottom.

## Usage notes

- Every trigger receives TACTIC_SCRIPT_KWARGS.
- Common keys are event, phase, operation_id, project_code, source, client_id, targets, search_key,
  process, and context.
- Action-specific data such as values, file, snapshot, or result_search_key is included when
  available.
- Print the dictionary while testing to inspect the exact payload.
- Captured Handler and DCC stdout and stderr are written to Script Editor's Output panel and to
  Debug Log when LOG events are enabled; when the triggering script already has an open tab, its
  output stays with that tab.
- Server scripts expose their returned RESULT there; their process stdout remains in the TACTIC
  server log.
- An exception from a Before script blocks the action.
- An exception from an After script is logged, but cannot undo the completed action and does not
  stop later After scripts.

## Examples

### Resolve real SObject instances from the payload

`targets`, `target`, and `snapshot` in `TACTIC_SCRIPT_KWARGS` are plain action descriptors. Resolve
their `search_key` values through the public API before reading fields, relationships, tasks, or
snapshots. This example is ready for Local Python; DCC Python uses the same API through its connected
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

Before object creation, `search_key` can be absent because no server object exists yet. After batch
creation, the new identities are supplied in `result_search_keys`.

### Resolve a Snapshot and its File objects

When a published file is opened, `snapshot.search_key` identifies its snapshot. Resolve it to a
`Snapshot`, then use the native File objects for repository paths and metadata.

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

### Before: inspect context and block the action

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

### After: react to a completed action

```python
data = TACTIC_SCRIPT_KWARGS

print('Completed:', data['event'])
print('Project:', data['project_code'])
for target in data.get('targets', []):
    print('Target:', target['search_key'])

RESULT = data.get('result_search_key')
```
