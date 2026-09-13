from __future__ import annotations


def relation_job_metadata(definition: dict, child_stype) -> dict:
    """Project schema relation data needed to create a related child."""
    definition = dict(definition or {})
    relationship = str(definition.get("relationship") or "")
    instance_type = str(definition.get("instance_type") or "")
    instance_path = definition.get("path")
    if relationship == "instance" and instance_type and not instance_path:
        try:
            configured = child_stype.get_schema().get_parent_instance(
                instance_type, child_stype.get_code(),
            )
        except (AttributeError, KeyError, TypeError):
            configured = None
        if isinstance(configured, dict):
            instance_path = configured.get("path")
    return {
        "relationship": relationship,
        "instanceType": instance_type,
        "instancePath": instance_path,
    }


def _snapshot_parent_key(
    server, command_result, search_type: str, project_code: str,
) -> str:
    payload = dict(command_result or {})
    info = payload.get("info")
    if isinstance(info, dict):
        payload = info
    snapshots = payload.get("snapshots") or []
    if not snapshots and payload.get("snapshot"):
        snapshots = [payload["snapshot"]]
    if not snapshots:
        raise RuntimeError("Ingest did not return the created snapshot")
    snapshot = snapshots[-1]
    if isinstance(snapshot, str):
        snapshot = server.get_by_search_key(snapshot) or {}
    if not isinstance(snapshot, dict):
        raise RuntimeError("Ingest returned invalid snapshot data")
    parent_type = str(snapshot.get("search_type") or "").split("?", 1)[0]
    parent_code = str(snapshot.get("search_code") or "")
    if parent_type and parent_type != search_type:
        raise RuntimeError(
            "Ingest snapshot belongs to an unexpected Search Type"
        )
    if not parent_code:
        raise RuntimeError("Ingest snapshot has no parent Search Object")
    return server.build_search_key(
        search_type, parent_code, project_code=project_code,
    )


def execute_ingest_with_relation(
    server, arguments: dict, job: dict, *, update_existing: bool,
) -> dict:
    """Execute a new child ingest and its relation in one transaction."""
    relation = dict(job.get("relation") or {})
    relationship = str(relation.get("relationship") or "")
    if update_existing or not relationship:
        return server.execute_cmd(
            "tactic.ui.tools.IngestUploadCmd", arguments
        )

    project_code = str(job["projectCode"])
    transaction_started = False
    try:
        server.start(
            "Ingest related Search Object",
            "Create a Search Object, publish its file, and link its parent",
        )
        transaction_started = True
        command_result = server.execute_cmd(
            "tactic.ui.tools.IngestUploadCmd", arguments
        )
        child_key = _snapshot_parent_key(
            server, command_result, str(job["searchType"]), project_code,
        )

        from thlib import tactic_classes as tc
        from thlib import tactic_query as tq

        tc.execute_procedure_serverside(
            tq.link_ingested_sobject,
            {
                "project_code": project_code,
                "child_key": child_key,
                "parent_key": str(job["parentKey"]),
                "relationship": relationship,
                "instance_type": str(relation.get("instanceType") or ""),
                "instance_path": relation.get("instancePath"),
            },
            project=project_code,
            server=server,
        )
        server.finish("Ingested and linked child Search Object")
        return command_result
    except Exception as error:
        if transaction_started:
            try:
                server.abort()
            except Exception as rollback_error:
                raise RuntimeError(
                    "Ingest failed and its transaction could not be rolled "
                    "back: %s" % rollback_error
                ) from error
        raise
