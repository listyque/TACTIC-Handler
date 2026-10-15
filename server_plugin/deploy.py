"""Install the bundled query package through TACTIC's script and plugin APIs."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from .build_plugin import MODULE_NAME, build


def _install_uploaded_plugin(expected_sha256):
    """Run on TACTIC once, after the client uploads the fixed package."""
    import hashlib
    import importlib
    import os
    from zipfile import ZipFile

    from pyasm.common import Environment
    from tactic.command import PluginInstaller

    if not Environment.get_security().is_admin():
        raise PermissionError("TACTIC administrator access is required to install the query plugin")

    module_name = "tactic_handler_queries"
    archive_name = module_name + ".zip"
    archive_path = os.path.join(Environment.get_upload_dir(), archive_name)
    with open(archive_path, "rb") as uploaded:
        archive_bytes = uploaded.read()
    if hashlib.sha256(archive_bytes).hexdigest() != expected_sha256:
        raise ValueError("Uploaded query plugin archive failed integrity check")

    expected = {
        f"{module_name}/__init__.py",
        f"{module_name}/api.py",
        f"{module_name}/command.py",
        f"{module_name}/manifest.xml",
    }
    with ZipFile(archive_path) as archive:
        members = archive.infolist()
        if (
            len(members) != len(expected)
            or {member.filename for member in members} != expected
            or any(member.is_dir() for member in members)
            or sum(member.file_size for member in members) > 2 * 1024 * 1024
        ):
            raise ValueError("Unexpected query plugin archive contents")
        plugin_dir = os.path.join(Environment.get_plugin_dir(), module_name)
        def matches(name):
            path = os.path.join(plugin_dir, name.split("/", 1)[1])
            try:
                with open(path, "rb") as installed:
                    return installed.read() == archive.read(name)
            except FileNotFoundError:
                return False

        unchanged = all(matches(name) for name in expected)

    if not unchanged:
        PluginInstaller(
            upload_file_name=archive_name, register=True, verbose=False
        ).execute()
    invalidate = getattr(importlib, "invalidate_caches", None)
    if invalidate:
        invalidate()
    return "unchanged" if unchanged else "installed"


def deploy(server):
    """Upload the exact client package, then install it with admin checks."""
    from thlib import tactic_classes as tc

    with TemporaryDirectory(prefix="tactic-handler-query-") as directory:
        archive = build(Path(directory) / (MODULE_NAME + ".zip"))
        digest = sha256(archive.read_bytes()).hexdigest()
        server.upload_file(str(archive))
        return tc.execute_procedure_serverside(
            _install_uploaded_plugin,
            {"expected_sha256": digest},
            server=server,
            return_dict=False,
        )
