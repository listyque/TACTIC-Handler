"""Guarded, backend-neutral seed engine for an isolated TACTIC test project."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "tests" / "fixtures" / "tactic_test_project.json"
ALLOW_ENV = "TACTIC_ALLOW_TEST_PROJECT_MUTATION"


class UnsafeTestProject(RuntimeError):
    pass


def load_manifest(path=DEFAULT_MANIFEST):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_test_project(project_code, manifest, production_project="",
                          require_mutation_permission=True):
    project_code = str(project_code or "").strip()
    prefix = str(manifest.get("projectCodePrefix") or "th_test_")
    if not project_code.startswith(prefix):
        raise UnsafeTestProject(
            f"Test project code must start with {prefix!r}: {project_code!r}"
        )
    if production_project and project_code == str(production_project):
        raise UnsafeTestProject("The test project matches the production project")
    if require_mutation_permission and os.environ.get(ALLOW_ENV) != "1":
        raise UnsafeTestProject(
            f"Set {ALLOW_ENV}=1 explicitly before seed or cleanup"
        )
    return project_code


@dataclass
class FixtureRecord:
    kind: str
    key: str
    values: dict


class MemoryFixtureBackend:
    """Reference backend used to prove idempotency without a TACTIC server."""

    def __init__(self):
        self.records: dict[tuple[str, str], FixtureRecord] = {}

    def ensure(self, kind, key, values, marker):
        identity = (str(kind), str(key))
        payload = {**dict(values), "fixtureMarker": marker}
        record = self.records.get(identity)
        if record is None:
            record = FixtureRecord(str(kind), str(key), payload)
            self.records[identity] = record
        else:
            record.values.update(payload)
        return record

    def cleanup(self, marker):
        removed = [
            identity for identity, record in self.records.items()
            if record.values.get("fixtureMarker") == marker
        ]
        for identity in removed:
            self.records.pop(identity, None)
        return len(removed)


class FixtureSeeder:
    COLLECTIONS = (
        "searchTypes", "groups", "users", "objects", "tasks",
        "milestones", "workHours", "notes", "snapshots", "chats",
    )

    def __init__(self, backend, manifest):
        self.backend = backend
        self.manifest = dict(manifest)
        self.marker = str(self.manifest["marker"])

    def seed(self):
        records = []
        for collection in self.COLLECTIONS:
            kind = collection[:-1] if collection.endswith("s") else collection
            for index, value in enumerate(self.manifest.get(collection) or []):
                if isinstance(value, str):
                    key, values = value, {"code": value}
                else:
                    values = dict(value)
                    key = str(values.get("key") or values.get("code") or index)
                records.append(
                    self.backend.ensure(kind, key, values, self.marker)
                )
        return records

    def cleanup(self):
        return self.backend.cleanup(self.marker)


def fixture_summary(manifest):
    return {
        collection: len(manifest.get(collection) or [])
        for collection in FixtureSeeder.COLLECTIONS
    }
