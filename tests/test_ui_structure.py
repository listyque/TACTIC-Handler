import json
from pathlib import Path
import re
import unittest

from thlib.ui.menu_schema import DEFAULT_MENUS, TOOL_WINDOWS
from thlib.ui.workspace_models.windows import FloatingWindowModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


_QML_SCROLLABLE = re.compile(
    r"\b((?:Controls\.)?SmoothListView|ListView|GridView|Flickable|ScrollView)\s*\{"
)
_QML_SHARED_SCROLLBAR = re.compile(r"\b(Controls\.ScrollBar)\s*\{")


def _qml_blocks(source, pattern):
    """Yield complete matching QML blocks while ignoring strings/comments."""
    for match in pattern.finditer(source):
        index = match.end()
        depth = 1
        quote = None
        escaped = False
        line_comment = False
        block_comment = False
        while index < len(source) and depth:
            char = source[index]
            following = source[index + 1] if index + 1 < len(source) else ""
            if line_comment:
                if char in "\r\n":
                    line_comment = False
            elif block_comment:
                if char == "*" and following == "/":
                    block_comment = False
                    index += 1
            elif quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char == "/" and following == "/":
                line_comment = True
                index += 1
            elif char == "/" and following == "*":
                block_comment = True
                index += 1
            elif char in "\"'":
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        if depth == 0:
            yield (
                match.group(1),
                source[match.start():index],
                source.count("\n", 0, match.start()) + 1,
            )


def _qml_scrollable_blocks(source):
    yield from _qml_blocks(source, _QML_SCROLLABLE)


def _qml_direct_content(block):
    """Return only properties and comments owned by the outer QML object."""
    opening = block.find("{")
    if opening < 0:
        return block
    output = []
    depth = 1
    index = opening + 1
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    while index < len(block) and depth:
        char = block[index]
        following = block[index + 1] if index + 1 < len(block) else ""
        if line_comment:
            if depth == 1:
                output.append(char)
            if char in "\r\n":
                line_comment = False
        elif block_comment:
            if depth == 1:
                output.append(char)
            if char == "*" and following == "/":
                if depth == 1:
                    output.append(following)
                block_comment = False
                index += 1
        elif quote:
            if depth == 1:
                output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char == "/" and following == "/":
            if depth == 1:
                output.extend((char, following))
            line_comment = True
            index += 1
        elif char == "/" and following == "*":
            if depth == 1:
                output.extend((char, following))
            block_comment = True
            index += 1
        elif char in "\"'":
            if depth == 1:
                output.append(char)
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif depth == 1:
            output.append(char)
        index += 1
    return "".join(output)


class UiStructureTests(unittest.TestCase):
    def test_scrollable_item_views_expose_their_scrollbar(self):
        offenders = []
        for path in QML.rglob("*.qml"):
            if path.name == "SmoothListView.qml":
                continue
            source = path.read_text(encoding="utf-8")
            for _component, block, line in _qml_scrollable_blocks(source):
                direct_content = _qml_direct_content(block)
                horizontal = bool(
                    re.search(
                        r"orientation\s*:\s*ListView\.Horizontal",
                        direct_content,
                    )
                    or "Flickable.HorizontalFlick" in direct_content
                    or re.search(
                        r"contentHeight\s*:\s*height\b", direct_content
                    )
                ) and "Flickable.VerticalFlick" not in direct_content
                axis = "horizontal" if horizontal else "vertical"
                if (
                    f"ScrollBar.{axis}" in direct_content
                    or f"ui-scrollbar: external-{axis}" in direct_content
                ):
                    continue
                offenders.append(
                    f"{path.relative_to(ROOT).as_posix()}:{line} ({axis})"
                )

        self.assertEqual(offenders, [])

    def test_shared_scrollbars_do_not_override_common_behavior(self):
        forbidden = (
            "policy:", "visible:", "enabled:", "opacity:",
            "interactive:", "minimumSize:", "implicitWidth:",
            "implicitHeight:", "width:", "height:", "anchors.",
            "onPressedChanged:",
        )
        offenders = []
        for path in QML.rglob("*.qml"):
            if path.name == "ScrollBar.qml":
                continue
            source = path.read_text(encoding="utf-8")
            for _component, block, line in _qml_blocks(
                source, _QML_SHARED_SCROLLBAR
            ):
                direct_content = _qml_direct_content(block)
                overridden = [
                    name for name in forbidden if name in direct_content
                ]
                if re.search(r"(?:^|\n)\s*[xy]\s*:", direct_content):
                    overridden.append("x/y:")
                if overridden:
                    offenders.append(
                        f"{path.relative_to(ROOT).as_posix()}:{line} "
                        f"({', '.join(overridden)})"
                    )

        self.assertEqual(offenders, [])

    def test_oversized_ui_architecture_debt_does_not_grow(self):
        contract_path = ROOT / "tests/contracts/ui_architecture_debt.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        violations = []

        groups = (
            (
                ROOT / "thlib/ui/qml",
                "*.qml",
                int(contract["qml_threshold"]),
                contract["qml_max_lines"],
            ),
            (
                ROOT / "thlib/ui",
                "*.py",
                int(contract["python_threshold"]),
                contract["python_max_lines"],
            ),
        )
        for folder, pattern, threshold, budget in groups:
            for relative in budget:
                if not (ROOT / relative).is_file():
                    violations.append(f"remove stale debt record: {relative}")
            for path in folder.rglob(pattern):
                line_count = len(path.read_text(encoding="utf-8").splitlines())
                if line_count <= threshold:
                    continue
                relative = path.relative_to(ROOT).as_posix()
                maximum = budget.get(relative)
                if maximum is None:
                    violations.append(
                        f"new oversized file: {relative} ({line_count} lines)"
                    )
                elif line_count > int(maximum):
                    violations.append(
                        f"architecture debt grew: {relative} "
                        f"({line_count} > {maximum})"
                    )

        self.assertEqual(violations, [])

    def test_preview_presenters_do_not_load_remote_file_paths_directly(self):
        presenters = (
            ROOT / "thlib" / "ui" / "models.py",
            ROOT / "thlib" / "ui" / "tasks.py",
            ROOT / "thlib" / "ui" / "user.py",
            ROOT / "thlib" / "ui" / "skey_previews.py",
            ROOT / "thlib" / "ui" / "workspace_models"
            / "results_presentation.py",
            ROOT / "thlib" / "ui" / "workspace_models"
            / "state_snapshot_state.py",
        )
        offenders = [
            str(path.relative_to(ROOT))
            for path in presenters
            if "get_full_web_path(" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_window_model_is_the_only_standalone_content_registry(self):
        for window in FloatingWindowModel._defaults():
            source = FloatingWindowModel._content_source(window)
            self.assertTrue(source.endswith(".qml"))
            self.assertTrue(
                (QML / source).is_file(), (window.window_id, source)
            )

        host = (QML / "WindowContent.qml").read_text(encoding="utf-8")
        self.assertNotIn("Component {", host)
        self.assertNotIn("ConfigurationView", host)
        self.assertNotIn("MessagesView", host)

    def test_experimental_assets_browser_is_removed_but_cards_remain(self):
        removed_window_id = "asset_browser"
        removed_command = "tool_assets_browser"

        self.assertFalse((QML / "AssetsBrowserView.qml").exists())
        self.assertNotIn(removed_command, TOOL_WINDOWS)
        self.assertNotIn(
            removed_window_id,
            {window.window_id for window in FloatingWindowModel._defaults()},
        )
        self.assertNotIn(
            removed_command,
            {
                item.get("command")
                for item in DEFAULT_MENUS["tools"]
            },
        )

        stale_window = {
            "window_id": removed_window_id,
            "title": "Assets Browser",
            "kind": removed_window_id,
            "x": 0.1,
            "y": 0.1,
            "width": 0.7,
            "height": 0.7,
            "visible": True,
            "z": 3,
            "blocking": False,
            "geometry_mode": "relative",
        }
        settings = {
            FloatingWindowModel._settings_key: json.dumps([stale_window]),
        }
        restored = FloatingWindowModel(settings)
        restored_ids = {
            restored.data(restored.index(row, 0), FloatingWindowModel.IdRole)
            for row in range(restored.rowCount())
        }
        self.assertNotIn(removed_window_id, restored_ids)

        search_workspace = (
            QML / "SearchResultSurface.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("delegate: WorkspaceCard {", search_workspace)
        self.assertIn('effectiveViewMode === "tiles"', search_workspace)

    def test_server_presets_is_a_configuration_owned_editor(self):
        view = (QML / "ServerPresetsView.qml").read_text(
            encoding="utf-8"
        )
        host = (QML / "FloatingWindow.qml").read_text(encoding="utf-8")
        configuration = (QML / "ConfigurationServerPage.qml").read_text(
            encoding="utf-8"
        )
        commands = {
            item.get("command") for item in DEFAULT_MENUS["tools"]
        }
        self.assertNotIn("tool_server_presets", commands)
        self.assertNotIn("tool_server_presets", TOOL_WINDOWS)
        self.assertIn(
            'windowModel.show_window("server_presets")', configuration
        )
        self.assertIn("serverPresetsController.begin_session()", view)
        self.assertIn('objectName: "serverPresetsList"', view)
        self.assertIn("presetList.scrollBarGutter", view)
        self.assertIn('root.kind === "server_presets"', host)
        self.assertIn("serverPresetsController.cancel()", host)

    def test_obsolete_preview_and_attachment_editors_are_removed(self):
        removed_window_ids = {"preview_editor", "attachments_editor"}
        removed_commands = {
            "tool_attachments",
            "tool_preview_editor",
            "tool_attachments_editor",
        }

        self.assertFalse((QML / "FilePreparationEditor.qml").exists())
        self.assertTrue(removed_commands.isdisjoint(TOOL_WINDOWS))
        self.assertTrue(removed_window_ids.isdisjoint({
            window.window_id for window in FloatingWindowModel._defaults()
        }))
        menu_commands = {
            item.get("command")
            for item in DEFAULT_MENUS["tools"]
        }
        self.assertTrue(removed_commands.isdisjoint(menu_commands))

        self.assertNotIn(
            "tool_screenshot_maker", TOOL_WINDOWS
        )
        self.assertIn(
            "screenshot_maker",
            FloatingWindowModel._context_required_windows,
        )
        commit_queue_menu = (
            QML / "CommitQueueActionMenus.qml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "root.screenshot.prepare_for_operation", commit_queue_menu
        )
        self.assertIn(
            'root.windows.show_child_window(',
            commit_queue_menu,
        )
        self.assertIn(
            '"screenshot_maker", "commit_queue")',
            commit_queue_menu,
        )
        self.assertTrue((QML / "AttachmentStagingPanel.qml").exists())
        self.assertTrue((QML / "AttachmentComposerControls.qml").exists())

    def test_tools_menu_routes_available_tool_windows(self):
        actions = [
            item for item in DEFAULT_MENUS["tools"]
            if item.get("command")
        ]
        commands = [item["command"] for item in actions]

        self.assertEqual(commands, [
            "tool_columns_editor",
            "tool_update",
            "tool_create_update",
        ])
        self.assertEqual(TOOL_WINDOWS, {
            "tool_columns_editor": "columns_editor",
            "tool_update": "update",
            "tool_create_update": "create_update",
        })

    def test_tools_menu_only_contains_surfaces_without_another_entrypoint(self):
        commands = [
            item["command"] for item in DEFAULT_MENUS["tools"]
            if item.get("command")
        ]

        main = (QML / "Main.qml").read_text(encoding="utf-8")
        self.assertNotIn("tool_activity_feed", commands)
        self.assertIn(
            'appController.open_window("activity_feed")', main
        )

    def test_application_help_reuses_one_topic_routed_native_window(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        self.assertIn("help", windows)
        self.assertNotIn("script_editor_help", windows)
        self.assertEqual(
            FloatingWindowModel._content_source(windows["help"]),
            "HelpView.qml",
        )
        self.assertTrue((QML / "HelpView.qml").is_file())
        self.assertFalse((QML / "ScriptEditorHelpView.qml").exists())

        help_view = (QML / "HelpView.qml").read_text(encoding="utf-8")
        help_articles = QML.parent / "help_articles"
        dock_panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")
        detached = (QML / "DetachedDockWindow.qml").read_text(
            encoding="utf-8"
        )
        grip = (QML / "controls" / "DockDragGrip.qml").read_text(
            encoding="utf-8"
        )
        script_editor = (QML / "ScriptEditorView.qml").read_text(
            encoding="utf-8"
        )
        for topic in (
            "overview", "shortcuts", "windows", "script_editor",
            "script_triggers",
            "deleting_objects", "errors",
            "dock.results", "dock.snapshot", "dock.tasks", "dock.notes",
            "dock.task_calendar", "dock.timesheet", "dock.work_reports",
            "dock.cost_reports", "dock.drop_plate", "dock.knowledge",
            "dock.advanced_search", "dock.repo_sync_queue",
            "dock.commit_queue", "dock.watch_folders", "dock.db_table",
            "dcc_clients", "handler_server",
        ):
            self.assertTrue((help_articles / f"{topic}.en.md").is_file())
            self.assertTrue((help_articles / f"{topic}.ru.md").is_file())
        self.assertIn("helpController.topics", help_view)
        self.assertIn("TextEdit.MarkdownText", help_view)
        self.assertIn("helpController.open_current_file()", help_view)
        self.assertNotIn("readonly property var topics", help_view)
        self.assertIn('windowModel.open_help("dock." + root.kind)', dock_panel)
        self.assertIn('windowModel.open_help("dock." + root.kind)', detached)
        handler_server = (QML / "HandlerServerView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'windowModel.open_help("dcc_clients")', handler_server
        )
        self.assertIn("signal contextRequested", grip)
        self.assertRegex(
            script_editor,
            r'windowModel\.open_help\(\s*"script_editor"\s*\)',
        )

    def test_error_window_uses_resizable_modal_window_host(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        error_window = windows["error"]
        self.assertEqual(error_window.kind, "error")
        self.assertTrue(error_window.blocking)
        self.assertEqual(
            FloatingWindowModel._content_source(error_window),
            "ErrorDialog.qml",
        )
        self.assertIn(
            "error", FloatingWindowModel._context_required_windows
        )

        content = (QML / "ErrorDialog.qml").read_text(encoding="utf-8")
        floating = (QML / "FloatingWindow.qml").read_text(encoding="utf-8")
        main = (QML / "Main.qml").read_text(encoding="utf-8")
        sizing = (QML / "WindowSizing.qml").read_text(encoding="utf-8")
        self.assertIn("Item {", content)
        self.assertNotIn("FramelessWindowHint", content)
        self.assertNotIn("Window {", content)
        self.assertIn('windowModel.open_help("errors")', content)
        self.assertIn("debugLog.copy_error_stacktrace()", content)
        self.assertIn("bodyFlickable.height", content)
        self.assertNotIn('iconName: "close"', content)
        self.assertIn("Qt.WindowMinMaxButtonsHint", floating)
        self.assertIn("Qt.WindowModal", floating)
        self.assertIn('root.kind === "error"', floating)
        self.assertIn('windowModel.show_window("error")', main)
        self.assertNotIn("    ErrorDialog {", main)
        self.assertIn('"error": 560', sizing)
        self.assertIn('"error": 400', sizing)

    def test_quick_filter_editor_uses_owned_modal_window_host(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        editor_window = windows["quick_filter_editor"]
        self.assertEqual(editor_window.kind, "quick_filter_editor")
        self.assertTrue(editor_window.blocking)
        self.assertEqual(
            FloatingWindowModel._content_source(editor_window),
            "QuickFilterEditorView.qml",
        )
        self.assertIn(
            "quick_filter_editor",
            FloatingWindowModel._context_required_windows,
        )

        search = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        content = (QML / "QuickFilterEditorView.qml").read_text(
            encoding="utf-8"
        )
        host = (QML / "FloatingWindow.qml").read_text(encoding="utf-8")
        sizing = (QML / "WindowSizing.qml").read_text(encoding="utf-8")

        self.assertIn(
            'windowModel.show_window("quick_filter_editor")', search
        )
        self.assertNotIn("QuickFilterEditorDialog", search)
        self.assertFalse((QML / "QuickFilterEditorDialog.qml").exists())
        self.assertIn("Item {", content)
        self.assertNotIn("Overlay.overlay", content)
        self.assertNotIn("Controls.Dialog {", content)
        # Session lifetime belongs to the controller's window-model signal,
        # including a reopen which does not reconstruct the retained QML.
        self.assertNotIn("quickFilterEditorController.begin_session()", host)
        self.assertNotIn("quickFilterEditorController.discard()", host)
        self.assertNotIn("Component.onCompleted:", content)
        self.assertIn('"quick_filter_editor": 620', sizing)
        self.assertIn('"quick_filter_editor": 520', sizing)

    def test_script_editor_reuses_workspace_tabs_and_semantic_icons(self):
        script_editor = (QML / "ScriptEditorView.qml").read_text(
            encoding="utf-8"
        )
        tab_visual = (QML / "controls" / "WorkspaceTabVisual.qml").read_text(
            encoding="utf-8"
        )
        icons = (QML / "controls" / "MaterialIcon.qml").read_text(
            encoding="utf-8"
        )
        icon_loader = (ROOT / "thlib" / "ui" / "icon_font.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("Controls.WorkspaceTabVisual", script_editor)
        self.assertIn("dirty: scriptTab.dirty", script_editor)
        self.assertIn("property bool dirty: false", tab_visual)
        for semantic_icon in (
            "script-python", "script-javascript", "script-expression",
            "script-xml", "scripts-tree", "wrap-lines",
        ):
            self.assertIn('"' + semantic_icon + '":', icons)
        for material_glyph in (
            "language-python", "language-javascript", "wrap", "xml",
        ):
            self.assertIn('"' + material_glyph + '"', icon_loader)

    def test_all_workspace_sobject_deletes_use_dependency_editor(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        self.assertEqual(windows["delete_sobject"].kind, "delete_sobject")
        self.assertTrue(windows["delete_sobject"].blocking)
        self.assertEqual(
            FloatingWindowModel._content_source(windows["delete_sobject"]),
            "DeleteSObjectView.qml",
        )
        item_actions = (
            ROOT / "thlib" / "ui" / "controllers" / "item_operations.py"
        ).read_text(encoding="utf-8")
        snapshot_actions = (
            ROOT / "thlib" / "ui" / "controllers" / "snapshot_actions.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'delete_controller.begin(selected_sources, "items")',
            item_actions,
        )
        self.assertIn(
            'delete_controller.begin([file_object], "snapshot_file")',
            snapshot_actions,
        )
        self.assertNotIn("sobject_delete_confirm", snapshot_actions)
        self.assertFalse((QML / "ConfirmationWindow.qml").exists())

    def test_sobject_duplicate_uses_dependency_aware_wizard(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        duplicate = windows["duplicate_sobject"]
        self.assertEqual(duplicate.kind, "duplicate_sobject")
        self.assertFalse(duplicate.blocking)
        self.assertEqual(
            FloatingWindowModel._content_source(duplicate),
            "DuplicateSObjectView.qml",
        )
        operations = (
            ROOT / "thlib" / "ui" / "controllers"
            / "item_operations.py"
        ).read_text(encoding="utf-8")
        self.assertIn("duplicate_controller.begin(source)", operations)
        self.assertNotIn("confirm_item_action", operations)
        qml = (QML / "DuplicateSObjectView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn('qsTr("Snapshots")', qml)
        self.assertIn('qsTr("Tasks and messages")', qml)
        self.assertIn('"copyProcessAttachments"', qml)
        self.assertIn('"copyTaskAttachments"', qml)

    def test_messages_deferred_presentation_dies_with_its_view(self):
        source = (QML / "MessagesView.qml").read_text(encoding="utf-8")
        self.assertNotIn("Qt.callLater", source)
        for timer_id in (
            "deferredReadStateTimer", "initialPresentationTimer",
            "finishPresentationTimer", "positionCachedAtLatestTimer",
            "focusMessageTimer", "focusComposerTimer",
            "settleAtLatestTimer", "scrollToLatestTimer",
        ):
            self.assertNotIn("id: " + timer_id, source)
        self.assertNotIn("id: messageSettleTimer", source)

    def test_production_ui_has_no_zero_delay_timer_dispatch(self):
        python_offenders = []
        python_roots = (
            ROOT / "thlib" / "ui",
            ROOT / "handler_server",
            ROOT / "tactic_handler_dcc",
            ROOT / "development_extensions",
            ROOT / "examples",
        )
        for python_root in python_roots:
            if not python_root.exists():
                continue
            for path in python_root.rglob("*.py"):
                source = path.read_text(encoding="utf-8")
                if re.search(r"QTimer\.singleShot\(\s*0\b", source):
                    python_offenders.append(str(path.relative_to(ROOT)))
                elif (
                    python_root == ROOT / "thlib" / "ui"
                    and re.search(r"\.start\(\s*0\s*\)", source)
                ):
                    python_offenders.append(str(path.relative_to(ROOT)))
                elif (
                    python_root == ROOT / "thlib" / "ui"
                    and re.search(r"\._schedule\(\s*0\s*\)", source)
                ):
                    python_offenders.append(str(path.relative_to(ROOT)))
        qml_offenders = []
        for path in QML.rglob("*.qml"):
            source = path.read_text(encoding="utf-8")
            if re.search(r"\binterval\s*:\s*0\b", source):
                qml_offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(python_offenders, [])
        self.assertEqual(qml_offenders, [])

        combo = (QML / "controls" / "ComboBox.qml").read_text(
            encoding="utf-8"
        )
        dock_panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")
        handler = (
            ROOT / "thlib" / "ui" / "handler_server_controller.py"
        ).read_text(encoding="utf-8")
        for timer_id in (
            "keyboardFocusRestoreTimer", "keyboardOpenTimer",
            "keyboardActivationGuard", "initialGeometryTimer",
        ):
            self.assertNotIn(timer_id, combo + dock_panel)
        self.assertNotIn("_drain_timer", handler)

    def test_sidebar_search_editor_reuses_advanced_search_in_native_preview(self):
        windows = {window.window_id: window for window in FloatingWindowModel._defaults()}
        preview = windows["sidebar_search_preview"]
        self.assertTrue(preview.blocking)
        self.assertEqual(FloatingWindowModel._content_source(preview), "SidebarSearchPreview.qml")
        self.assertNotIn("sidebar_advanced_search", windows)
        source = (QML / "SidebarSearchPreview.qml").read_text(encoding="utf-8")
        self.assertIn("AdvancedSearchView {", source)
        self.assertIn("SearchQuickFilterPopup {", source)
        self.assertIn("SearchResultsPane {", source)
        self.assertIn("sidebarEditorController.previewSurfaces", source)

    def test_saved_searches_and_process_visibility_are_separate_tools(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        self.assertNotIn("filter_editor", windows)
        self.assertEqual(
            FloatingWindowModel._content_source(
                windows["process_filter_editor"]
            ),
            "ProcessFilterEditorView.qml",
        )
        self.assertFalse((QML / "FilterEditorView.qml").exists())
        advanced_search = (QML / "AdvancedSearchView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("filterPresetModel", advanced_search)
        preset_bar = (QML / "SearchPresetBar.qml").read_text(encoding="utf-8")
        self.assertIn("SearchPresetBar {", advanced_search)
        self.assertIn("save_current_search_as", preset_bar)
        self.assertIn("copy_selected_search_link", preset_bar)
        self.assertIn("detach_generated_search_filter", advanced_search)

    def test_process_filter_window_keeps_legacy_compact_density(self):
        source = (QML / "ProcessFilterEditorView.qml").read_text(
            encoding="utf-8"
        )
        sync_source = (QML / "RepositorySyncEditorView.qml").read_text(
            encoding="utf-8"
        )
        tree_source = (
            QML / "controls" / "ProcessSelectionTree.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("Layout.preferredHeight: 42", source)
        self.assertIn("Controls.ProcessSelectionTree", source)
        self.assertIn("Controls.ProcessSelectionTree", sync_source)
        self.assertNotIn("Controls.SmoothListView", source)
        self.assertNotIn("Controls.SmoothListView", sync_source)
        self.assertIn("columns: root.width < 720 ? 1 : 2", tree_source)
        self.assertIn("Layout.columnSpan: toggleGrid.columns", tree_source)
        self.assertNotIn("compact: root.compact", source)
        self.assertIn("height: rowVisible ? 30 : 0", tree_source)
        self.assertIn("root.theme.surfaceContainerHigh", tree_source)
        self.assertIn("Qt.ShiftModifier", tree_source)
        self.assertIn('qsTr("Show Togglers")', tree_source)
        self.assertIn('qsTr(" (child)")', tree_source)
        self.assertIn('qsTr(" (builtin)")', tree_source)
        self.assertNotIn('showTreeIcons', tree_source)
        self.assertNotIn('showTreeIcons', sync_source)
        self.assertIn('"process-marker"', tree_source)
        self.assertIn('forceSolid: treeRow.kind === "process"', tree_source)
        self.assertIn(
            'anchors.leftMargin: 5 + treeRow.depth * 18', tree_source
        )
        self.assertIn("Layout.preferredHeight: 48", source)
        self.assertIn('qsTr("Pipeline for:")', source)

        window = next(
            item for item in FloatingWindowModel._defaults()
            if item.window_id == "process_filter_editor"
        )
        self.assertEqual((window.width, window.height), (.26, .50))

        sizing = (QML / "WindowSizing.qml").read_text(encoding="utf-8")
        self.assertEqual(sizing.count('"process_filter_editor": 440'), 1)
        self.assertEqual(sizing.count('"process_filter_editor": 360'), 1)

    def test_result_tools_and_saved_search_picker_live_with_search_tabs(self):
        source = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        header = source[
            source.index("id: searchHeader"):source.index("id: searchTabs")
        ]
        tabs = source[
            source.index("id: searchTabs"):source.index("id: resultsToolbar")
        ]
        self.assertLess(
            header.index("id: searchRefresh"),
            header.index("id: searchField"),
        )
        self.assertNotIn("id: searchRefresh", tabs)
        for control in (
            "id: resultSortButton", "id: resultGroupButton",
            "id: resultsViewButton",
        ):
            self.assertNotIn(control, header)
            self.assertIn(control, tabs)

        self.assertIn('iconName: "advanced-search"', tabs)
        menus = (QML / "SearchResultMenus.qml").read_text(encoding="utf-8")
        self.assertIn("SearchResultMenus {", source)
        self.assertIn("resultFilterMenuActions()", menus)
        self.assertIn('command": "preset:" + row', menus)

        view_button = tabs[
            tabs.index("id: resultsViewButton"):
            tabs.index("id: searchTabActionsOverflowButton")
        ]
        self.assertIn(
            "root.resultViewIcon(", view_button
        )
        self.assertNotIn("root.compactRows", view_button)
        for control in (
            "id: resultSortButton", "id: resultGroupButton",
            "id: resultsViewButton",
        ):
            control_block = tabs[
                tabs.index(control):tabs.index(control) + 420
            ]
            self.assertIn(
                "visible: !root.compactTabActions",
                control_block,
            )
        overflow_index = tabs.index("id: searchTabActionsOverflowButton")
        history_index = tabs.index("id: tabHistoryControl")
        self.assertLess(overflow_index, history_index)
        self.assertGreater(
            history_index, tabs.index("id: resultsViewButton")
        )
        overflow_block = tabs[overflow_index:history_index]
        self.assertIn(
            "visible: root.compactTabActions", overflow_block
        )
        self.assertIn(
            "readonly property bool compactTabActions: width < 720",
            source,
        )
        self.assertIn('if (mode === "tiles")', source)
        self.assertIn('return "dashboard"', source)
        self.assertIn("id: searchTabActionsMenu", source)
        self.assertIn(
            "resultsViewMenu.openBelow(", source
        )

        tag_block = header[
            header.index("id: tagCloudButton"):
            header.index("id: quickFilterButton")
        ]
        quick_filter_block = header[
            header.index("id: quickFilterButton"):
            header.index("id: searchGear")
        ]
        self.assertIn("visible: true", tag_block)
        self.assertIn("visible: true", quick_filter_block)
        self.assertNotIn("id: searchOverflowButton", header)
        self.assertNotIn("id: searchOverflowMenu", source)

    def test_tag_popup_has_a_bounded_scrollable_viewport(self):
        source = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("TagCloudPopup {", source)
        popup = (QML / "TagCloudPopup.qml").read_text(encoding="utf-8")
        self.assertIn(
            "fixedSurfaceHeight: root.theme.controlHeight * 8", popup
        )
        self.assertIn("Controls.ScrollablePopup", popup)
        scrollable = (
            QML / "controls" / "ScrollablePopup.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('objectName: "scrollablePopupViewport"', scrollable)
        self.assertIn("ScrollBar.vertical: Controls.ScrollBar", scrollable)
        self.assertIn("scrollBarReserve", scrollable)

    def test_search_filter_popups_expose_contextual_reset_actions(self):
        quick_popup = (QML / "SearchQuickFilterPopup.qml").read_text(
            encoding="utf-8"
        )
        tag_popup = (QML / "TagCloudPopup.qml").read_text(encoding="utf-8")

        self.assertIn('objectName: "resetSearchQuickFiltersButton"', quick_popup)
        self.assertIn(
            "root.controller.active_quick_filter_count > 0", quick_popup
        )
        self.assertIn(
            "onClicked: root.controller.clear_quick_filters()", quick_popup
        )
        self.assertIn(
            'objectName: "restoreStandardQuickFiltersButton"', quick_popup
        )
        self.assertIn(
            "root.controller.reset_quick_filters_to_standard()", quick_popup
        )
        self.assertIn('objectName: "resetSearchTagsButton"', tag_popup)
        self.assertIn("root.controller.active_tag_count > 0", tag_popup)
        self.assertIn(
            'onClicked: root.controller.toggle_tag("")', tag_popup
        )

    def test_quick_filter_popups_share_the_bounded_surface(self):
        search_popup = (QML / "SearchQuickFilterPopup.qml").read_text(
            encoding="utf-8"
        )
        task_popup = (QML / "TaskQuickFilterPopup.qml").read_text(
            encoding="utf-8"
        )

        for source in (search_popup, task_popup):
            self.assertIn("preferredSurfaceWidth: 440", source)
            self.assertIn("maximumSurfaceHeight: 400", source)
            self.assertNotIn("contentItem: Flickable", source)

    def test_narrow_paginated_search_footer_keeps_primary_actions_inside(self):
        source = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        footer = source[
            source.index("id: resultsToolbar"):
            source.index("id: resultsArea")
        ]

        self.assertIn("property bool narrow: width < 520", footer)
        self.assertIn("property bool ultraNarrow: width < 340", footer)
        self.assertIn(
            "spacing: resultsToolbar.narrow ? 4 : 8", footer
        )
        self.assertIn(
            "text: resultsToolbar.narrow\n"
            "                        ? String(appController.result_count)",
            footer,
        )
        self.assertIn('objectName: "searchCreateItemButton"', footer)
        self.assertIn("Layout.maximumWidth: 40", footer)
        self.assertIn(
            "Layout.maximumWidth: resultsToolbar.compact ? 40 : 160",
            footer,
        )
        page_size = footer[
            footer.index("id: pageSizeButton"):
            footer.index("id: loadModeButton")
        ]
        self.assertIn("pageSizeContent.implicitWidth + 23", page_size)
        self.assertIn(
            "Layout.minimumWidth: Layout.preferredWidth", page_size
        )
        self.assertIn("id: pageSizeLabel", page_size)
        self.assertIn("Layout.minimumWidth: implicitWidth", page_size)
        self.assertIn("Layout.minimumWidth: 16", page_size)

    def test_sidebar_editor_and_drawer_share_the_same_tree_row(self):
        drawer_source = (QML / "NavigationDrawer.qml").read_text(
            encoding="utf-8"
        )
        for name in ("NavigationDrawer.qml", "SidebarEditorView.qml"):
            source = (QML / name).read_text(encoding="utf-8")
            self.assertIn("SidebarTreeRow {", source)

        shared_row = (QML / "SidebarTreeRow.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ItemPreview {", shared_row)
        self.assertIn("Controls.MaterialRipple {", shared_row)
        self.assertIn("id: rowActivation", shared_row)
        self.assertIn("rowHover.hovered", shared_row)
        self.assertNotIn("rowMouse", shared_row)
        self.assertIn("Controls.SmoothListView {", drawer_source)
        self.assertIn("onWheel: wheel => wheel.accepted = true", drawer_source)

    def test_dock_content_registry_only_routes_feature_views(self):
        registry = (QML / "DockContentRegistry.qml").read_text(
            encoding="utf-8"
        )
        self.assertLess(len(registry.splitlines()), 600)
        self.assertIn("SearchWorkspaceView {", registry)
        self.assertNotIn("id: searchHeader", registry)
        self.assertNotIn("id: resultsArea", registry)
        self.assertNotIn("legacyRepoSyncContent", registry)
        search = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("id: searchHeader", search)
        self.assertIn("id: resultsArea", search)

    def test_search_results_keep_their_model_and_viewport_between_tabs(self):
        search = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        surface = (QML / "SearchResultSurface.qml").read_text(
            encoding="utf-8"
        )
        dock_panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")

        self.assertIn("surfacesModel: workspaceResultSurfacesModel", search)
        pane = (QML / "SearchResultsPane.qml").read_text(encoding="utf-8")
        self.assertIn("model: root.surfacesModel", pane)
        self.assertGreaterEqual(surface.count("model: root.resultModel"), 2)
        self.assertNotIn(
            "model: visible ? root.resultModel : null", surface
        )
        self.assertIn("onResult_viewport_capture_requested", search)
        self.assertIn("onResult_viewport_restore_requested", search)
        self.assertNotIn("restoredSelectionTimer", search)
        self.assertIn("animateSelection: false", search)
        self.assertNotIn("Behavior on width", search)
        self.assertIn("Behavior on scale", search)
        self.assertIn("searchTabsView.dragSourceIndex >= 0", search)
        self.assertIn("opacity: modelVisible ? 1 : 0", dock_panel)
    def test_dock_host_only_owns_layout_and_routes_content(self):
        host = (QML / "DockHost.qml").read_text(encoding="utf-8")
        panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")
        self.assertLess(len(host.splitlines()), 600)
        self.assertIn("DockContentRegistry", host)
        self.assertNotIn("TaskDockView", host)
        self.assertNotIn("CommunicationView", host)
        self.assertIn("model: visibleDockModel", host)
        self.assertIn("model: detachedDockModel", host)
        self.assertIn("&& dockDelegate.stackActive", host)
        self.assertIn(
            "Component.onCompleted: Qt.callLater(root.ensureDockMinimumSizes)",
            host,
        )
        self.assertIn("function onPanelVisibilityChanged()", host)
        self.assertNotIn(
            "onVisibleChanged: if (visible) dockModel.raise_panel(panelId)",
            panel,
        )
        self.assertIn(
            "onPressed: dockModel.raise_panel(root.panelId)", panel
        )

        window_host = (QML / "WindowHost.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("model: visibleWindowModel", window_host)
        self.assertNotIn("model: windowModel", window_host)

    def test_knowledge_dock_and_workspace_menu_share_book_icon(self):
        panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")
        menu = (QML / "DockMenu.qml").read_text(encoding="utf-8")
        help_view = (QML / "HelpView.qml").read_text(encoding="utf-8")
        knowledge_help = (
            QML.parent / "help_articles" / "dock.knowledge.en.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'panelKind === "knowledge" ? "book-open"', panel
        )
        self.assertIn('kind === "knowledge" ? "book-open"', menu)
        self.assertIn("helpController.article", help_view)
        self.assertIn("icon: book-open", knowledge_help)

    def test_shared_effects_are_not_instantiated_while_idle(self):
        controls = QML / "controls"
        button = (controls / "CompactIconButton.qml").read_text(
            encoding="utf-8"
        )
        ripple = (controls / "MaterialRipple.qml").read_text(
            encoding="utf-8"
        )
        tooltip = (controls / "ToolTip.qml").read_text(encoding="utf-8")
        popup = (controls / "PopupBackground.qml").read_text(encoding="utf-8")

        self.assertIn("active: root.elevated", button)
        self.assertIn("active: root.pointerHovered", button)
        self.assertNotIn("visible: root.elevated", button)
        self.assertIn("active: root.rendering", ripple)
        self.assertNotIn("active: root.rendering\n            &&", ripple)
        self.assertIn(
            "layer.enabled: visible && root.shapeRadius > 0",
            ripple,
        )
        self.assertNotIn("ScriptAction", ripple)
        self.assertIn("Qt.callLater(function()", ripple)
        self.assertIn("active: visible", tooltip)
        self.assertIn("active: popup.visible", popup)

    def test_compact_icon_button_routes_activation_once(self):
        button = (QML / "controls" / "CompactIconButton.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Controls.ActivationHandler", button)
        self.assertIn("onActivated: modifiers => root.activate(modifiers)", button)
        self.assertIn("root.clickedWithModifiers(modifiers)", button)
        self.assertNotIn("onClicked: {\n", button)

    def test_shared_touch_activation_is_release_based_and_deduplicated(self):
        controls = QML / "controls"
        handler = (controls / "ActivationHandler.qml").read_text(
            encoding="utf-8"
        )
        qmldir = (controls / "qmldir").read_text(encoding="utf-8")

        self.assertIn(
            "ActivationHandler 1.0 ActivationHandler.qml", qmldir
        )
        self.assertIn(
            "gesturePolicy: TapHandler.DragThreshold", handler
        )
        self.assertIn(
            "acceptedDevices: PointerDevice.TouchScreen", handler
        )
        self.assertIn("acceptedButtons: Qt.LeftButton", handler)
        self.assertNotIn("acceptedButtons: Qt.NoButton", handler)
        self.assertIn("duplicateWindow: 180", handler)
        self.assertIn("now - root.lastActivationAt", handler)

        for relative in (
            "controls/CompactIconButton.qml",
            "controls/FilledActionButton.qml",
            "controls/PreviewNavigationButton.qml",
            "controls/StatusChip.qml",
            "MessageReactionChip.qml",
            "SidebarTreeRow.qml",
            "AttachmentCard.qml",
            "ColumnsEditorView.qml",
            "SearchWorkspaceView.qml",
            "DockPanel.qml",
            "MessageForwardPreview.qml",
            "MessageReplyPreview.qml",
            "MessagesView.qml",
            "ServerPresetsView.qml",
            "SKeyPreviewCard.qml",
            "SObjectSnapshotTree.qml",
            "SObjectInfoView.qml",
            "TaskWorkspaceSummary.qml",
            "WatchFoldersView.qml",
            "controls/InfoValueStrip.qml",
            "ActivityEventCard.qml",
            "AdvancedSearchView.qml",
            "MatchingTemplatesView.qml",
            "NotificationStack.qml",
            "TaskBrowserTable.qml",
            "TaskGanttView.qml",
            "TaskTableEditorCell.qml",
        ):
            source = (QML / relative).read_text(encoding="utf-8")
            self.assertIn("ActivationHandler", source, relative)

        quick_filter_chip = (QML / "QuickFilterChip.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Controls.PopupAction", quick_filter_chip)
        self.assertNotIn("ActivationHandler", quick_filter_chip)

    def test_text_area_consumers_do_not_mix_font_size_units(self):
        for name in (
            "DescriptionEditor.qml",
            "MessageComposerField.qml",
        ):
            source = (QML / name).read_text(encoding="utf-8")
            self.assertNotIn("font.pixelSize", source, name)

    def test_hidden_editors_defer_model_generation_until_opened(self):
        columns = (ROOT / "thlib" / "ui" / "columns_editor.py").read_text(
            encoding="utf-8"
        )
        columns_init = columns.split("def __init__", 1)[1].split(
            "def _reload_if_in_use", 1
        )[0]
        presets = (ROOT / "thlib" / "ui" / "editor_tools.py").read_text(
            encoding="utf-8"
        )
        presets_init = presets.split("def __init__", 1)[1].split(
            "@Property", 1
        )[0]

        self.assertNotIn("self.reload()", columns_init)
        self.assertIn("self._reload_if_in_use", columns_init)
        self.assertNotIn("self.reload()", presets_init)
        self.assertIn(
            "columnsEditorController.begin_session()",
            (QML / "ColumnsEditorView.qml").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "serverPresetsController.begin_session()",
            (QML / "ServerPresetsView.qml").read_text(encoding="utf-8"),
        )

    def test_retained_dock_views_suspend_hidden_presentation_work(self):
        advanced = (QML / "AdvancedSearchView.qml").read_text(
            encoding="utf-8"
        )
        results = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        notes = (QML / "CommunicationView.qml").read_text(
            encoding="utf-8"
        )

        for source in (advanced, results, notes):
            self.assertIn(
                "parent ? parent.visible : visible", source
            )
        self.assertIn("enabled: root.presentationActive", advanced)
        self.assertIn("enabled: root.presentationActive", notes)
        self.assertNotIn("if (!root.visible)", advanced)

    def test_commit_queue_dock_uses_its_own_header(self):
        source = (QML / "DockPanel.qml").read_text(encoding="utf-8")
        self.assertIn(
            'kind === "results" || kind === "commit_queue"', source
        )
        self.assertIn(
            "height: root.headerlessSinglePanel ? 0", source
        )
        host = (QML / "DockHost.qml").read_text(encoding="utf-8")
        self.assertIn(
            'target.kind !== "commit_queue"', host)

    def test_infinite_results_only_append_after_user_scroll(self):
        workspace = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        results = (QML / "SearchResultSurface.qml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("function onSearch_state_changed", results)
        self.assertNotIn("onAtYEndChanged", results)
        self.assertNotIn("property bool infiniteScrollArmed", results)
        self.assertEqual(results.count("takePaginationPermit(false)"), 2)
        self.assertIn("SearchResultsPane {", workspace)
        pane = (QML / "SearchResultsPane.qml").read_text(encoding="utf-8")
        self.assertIn("visible: root.controller.loading_more", pane)

    def test_main_top_bar_is_fixed_and_compact(self):
        source = (QML / "Main.qml").read_text(encoding="utf-8")
        top_bar = source.split("id: topAppBar", 1)[1].split(
            "id: workspaceLayer", 1
        )[0]
        self.assertIn("height: 44", top_bar)
        self.assertIn("controlExtent: 36", top_bar)
        self.assertIn("controlSurfaceExtent: 32", top_bar)
        self.assertIn("height: topAppBar.height", top_bar)
        self.assertNotIn("expansionProgress", top_bar)
        self.assertNotIn("topAppBarHover", top_bar)
        self.assertNotIn("topAppBarCollapseTimer", top_bar)
        self.assertIn("z: 100", top_bar)

    def test_main_window_minimum_follows_the_visible_dock_tree(self):
        source = (QML / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('sizing.windowMinimumWidth("main")', source)
        self.assertIn("dockModel.minimumHostWidth + sectionRail.width", source)
        self.assertIn('sizing.windowMinimumHeight("main")', source)
        self.assertIn("dockModel.minimumHostHeight + topAppBar.height", source)
        sizing = (QML / "WindowSizing.qml").read_text(encoding="utf-8")
        self.assertIn('"main": 560', sizing)
        self.assertIn('"main": 480', sizing)

    def test_main_window_clamps_native_geometry_before_persistence(self):
        source = (QML / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("function clampToAvailableScreen()", source)
        self.assertIn("appController.clamp_main_window_geometry(", source)
        completed = source.split("Component.onCompleted:", 1)[1].split(
            "onClosing:", 1
        )[0]
        self.assertIn("!qmlSmokeMode", completed)
        self.assertLess(
            completed.index("window.clampToAvailableScreen()"),
            completed.index("window.windowStateReady = true"),
        )

    def test_notifications_use_an_independent_custom_toast_window(self):
        main = (QML / "Main.qml").read_text(encoding="utf-8")
        toast = (QML / "NotificationToastWindow.qml").read_text(
            encoding="utf-8"
        )
        tray = (ROOT / "thlib" / "ui" / "tray.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("NotificationToastWindow {", main)
        self.assertNotIn("NotificationStack {", main)
        self.assertIn("NotificationStack {", toast)
        self.assertNotIn("showMessage(", tray)

    def test_search_chrome_keeps_search_above_tabs(self):
        source = (QML / "SearchWorkspaceView.qml").read_text(
            encoding="utf-8"
        )
        header_index = source.index("id: searchHeader")
        shelf_index = source.index("id: scriptShelfLoader", header_index)
        tabs_index = source.index("id: searchTabs", shelf_index)
        toolbar_index = source.index("id: resultsToolbar", tabs_index)
        results_index = source.index("id: resultsArea", tabs_index)
        self.assertLess(header_index, tabs_index)
        self.assertLess(header_index, shelf_index)
        self.assertLess(shelf_index, tabs_index)
        self.assertLess(tabs_index, toolbar_index)
        self.assertLess(toolbar_index, results_index)

        header = source[header_index:tabs_index]
        tabs = source[tabs_index:results_index]
        self.assertIn("anchors.top: parent.top", header)
        self.assertIn(
            "height: root.theme.dockWorkspaceHeaderHeight / 2",
            header,
        )
        self.assertIn(
            "radius: Math.max(0, root.theme.surfaceRadius - 1)",
            header,
        )
        shelf = source[shelf_index:tabs_index]
        self.assertIn("anchors.top: searchHeader.bottom", shelf)
        self.assertIn("anchors.top: scriptShelfLoader.bottom", tabs)
        self.assertIn(
            "height: root.theme.dockWorkspaceHeaderHeight / 2",
            tabs,
        )
        self.assertIn("id: searchTabsView", tabs)
        self.assertIn("id: addSearchTabButton", tabs)
        self.assertLess(
            tabs.index("id: addSearchTabButton"),
            tabs.index("id: searchTabsView"),
        )
        toolbar = source[max(0, toolbar_index - 80):results_index]
        self.assertIn(
            "Controls.DockWorkspaceFooter {",
            toolbar,
        )
        footer_control = (
            QML / "controls" / "DockWorkspaceFooter.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("readonly property real cornerRadius: Math.max(", footer_control)
        self.assertIn("radius: cornerRadius", footer_control)

    def test_project_qml_uses_shared_controls_for_common_primitives(self):
        forbidden = re.compile(
            r"^\s*(?:Button|TextField|TextArea|Dialog|Popup|BusyIndicator)\s*\{",
            re.MULTILINE,
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if forbidden.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_knowledge_base_uses_the_shared_dock_footer_surface(self):
        knowledge = (QML / "KnowledgeBaseView.qml").read_text(
            encoding="utf-8"
        )
        dock_panel = (QML / "DockPanel.qml").read_text(encoding="utf-8")

        self.assertIn("Controls.DockWorkspaceFooter {", knowledge)
        self.assertIn('objectName: "knowledgeDockSurface"', knowledge)
        self.assertIn("topDividerVisible: false", knowledge)
        self.assertNotIn('kind === "knowledge"', dock_panel)

        proxy_names = {
            "Button.qml", "BusyIndicator.qml", "TextField.qml",
            "TextArea.qml", "CheckBox.qml", "Switch.qml", "TabButton.qml",
            "SegmentedButton.qml", "DateField.qml", "Dialog.qml",
            "DialogActions.qml", "Popup.qml", "ComboBox.qml",
            "ScrollBar.qml", "Slider.qml", "SpinBox.qml", "ToolTip.qml",
            "FilledActionButton.qml", "CompactIconButton.qml",
            "DockDragGrip.qml", "ItemCountActionButton.qml", "StatusChip.qml",
            "PreviewNavigationButton.qml", "MaterialIcon.qml",
            "MaterialRipple.qml", "SmoothListView.qml",
            "WorkspaceTabVisual.qml",
        }
        self.assertEqual(
            sorted(path.name for path in QML.glob("*.qml")
                   if path.name in proxy_names),
            [],
        )
        for path in QML.rglob("*.qml"):
            self.assertNotRegex(
                path.read_text(encoding="utf-8"),
                r"\bMd3[A-Z][A-Za-z0-9]*\b",
                str(path.relative_to(ROOT)),
            )

    def test_qml_architecture_contract_is_canonical(self):
        policy = ROOT / "docs" / "ui_component_policy.md"
        self.assertTrue(policy.is_file())
        text = policy.read_text(encoding="utf-8")
        for section in (
            "## Component layers",
            "## Shared-control gate",
            "## Responsive layout",
            "## View size and responsibility budget",
            "## Review checklist",
        ):
            self.assertIn(section, text)
        self.assertIn(
            "docs/ui_component_policy.md",
            (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "docs/ui_component_policy.md",
            (ROOT / "thlib" / "ui" / "AGENTS.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_qml_component_map_is_documented(self):
        component_map = ROOT / "docs" / "ui_component_map.md"
        self.assertTrue(component_map.is_file())
        self.assertIn(
            "ui_component_map.md",
            (ROOT / "docs" / "index.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "## Decision order",
            component_map.read_text(encoding="utf-8"),
        )
    def test_feature_qml_motion_uses_theme_tokens(self):
        numeric_duration = re.compile(r"\bduration\s*:\s*\d+")
        self.assertIsNotNone(
            numeric_duration.search("NumberAnimation { duration: 120 }")
        )
        self.assertIsNone(
            numeric_duration.search(
                "NumberAnimation { duration: theme.motionFast }"
            )
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if numeric_duration.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

        theme = (QML / "Theme.qml").read_text(encoding="utf-8")
        for token in (
            "motionInstant", "motionFast", "motionMedium",
            "motionSlow", "motionExtended", "clickMotionFast",
            "clickMotionMedium", "hoverMotionFast", "hoverMotionMedium",
        ):
            self.assertIn("readonly property int " + token, theme)

    def test_shared_controls_do_not_import_feature_qml(self):
        reverse_import = re.compile(
            r'^\s*import\s+"\.\."\s+as\s+',
            re.MULTILINE,
        )
        self.assertIsNotNone(
            reverse_import.search('import ".." as Feature')
        )
        offenders = []
        for path in (QML / "controls").glob("*.qml"):
            if reverse_import.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_item_preview_is_a_shared_control(self):
        self.assertFalse((QML / "ItemPreview.qml").exists())
        self.assertTrue((QML / "controls" / "ItemPreview.qml").is_file())
        qmldir = (QML / "controls" / "qmldir").read_text(encoding="utf-8")
        self.assertIn("ItemPreview 1.0 ItemPreview.qml", qmldir)
        unqualified = re.compile(r"(?<!Controls\.)\bItemPreview\s*\{")
        self.assertIsNotNone(unqualified.search("ItemPreview {"))
        self.assertIsNone(unqualified.search("Controls.ItemPreview {"))
        offenders = []
        for path in QML.glob("*.qml"):
            if unqualified.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])
    def test_qmldir_entries_resolve_and_shared_foundations_are_unique(self):
        for directory in (QML, QML / "controls"):
            qmldir = directory / "qmldir"
            for raw_line in qmldir.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith("module "):
                    continue
                source_name = line.split()[-1]
                if source_name.endswith(".qml"):
                    self.assertTrue(
                        (directory / source_name).is_file(),
                        str(directory / source_name),
                    )

        shared = (
            "Typography.qml", "ItemPreview.qml", "ItemSurface.qml",
            "ResponsiveFlow.qml", "ProfileInfoRow.qml", "EmptyState.qml",
        )
        controls = QML / "controls"
        for name in shared:
            self.assertTrue((controls / name).is_file(), name)
            self.assertFalse((QML / name).exists(), name)

        unqualified_typography = re.compile(
            r"(?<!Controls\.)\bTypography\."
        )
        offenders = []
        self.assertIsNotNone(
            unqualified_typography.search("Typography.body")
        )
        self.assertIsNone(
            unqualified_typography.search("Controls.Typography.body")
        )
        for path in QML.glob("*.qml"):
            if unqualified_typography.search(
                path.read_text(encoding="utf-8")
            ):
                offenders.append(path.name)
        self.assertEqual(offenders, [])
    def test_inline_busy_indicators_receive_the_active_theme(self):
        pattern = re.compile(
            r"Controls\.BusyIndicator\s*\{([^{}]|\{[^{}]*\})*\}",
            re.DOTALL,
        )
        offenders = []
        for path in QML.glob("*.qml"):
            for block in pattern.finditer(path.read_text(encoding="utf-8")):
                if "uiTheme:" not in block.group(0):
                    offenders.append(path.name)
                    break
                if "running:" not in block.group(0):
                    offenders.append(path.name)
                    break
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
