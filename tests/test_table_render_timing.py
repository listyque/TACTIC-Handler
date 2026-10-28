import unittest

from tests.profile_table_render import parse_timings


class TableRenderTimingTests(unittest.TestCase):
    def test_render_excludes_layout_sync_and_present_wait(self):
        log = """TABLE_RENDER_PHASE scroll
qt.scenegraph.time.renderloop: Frame prepared, polish=45 ms, lock=0 ms
qt.scenegraph.time.renderer: time in renderer: total=4ms, preprocess=1, updates=0, rendering=3
qt.scenegraph.time.renderloop: frame rendered in 30ms, sync=10, render=4, swap=16
qt.scenegraph.time.renderloop: last retrieved GPU frame time was 99 ms
qt.scenegraph.time.renderloop: last retrieved GPU frame time was 88 ms
qt.scenegraph.time.renderloop: last retrieved GPU frame time was 77 ms
qt.scenegraph.time.renderloop: last retrieved GPU frame time was 0.5 ms
TABLE_RENDER_PHASE modes
qt.scenegraph.time.renderer: time in renderer: total=999ms, preprocess=0, updates=0, rendering=999
"""
        result = parse_timings(log)
        self.assertEqual(set(result), {"scroll"})
        for key, expected in {"rendererCpu": 4, "drawCommandsCpu": 3,
                              "syncCpu": 10, "polishCpu": 45,
                              "presentWait": 16, "gpu": .5}.items():
            self.assertEqual(result["scroll"][key]["medianMs"], expected)

    def test_missing_or_unsettled_gpu_is_unavailable(self):
        result = parse_timings("TABLE_RENDER_PHASE refresh\n"
                               "last retrieved GPU frame time was 1 ms")
        self.assertIsNone(result["refresh"]["gpu"])
        self.assertIsNone(result["refresh"]["rendererCpu"])
        result = parse_timings("TABLE_RENDER_PHASE initial\n"
                               "last retrieved GPU frame time was 1 ms")
        self.assertNotIn("gpu", result["initial"])
