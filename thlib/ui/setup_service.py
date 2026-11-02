"""Local setup operations using the client's native configuration and RPC."""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import subprocess
from urllib.parse import urlparse

from thlib.environment import env_mode, env_read_config, env_server, env_tactic
from thlib.ui.server_address import (
    is_valid_tactic_server_url,
    normalize_tactic_server_url,
)


def read_initial() -> dict:
    scope = f"{env_mode.node}/environment_config"
    presets = env_read_config(filename="presets_conf", unique_id=scope) or {}
    current = presets.get("server_presets", {}).get("current", "default")
    values = (
        env_read_config(filename=current, unique_id=scope + "/server_presets") or {}
    )
    ui = (
        env_read_config(filename="ui_settings", unique_id="ui_main", long_abs_path=True)
        or {}
    )
    directories = (
        env_read_config(
            filename="tactic_dirs_" + current,
            unique_id=scope + "/server_presets",
            sub_id="TACTIC_BASE_DIRS",
        )
        or {}
    )
    active = [
        (alias, directories[key])
        for alias, key in (
            ("base", "asset_base_dir"),
            ("client", "win32_client_repo_dir"),
            ("local", "win32_local_repo_dir"),
            ("sandbox", "win32_sandbox_dir"),
        )
        if len(directories.get(key, [])) >= 5 and directories[key][4]
    ]
    from thlib.global_functions import get_value_from_config

    checkin = (
        env_read_config(filename="checkin", unique_id="ui_conf", long_abs_path=True)
        or {}
    )
    try:
        index = int(get_value_from_config(checkin, "repositoryComboBox") or 0)
    except (TypeError, ValueError):
        index = 0
    alias, repository = (
        (active[index] if 0 <= index < len(active) else active[0])
        if active
        else ("base", [""])
    )
    return {
        "server": values.get("server") or "",
        "login": values.get("user") or "",
        "project": ui.get("server/currentProject", ""),
        "repository": repository[0],
        "repositoryAlias": alias,
    }


def shelf_buttons(
    configuration: dict, scripts: list[dict], denied: list[str]
) -> list[dict]:
    """Use authenticated policy and metadata; never download or rewrite bodies."""
    languages = {"local_python", "dcc_python", "python", "server_js", "expression"}
    available = {
        "/".join(
            (str(row.get("folder") or "").strip("/"), str(row.get("title") or ""))
        ).strip("/")
        for row in scripts
        if row.get("language", "local_python") in languages
    }
    return [
        dict(button)
        for button in configuration.get("buttons", [])
        if button.get("script") in available
        and "*" not in denied
        and button["script"] not in denied
    ]


class SetupSession:
    def __init__(self):
        self.server = None
        self.url = self.login = self.project = ""
        self.shelves = []

    def authenticate(self, address: str, login: str, password: str) -> list[dict]:
        from thlib.side.client.tactic_client_lib.tactic_server_stub import (
            TacticServerStub,
        )
        from thlib.proxy import UrllibTransport

        self.server = None
        self.shelves = []
        self.url = normalize_tactic_server_url(address)
        self.login = login.strip()
        parsed = urlparse(self.url)
        if (
            not is_valid_tactic_server_url(self.url)
            or parsed.username
            or parsed.password
        ):
            raise ValueError(
                "Enter a server root URL, for example https://tactic.example.com"
            )
        if not self.login or not password:
            raise ValueError("Enter your login and password")
        server = TacticServerStub(setup=False, protocol="xmlrpc", login=self.login)
        env_server.set_timeout(20)
        server.set_transport(UrllibTransport())
        server.set_server(self.url)
        if parsed.scheme == "https":
            from xmlrpc.client import ServerProxy

            # The legacy stub's HTTPS branch ignores its supplied transport.
            server.server = ServerProxy(
                self.url + "/tactic/default/Api/",
                allow_none=True,
                transport=server.transport,
            )
        server.set_project("sthpw")
        try:
            ticket = server.get_ticket(self.login, password)
            if not isinstance(ticket, str) or not ticket:
                raise ValueError("No authentication ticket")
            server.set_ticket(ticket)
            projects = server.query(
                "sthpw/project", columns=["code", "title", "is_template"]
            )
        except Exception:
            # A remote fault may echo submitted arguments; never display credentials.
            raise RuntimeError(
                "Sign-in failed. Check the server address and credentials."
            ) from None
        self.server = server
        return [
            {"code": row["code"], "title": row.get("title") or row["code"]}
            for row in projects
            if row.get("code") not in {"sthpw", "admin"}
            and row.get("is_template") not in (True, "true", "t", 1)
        ]

    def load_project(self, project: str) -> list[dict]:
        from thlib import tactic_classes as tc
        from thlib.script_access import query_runner_access
        from thlib.ui.script_shelf import (
            shelf_configuration_from_xml,
            SCRIPT_SHELF_SEARCH_TYPE,
        )

        if self.server is None or not project or any(c in project for c in "/\\"):
            raise ValueError("Sign in and select a project first")
        self.project = project
        self.server.set_project(project)
        policy = tc.execute_procedure_serverside(
            query_runner_access,
            {"project_code": project},
            project=project,
            server=self.server,
        )
        if policy.get("project") != project or not isinstance(
            policy.get("denied"), list
        ):
            raise ValueError("The server returned an invalid script access policy")
        scripts = self.server.query(
            "config/custom_script", columns=["folder", "title", "language"]
        )
        records = self.server.query(
            "config/widget_config",
            [("category", "script_shelf"), ("search_type", SCRIPT_SHELF_SEARCH_TYPE)],
        )
        self.shelves = []
        for row in records:
            if row.get("login") and row["login"] != self.login:
                continue
            try:
                configuration = shelf_configuration_from_xml(
                    row.get("config"), row["view"]
                )
            except (ValueError, TypeError):
                continue
            # A tab-specific personal shelf has no meaning during workstation setup.
            if row.get("login") and configuration.get("scope") != "global":
                continue
            buttons = shelf_buttons(configuration, scripts, policy["denied"])
            self.shelves.append(
                {
                    "id": str(row["code"]),
                    "title": row.get("title") or "Shared shelf",
                    "personal": bool(row.get("login")),
                    "buttons": buttons,
                }
            )
        self.shelves.sort(
            key=lambda row: (not row["personal"], row["title"].casefold())
        )
        return copy.deepcopy(self.shelves)


def create_shortcuts(desktop: Path, bundle: Path) -> None:
    """Use the Windows Shell's actual Desktop location, including redirection."""
    if os.name != "nt":
        raise OSError("Desktop shortcuts require Windows")
    targets = [
        ("TACTIC Handler", bundle / "TACTIC Handler.exe"),
        ("TACTIC Handler Setup", bundle / "TH Setup.exe"),
    ]
    if any(not target.is_file() for _, target in targets):
        raise FileNotFoundError("Keep both EXE launchers with the Handler runtime")
    # Pass paths as environment values, never interpolate them as PowerShell code.
    script = "$shell = New-Object -ComObject WScript.Shell\n"
    environment = dict(os.environ)
    for index, (name, target) in enumerate(targets):
        environment[f"TH_SETUP_LINK_{index}"] = str(desktop / (name + ".lnk"))
        environment[f"TH_SETUP_TARGET_{index}"] = str(target)
        script += (
            f"$link = $shell.CreateShortcut($env:TH_SETUP_LINK_{index})\n"
            f"$link.TargetPath = $env:TH_SETUP_TARGET_{index}\n"
            f"$link.WorkingDirectory = [IO.Path]::GetDirectoryName($env:TH_SETUP_TARGET_{index})\n"
            f"$link.IconLocation = $env:TH_SETUP_TARGET_{index} + ',0'\n$link.Save()\n"
        )
    desktop.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        env=environment,
        check=True,
        capture_output=True,
        timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def apply_setup(session: SetupSession, root: Path, values: dict, desktop: Path) -> None:
    from tactic_handler_dcc import maya_integration
    from tactic_handler_dcc.connectors import plugin_catalog
    from thlib.ui.repository_editor import _empty_base_dirs, RepositoryEditorController

    repository = Path(values["repository"]).expanduser()
    default_missing = repository == root.parent / "repo" and not repository.exists()
    if not repository.is_absolute() or (
        not repository.is_dir() and not default_missing
    ):
        raise ValueError(
            "Choose an existing repository folder accessible from this computer"
        )
    alias = values["repositoryAlias"]
    keys = {
        "base": "asset_base_dir",
        "client": "win32_client_repo_dir",
        "local": "win32_local_repo_dir",
        "sandbox": "win32_sandbox_dir",
    }
    if alias not in keys or session.server is None:
        raise ValueError("Sign in and select a repository")
    # Refresh permissions immediately before installation, rather than trusting the preview.
    shelves = session.load_project(values["project"])
    selected = next((row for row in shelves if row["id"] == values["shelf"]), None)
    if values["shelf"] and selected is None:
        raise ValueError(
            "The selected shelf is no longer available. Reload the project."
        )
    current_maya = {row["id"]: row for row in maya_integration.discover()}
    profiles = []
    for identity in values["mayaProfiles"]:
        row = current_maya.get(identity)
        if not row or not row["supported"]:
            raise ValueError("The selected Maya profile is no longer available")
        if row.get("pids"):
            raise ValueError(
                "Close the selected Maya versions before installing their shelves"
            )
        if row["status"] in {"Modified files", "Unrecognized integration"}:
            raise ValueError(
                "Existing integration files were modified; preserve or remove them manually first"
            )
        profiles.append(Path(row["profile"]))
    enabled = set(values["plugins"])
    catalog = {row["id"] for row in plugin_catalog()}
    if not enabled <= catalog or (profiles and "maya" not in enabled):
        raise ValueError("Enable the Maya plugin before selecting its versions")

    settings = Path(env_mode.get_current_path()) / "settings"
    paths = list(settings.rglob("*")) if settings.exists() else []
    for profile in profiles:
        paths.extend(
            profile / name
            for name in (
                "modules/TACTIC_Stream.mod",
                "tactic_stream_payload/scripts/userSetup.py",
                "tactic_stream_payload/scripts/tactic_stream_maya.py",
                "tactic_stream_payload/integration.json",
                "prefs/shelves/shelf_TACTIC_Stream.mel",
            )
        )
    links = [
        desktop / (name + ".lnk") for name in ("TACTIC Handler", "TACTIC Handler Setup")
    ]
    if values["shortcuts"]:
        paths.extend(links)
    if any(path.is_symlink() for path in paths):
        raise ValueError("Setup will not replace symbolic links")
    originals = {
        path: path.read_bytes() if path.exists() else None
        for path in paths
        if not path.is_dir()
    }
    created_repository = False
    try:
        if default_missing:
            repository.mkdir()
            created_repository = True
        env_server.reload()
        if (
            normalize_tactic_server_url(env_server.get_server()) != session.url
            or env_server.get_user() != session.login
        ):
            identity = (
                "setup-"
                + hashlib.sha256(
                    (session.url + "\n" + session.login).encode()
                ).hexdigest()[:12]
            )
            if identity not in env_server.get_server_presets()["presets_list"]:
                env_server.add_server_preset(identity)
            env_server.set_cur_srv_preset(identity)
            env_server.load_current_preset()
        env_server.set_server(session.url)
        env_server.set_user(session.login)
        env_server.set_ticket(session.server.login_ticket)
        env_server.set_rpc_transport("xmlrpc")
        env_server.save_defaults()
        env_server.save_server_presets_defaults()
        env_tactic.reset()
        # Preserve every other repository mapping; this changes only the chosen local alias.
        unique_id = f"{env_mode.node}/environment_config/server_presets"
        filename = "tactic_dirs_" + env_server.get_cur_srv_preset()
        env_tactic.base_dirs = (
            env_read_config(
                filename=filename, unique_id=unique_id, sub_id="TACTIC_BASE_DIRS"
            )
            or _empty_base_dirs()
        )
        value = list(env_tactic.base_dirs[keys[alias]])
        value[0], value[4] = str(repository), True
        env_tactic.base_dirs[keys[alias]] = value
        env_tactic.save_base_dirs()
        active = [
            key
            for key in (
                "asset_base_dir",
                "win32_client_repo_dir",
                "win32_local_repo_dir",
                "win32_sandbox_dir",
            )
            if env_tactic.base_dirs[key][4]
        ]
        RepositoryEditorController._set_checkin_default(active.index(keys[alias]))
        from thlib.environment import env_write_config

        env_write_config(
            {"disabled": sorted(catalog - enabled)},
            filename="ui_dcc_plugins",
            unique_id="ui_main",
            long_abs_path=True,
            scope="installation",
        )
        ui_settings = (
            env_read_config(
                filename="ui_settings", unique_id="ui_main", long_abs_path=True
            )
            or {}
        )
        ui_settings["server/currentProject"] = session.project
        env_write_config(
            ui_settings, filename="ui_settings", unique_id="ui_main", long_abs_path=True
        )
        for profile in profiles:
            maya_integration.install(
                profile,
                root,
                shelf={
                    "project": session.project,
                    "buttons": selected["buttons"] if selected else [],
                },
            )
        if values["shortcuts"]:
            create_shortcuts(desktop, root.parent)
    except Exception:
        # Roll back only files owned by this operation, while the client is locked out.
        for path in settings.rglob("*") if settings.exists() else []:
            if path.is_file() and path not in originals:
                path.unlink()
        for path, data in originals.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        env_server.reload()
        env_tactic.reset()
        if created_repository:
            try:
                repository.rmdir()
            except OSError:
                pass  # Preserve files added externally while setup was running.
        raise
