import unittest

from thlib.ui.cache_policy import CACHE_POLICIES, cache_policy
from thlib.ui.communication_feed import MessagesController
from thlib.ui.models import ProjectModel
from thlib.ui.skey_previews import SearchKeyPreviewResolver


class CachePolicyTests(unittest.TestCase):
    def test_cache_policies_are_complete_and_unique(self):
        names = [policy.name for policy in CACHE_POLICIES]
        self.assertEqual(len(names), len(set(names)))
        for policy in CACHE_POLICIES:
            self.assertTrue(policy.owner)
            self.assertTrue(policy.key)
            self.assertTrue(policy.invalidation)
            self.assertTrue(policy.explicit_refresh)
            self.assertGreater(policy.maximum_entries, 0)
            self.assertTrue(
                policy.ttl_seconds is None or policy.ttl_seconds > 0
            )

    def test_declared_limits_match_bounded_implementations(self):
        self.assertEqual(
            cache_policy("project_preview").maximum_entries,
            ProjectModel._preview_cache_limit,
        )
        self.assertEqual(
            cache_policy("message_history").maximum_entries,
            MessagesController.CONVERSATION_CACHE_LIMIT,
        )
        self.assertEqual(
            cache_policy("skey_preview").maximum_entries,
            SearchKeyPreviewResolver.CACHE_LIMIT,
        )

    def test_project_preview_cache_is_lru_bounded(self):
        model = ProjectModel()
        for index in range(model._preview_cache_limit + 5):
            model._store_preview(str(index), "")
        self.assertEqual(
            len(model._preview_cache), model._preview_cache_limit
        )
        self.assertNotIn("0", model._preview_cache)


if __name__ == "__main__":
    unittest.main()
