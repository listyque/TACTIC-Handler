from __future__ import annotations

import unittest

from thlib.ui.rendering import (
    apply_render_backend,
    effective_render_backend,
    normalize_render_backend,
)


class RenderingPolicyTests(unittest.TestCase):
    def test_windows_automatic_backend_avoids_d3d_swapchain(self):
        self.assertEqual(
            effective_render_backend("automatic", platform_name="win32"),
            "opengl",
        )
        self.assertEqual(
            effective_render_backend("automatic", platform_name="linux"),
            "",
        )

    def test_supported_backend_is_applied_and_invalid_value_is_normalized(self):
        environment = {}

        selected = apply_render_backend(
            "software",
            environment=environment,
            platform_name="win32",
        )

        self.assertEqual(selected, "software")
        self.assertEqual(environment["QT_QUICK_BACKEND"], "software")
        self.assertNotIn("QSG_RHI_BACKEND", environment)
        self.assertEqual(normalize_render_backend("angle"), "automatic")

    def test_explicit_process_backend_overrides_persisted_preference(self):
        environment = {"QSG_RHI_BACKEND": "vulkan"}

        selected = apply_render_backend(
            "d3d11",
            environment=environment,
            platform_name="win32",
        )

        self.assertEqual(selected, "d3d11")
        self.assertEqual(environment["QSG_RHI_BACKEND"], "vulkan")

    def test_explicit_software_scene_graph_overrides_persisted_preference(self):
        environment = {"QT_QUICK_BACKEND": "software"}

        selected = apply_render_backend(
            "opengl",
            environment=environment,
            platform_name="win32",
        )

        self.assertEqual(selected, "opengl")
        self.assertEqual(environment["QT_QUICK_BACKEND"], "software")
        self.assertNotIn("QSG_RHI_BACKEND", environment)


if __name__ == "__main__":
    unittest.main()
