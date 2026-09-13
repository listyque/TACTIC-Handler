from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from tests.support.tactic_test_project import (
    ALLOW_ENV,
    FixtureSeeder,
    MemoryFixtureBackend,
    UnsafeTestProject,
    fixture_summary,
    load_manifest,
    validate_test_project,
)


class TacticTestProjectTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest()

    def test_production_like_project_codes_are_rejected(self):
        with self.assertRaises(UnsafeTestProject):
            validate_test_project("niki_friends", self.manifest, False)

    def test_mutation_requires_explicit_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(UnsafeTestProject):
                validate_test_project("th_test_handler", self.manifest)
        with patch.dict(os.environ, {ALLOW_ENV: "1"}, clear=True):
            self.assertEqual(
                validate_test_project("th_test_handler", self.manifest),
                "th_test_handler",
            )

    def test_seed_is_idempotent_and_cleanup_is_marker_scoped(self):
        backend = MemoryFixtureBackend()
        backend.ensure("object", "unrelated", {"name": "Keep"}, "other")
        seeder = FixtureSeeder(backend, self.manifest)

        first = seeder.seed()
        second = seeder.seed()

        self.assertEqual(len(first), len(second))
        self.assertEqual(len(backend.records), len(first) + 1)
        self.assertEqual(seeder.cleanup(), len(first))
        self.assertIn(("object", "unrelated"), backend.records)
        self.assertEqual(seeder.cleanup(), 0)

    def test_fixture_covers_every_required_domain(self):
        summary = fixture_summary(self.manifest)
        for collection in FixtureSeeder.COLLECTIONS:
            with self.subTest(collection=collection):
                self.assertGreater(summary[collection], 0)


if __name__ == "__main__":
    unittest.main()
