from __future__ import annotations

import unittest

from thlib.ui.rendering import (
    apply_render_backend,
    effective_render_backend,
    normalize_render_backend,
)


class RenderingPolicyTests(unittest.TestCase):
    def test_windows_opengl_does_not_block_resize_on_vsync(self):
        for environment in (
            {}, {"QSG_RHI_BACKEND": "opengl"},
            {"QT_QUICK_BACKEND": "rhi", "QSG_RHI_BACKEND": "opengl"},
        ):
            with self.subTest(environment=environment.copy()):
                apply_render_backend(
                    "automatic", environment=environment, platform_name="win32",
                )
                self.assertEqual(environment["QSG_RHI_BACKEND"], "opengl")
                self.assertEqual(environment["QSG_NO_VSYNC"], "1")

    def test_explicit_vsync_and_other_renderers_keep_their_policy(self):
        for backend, platform in (
            ('opengl', 'win32'), ('d3d11', 'win32'), ('software', 'win32'),
            ('opengl', 'linux'),
        ):
            environment = {'QSG_NO_VSYNC': '0'}
            apply_render_backend(backend, environment=environment, platform_name=platform)
            self.assertEqual(environment['QSG_NO_VSYNC'], '0')
        for backend, platform in (
            ('d3d11', 'win32'), ('software', 'win32'), ('opengl', 'linux'),
        ):
            environment = {}
            apply_render_backend(backend, environment=environment, platform_name=platform)
            self.assertNotIn('QSG_NO_VSYNC', environment)

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
        self.assertNotIn("QSG_NO_VSYNC", environment)


if __name__ == "__main__":
    unittest.main()
