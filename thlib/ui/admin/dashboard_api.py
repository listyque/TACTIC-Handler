"""Native administration transport over the installed DashboardCmd contract."""


def dashboard_editor_request(
    action: str,
    project_code: str,
    identity: str = "",
    document: dict = None,
    expected_revision: str = "",
    operation_id: str = "",
    detail_key: str = "",
) -> str:
    import json
    from pyasm.biz import Project
    from pyasm.command import Command
    from tactic.ui.panel.dashboard_cmd import DashboardCmd

    def call(kind, **values):
        return Command.execute_cmd(
            DashboardCmd(action=kind, project_code=project_code, **values)
        )

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
    state = call("read", **({"name": identity} if identity else {}))
    catalog = [
        dict(identity=row["view"][10:], label=row["view"][10:])
        for row in state["dashboards"]
    ]
    result = dict(
        catalog=catalog,
        canWrite=True,
        metadata=dict(
            revision=state["revision"],
            searchTypes=[
                dict(
                    value=row.get_code(), label=row.get_value("title") or row.get_code()
                )
                for row in Project.get().get_search_types()
            ],
        ),
    )
    if identity:
        compiled = call(
            "preview", document=state["document"], expected_revision=state["revision"]
        )
        result.update(
            identity=identity,
            revision=state["revision"],
            document=compiled["document"],
            metadata=dict(
                result["metadata"],
                compiled=compiled["model"],
                checkedDocument=compiled["document"],
            ),
        )
    return json.dumps(result, ensure_ascii=False)
