"""Native administration transport over the installed DashboardCmd contract."""


def dashboard_editor_request(
    action: str,
    project_code: str,
    identity: str = "",
    document: dict = None,
    expected_revision: str = "",
    operation_id: str = "",
    detail_key: str = "",
    search_type: str = "",
    query: str | None = None,
    record_key: str = "",
    edit_view: str = "edit",
) -> str:
    import json
    from pyasm.command import Command
    from tactic.ui.panel.dashboard_cmd import DashboardCmd

    def call(kind, **values):
        return Command.execute_cmd(
            DashboardCmd(action=kind, project_code=project_code, **values)
        )

    if action == "source":
        return json.dumps(call("sources", search_type=search_type, query=query, record_key=record_key,edit_view=edit_view), ensure_ascii=False)

    if action == "preview":
        return json.dumps(
            call(
                "preview",
                document=document,
                expected_revision=expected_revision,
                detail_key=detail_key,
            ),
            ensure_ascii=False,
        )
    if action == "operation":
        return json.dumps(
            call("operation", operation_id=operation_id), ensure_ascii=False
        )
    if action not in ("list", "load", "save"):
        raise ValueError("Unknown page layout operation")
    if action == "save":
        call(
            "apply",
            document=document,
            expected_revision=expected_revision,
            operation_id=operation_id,
        )
        identity = document["name"]
    state = call("read", **({"name": identity, "include_preview": True} if identity else {}))
    catalog = [
        dict(identity=row["view"][10:], label=row["view"][10:])
        for row in state["dashboards"]
    ]
    result = dict(
        catalog=catalog,
        canWrite=True,
        metadata=dict(
            revision=state["revision"],
            searchTypes=state["sourceTypes"],
        ),
    )
    if identity:
        result.update(
            identity=identity,
            revision=state["revision"],
            document=state["document"],
            metadata=dict(
                result["metadata"],
                compiled=state["model"],
                sourceXml=state["xml"],
                checkedDocument=state["document"],
            ),
        )
    return json.dumps(result, ensure_ascii=False)
