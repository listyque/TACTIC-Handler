from __future__ import annotations


def operation_availability(operation: str) -> tuple[bool, str]:
    from thlib.environment import env_mode

    mode = env_mode.get_mode()
    if operation == "open" and mode == "standalone":
        return True, ""
    if mode != "maya":
        return False, f"{operation.title()} is available only in Maya"
    return True, ""


def execute_file_operation(operation: str, file_object) -> None:
    available, reason = operation_availability(operation)
    if not available:
        raise RuntimeError(reason)
    from thlib.environment import env_mode

    if env_mode.get_mode() == "maya":
        import thlib.maya_functions as maya_functions

        callbacks = {
            "open": maya_functions.open_scene,
            "import": maya_functions.import_scene,
            "reference": maya_functions.reference_scene,
        }
        callback = callbacks.get(operation)
        if callback is None:
            raise ValueError(f"Unsupported Maya operation: {operation}")
        callback(file_object)
        return
    if operation == "open":
        file_object.open_file()
        return
    raise RuntimeError(f"{operation.title()} is unavailable")
