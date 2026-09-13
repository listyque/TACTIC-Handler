from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

from thlib.checkin_operation import (
    CheckinCancelled, execute_checkin_payload,
)


class CheckinVerticalTests(unittest.TestCase):
    def _payload(self, mode="upload"):
        return {
            "searchKey": "skey://demo/asset?code=ASSET001",
            "context": "publish",
            "files": [{"path": "scene.ma"}],
            "filesDict": ["scene.ma"],
            "snapshotType": "file",
            "description": "Publish scene",
            "mode": mode,
            "updateVersionless": True,
            "generatePreviews": True,
        }

    def test_full_operation_returns_the_native_snapshot_identity(self):
        import thlib.tactic_classes as tc

        payload = self._payload("upload")
        prepared = {
            "payload": payload,
            "filesObjects": [object()],
            "filePaths": [["scene.ma"]],
            "filesDict": payload["filesDict"],
            "virtualSnapshot": [["scene", {"versioned": {}}]],
        }
        with (
            patch(
                "thlib.checkin_operation.prepare_checkin",
                return_value=prepared,
            ) as prepare,
            patch(
                "thlib.checkin_operation.stage_checkin",
                return_value=True,
            ) as stage,
            patch.object(
                tc, "checkin_snapshot",
                return_value={
                    "code": "SNAPSHOT001",
                    "__search_key__": (
                        "skey://sthpw/snapshot?code=SNAPSHOT001"
                    ),
                },
            ) as checkin,
        ):
            result = execute_checkin_payload(payload, {"value": ["repo"]})

        prepare.assert_called_once()
        stage.assert_called_once()
        self.assertEqual(result["code"], "SNAPSHOT001")
        self.assertIn("code=SNAPSHOT001", result["__search_key__"])
        self.assertEqual(checkin.call_args.kwargs["mode"], "upload")
        self.assertIs(
            checkin.call_args.kwargs["virtual_snapshot"],
            prepared["virtualSnapshot"],
        )

    def test_move_and_preallocate_modes_keep_server_semantics(self):
        import thlib.tactic_classes as tc

        for source_mode, snapshot_mode in (
            ("move", "inplace"),
            ("preallocate", "preallocate"),
        ):
            payload = self._payload(source_mode)
            prepared = {
                "payload": payload,
                "filesObjects": [],
                "filePaths": [],
                "filesDict": [],
                "virtualSnapshot": [],
            }
            with (
                self.subTest(mode=source_mode),
                patch(
                    "thlib.checkin_operation.prepare_checkin",
                    return_value=prepared,
                ),
                patch(
                    "thlib.checkin_operation.stage_checkin",
                    return_value=True,
                ),
                patch.object(
                    tc, "checkin_snapshot",
                    return_value={"__search_key__": "skey://snapshot?code=S1"},
                ) as checkin,
            ):
                execute_checkin_payload(payload, {"value": ["repo"]})
                self.assertEqual(
                    checkin.call_args.kwargs["mode"], snapshot_mode,
                )

    def test_cancel_before_snapshot_creation_never_calls_tactic(self):
        import thlib.tactic_classes as tc

        payload = self._payload()
        prepared = {
            "payload": payload,
            "filesObjects": [],
            "filePaths": [],
            "filesDict": [],
            "virtualSnapshot": [],
        }
        cancelled = threading.Event()
        cancelled.set()
        with (
            patch(
                "thlib.checkin_operation.prepare_checkin",
                return_value=prepared,
            ),
            patch(
                "thlib.checkin_operation.stage_checkin",
                return_value=True,
            ),
            patch.object(tc, "checkin_snapshot") as checkin,
        ):
            with self.assertRaises(CheckinCancelled):
                execute_checkin_payload(
                    payload, {"value": ["repo"]},
                    cancel_event=cancelled,
                )
        checkin.assert_not_called()

    def test_missing_snapshot_identity_is_a_failed_checkin(self):
        import thlib.tactic_classes as tc

        payload = self._payload()
        prepared = {
            "payload": payload,
            "filesObjects": [],
            "filePaths": [],
            "filesDict": [],
            "virtualSnapshot": [],
        }
        with (
            patch(
                "thlib.checkin_operation.prepare_checkin",
                return_value=prepared,
            ),
            patch(
                "thlib.checkin_operation.stage_checkin",
                return_value=True,
            ),
            patch.object(tc, "checkin_snapshot", return_value={}),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "did not return the created snapshot"
            ):
                execute_checkin_payload(payload, {"value": ["repo"]})


if __name__ == "__main__":
    unittest.main()
