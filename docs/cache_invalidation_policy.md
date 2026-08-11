# Modern UI cache and invalidation policy

Caches remain owned by the controller/model that owns the corresponding data
lifecycle. This avoids a global cache that cannot understand TACTIC mutations.

| Cache | Owner | Key | TTL | Invalidation / refresh | Stale | Maximum |
|---|---|---|---:|---|---:|---:|
| Message history | `MessagesController` | server, login, conversation code | none | session change, delete/mutation/new server timestamp; Refresh conversation | yes | 12 chats |
| SKey preview | `SearchKeyPreviewResolver` | server, login, code-based skey | none | scope changes through the key; Retry link | yes | 768 links |
| Project preview | `ProjectModel` | project code | none | replace projects/repository refresh; Refresh previews | yes | 256 projects |
| Search tab session | `NavigationMixin` | project, section, tab id | none | Clear cache/schema reload/user edits; Reload cache | yes | 128 tabs per project |
| Result controls | `PresentationMixin` | loaded node id and task/process payload | none | node replacement/detail refresh/model reset | no | 5000 loaded nodes |

`None` TTL is deliberate for these records: freshness is event-driven. Server
and user identity are always part of data that can cross a login boundary.
Explicit refresh must invalidate only the owning scope before scheduling a new
request; it must not clear unrelated application state.

The message, SKey, and project-preview caches are bounded LRU collections.
Search sessions are persisted user workspace state, so the stated maximum is a
workspace policy rather than a time-based eviction rule. A future split of the
large results dock must preserve these owners and invalidation events.
