"""Server procedure for the project-scoped Knowledge Base store."""


def knowledge_request(
    action: str,
    project_code: str,
    identity: str = "",
    document: dict = None,
    organization: list = None,
    expected_revision: str = "",
    query: str = "",
    attachment_key: str = "",
    history_revision: str = "",
) -> str:
    """Execute inside TACTIC; do not import desktop UI modules here."""
    import hashlib
    import json
    import re
    import xml.etree.ElementTree as ElementTree
    from urllib.parse import urlparse

    from pyasm.biz import Project, Snapshot
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from tactic_client_lib import TacticServerStub

    table = "th_knowledge_article"
    search_type = "%s/%s" % (project_code, table)
    allowed_actions = {
        "attachments", "delete_attachment", "initialize",
        "history", "history_revision", "link_index", "list", "load",
        "organize", "reserve", "save", "save_draft",
    }
    if action not in allowed_actions:
        raise ValueError("Unknown Knowledge Base operation")
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError("Select a project before opening its Knowledge Base")

    security = Environment.get_security()
    administrator = bool(security.is_admin())
    api = TacticServerStub.get(protocol="local")
    current_login = str(api.get_login() or "")
    group_search = Search("sthpw/login_in_group")
    group_search.add_filter("login", current_login)
    group_names = {
        str(row.get_value("login_group") or "").casefold()
        for row in group_search.get_sobjects()
    }
    can_edit = administrator or any(
        name == "admin" or "supervisor" in name for name in group_names
    )

    registered = Search("sthpw/search_object")
    registered.add_filter("code", search_type)
    registered_exists = registered.get_sobject() is not None
    definitions = (
        ("kind", "varchar(32)"),
        ("parent_code", "varchar(256)"),
        ("content", "text"),
        ("content_text", "text"),
        ("sort_order", "integer"),
        ("updated_by", "varchar(256)"),
        ("linked_skeys", "text"),
    )
    message_definitions = (
        ("sthpw/message", (("metadata", "text"),)),
        ("sthpw/message_log", (("metadata", "text"),)),
    )

    def available_columns(value):
        try:
            return set(SearchType.get_columns(value) or [])
        except AttributeError as error:
            if "undefined" not in str(error).casefold():
                raise
            return None

    message_columns = {
        message_search_type: available_columns(message_search_type)
        for message_search_type, _required_columns in message_definitions
    }
    messages_initialized = all(
        message_columns[message_search_type] is not None
        and all(
            name in message_columns[message_search_type]
            for name, _data_type in required_columns
        )
        for message_search_type, required_columns in message_definitions
    )
    columns = available_columns(search_type) if registered_exists else set()
    initialized = registered_exists and columns is not None and all(
        name in columns for name, _data_type in definitions
    )

    if action == "initialize":
        if not administrator:
            raise PermissionError(
                "A TACTIC administrator must initialize the Knowledge Base"
            )
        if not registered_exists:
            api.create_search_type(
                table,
                "Knowledge Base Content",
                "Project articles and sections for TACTIC Handler",
                has_pipeline=False,
            )
            SearchType.clear_column_cache(search_type)
            columns = available_columns(search_type)
        if columns is None:
            raise ValueError(
                "The Knowledge Base Search Type is registered but unavailable. "
                "Restore the project database or its Search Type registration."
            )
        for name, data_type in definitions:
            if name not in columns:
                api.add_column_to_search_type(
                    search_type, name, data_type
                )
        SearchType.clear_column_cache(search_type)
        for message_search_type, required_columns in message_definitions:
            current_message_columns = available_columns(message_search_type)
            if current_message_columns is None:
                raise ValueError(
                    "Required TACTIC Search Type [%s] is unavailable."
                    % message_search_type
                )
            for name, data_type in required_columns:
                if name not in current_message_columns:
                    api.add_column_to_search_type(
                        message_search_type, name, data_type
                    )
            SearchType.clear_column_cache(message_search_type)
        messages_initialized = True
        initialized = True
        action = "list"

    if not initialized:
        return json.dumps({
            "initialized": False,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "catalog": [],
            "links": [],
            "query": str(query or ""),
        })

    def normalize_linked_skeys(values):
        if values is None:
            return []
        if not isinstance(values, (list, tuple)):
            raise ValueError("Linked objects must be a list of search keys")
        result = []
        for raw_value in values:
            value = str(raw_value or "").strip()
            if value and not value.startswith("skey://"):
                value = "skey://" + value
            parsed = urlparse(value)
            if (
                parsed.scheme.casefold() != "skey"
                or not parsed.netloc
                or not parsed.path.strip("/")
            ):
                raise ValueError("A linked object must use a valid skey:// URL")
            if len(value) > 2048:
                raise ValueError("A linked object search key is too long")
            if value not in result:
                result.append(value)
            if len(result) > 128:
                raise ValueError("An article cannot link more than 128 objects")
        return result

    def validate_document(values):
        values = dict(values or {})
        allowed = {
            "contentMarkdown", "contentText", "description", "kind",
            "linkedSearchKeys", "parentCode", "sortOrder", "title",
            "draft",
        }
        if set(values) - allowed:
            raise ValueError("Unknown Knowledge Base field")
        kind = str(values.get("kind") or "article").strip().casefold()
        if kind not in {"article", "section"}:
            raise ValueError("Knowledge Base entries must be articles or sections")
        title = str(values.get("title") or "").strip()
        if not title:
            raise ValueError("Enter a title")
        if len(title) > 256:
            raise ValueError("The title is too long")
        description = str(values.get("description") or "").strip()
        if len(description) > 4000:
            raise ValueError("The summary is too long")
        content = str(values.get("contentMarkdown") or "")
        content_text = str(values.get("contentText") or "").strip()
        if kind == "section":
            content = content_text = ""
        linked_skeys = (
            normalize_linked_skeys(values.get("linkedSearchKeys"))
            if kind == "article" else []
        )
        if len(content.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("The article is larger than 2 MB")
        if len(content_text) > 1_000_000:
            raise ValueError("The searchable article text is too long")
        try:
            sort_order = int(values.get("sortOrder") or 0)
        except (TypeError, ValueError):
            raise ValueError("Article order must be an integer")
        return {
            "kind": kind,
            "title": title,
            "description": description,
            "contentMarkdown": content,
            "contentText": content_text,
            "linkedSearchKeys": linked_skeys,
            "parentCode": str(values.get("parentCode") or "").strip(),
            "sortOrder": sort_order,
        }

    def item_for(identity_value):
        if not identity_value:
            return None
        identity_value = str(identity_value).strip()
        try:
            item_id = int(identity_value)
        except (TypeError, ValueError):
            item_id = None
        if item_id is not None:
            search = Search(search_type)
            search.add_filter("id", item_id)
            item = search.get_sobject()
            if item is not None:
                return item
        if "code" in columns:
            search = Search(search_type)
            search.add_filter("code", identity_value)
            item = search.get_sobject()
            if item is not None:
                return item
        return None

    def item_identity(item):
        code = (
            item.get_value("code", no_exception=True)
            if "code" in columns else ""
        )
        return str(item.get_id() or code or "")

    def item_references(item):
        references = [item_identity(item)]
        if "code" in columns:
            code = str(item.get_value("code", no_exception=True) or "")
            if code and code not in references:
                references.append(code)
        return references

    def item_is_draft(item):
        return (
            "s_status" in columns
            and str(item.get_value("s_status", no_exception=True) or "")
            .strip().casefold() == "draft"
        )

    def item_owner(item):
        login = (
            item.get_value("login", no_exception=True)
            if "login" in columns else ""
        )
        return str(login or item.get_value(
            "updated_by", no_exception=True
        ) or "")

    def draft_is_visible(item):
        return not item_is_draft(item) or item_owner(item) == current_login

    revision_fields = (
        "name", "description", "kind", "parent_code", "content",
        "content_text", "sort_order", "updated_by", "linked_skeys",
        "timestamp", "last_update", "s_status",
    )
    catalog_fields = (
        "name", "description", "kind", "parent_code", "sort_order",
        "updated_by", "timestamp",
    )

    def revision(item):
        payload = {
            field: item.get_value(field, no_exception=True) or ""
            for field in revision_fields
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def search_key(item):
        value = str(SearchKey.get_by_sobject(item, use_id=False) or "")
        return value if value.startswith("skey://") else "skey://" + value

    def article_object_logs(item, limit=80):
        """Return the native audit index for one project-scoped entry."""
        indexed_types = (
            "%s?project=%s" % (search_type, project_code),
            search_type,
        )
        for indexed_type in indexed_types:
            source = Search("sthpw/sobject_log")
            source.add_filter("search_type", indexed_type)
            source.add_filter("search_id", item.get_id())
            source.add_order_by("timestamp", direction="desc")
            source.set_limit(limit)
            rows = list(source.get_sobjects())
            if rows:
                return rows
        return []

    def article_metadata(item):
        created_at = str(
            item.get_value("timestamp", no_exception=True) or ""
        )
        updated_at = str(
            item.get_value("last_update", no_exception=True) or ""
        )
        if not updated_at:
            audit_rows = article_object_logs(item, limit=1)
            if audit_rows:
                updated_at = str(
                    audit_rows[0].get_value(
                        "timestamp", no_exception=True
                    ) or ""
                )
        updated_at = updated_at or created_at
        author = str(
            item.get_value("login", no_exception=True)
            or item.get_value("updated_by", no_exception=True)
            or ""
        )
        return {
            "author": author,
            "createdAt": created_at,
            "updatedBy": str(
                item.get_value("updated_by", no_exception=True) or author
            ),
            "updatedAt": updated_at,
        }

    history_state_fields = revision_fields + ("login",)
    visible_history_fields = {
        "content", "description", "kind", "linked_skeys", "name",
        "parent_code", "sort_order", "s_status",
    }

    def transaction_xml(transaction, data):
        """Expand compressed TACTIC transaction XML through its native API."""
        getter = getattr(transaction, "get_xml_value", None)
        if getter:
            try:
                xml_value = getter("transaction")
                serializer = getattr(xml_value, "to_string", None)
                if serializer:
                    try:
                        value = serializer(pretty=False)
                    except TypeError:
                        value = serializer()
                    if isinstance(value, bytes):
                        return value.decode("utf-8", errors="replace")
                    return str(value or "")
            except (AttributeError, TypeError, ValueError):
                pass
        return str(data.get("transaction") or "")

    def transaction_article_nodes(transaction, references):
        data = transaction.get_data()
        source = transaction_xml(transaction, data).strip()
        if not source or "<" not in source:
            return data, []
        try:
            root = ElementTree.fromstring(source)
        except (ElementTree.ParseError, TypeError, ValueError):
            return data, []
        nodes = []
        for node in root.iter("sobject"):
            node_type = str(
                node.get("search_type") or ""
            ).split("?", 1)[0]
            node_identity = str(
                node.get("search_code") or node.get("search_id") or ""
            )
            if node_type == search_type and node_identity in references:
                nodes.append(node)
        return data, nodes

    def historical_document(state):
        raw_links = str(state.get("linked_skeys") or "").strip()
        try:
            linked_skeys = json.loads(raw_links) if raw_links else []
        except (TypeError, ValueError):
            linked_skeys = []
        if not isinstance(linked_skeys, list):
            linked_skeys = []
        try:
            sort_order = int(state.get("sort_order") or 0)
        except (TypeError, ValueError):
            sort_order = 0
        return {
            "title": str(state.get("name") or ""),
            "description": str(state.get("description") or ""),
            "kind": str(state.get("kind") or "article"),
            "parentCode": str(state.get("parent_code") or ""),
            "contentMarkdown": str(state.get("content") or ""),
            "contentText": str(state.get("content_text") or ""),
            "linkedSearchKeys": normalize_linked_skeys(linked_skeys),
            "sortOrder": sort_order,
            "draft": str(state.get("s_status") or "").casefold() == "draft",
        }

    def article_history(article, selected_revision=""):
        """Reconstruct article states by walking its audit trail backwards."""
        state = {
            field: article.get_value(field, no_exception=True) or ""
            for field in history_state_fields
        }
        article_references = set(item_references(article))
        transaction_ids = []
        for object_log in article_object_logs(article):
            transaction_id = object_log.get_value(
                "transaction_log_id", no_exception=True
            )
            if (
                transaction_id not in (None, "")
                and transaction_id not in transaction_ids
            ):
                transaction_ids.append(transaction_id)

        transactions = []
        if transaction_ids:
            transaction_search = Search("sthpw/transaction_log")
            transaction_search.add_filters("id", transaction_ids)
            transaction_search.add_order_by("timestamp", direction="desc")
            transaction_search.set_limit(80)
            transactions = list(transaction_search.get_sobjects())
            transactions.sort(
                key=lambda value: str(
                    value.get_value("timestamp", no_exception=True) or ""
                ),
                reverse=True,
            )

        entries = []
        selected = None
        seen_revisions = set()
        for transaction in transactions:
            transaction_data, nodes = transaction_article_nodes(
                transaction, article_references
            )
            if not nodes:
                continue
            revision_id = str(
                transaction_data.get("code")
                or transaction.get_id()
                or transaction_data.get("id")
                or ""
            )
            if not revision_id or revision_id in seen_revisions:
                continue
            seen_revisions.add(revision_id)
            actions = {
                str(node.get("action") or "update").strip().casefold()
                for node in nodes
            }
            changed_fields = []
            for node in nodes:
                for column in node.findall("column"):
                    field = str(column.get("name") or "").strip()
                    if field in visible_history_fields and field not in changed_fields:
                        changed_fields.append(field)
            document_state = historical_document(state)
            timestamp = str(
                transaction_data.get("timestamp")
                or state.get("last_update")
                or state.get("timestamp")
                or ""
            )
            actor = str(
                transaction_data.get("login")
                or state.get("updated_by")
                or ""
            )
            entry = {
                "revisionId": revision_id,
                "timestamp": timestamp,
                "actor": actor,
                "title": document_state["title"],
                "description": document_state["description"],
                "changedFields": changed_fields,
                "action": "create" if actions & {"create", "insert"} else "update",
                "current": not entries,
            }
            entries.append(entry)
            if revision_id == selected_revision:
                selected = dict(entry)
                selected.update({
                    "document": document_state,
                    "articleMetadata": {
                        "author": str(
                            state.get("login")
                            or state.get("updated_by")
                            or actor
                        ),
                        "createdAt": str(state.get("timestamp") or ""),
                        "updatedBy": actor,
                        "updatedAt": timestamp,
                    },
                })

            created_here = False
            for node in reversed(nodes):
                action_name = str(
                    node.get("action") or ""
                ).strip().casefold()
                created_here = created_here or action_name in {"create", "insert"}
                for column in node.findall("column"):
                    field = str(column.get("name") or "").strip()
                    if field in state:
                        state[field] = str(column.get("from") or "")
            if created_here:
                break

        if not entries:
            document_state = historical_document(state)
            synthetic_id = "current:" + revision(article)
            entry = {
                "revisionId": synthetic_id,
                "timestamp": str(
                    state.get("last_update") or state.get("timestamp") or ""
                ),
                "actor": str(state.get("updated_by") or state.get("login") or ""),
                "title": document_state["title"],
                "description": document_state["description"],
                "changedFields": [],
                "action": "current",
                "current": True,
            }
            entries.append(entry)
            if synthetic_id == selected_revision:
                selected = dict(entry)
                selected.update({
                    "document": document_state,
                    "articleMetadata": article_metadata(article),
                })
        return entries, selected

    def catalog(search_query=""):
        source = Search(search_type)
        rows = []
        folded_query = str(search_query or "").strip().casefold()
        identity_fields = (
            ("id", "code") if "code" in columns else ("id",)
        )
        for column in identity_fields + catalog_fields + (
            ("content_text",) if folded_query else ()
        ):
            source.add_column(column)
        if "s_status" in columns:
            source.add_column("s_status")
        if "login" in columns:
            source.add_column("login")
        if folded_query:
            wildcard = "%" + str(search_query or "").strip() + "%"
            source.add_op("begin")
            source.add_filter("name", wildcard, op="like")
            source.add_filter("description", wildcard, op="like")
            source.add_filter("content_text", wildcard, op="like")
            source.add_op("or")
        items = list(source.get_sobjects())
        canonical_identities = {}
        for item in items:
            canonical = item_identity(item)
            for reference in item_references(item):
                canonical_identities[reference] = canonical
        for item in items:
            if not draft_is_visible(item):
                continue
            info = {
                field: item.get_value(field, no_exception=True) or ""
                for field in catalog_fields
            }
            title = str(info["name"] or item_identity(item))
            description = str(info["description"] or "")
            content_text = str(
                item.get_value("content_text", no_exception=True) or ""
            ) if folded_query else ""
            haystack = "\n".join((title, description, content_text)).casefold()
            match_at = haystack.find(folded_query) if folded_query else -1
            excerpt_source = description or content_text
            if folded_query and match_at >= 0 and not description:
                plain_at = content_text.casefold().find(folded_query)
                start = max(0, plain_at - 70)
                excerpt_source = content_text[start:start + 220]
            rows.append({
                "identity": item_identity(item),
                "title": title,
                "description": description,
                "excerpt": excerpt_source[:240],
                "kind": str(info["kind"] or "article"),
                "parentCode": str(info["parent_code"] or ""),
                "sortOrder": int(info["sort_order"] or 0),
                "updatedBy": str(info["updated_by"] or ""),
                "timestamp": str(info["timestamp"] or ""),
                "searchKey": search_key(item),
                "draft": item_is_draft(item),
            })
        for row in rows:
            parent = row["parentCode"]
            row["parentCode"] = canonical_identities.get(parent, parent)
        rows.sort(key=lambda row: (
            row["parentCode"], row["sortOrder"],
            row["kind"] != "section", row["title"].casefold(),
        ))
        return rows

    def item_linked_skeys(item):
        raw_value = str(
            item.get_value("linked_skeys", no_exception=True) or ""
        ).strip()
        if not raw_value:
            return []
        try:
            values = json.loads(raw_value)
        except (TypeError, ValueError):
            return []
        if not isinstance(values, list):
            return []
        result = []
        for raw_search_key in values:
            search_key = str(raw_search_key or "").strip()
            if search_key and not search_key.startswith("skey://"):
                search_key = "skey://" + search_key
            if search_key and search_key not in result:
                result.append(search_key)
        return result

    def link_index():
        source = Search(search_type)
        source.add_column("id")
        if "code" in columns:
            source.add_column("code")
        source.add_column("name")
        source.add_column("kind")
        source.add_column("linked_skeys")
        source.add_column("sort_order")
        if "s_status" in columns:
            source.add_column("s_status")
        records = [
            {
                "identity": item_identity(item),
                "title": str(
                    item.get_value("name", no_exception=True) or ""
                ),
                "linkedSearchKeys": item_linked_skeys(item),
                "sortOrder": int(
                    item.get_value("sort_order", no_exception=True) or 0
                ),
            }
            for item in source.get_sobjects()
            if str(item.get_value("kind", no_exception=True) or "article")
            == "article"
            and not item_is_draft(item)
        ]
        records.sort(key=lambda record: (
            record["sortOrder"], record["title"].casefold(),
            record["identity"],
        ))
        return records

    def section_contents(rows, section_identity):
        by_parent = {}
        for row in rows:
            by_parent.setdefault(str(row.get("parentCode") or ""), []).append(
                row
            )
        for children in by_parent.values():
            children.sort(key=lambda row: (
                int(row.get("sortOrder") or 0),
                str(row.get("kind") or "article") != "section",
                str(row.get("title") or "").casefold(),
            ))
        outline = []
        visited = set()

        def append_children(parent_identity, level):
            for child in by_parent.get(parent_identity, []):
                child_identity = str(child.get("identity") or "")
                if not child_identity or child_identity in visited:
                    continue
                visited.add(child_identity)
                outline.append({
                    "identity": child_identity,
                    "title": str(child.get("title") or child_identity),
                    "description": str(child.get("description") or ""),
                    "kind": str(child.get("kind") or "article"),
                    "level": level,
                })
                append_children(child_identity, level + 1)

        append_children(str(section_identity or ""), 1)
        return outline

    def article_attachment_objects(article, *, latest_only=True):
        snapshots = list(Snapshot.get_by_sobjects([article]) or [])
        known_codes = {
            str(snapshot.get_code() or "") for snapshot in snapshots
        }
        for snapshot in article.get_connections(context="attachment") or []:
            code = str(snapshot.get_code() or "")
            if snapshot is not None and code not in known_codes:
                snapshots.append(snapshot)
                known_codes.add(code)
        snapshots = [
            snapshot for snapshot in snapshots
            if str(snapshot.get_value(
                "context", no_exception=True
            ) or "").startswith("attachment/knowledge")
        ]
        if latest_only:
            snapshots = [
                snapshot for snapshot in snapshots
                if (
                    snapshot.get_version() in (-1, 0, "-1", "0")
                    or snapshot.is_latest()
                )
            ]
        return snapshots

    if action in {
        "attachments", "delete_attachment", "organize",
        "reserve", "save", "save_draft",
    } and not can_edit:
        raise PermissionError("Supervisor access is required to edit articles")

    item = item_for(identity)
    if item is not None and not draft_is_visible(item):
        item = None
    if identity and item is None:
        return json.dumps({
            "initialized": True,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "catalog": catalog(query),
            "links": link_index(),
            "query": str(query or ""),
            "entryMissing": True,
            "missingIdentity": str(identity),
            "requestedAction": action,
        })
    if item is not None:
        identity = item_identity(item)

    if action in {"history", "history_revision"}:
        if item is None:
            raise ValueError("Select a Knowledge Base article")
        if str(item.get_value("kind") or "article") != "article":
            raise ValueError("Change history is available for articles")
        requested_revision = (
            str(history_revision or "")
            if action == "history_revision" else ""
        )
        history_entries, selected_history = article_history(
            item, requested_revision
        )
        if action == "history_revision" and selected_history is None:
            raise ValueError(
                "This article revision is no longer available in the "
                "TACTIC transaction log"
            )
        return json.dumps({
            "initialized": True,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "identity": identity,
            "history": history_entries if action == "history" else [],
            "historyRevision": selected_history,
        })

    if action == "organize":
        if not isinstance(organization, list):
            raise ValueError("Knowledge Base organization must be a list")
        if len(organization) > 4096:
            raise ValueError("Too many Knowledge Base entries to organize")
        rows = catalog("")
        rows_by_identity = {
            str(row.get("identity") or ""): row for row in rows
            if str(row.get("identity") or "")
        }
        parents = {
            row_identity: str(row.get("parentCode") or "")
            for row_identity, row in rows_by_identity.items()
        }
        changes = []
        seen = set()
        for raw_entry in organization:
            if not isinstance(raw_entry, dict):
                raise ValueError("Invalid Knowledge Base organization entry")
            entry_identity = str(raw_entry.get("identity") or "").strip()
            if not entry_identity or entry_identity in seen:
                raise ValueError("Knowledge Base entries must be unique")
            seen.add(entry_identity)
            entry_item = item_for(entry_identity)
            if entry_item is None or not draft_is_visible(entry_item):
                raise ValueError("A Knowledge Base entry no longer exists")
            canonical_identity = item_identity(entry_item)
            raw_parent = str(raw_entry.get("parentCode") or "").strip()
            parent_item = item_for(raw_parent) if raw_parent else None
            if parent_item is not None and not draft_is_visible(parent_item):
                parent_item = None
            if raw_parent and parent_item is None:
                raise ValueError("Choose an existing section as the parent")
            if parent_item is not None and str(
                parent_item.get_value("kind", no_exception=True) or "article"
            ) != "section":
                raise ValueError("Only a section can contain Knowledge Base entries")
            parent_identity = (
                item_identity(parent_item) if parent_item is not None else ""
            )
            try:
                sort_order = int(raw_entry.get("sortOrder") or 0)
            except (TypeError, ValueError):
                raise ValueError("Article order must be an integer")
            parents[canonical_identity] = parent_identity
            changes.append((entry_item, canonical_identity, parent_identity, sort_order))

        for entry_identity in parents:
            current = entry_identity
            visited = set()
            while current:
                if current in visited:
                    raise ValueError("A section cannot be moved inside its child")
                visited.add(current)
                current = parents.get(current, "")

        for entry_item, _entry_identity, parent_identity, sort_order in changes:
            entry_item.set_value("parent_code", parent_identity)
            entry_item.set_value("sort_order", sort_order)
            entry_item.commit()
        return json.dumps({
            "initialized": True,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "catalog": catalog(query),
            "links": link_index(),
            "query": str(query or ""),
            "organizationSaved": True,
        })

    if action in {"reserve", "save", "save_draft"}:
        values = validate_document(document)
        if item is not None and revision(item) != expected_revision:
            raise ValueError(
                "This article changed on the server. Reload it before saving."
            )
        parent = item_for(values["parentCode"])
        if parent is not None and not draft_is_visible(parent):
            parent = None
        if values["parentCode"] and (
            parent is None
            or str(parent.get_value("kind") or "article") != "section"
        ):
            raise ValueError("Choose an existing section as the parent")
        parent_identity = item_identity(parent) if parent is not None else ""
        if item is not None and parent_identity == item_identity(item):
            raise ValueError("An entry cannot contain itself")
        if item is not None and values["kind"] == "section":
            ancestor = parent
            visited = set()
            current_identity = item_identity(item)
            while ancestor is not None:
                ancestor_code = item_identity(ancestor)
                if ancestor_code == current_identity:
                    raise ValueError("A section cannot be moved inside its child")
                if not ancestor_code or ancestor_code in visited:
                    break
                visited.add(ancestor_code)
                ancestor = item_for(str(
                    ancestor.get_value("parent_code") or ""
                ))
        creating_item = item is None
        if creating_item:
            item = SearchType.create(search_type)
        item.set_value("name", values["title"])
        item.set_value("description", values["description"])
        item.set_value("kind", values["kind"])
        item.set_value("parent_code", parent_identity)
        item.set_value("content", values["contentMarkdown"])
        item.set_value("content_text", values["contentText"])
        item.set_value(
            "linked_skeys",
            json.dumps(values["linkedSearchKeys"], separators=(",", ":")),
        )
        item.set_value("sort_order", values["sortOrder"])
        item.set_value("updated_by", current_login)
        if creating_item and "login" in columns:
            item.set_value("login", current_login)
        if "s_status" in columns:
            item.set_value(
                "s_status",
                "draft" if action in {"reserve", "save_draft"} else "",
            )
        elif action in {"reserve", "save_draft"}:
            raise ValueError(
                "This Knowledge Base table cannot store drafts. "
                "Add the standard s_status column before uploading files."
            )
        item.commit()
        identity = item_identity(item)
        committed_item = item_for(identity)
        if committed_item is not None:
            item = committed_item

    def attachment_snapshots(article):
        snapshots = article_attachment_objects(article)
        files_by_snapshot = (
            Snapshot.get_files_dict_by_snapshots(snapshots)
            if snapshots else {}
        )
        result = []
        for snapshot in snapshots:
            snapshot_data = snapshot.get_data()
            snapshot_data["__search_key__"] = SearchKey.get_by_sobject(
                snapshot, use_id=False
            )
            snapshot_data["__files__"] = [
                file_object.get_data()
                for file_object in (
                    files_by_snapshot.get(snapshot.get_code()) or []
                )
            ]
            result.append(snapshot_data)
        result.sort(
            key=lambda record: str(record.get("timestamp") or ""),
            reverse=True,
        )
        return result

    if action == "delete_attachment":
        if item is None:
            raise ValueError("Select a Knowledge Base article")
        normalized_key = str(attachment_key or "").strip()
        if normalized_key.startswith("skey://"):
            normalized_key = normalized_key[7:]
        snapshot = SearchKey.get_by_search_key(normalized_key)
        if snapshot is None or snapshot.get_base_search_type() != "sthpw/snapshot":
            raise ValueError("Choose an existing article attachment")
        allowed_keys = set()
        for record in attachment_snapshots(item):
            value = str(record.get("__search_key__") or "")
            allowed_keys.add(value[7:] if value.startswith("skey://") else value)
        canonical_key = str(SearchKey.get_by_sobject(
            snapshot, use_id=False
        ) or "")
        if canonical_key.startswith("skey://"):
            canonical_key = canonical_key[7:]
        if canonical_key not in allowed_keys:
            raise ValueError("The attachment does not belong to this article")
        snapshot.retire()

    links = link_index()
    if action == "link_index":
        return json.dumps({
            "initialized": True,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "links": links,
            "query": str(query or ""),
        })

    rows = catalog(query)
    if action == "list":
        return json.dumps({
            "initialized": True,
            "canEdit": can_edit,
            "canInitialize": administrator,
            "messagesInitialized": messages_initialized,
            "catalog": rows,
            "links": links,
            "query": str(query or ""),
        })

    if item is None:
        raise ValueError("Select a Knowledge Base entry")
    raw_parent = str(item.get_value("parent_code") or "")
    parent = item_for(raw_parent)
    result_document = {
        "title": str(item.get_value("name") or ""),
        "description": str(item.get_value("description") or ""),
        "kind": str(item.get_value("kind") or "article"),
        "parentCode": item_identity(parent) if parent is not None else raw_parent,
        "contentMarkdown": str(item.get_value("content") or ""),
        "contentText": str(item.get_value("content_text") or ""),
        "linkedSearchKeys": item_linked_skeys(item),
        "sortOrder": int(item.get_value("sort_order") or 0),
        "draft": item_is_draft(item),
    }
    outline = []
    if result_document["kind"] == "section":
        all_rows = rows if not str(query or "").strip() else catalog("")
        outline = section_contents(all_rows, identity)
    return json.dumps({
        "initialized": True,
        "canEdit": can_edit,
        "canInitialize": administrator,
        "messagesInitialized": messages_initialized,
        "catalog": rows,
        "identity": identity,
        "searchKey": search_key(item),
        "revision": revision(item),
        "document": result_document,
        "articleMetadata": article_metadata(item),
        "links": links,
        "sectionContents": outline,
        "attachmentSnapshots": (
            attachment_snapshots(item)
            if result_document["kind"] == "article" else []
        ),
        "query": str(query or ""),
    })
