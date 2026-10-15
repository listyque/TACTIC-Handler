"""Portable application release archives and validation."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


VERSION_FIELDS = ("major", "minor", "build", "revision")
VERSION_PATTERN = re.compile(r"(\d+)[._-](\d+)[._-](\d+)[._-](\d+)\.zip$", re.I)
MAX_ARCHIVE_SIZE = 2 * 1024 * 1024 * 1024
MAX_MEMBERS = 20000
RELEASE_ROOT_DIRS = {
    "handler_server", "installer", "project_templates", "scripts",
    "server_plugin", "side_tools", "tactic_handler_api",
    "tactic_handler_dcc", "thlib",
}
RELEASE_ROOT_FILES = {
    "__init__.py", "default.gitattributes", "default.gitignore",
    "execute_after_start.py", "launch.py", "launch.pyw", "LICENSE",
    "README.md", "README.ru.md", "requirements.txt", "release.json",
    "CHANGELOG.md",
}
EXCLUDED_PARTS = {
    ".git", ".idea", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "settings", "log", "updates", "backup", "_tmp",
    ".cache", ".release", "custom_scripts", "tests", "docs", ".agents",
    ".codex", ".artifacts", ".tmp", "node_modules", "venv", ".venv",
}


def version_tuple(data: dict) -> tuple[int, int, int, int]:
    return tuple(int(data[field]) for field in VERSION_FIELDS)


def version_text(version: tuple[int, int, int, int]) -> str:
    return ".".join(map(str, version))


def version_from_filename(filename: str) -> tuple[int, int, int, int] | None:
    match = VERSION_PATTERN.search(Path(filename).name)
    return tuple(map(int, match.groups())) if match else None


def current_version(app_dir: Path | None = None) -> tuple[int, int, int, int]:
    if app_dir is None:
        app_dir = Path(__file__).resolve().parents[1]
    with (app_dir / "thlib" / "version.json").open(encoding="utf-8") as stream:
        return version_tuple(json.load(stream))


def read_changelog(app_dir: Path | None = None) -> str:
    """Read the release history bundled with this application."""
    app_dir = Path(app_dir or Path(__file__).resolve().parents[1])
    return (app_dir / "CHANGELOG.md").read_text(encoding="utf-8")


def release_notes(changelog: str, version: tuple[int, int, int, int]) -> str:
    """Return the Markdown body under an exact version heading."""
    match = re.search(
        r"^## " + re.escape(version_text(version))
        + r" - [^\n]+\n(.*?)(?=^## |\Z)",
        changelog, re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def portable_root(app_dir: Path | None = None) -> Path | None:
    app_dir = Path(app_dir or Path(__file__).resolve().parents[1]).resolve()
    root = app_dir.parent
    if (app_dir.name.lower() == "app" and (root / "_launcher.pyw").is_file()
            and (root / "_runtime" / "pythonw.exe").is_file()):
        return root
    return None


def archive_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if len(members) > MAX_MEMBERS:
        raise ValueError("Update archive contains too many entries")
    seen = set()
    total = 0
    for member in members:
        name = member.filename
        path = PurePosixPath(name)
        parts = name.rstrip("/").split("/")
        if (not name or "\\" in name or name.startswith("/")
                or ":" in name or any(part in {"", ".", ".."} for part in parts)
                or any(part in EXCLUDED_PARTS for part in path.parts)
                or (parts[0] not in RELEASE_ROOT_DIRS
                    and (len(parts) != 1 or parts[0] not in RELEASE_ROOT_FILES))
                or any(part.rstrip(". ") != part or part.split(".")[0].upper()
                       in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                           *(f"LPT{i}" for i in range(1, 10))} for part in parts)
                or stat.S_ISLNK(member.external_attr >> 16)):
            raise ValueError(f"Unsafe update archive entry: {name}")
        folded = str(path).casefold().rstrip("/")
        if folded in seen:
            raise ValueError(f"Duplicate update archive entry: {name}")
        seen.add(folded)
        total += member.file_size
        if total > MAX_ARCHIVE_SIZE:
            raise ValueError("Update archive exceeds the size limit")
    if "launch.py" not in seen or "thlib/version.json" not in seen:
        raise ValueError("Update archive must contain launch.py and thlib/version.json")
    return members


def stage_archive(archive_path: Path, destination: Path,
                  expected_version: tuple[int, int, int, int]) -> None:
    """Validate and extract a release outside the live application directory."""
    destination = Path(destination)
    with zipfile.ZipFile(archive_path) as archive:
        members = archive_members(archive)
        version = json.loads(archive.read("thlib/version.json"))
        if version_tuple(version) != expected_version:
            raise ValueError("Archive version does not match the selected release")
        destination.mkdir(parents=True, exist_ok=False)
        try:
            for member in members:
                target = destination.joinpath(*PurePosixPath(member.filename).parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
        except Exception:
            shutil.rmtree(destination)
            raise


def create_update_archive(app_dir: Path, archive_path: Path,
                          version: tuple[int, int, int, int],
                          changes: str = "", misc: str = "") -> None:
    """Publish app code only; never package settings or modify the running version."""
    app_dir = Path(app_dir)
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    version_bytes = json.dumps(dict(zip(VERSION_FIELDS, version))).encode("utf-8")
    changelog = read_changelog(app_dir)
    notes = release_notes(changelog, version)
    if not notes:
        raise ValueError(
            f"Add release notes for {version_text(version)} to CHANGELOG.md "
            "before creating its update archive"
        )
    changes = changes.strip() or notes
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(app_dir):
            if Path(root) == app_dir:
                dirs[:] = [name for name in dirs if name in RELEASE_ROOT_DIRS]
            else:
                dirs[:] = [name for name in dirs if name not in EXCLUDED_PARTS]
            for filename in files:
                source = Path(root) / filename
                relative = source.relative_to(app_dir).as_posix()
                if (filename in EXCLUDED_PARTS or filename == "release.json"
                        or filename.endswith((".pyc", ".pyo"))
                        or (Path(root) == app_dir
                            and filename not in RELEASE_ROOT_FILES)
                        or source.is_symlink()):
                    continue
                if relative == "thlib/version.json":
                    continue
                archive.write(source, relative)
        archive.writestr("thlib/version.json", version_bytes)
        archive.writestr("release.json", json.dumps({
            "version": version_text(version), "changes": changes, "misc": misc,
        }, ensure_ascii=False).encode("utf-8"))
