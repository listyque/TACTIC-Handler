import unittest

from modern_ui.models import ProjectModel


class _PreviewFile:
    def __init__(self):
        self.calls = 0

    def get_full_abs_path(self):
        self.calls += 1
        if self.calls == 1:
            raise TypeError("repository configuration is not ready")
        return ""


class _File:
    def __init__(self, preview):
        self._preview = preview

    def get_icon_preview(self):
        return self._preview


class _Snapshot:
    def __init__(self, preview):
        self._file = _File(preview)

    def get_files_objects(self, group_by=None):
        return {"icon": [self._file]}


class _Context:
    def __init__(self, preview):
        self._snapshot = _Snapshot(preview)

    def get_versionless(self):
        return {"latest": self._snapshot}

    def get_versions(self):
        return {}


class _Process:
    def __init__(self, preview):
        self._context = _Context(preview)

    def get_contexts(self):
        return {"icon": self._context}


class _Project:
    def __init__(self, preview):
        self._process = _Process(preview)

    def get_code(self):
        return "PROJECT"

    def get_process(self, name):
        return self._process if name == "icon" else None


class ProjectModelPreviewTests(unittest.TestCase):
    def test_repository_not_ready_does_not_crash_or_cache_miss(self):
        preview = _PreviewFile()
        model = ProjectModel()
        project = _Project(preview)

        self.assertEqual(model.preview_for(project), "")
        self.assertNotIn("PROJECT", model._preview_cache)

        self.assertEqual(model.preview_for(project), "")
        self.assertEqual(preview.calls, 2)
        self.assertIn("PROJECT", model._preview_cache)


if __name__ == "__main__":
    unittest.main()