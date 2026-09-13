"""Server-backed saved revision history for TACTIC custom scripts."""


def script_history_request(
    action: str,
    project_code: str,
    search_key: str,
    revision_id: str = "",
) -> str:
    """Run inside TACTIC and reconstruct one script from its audit log."""
    import hashlib
    import json
    import xml.etree.ElementTree as ElementTree

    from pyasm.biz import Project
    from pyasm.search import Search, SearchKey

    if action not in {"history", "revision"}:
        raise ValueError("Unknown custom script history operation")
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError("Select the script project first")

    normalized_key = str(search_key or "").strip()
    if normalized_key.startswith("skey://"):
        normalized_key = normalized_key[7:]
    script = SearchKey.get_by_search_key(normalized_key)
    if script is None:
        return json.dumps({"entryMissing": True, "searchKey": search_key})
    base_type = str(script.get_base_search_type() or "").split("?", 1)[0]
    if base_type != "config/custom_script":
        raise ValueError("Choose a TACTIC custom script")

    fields = ("script", "folder", "title", "language")
    state = {
        field: script.get_value(field, no_exception=True) or ""
        for field in fields
    }
    references = {
        str(script.get_id() or ""),
        str(script.get_value("code", no_exception=True) or ""),
    }

    transaction_ids = []
    search_types = []
    get_search_type = getattr(script, "get_search_type", None)
    if callable(get_search_type):
        search_types.append(str(get_search_type() or ""))
    search_types.extend((
        "config/custom_script?project=%s" % project_code,
        "config/custom_script",
    ))
    for indexed_type in dict.fromkeys(filter(None, search_types)):
        object_logs = Search("sthpw/sobject_log")
        object_logs.add_filter("search_type", indexed_type)
        object_logs.add_filter("search_id", script.get_id())
        object_logs.add_order_by("timestamp", direction="desc")
        object_logs.set_limit(80)
        for object_log in object_logs.get_sobjects():
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
            key=lambda item: str(
                item.get_value("timestamp", no_exception=True) or ""
            ),
            reverse=True,
        )

    def transaction_nodes(transaction):
        data = transaction.get_data()
        source = ""
        getter = getattr(transaction, "get_xml_value", None)
        if getter:
            try:
                value = getter("transaction")
                serializer = getattr(value, "to_string", None)
                if serializer:
                    try:
                        source = serializer(pretty=False)
                    except TypeError:
                        source = serializer()
                    if isinstance(source, bytes):
                        source = source.decode("utf-8", errors="replace")
            except (AttributeError, TypeError, ValueError):
                source = ""
        source = str(source or data.get("transaction") or "").strip()
        if not source or "<" not in source:
            return data, []
        try:
            root = ElementTree.fromstring(source)
        except (ElementTree.ParseError, TypeError, ValueError):
            return data, []
        nodes = []
        for node in root.iter("sobject"):
            node_type = str(node.get("search_type") or "").split("?", 1)[0]
            identity = str(
                node.get("search_code") or node.get("search_id") or ""
            )
            if node_type == base_type and identity in references:
                nodes.append(node)
        return data, nodes

    entries = []
    selected = None
    seen = set()
    for transaction in transactions:
        transaction_data, nodes = transaction_nodes(transaction)
        if not nodes:
            continue
        current_revision = str(
            transaction_data.get("code")
            or transaction.get_id()
            or transaction_data.get("id")
            or ""
        )
        if not current_revision or current_revision in seen:
            continue
        seen.add(current_revision)
        changed_fields = []
        actions = set()
        for node in nodes:
            actions.add(str(node.get("action") or "update").casefold())
            for column in node.findall("column"):
                field = str(column.get("name") or "")
                if field in fields and field not in changed_fields:
                    changed_fields.append(field)
        entry = {
            "revisionId": current_revision,
            "timestamp": str(transaction_data.get("timestamp") or ""),
            "actor": str(transaction_data.get("login") or ""),
            "changedFields": changed_fields,
            "action": (
                "create" if actions & {"create", "insert"} else "update"
            ),
            "current": not entries,
        }
        entries.append(entry)
        if current_revision == revision_id:
            selected = dict(entry)
            selected.update(state)

        created_here = False
        for node in reversed(nodes):
            action_name = str(node.get("action") or "").casefold()
            created_here = created_here or action_name in {"create", "insert"}
            for column in node.findall("column"):
                field = str(column.get("name") or "")
                if field in state:
                    state[field] = str(column.get("from") or "")
        if created_here:
            break

    if not entries:
        fingerprint = hashlib.sha256(
            json.dumps(state, sort_keys=True).encode("utf-8")
        ).hexdigest()
        entry = {
            "revisionId": "current:" + fingerprint,
            "timestamp": "",
            "actor": "",
            "changedFields": [],
            "action": "current",
            "current": True,
        }
        entries.append(entry)
        if entry["revisionId"] == revision_id:
            selected = dict(entry)
            selected.update(state)

    if action == "revision" and selected is None:
        raise ValueError(
            "This script revision is no longer available in the TACTIC "
            "transaction log"
        )
    return json.dumps({
        "searchKey": search_key,
        "history": entries if action == "history" else [],
        "revision": selected,
    })
