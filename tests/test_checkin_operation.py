import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from thlib.checkin_operation import (
    CheckinCancelled,
    _copy_file,
    execute_checkin_payload,
    prepare_checkin,
    stage_checkin,
)
from thlib.ui.checkin_out import (
    _naming_path, _naming_snapshots, prepare_dcc_scene_placeholders,
)


class CheckinOperationTest(unittest.TestCase):


    def test_file_sizes_preserve_empty_files_and_sequence_order(self):
        from thlib.global_functions import FileObject

        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / 'empty.bin'
            filled = Path(directory) / 'filled.bin'
            empty.write_bytes(b'')
            filled.write_bytes(b'content')
            obj = FileObject()
            self.assertEqual(obj.get_sizes_list(files_list=[str(empty)]), [0])
            self.assertEqual(obj.get_sizes_list(True, [str(empty)]), 0)
            paths = [str(empty), str(filled), str(empty)]
            self.assertEqual(obj.get_sizes_list(files_list=paths), [0, 7, 0])
            self.assertEqual(obj.get_sizes_list(True, paths), 7)
            self.assertIsNone(obj.get_sizes_list(files_list=[str(empty) + '.missing']))
            obj.set_sizes_list([0])
            self.assertEqual(obj.get_sizes_list(), [0])
            self.assertEqual(obj.get_sizes_list(together=True), 0)

    def test_checkin_strips_public_skey_scheme_at_tactic_boundary(self):
        import thlib.tactic_classes as tc

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "guide.txt"
            source.write_text("guide", encoding="utf-8")
            public_search_key = (
                "skey://demo/th_knowledge_article?code=KB0001"
            )
            payload = {
                "searchKey": public_search_key,
                "context": "attachment/knowledge/guide",
                "files": [{
                    "path": str(source),
                    "template": "$FILENAME.$EXT",
                }],
                "filesDict": [("guide", {
                    "t": ["file"], "s": [""], "e": ["txt"],
                    "p": [""], "m": None,
                })],
            }
            repository = {
                "value": [str(Path(directory) / "repository"), "", "", "base"]
            }
            snapshot = {"__search_key__": "sthpw/snapshot?code=SNAP001"}
            native_search_key = (
                "demo/th_knowledge_article?code=KB0001"
            )

            with (
                patch.object(tc, "get_virtual_snapshot", return_value=[]) as naming,
                patch(
                    "thlib.checkin_operation.stage_checkin",
                    return_value=True,
                ),
                patch.object(
                    tc, "checkin_snapshot", return_value=snapshot,
                ) as checkin,
            ):
                result = execute_checkin_payload(payload, repository)

            self.assertEqual(result, snapshot)
            self.assertEqual(
                naming.call_args.args[0], native_search_key
            )
            self.assertEqual(
                checkin.call_args.kwargs["search_key"], native_search_key
            )
            self.assertEqual(payload["searchKey"], public_search_key)

    def test_virtual_naming_result_keeps_one_snapshot_per_input_file(self):
        result = [
            ["scene", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["scene", "_v001", ".ma"]],
                },
                "versionless": {
                    "paths": ["assets"],
                    "names": [["scene", "", ".ma"]],
                },
            }],
            ["preview", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["preview", "_v001", ".jpg"]],
                },
            }],
        ]

        snapshots = _naming_snapshots(result)

        self.assertEqual(len(snapshots), 2)
        self.assertEqual(
            _naming_path(snapshots[0], "versioned"),
            "assets/versions/scene_v001.ma",
        )
        self.assertEqual(
            _naming_path(snapshots[0], "versionless"),
            "assets/scene.ma",
        )
        self.assertEqual(
            _naming_path(snapshots[1], "versioned"),
            "assets/versions/preview_v001.jpg",
        )

    def test_dcc_queue_keeps_real_preview_and_only_stubs_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "preview.jpg"
            preview.write_bytes(b"real playblast")
            prepared = prepare_dcc_scene_placeholders({
                "scene_type": "mayaAscii",
                "extension": "ma",
                "preview_path": str(preview),
                "preview_type": "playblast",
            }, True)

            self.assertEqual(
                Path(prepared["placeholder_paths"][0]).name,
                "scene.ma",
            )
            self.assertEqual(
                Path(prepared["placeholder_paths"][1]), preview
            )
            self.assertEqual(preview.read_bytes(), b"real playblast")
            self.assertEqual(
                prepared["file_types"], ["main", "playblast"]
            )

    def test_dcc_queue_rejects_a_missing_preview(self):
        with self.assertRaisesRegex(ValueError, "preview was not created"):
            prepare_dcc_scene_placeholders({"extension": "nk"}, True)

    def test_cancelled_copy_does_not_leave_completed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.bin"
            destination = Path(directory) / "destination.part"
            source.write_bytes(b"content")
            cancel = threading.Event()
            cancel.set()

            with self.assertRaises(CheckinCancelled):
                _copy_file(source, destination, cancel)
            self.assertNotEqual(source.read_bytes(), destination.read_bytes())

    def test_preparation_restores_native_file_metadata(self):
        import thlib.tactic_classes as tc

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "scene.ma"
            source.write_text("scene", encoding="utf-8")
            payload = {
                "searchKey": "demo/asset?project=demo&code=ASSET001",
                "context": "publish",
                "applicationInfo": {"p": "Autodesk Maya 2026"},
                "files": [{
                    "path": str(source),
                    "template": "$FILENAME.$EXT",
                }],
                "filesDict": [("scene", {
                    "t": ["file"], "s": [""], "e": ["ma"],
                    "p": [""], "m": None,
                })],
            }

            with patch.object(tc, "get_virtual_snapshot", return_value=[]):
                result = prepare_checkin(payload)

            metadata = result["filesDict"][0][1]["m"]
            self.assertEqual(metadata["filename"], "scene")
            self.assertEqual(metadata["ext"], "ma")
            self.assertIn("name_part", metadata)
            self.assertEqual(
                metadata["app_info"]["p"], "Autodesk Maya 2026"
            )

    def test_execution_refreshes_preview_and_preserves_previous_file(self):
        import thlib.tactic_classes as tc
        from thlib.ui.checkin_out import CheckinOutController

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_bytes(b"new content")
            repository = root / "repository"
            old_file = repository / "versions/shot_v001.md"
            old_file.parent.mkdir(parents=True)
            old_file.write_bytes(b"previous version")

            def plan(version):
                return [["source", {
                    "versioned": {"paths": ["versions"],
                                  "names": [[f"shot_v{version:03d}", "", ".md"]]},
                    "versionless": {"paths": ["latest"],
                                    "names": [["shot", "", ".md"]]},
                }]]

            payload = {
                "searchKey": "demo/shot?project=demo&code=SHOT001",
                "context": "publish", "mode": "copy",
                "versionlessMode": "copy", "updateVersionless": False,
                "files": [{"path": str(source), "template": "$FILENAME.$EXT"}],
                "filesDict": [["source", {"t": ["main"], "s": [""],
                                          "e": ["md"], "p": [""], "m": None}]],
                "virtualSnapshot": plan(1),
            }
            snapshot = {"__search_key__": "sthpw/snapshot?code=S2"}
            with patch.object(tc, "get_virtual_snapshot", return_value=plan(2)) as naming:
                inputs = CheckinOutController._prepare_checkin(payload)
                self.assertEqual(inputs["virtualSnapshot"], plan(2))
                with patch.object(tc, "checkin_snapshot", return_value=snapshot):
                    execute_checkin_payload(payload, {"value": [str(repository)]})
                self.assertEqual(naming.call_count, 2)
                reserved = {**payload, "dccScene": {"applicationType": "maya"}}
                reserved_inputs = CheckinOutController._prepare_checkin(reserved)
                self.assertEqual(reserved_inputs["virtualSnapshot"], plan(1))
                self.assertEqual(naming.call_count, 2)
            self.assertEqual(old_file.read_bytes(), b"previous version")
            self.assertEqual((repository / "versions/shot_v002.md").read_bytes(), b"new content")
            self.assertEqual(payload["virtualSnapshot"], plan(1))

    def test_preparation_reuses_the_path_reserved_before_dcc_save(self):
        import thlib.tactic_classes as tc

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "asset_model_v001.ma"
            source.write_text("scene", encoding="utf-8")
            virtual_snapshot = [["scene", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["asset_model_v001", ".ma"]],
                },
                "versionless": {
                    "paths": ["assets"],
                    "names": [["asset_model", ".ma"]],
                },
            }]]
            payload = {
                "searchKey": "demo/asset?project=demo&code=ASSET001",
                "context": "model",
                "files": [{
                    "path": str(source),
                    "template": "$FILENAME.$EXT",
                }],
                "filesDict": [("scene", {
                    "t": ["main"], "s": [""], "e": ["ma"],
                    "p": [""], "m": None,
                })],
                "virtualSnapshot": virtual_snapshot,
            }

            with patch.object(tc, "get_virtual_snapshot") as naming:
                result = prepare_checkin(payload)

            naming.assert_not_called()
            self.assertEqual(result["virtualSnapshot"], virtual_snapshot)

    def test_extensionless_file_keeps_exact_name_through_extended_checkin(self):
        import thlib.tactic_classes as tc

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "aid_kit_model"
            source.write_bytes(b"model")
            payload = {
                "searchKey": "demo/asset?project=demo&code=ASSET001",
                "context": "model",
                "updateVersionless": False,
                "generatePreviews": False,
                "sequencePadding": 3,
                "mode": "upload",
                "files": [{
                    "path": str(source),
                    "template": "$FILENAME",
                }],
                "filesDict": [("aid_kit_model", {
                    "t": ["file"], "s": [""], "e": [""],
                    "p": [""], "m": None,
                })],
            }

            def virtual_snapshot(_key, _context, files_dict, **_kwargs):
                name_part = files_dict[0][1]["m"]["name_part"]
                names = [["aid_kit_model_v001", name_part, ""]]
                return [["aid_kit_model", {
                    "versioned": {"paths": ["assets/versions"], "names": names},
                    "versionless": {"paths": ["assets"], "names": names},
                }]]

            with patch.object(
                tc, "get_virtual_snapshot", side_effect=virtual_snapshot
            ):
                inputs = prepare_checkin(payload)

            metadata = inputs["filesDict"][0][1]["m"]
            self.assertEqual(metadata.get("ext", ""), "")
            self.assertEqual(metadata["name_part"], "")

            repository_root = root / "repository"
            repository = {
                "name": "asset_base_dir",
                "value": [str(repository_root), "", "", "base"],
            }
            self.assertTrue(stage_checkin(inputs, repository))
            staged = repository_root / "assets/versions/aid_kit_model_v001"
            self.assertTrue(staged.is_file())
            self.assertEqual(staged.name, "aid_kit_model_v001")

            server = Mock()
            server.split_search_key.return_value = ("demo/asset", "ASSET001")
            server.get_base_dirs.return_value = {
                "asset_base_dir": str(root / "different_repository"),
            }
            snapshot = {"__search_key__": "sthpw/snapshot?code=SNAP001"}
            with (patch.object(tc, "server_start", return_value=server),
                  patch.object(
                      tc, "execute_procedure_serverside", return_value=snapshot
                  ) as execute):
                result = tc.checkin_snapshot(
                    search_key=payload["searchKey"],
                    context=payload["context"],
                    update_versionless=False,
                    repo_name=repository,
                    virtual_snapshot=inputs["virtualSnapshot"],
                    files_dict=inputs["filesDict"],
                    mode="upload",
                    create_icon=False,
                    files_objects=inputs["filesObjects"],
                )

            self.assertEqual(result, snapshot)
            files_info = json.loads(execute.call_args.args[1]["files_info"])
            self.assertEqual(
                Path(files_info["version_files"][0]).name,
                "aid_kit_model_v001",
            )
            self.assertEqual(
                files_info["upload_file_names"][0],
                "aid_kit_model_v001",
            )
            server.upload_file.assert_called_once_with(
                files_info["version_files"][0], progress_signal=None
            )

            server.upload_file.reset_mock()
            server.start.reset_mock()
            server.finish.reset_mock()
            server.get_base_dirs.return_value = {
                "asset_base_dir": str(repository_root),
            }
            with (patch.object(tc, "server_start", return_value=server),
                  patch.object(
                      tc, "execute_procedure_serverside", return_value=snapshot
                  ) as execute):
                tc.checkin_snapshot(
                    search_key=payload["searchKey"],
                    context=payload["context"],
                    update_versionless=False,
                    repo_name=repository,
                    virtual_snapshot=inputs["virtualSnapshot"],
                    files_dict=inputs["filesDict"],
                    mode="upload",
                    create_icon=False,
                    files_objects=inputs["filesObjects"],
                )

            server.upload_file.assert_not_called()
            self.assertEqual(execute.call_args.args[1]["mode"], "inplace")
            self.assertEqual(execute.call_args.args[1]["transaction_title"], "Inplace Checkin")
            self.assertIn("Finished.", execute.call_args.args[1]["transaction_description"])
            server.start.assert_not_called()
            server.finish.assert_not_called()

            for mode in ("inplace", "preallocate"):
                server.abort.reset_mock()
                with (patch.object(tc, "server_start", return_value=server),
                      patch.object(tc, "execute_procedure_serverside", side_effect=RuntimeError("save failed"))):
                    with self.assertRaisesRegex(RuntimeError, "save failed"):
                        tc.checkin_snapshot(
                            search_key=payload["searchKey"], context=payload["context"],
                            update_versionless=False, repo_name=repository,
                            virtual_snapshot=inputs["virtualSnapshot"], files_dict=inputs["filesDict"],
                            mode=mode, create_icon=False, files_objects=inputs["filesObjects"],
                        )
                server.start.assert_not_called()
                server.finish.assert_not_called()
                server.abort.assert_not_called()

    def test_extended_server_upload_opens_extensionless_temp_name(self):
        import thlib.tactic_query as tq

        snapshot = Mock()
        snapshot.get_code.return_value = "SNAP001"
        snapshot_type = SimpleNamespace(create=Mock(return_value=snapshot))
        search = Mock()
        search.get_sobjects.return_value = []
        search_type = Mock(return_value=search)
        file_record = Mock()
        checkin = Mock()
        checkin.get_file_objects.return_value = [file_record]
        file_append = Mock(return_value=checkin)
        api = Mock()
        api._get_sobjects.return_value = [Mock()]
        api._get_sobject_dict.return_value = {
            "__search_key__": "sthpw/snapshot?code=SNAP001"
        }
        native_server = SimpleNamespace(
            server=api,
            set_project=Mock(),
            split_search_key=Mock(return_value=("demo/asset", "ASSET001")),
            eval=Mock(),
        )
        environment = SimpleNamespace(
            get=Mock(return_value=SimpleNamespace(
                get_upload_dir=Mock(return_value="/upload")
            ))
        )
        modules = {
            "pyasm.biz": SimpleNamespace(
                Snapshot=snapshot_type,
                IconCreator=Mock(),
                Project=Mock(),
            ),
            "pyasm.checkin": SimpleNamespace(FileAppendCheckin=file_append),
            "pyasm.search": SimpleNamespace(Search=search_type),
            "pyasm.common": SimpleNamespace(Environment=environment),
        }
        files_info = {
            "version_files": ["/repo/aid_kit_model_v001"],
            "version_files_paths": ["assets/versions"],
            "versionless_files": ["/repo/aid_kit_model"],
            "versionless_files_paths": ["assets"],
            "files_types": ["file"],
            "file_sizes": [5],
            "upload_file_names": ["aid_kit_model_v001"],
            "version_metadata": [{
                "filename": "aid_kit_model",
                "new_filename": "aid_kit_model_v001",
                "new_file_ext": "",
            }],
            "versionless_metadata": [{}],
        }

        with (patch.dict(sys.modules, modules),
              patch.object(tq, "server", native_server, create=True)):
            result = tq.create_snapshot_extended(
                search_key="demo/asset?project=demo&code=ASSET001",
                context="model",
                project_code="demo",
                update_versionless=False,
                repo_name="base",
                files_info=json.dumps(files_info),
                mode="upload",
                create_icon=False,
            )
            legacy_files_info = json.loads(json.dumps(files_info))
            legacy_files_info.pop("upload_file_names")
            tq.create_snapshot_extended(
                search_key="demo/asset?project=demo&code=ASSET001",
                context="model",
                project_code="demo",
                update_versionless=False,
                repo_name="base",
                files_info=json.dumps(legacy_files_info),
                mode="upload",
                create_icon=False,
            )
            extension_files_info = json.loads(json.dumps(legacy_files_info))
            extension_files_info["version_metadata"][0].update({
                "filename": "aid_kit_model",
                "new_filename": "aid_kit_model_v001",
                "new_file_ext": "ma",
            })
            tq.create_snapshot_extended(
                search_key="demo/asset?project=demo&code=ASSET001",
                context="model",
                project_code="demo",
                update_versionless=False,
                repo_name="base",
                files_info=json.dumps(extension_files_info),
                mode="upload",
                create_icon=False,
            )

        self.assertEqual(
            file_append.call_args_list[0].args[1],
            ["/upload/aid_kit_model_v001"],
        )
        self.assertEqual(
            file_append.call_args_list[1].args[1],
            ["/upload/aid_kit_model_v001"],
        )
        self.assertEqual(
            file_append.call_args_list[2].args[1],
            ["/upload/aid_kit_model_v001.ma"],
        )
        self.assertFalse(file_append.call_args_list[1].args[1][0].endswith("."))
        file_record.set_value.assert_any_call(
            name="source_path", value="/upload/aid_kit_model"
        )
        self.assertEqual(result["__search_key__"], "sthpw/snapshot?code=SNAP001")

    def test_optional_versionless_links_preserve_numbered_files(self):
        class FileObject:
            @staticmethod
            def get_all_new_files_list(name, directory, **_kwargs):
                return [str(Path(directory) / str(name))]

        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            repository = root / "repository"
            for mode in ("copy", "hardlink", "symlink"):
                latest = repository / mode / "latest/image.png"
                inputs = {
                    "payload": {"updateVersionless": True,
                                "generatePreviews": True, "versionlessMode": mode},
                    "filesObjects": [FileObject()], "filePaths": [[str(source)]],
                }
                for version in (1, 2):
                    source.write_bytes(bytes([version]))
                    numbered = repository / mode / ("v%s/image.png" % version)
                    inputs["virtualSnapshot"] = [["image", {
                        "versioned": {"paths": [mode + "/v%s" % version,
                            mode + "/v%s/web" % version, mode + "/v%s/icon" % version],
                            "names": ["image.png"] * 3},
                        "versionless": {"paths": [mode + "/latest", mode + "/latest/web", mode + "/latest/icon"],
                            "names": ["image.png"] * 3}}]]
                    def generate(_source, web, icon):
                        Path(web).write_bytes(b"web" + bytes([version]))
                        Path(icon).write_bytes(b"icon" + bytes([version]))
                    with patch("thlib.tactic_classes.generate_web_and_icon", side_effect=generate):
                        try:
                            stage_checkin(inputs, {"value": [str(repository)]})
                        except OSError as error:
                            if mode == "symlink" and getattr(error, "winerror", None) == 1314:
                                break
                            raise
                    self.assertEqual(latest.read_bytes(), bytes([version]))
                    for suffix in ("", "web/", "icon/"):
                        self.assertEqual(os.path.samefile(numbered.parent / suffix / "image.png",
                            latest.parent / suffix / "image.png"), mode != "copy")
                    if version == 2:
                        self.assertEqual((repository / mode / "v1/image.png").read_bytes(), bytes([1]))
                inputs["payload"]["onlyVersionless"] = True
                inputs["payload"]["generatePreviews"] = False
                source.write_bytes(b"only versionless")
                stage_checkin(inputs, {"value": [str(repository)]})
                self.assertEqual(latest.read_bytes(), b"only versionless")
                self.assertFalse(latest.is_symlink())
                self.assertFalse(list(repository.rglob("*.part")))

    def test_preview_is_generated_once_for_versioned_and_versionless(self):
        class FileObject:
            @staticmethod
            def get_all_new_files_list(name, directory, **_kwargs):
                return [str(Path(directory) / str(name))]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(b"image")
            inputs = {
                "payload": {
                    "updateVersionless": True,
                    "generatePreviews": True,
                    "sequencePadding": 3,
                    "mode": "copy",
                },
                "filesObjects": [FileObject()],
                "filePaths": [[str(source)]],
                "virtualSnapshot": [["source", {
                    "versioned": {
                        "paths": ["versions", "web/versions", "icon/versions"],
                        "names": ["source_v001.png", "source_v001.jpg", "source_v001.jpg"],
                    },
                    "versionless": {
                        "paths": ["latest", "web/latest", "icon/latest"],
                        "names": ["source.png", "source.jpg", "source.jpg"],
                    },
                }]],
            }

            def generate(_source, web_path, icon_path):
                Path(web_path).write_bytes(b"web")
                Path(icon_path).write_bytes(b"icon")

            with patch(
                "thlib.tactic_classes.generate_web_and_icon",
                side_effect=generate,
            ) as generator:
                self.assertTrue(stage_checkin(
                    inputs,
                    {"value": [str(root / "repository")]},
                ))

            self.assertEqual(generator.call_count, 1)
            self.assertTrue((root / "repository/web/latest/source.jpg").is_file())
            self.assertTrue((root / "repository/icon/latest/source.jpg").is_file())

    def test_failed_preview_generation_never_reuses_old_derivatives(self):
        class FileObject:
            @staticmethod
            def get_all_new_files_list(name, directory, **_kwargs):
                return [str(Path(directory) / str(name))]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(b"new-image")
            repository_root = root / "repository"
            old_web = repository_root / "web/versions/source_v002.jpg"
            old_icon = repository_root / "icon/versions/source_v002.png"
            old_web.parent.mkdir(parents=True)
            old_icon.parent.mkdir(parents=True)
            old_web.write_bytes(b"old-web")
            old_icon.write_bytes(b"old-icon")
            inputs = {
                "payload": {
                    "updateVersionless": True,
                    "generatePreviews": True,
                    "sequencePadding": 3,
                    "mode": "copy",
                },
                "filesObjects": [FileObject()],
                "filePaths": [[str(source)]],
                "virtualSnapshot": [["source", {
                    "versioned": {
                        "paths": [
                            "versions", "web/versions", "icon/versions",
                        ],
                        "names": [
                            "source_v002.png", "source_v002.jpg",
                            "source_v002.png",
                        ],
                    },
                    "versionless": {
                        "paths": ["latest", "web/latest", "icon/latest"],
                        "names": ["source.png", "source.jpg", "source.png"],
                    },
                }]],
            }

            with patch(
                "thlib.tactic_classes.generate_web_and_icon",
                return_value=None,
            ):
                with self.assertRaisesRegex(
                    OSError, "could not generate the web preview"
                ):
                    stage_checkin(
                        inputs,
                        {"value": [str(repository_root)]},
                    )

            self.assertEqual(old_web.read_bytes(), b"old-web")
            self.assertEqual(old_icon.read_bytes(), b"old-icon")
            self.assertEqual(list(repository_root.rglob("*.part.*")), [])

    def test_native_preview_generation_reports_an_unreadable_image(self):
        import thlib.tactic_classes as tc

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "broken.png"
            web = root / "web.jpg"
            icon = root / "icon.png"
            source.write_bytes(b"not-an-image")
            web.write_bytes(b"old-web")
            icon.write_bytes(b"old-icon")

            with self.assertRaisesRegex(
                ValueError, "Unable to decode preview image"
            ):
                tc.generate_web_and_icon(str(source), str(web), str(icon))

            self.assertEqual(web.read_bytes(), b"old-web")
            self.assertEqual(icon.read_bytes(), b"old-icon")


if __name__ == "__main__":
    unittest.main()
