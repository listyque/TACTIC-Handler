"""Per-user Windows Maya discovery and reversible, offline integration files."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


MODULE = "TACTIC_Stream"
SHELF_COMMAND = "import tactic_stream_maya; tactic_stream_maya.connect(show=True)"


def maya_app_directory() -> Path:
    override = os.environ.get("MAYA_APP_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name != "nt":
        raise OSError("Automatic Maya discovery currently supports Windows only")
    import ctypes

    documents = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, documents)
    if result:
        raise OSError("Unable to locate the Windows Documents folder")
    return Path(documents.value) / "maya"


def running_maya() -> list[dict]:
    if os.name != "nt":
        return []
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='maya.exe'\" "
         "-ErrorAction Stop | Select-Object ProcessId,ExecutablePath | "
         "ConvertTo-Json -Compress"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=8, check=True, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    records = json.loads(result.stdout) if result.stdout.strip() else []
    return [records] if isinstance(records, dict) else records


def installed_maya() -> list[dict]:
    paths = {}
    for key in ("ProgramFiles", "ProgramW6432"):
        directory = os.environ.get(key)
        if directory:
            for path in (Path(directory) / "Autodesk").glob("Maya*/bin/maya.exe"):
                match = re.fullmatch(r"Maya(20\d{2})", path.parents[1].name, re.IGNORECASE)
                if match:
                    paths[path.resolve()] = match[1]
    if os.name == "nt":
        import winreg

        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    r"SOFTWARE\Autodesk\Maya", 0,
                                    winreg.KEY_READ | view) as key:
                    versions = [winreg.EnumKey(key, i)
                                for i in range(winreg.QueryInfoKey(key)[0])]
                for version in versions:
                    try:
                        with winreg.OpenKey(
                            winreg.HKEY_LOCAL_MACHINE,
                            rf"SOFTWARE\Autodesk\Maya\{version}\Setup\InstallPath",
                            0, winreg.KEY_READ | view,
                        ) as key:
                            location = winreg.QueryValueEx(key, "MAYA_INSTALL_LOCATION")[0]
                            path = (Path(location) / "bin" / "maya.exe").resolve()
                            if re.fullmatch(r"20\d{2}", version):
                                paths[path] = version
                    except FileNotFoundError:
                        continue
            except FileNotFoundError:
                continue
    return [{"executable": str(path), "version": version}
            for path, version in sorted(paths.items(), key=lambda item: str(item[0]))
            if path.is_file()]


def _paths(profile: Path) -> tuple[Path, Path]:
    return profile / "tactic_stream_payload", profile / "modules" / f"{MODULE}.mod"


def _receipt(profile: Path) -> dict:
    directory, _module = _paths(profile)
    path = directory / "integration.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("format") != 1 or not isinstance(value.get("files"), dict):
        raise ValueError("Invalid Maya integration receipt")
    expected = {
        f"modules/{MODULE}.mod",
        "tactic_stream_payload/scripts/userSetup.py",
        "tactic_stream_payload/scripts/tactic_stream_maya.py",
        f"prefs/shelves/shelf_{MODULE}.mel",
    }
    if set(value["files"]) != expected:
        raise ValueError("Invalid Maya integration file inventory")
    _validate_paths(profile, list(value["files"]) + ["tactic_stream_payload/integration.json"])
    return value


def _validate_paths(profile: Path, names) -> None:
    for name in names:
        path = profile / name
        if not path.resolve().is_relative_to(profile):
            raise ValueError("Integration path is redirected outside the Maya profile")
        for part in (path, *path.parents):
            if part == profile:
                break
            if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
                raise ValueError("Integration paths must not contain links")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unchanged(profile: Path, relative: str, digest: str) -> bool:
    path = profile / relative
    if not path.exists():
        return True
    if path.is_symlink() or not path.is_file():
        return False
    data = path.read_bytes()
    if _digest(data) == digest:
        return True
    # Maya serializes shelf appearance on exit; ownership is the single fixed button.
    if relative == f"prefs/shelves/shelf_{MODULE}.mel":
        text = data.decode("utf-8", errors="replace")
        token = r'(?:-[A-Za-z]\w*|[+-]?(?:\d+(?:\.\d*)?|\.\d+)|"(?:[^"\\]|\\.)*")'
        native_shelf = (
            rf'\s*global proc shelf_{MODULE}\s*\(\s*\)\s*\{{\s*'
            rf'(?:global string \$gBuffStr\d*;\s*)*shelfButton\s+{token}(?:\s+{token})*\s*;\s*\}}\s*'
        )
        visual_flags = set((
            "align annotation backgroundColor command commandRepeatable docTag enable "
            "enableBackground enableCommandRepeat flat flexibleWidthType flexibleWidthValue "
            "flipX flipY height highlightColor image image1 image2 image3 imageOverlayLabel "
            "label labelOffset manage marginHeight marginWidth overlayLabelBackColor "
            "overlayLabelColor preventOverride rotation sourceType style useAlpha visible width"
        ).split())
        flags = {match[1:] for match in re.findall(token, text) if re.fullmatch(r'-[A-Za-z]\w*', match)}
        commands = re.findall(r'-command\s+("(?:[^"\\]|\\.)*")', text)
        return (
            re.fullmatch(native_shelf, text) is not None
            and flags <= visual_flags
            and commands == [json.dumps(SHELF_COMMAND)]
            and '-docTag "tactic_stream/integration"' in text
            and '-sourceType "python"' in text
            and not re.search(r"-(?:doubleClickCommand|dragCallback|dropCallback)\b", text)
        )
    return False


def integration_state(profile: Path) -> dict:
    directory, module = _paths(profile)
    markers = (module, directory / "integration.json", directory / "scripts/userSetup.py",
               directory / "scripts/tactic_stream_maya.py")
    if not any(path.exists() for path in markers):
        return {"status": "Not installed", "handlerRoot": "", "managed": False}
    try:
        receipt = _receipt(profile)
        modified = [name for name, digest in receipt["files"].items()
                    if not _unchanged(profile, name, digest)]
        missing = [name for name in receipt["files"] if not (profile / name).is_file()]
        return {
            "status": "Modified files" if modified else "Incomplete" if missing else "Installed",
            "handlerRoot": str(receipt.get("handler_root") or ""),
            "managed": True, "modified": modified,
        }
    except (OSError, ValueError, TypeError):
        return {"status": "Unrecognized integration", "handlerRoot": "", "managed": False}


def discover(*, app_directory=None, executables=None, processes=None) -> list[dict]:
    directory = Path(app_directory) if app_directory is not None else maya_app_directory()
    executables = installed_maya() if executables is None else executables
    processes = running_maya() if processes is None else processes
    versions = {}
    executable_versions = {}
    for executable in executables:
        if isinstance(executable, dict):
            version = str(executable["version"])
            executable = str(executable["executable"])
        else:
            match = re.search(r"Maya(20\d{2})", str(executable), re.IGNORECASE)
            version = match[1] if match else ""
        if re.fullmatch(r"20\d{2}", version):
            executable_versions[os.path.normcase(str(executable))] = version
            versions.setdefault(version, {"executable": str(executable), "pids": []})
    for process in processes:
        executable = str(process.get("ExecutablePath") or "")
        match = re.search(r"Maya(20\d{2})", executable, re.IGNORECASE)
        version = executable_versions.get(os.path.normcase(executable)) or (match[1] if match else "")
        if version:
            row = versions.setdefault(version, {"executable": executable, "pids": []})
            row["pids"].append(int(process["ProcessId"]))
    if directory.is_dir():
        for profile in directory.iterdir():
            if profile.is_dir() and re.fullmatch(r"20\d{2}", profile.name):
                versions.setdefault(profile.name, {"executable": "", "pids": []})
    rows = []
    for version, values in sorted(versions.items(), reverse=True):
        profile = directory / version
        rows.append({
            "id": str(profile.resolve()), "version": version,
            "profile": str(profile.resolve()), "supported": int(version) >= 2022,
            **values, **integration_state(profile),
        })
    return rows


def _clear_bootstrap_bytecode(profile: Path) -> None:
    cache = _paths(profile)[0] / "scripts/__pycache__"
    _validate_paths(profile, [str(cache.relative_to(profile))])
    for module in ("tactic_stream_maya", "userSetup"):
        for path in cache.glob(module + ".*.pyc"):
            path.unlink()
    try:
        cache.rmdir()
    except OSError:
        pass  # Other modules' caches remain owned by their authors.


def install(profile: Path | str, handler_root: Path | str) -> None:
    profile, root = Path(profile).resolve(), Path(handler_root).resolve()
    if not re.fullmatch(r"20\d{2}", profile.name) or int(profile.name) < 2022:
        raise ValueError("A Python 3 Maya version profile is required")
    if not (root / "launch.pyw").is_file():
        raise FileNotFoundError("The Handler application root is unavailable")
    icon = root / "thlib/ui/gliph/maya_shelf/tactic_logo.png"
    if not icon.is_file():
        raise FileNotFoundError("The Handler Maya shelf icon is unavailable")
    directory, module = _paths(profile)
    state = integration_state(profile)
    if state["status"] in {"Modified files", "Unrecognized integration"}:
        raise ValueError("Existing integration files were modified; preserve or remove them manually first")
    shelf = profile / "prefs" / "shelves" / f"shelf_{MODULE}.mel"
    if not state["managed"] and shelf.exists() and not _unchanged(
        profile, str(shelf.relative_to(profile)).replace("\\", "/"), ""
    ):
        raise FileExistsError("The TACTIC_Stream shelf already exists and is not managed by this integration")
    bootstrap = Path(__file__).with_name("maya_bootstrap.py").read_bytes()
    startup = (
        "import maya.cmds as _ts_cmds\n"
        "if not _ts_cmds.about(batch=True):\n"
        "    import maya.utils as _ts_utils\n"
        "    import tactic_stream_maya as _ts_maya\n"
        "    _ts_utils.executeDeferred(_ts_maya.autostart)\n"
    ).encode("utf-8")
    # Keep the entire module payload outside Maya's modules search directory.
    module_data = f"+ MAYAVERSION:{profile.name} {MODULE} 1.0 ../tactic_stream_payload\n"
    # .mod roots can contain spaces and Unicode; relative paths avoid quoting ambiguity.
    data = {
        f"modules/{MODULE}.mod": module_data.encode("utf-8"),
        "tactic_stream_payload/scripts/userSetup.py": startup,
        "tactic_stream_payload/scripts/tactic_stream_maya.py": bootstrap,
        f"prefs/shelves/shelf_{MODULE}.mel": (
            f"global proc shelf_{MODULE} () {{\n"
            '    shelfButton -label "TACTIC Handler" '
            f'-image1 {json.dumps(icon.as_posix(), ensure_ascii=False)} '
            '-imageOverlayLabel "" -annotation "Open TACTIC Handler" '
            '-overlayLabelColor 0.9 0.9 0.9 -overlayLabelBackColor 0.08 0.08 0.08 0.85 '
            '-useAlpha 1 -width 35 -height 34 '
            '-docTag "tactic_stream/integration" -sourceType "python" '
            f"-command {json.dumps(SHELF_COMMAND)};\n}}\n"
        ).encode("utf-8"),
    }
    receipt_path = directory / "integration.json"
    receipt = json.dumps({"format": 1, "handler_root": str(root),
                          "files": {name: _digest(value) for name, value in data.items()}},
                         ensure_ascii=False, indent=2).encode("utf-8")
    files = {profile / name: value for name, value in data.items()}
    files[receipt_path] = receipt
    _validate_paths(profile, [str(path.relative_to(profile)) for path in files])
    # Publish the module only after its complete payload exists.
    files[module] = files.pop(module)
    originals = {path: path.read_bytes() if path.exists() else None for path in files}
    try:
        _clear_bootstrap_bytecode(profile)
        for path, value in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_bytes(value)
            os.replace(temporary, path)
    except OSError:
        for path, previous in originals.items():
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous)
        for path in (directory / "scripts", directory):
            try:
                path.rmdir()
            except OSError:
                pass
        raise
    finally:
        for path in files:
            path.with_name(path.name + ".tmp").unlink(missing_ok=True)


def remove(profile: Path | str) -> None:
    profile = Path(profile).resolve()
    receipt = _receipt(profile)
    modified = [name for name, digest in receipt["files"].items()
                if not _unchanged(profile, name, digest)]
    if modified:
        raise ValueError("Modified integration files were preserved: " + ", ".join(modified))
    directory, _module = _paths(profile)
    paths = [profile / name for name in receipt["files"]]
    paths.append(directory / "integration.json")
    originals = {path: path.read_bytes() for path in paths if path.exists()}
    try:
        for path in paths:
            path.unlink(missing_ok=True)
        _clear_bootstrap_bytecode(profile)
    except OSError:
        for path, data in originals.items():
            path.write_bytes(data)
        raise
    for path in (directory / "scripts", directory):
        try:
            path.rmdir()
        except OSError:
            pass
