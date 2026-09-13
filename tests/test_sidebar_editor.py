from xml.etree import ElementTree

from thlib.ui.sidebar_editor import (
    _LINK_CLASS,
    _SECTION_CLASS,
    SidebarEditorController,
    _all_elements,
    _children,
    _direct_text,
    _display_class,
    _display_option,
    _parse_document,
    _result_view_mode,
    _serialize,
    _set_direct_text,
    _set_display_class,
    _sidebar_rule_allowed,
    _slug,
    _widget_type,
)
from thlib.ui.sidebar_icons import (
    icon_name_for_tactic,
    icon_name_from_tactic,
)
from thlib.ui.models import NavigationModel


def test_sidebar_icon_names_round_trip_through_tactic_format():
    assert icon_name_for_tactic("project-diagram") == "FAS_PROJECT_DIAGRAM"
    assert icon_name_for_tactic("FAS_PROJECT_DIAGRAM") == "FAS_PROJECT_DIAGRAM"
    assert icon_name_from_tactic("FAS_PROJECT_DIAGRAM") == "project-diagram"
    assert icon_name_from_tactic("custom-project-icon") == "custom-project-icon"


def test_sidebar_icon_selection_stores_tactic_name_and_exposes_clean_glyph():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Application:
        _registry = Registry()
        navigation_model = NavigationModel()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [{
        "search_type": "SideBarWdg",
        "view": "definition",
        "config": (
            "<config><element name='assets' title='Assets' "
            "icon='FAS_BOX'><display class='LinkWdg'/>"
            "</element></config>"
        ),
    }, {
        "search_type": "SideBarWdg",
        "view": "project_view",
        "config": "<config><element name='assets'/></config>",
    }]))
    controller.select_entry(0)

    controller.update_selected("icon", "project-diagram")

    assert controller.selectedEntry["icon"] == "FAS_PROJECT_DIAGRAM"
    assert controller.selectedEntry["glyph"] == "project-diagram"
    assert "icon=\"FAS_PROJECT_DIAGRAM\"" in controller.xmlText


def test_sidebar_fragment_uses_native_config_wrapper():
    root = _parse_document(
        '<element name="assets" title="Assets">'
        '<display class="LinkWdg"/>'
        '<search_type>demo/assets</search_type>'
        '</element>'
    )

    items = _children(root)
    assert root.tag == "config"
    assert len(items) == 1
    assert items[0].get("name") == "assets"
    assert _display_class(items[0]) == _LINK_CLASS
    assert _direct_text(items[0], "search_type") == "demo/assets"


def test_sidebar_edit_helpers_preserve_native_xml_shape():
    element = ElementTree.Element("element", {"name": "shots"})
    _set_display_class(element, _SECTION_CLASS)
    _set_direct_text(element, "view", "shot_links")

    document = ElementTree.Element("config")
    document.append(element)
    restored = _parse_document(_serialize(document))
    restored_element = _children(restored)[0]

    assert _display_class(restored_element) == _SECTION_CLASS
    assert _direct_text(restored_element, "view") == "shot_links"
    assert restored_element.find("./display/view") is not None


def test_sidebar_empty_child_value_removes_node():
    element = ElementTree.fromstring(
        "<element><search_view>archive</search_view></element>"
    )
    _set_direct_text(element, "search_view", "")

    assert element.find("./search_view") is None


def test_sidebar_names_are_stable_codes():
    assert _slug("My Assets / Ready") == "my_assets_ready"
    assert _slug("", "sidebar_section") == "sidebar_section"


def test_sidebar_session_starts_with_handler_branch_filter_enabled():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Application:
        _registry = Registry()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    reloads = []
    controller.reload = lambda: reloads.append(True)

    controller.begin_session()

    assert controller.handlerOnly is True
    assert reloads == [True]




def test_nested_view_elements_match_native_views_config_behavior():
    root = _parse_document(
        "<config><view><element name='assets'/></view></config>"
    )

    assert [item.get("name") for item in _all_elements(root)] == ["assets"]


def test_tactic_handler_references_resolve_through_definition():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded((
        "demo", "Demo", object(), [
            {
                "search_type": "SideBarWdg",
                "view": "definition",
                "config": (
                    "<config><element name='assets' title='My Assets' "
                    "icon='cube'><display class='LinkWdg'/>"
                    "<search_type>demo/assets</search_type></element></config>"
                ),
            },
            {
                "search_type": "SideBarWdg",
                "view": "tactic_handler",
                "config": (
                    "<config><view><element name='assets'/></view></config>"
                ),
            },
        ],
    ))

    assert len(controller.entries._records) == 1
    assert controller.entries._records[0]["title"] == "My Assets"
    assert controller.entries._records[0]["searchType"] == "demo/assets"

    controller.select_entry(0)
    controller.update_selected("title", "Assets Dashboard")
    assert controller.selectedRow == 0
    assert controller.entries._records[0]["title"] == "Assets Dashboard"
    assert (
        _all_elements(controller._documents["tactic_handler"])[0].attrib
        == {"name": "assets"}
    )


def test_sidebar_editor_uses_project_view_as_complete_native_tree():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded((
        "demo", "Demo", object(), [
            {
                "search_type": "SideBarWdg",
                "view": "definition",
                "config": (
                    "<config>"
                    "<element name='assets' title='Assets'>"
                    "<display class='LinkWdg'/></element>"
                    "<element name='episodes' title='Episodes'>"
                    "<display class='LinkWdg'/></element>"
                    "</config>"
                ),
            },
            {
                "search_type": "SideBarWdg",
                "view": "tactic_handler",
                "config": "<config><element name='assets'/></config>",
            },
            {
                "search_type": "SideBarWdg",
                "view": "project_view",
                "config": (
                    "<config><element name='episodes'/>"
                    "<element name='assets'/></config>"
                ),
            },
        ],
    ))

    assert [item["name"] for item in controller.entries._records] == [
        "episodes", "assets",
    ]
    controller.select_entry(1)
    assert controller.selectedRow == 1
    assert controller.selectedEntry["name"] == "assets"


def test_sidebar_security_uses_project_specific_link_rule():
    rules = (
        "<rules>"
        "<rule group='link' element='assets' access='allow' project='demo'/>"
        "<rule group='link' element='shots' access='allow' project='other'/>"
        "</rules>"
    )

    assert _sidebar_rule_allowed(rules, "assets", "demo") is True
    assert _sidebar_rule_allowed(rules, "assets", "other") is False
    assert _sidebar_rule_allowed(rules, "shots", "demo") is False


def test_sidebar_editor_folders_toggle_child_visibility():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded((
        "demo", "Demo", object(), [
            {
                "search_type": "SideBarWdg",
                "view": "definition",
                "config": (
                    "<config>"
                    "<element name='production' title='Production'>"
                    "<display class='SideBarSectionLinkWdg'>"
                    "<view>production</view></display></element>"
                    "<element name='episodes' title='Episodes'>"
                    "<display class='LinkWdg'/></element>"
                    "</config>"
                ),
            },
            {
                "search_type": "SideBarWdg",
                "view": "project_view",
                "config": "<config><element name='production'/></config>",
            },
            {
                "search_type": "SideBarWdg",
                "view": "production",
                "config": "<config><element name='episodes'/></config>",
            },
        ],
    ))

    assert controller.entries._records[0]["entryType"] == "section"
    assert controller.entries._records[1]["depth"] == 1
    assert controller.entries._records[1]["entryVisible"] is True
    controller.toggle_folder(0)
    assert controller.entries._records[0]["expanded"] is False
    assert controller.entries._records[1]["entryVisible"] is False


def test_sidebar_editor_preserves_folder_subfolder_order_from_views():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    definition = (
        "<config>"
        "<element name='dashboard' title='My Dashboard'>"
        "<display class='SideBarSectionLinkWdg'><view>dashboard</view>"
        "</display></element>"
        "<element name='assets' title='My Assets'><display class='LinkWdg'/></element>"
        "<element name='episodes' title='My Episodes'><display class='LinkWdg'/></element>"
        "<element name='handler' title='TACTIC Handler'>"
        "<display class='SideBarSectionLinkWdg'><view>tactic_handler</view>"
        "</display></element>"
        "<element name='handler_episodes' title='Episodes'>"
        "<display class='SideBarSectionLinkWdg'><view>handler_episodes</view>"
        "</display></element>"
        "<element name='ready' title='Ready to Sound'><display class='LinkWdg'/></element>"
        "<element name='separator'><display class='SeparatorWdg'/></element>"
        "</config>"
    )
    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [
        {"search_type": "SideBarWdg", "view": "definition", "config": definition},
        {
            "search_type": "SideBarWdg", "view": "project_view",
            "config": (
                "<config><element name='dashboard'/>"
                "<element name='separator'/><element name='handler'/></config>"
            ),
        },
        {
            "search_type": "SideBarWdg", "view": "dashboard",
            "config": "<config><element name='assets'/><element name='episodes'/></config>",
        },
        {
            "search_type": "SideBarWdg", "view": "tactic_handler",
            "config": "<config><element name='handler_episodes'/></config>",
        },
        {
            "search_type": "SideBarWdg", "view": "handler_episodes",
            "config": "<config><element name='ready'/></config>",
        },
    ]))

    assert [item["name"] for item in controller.entries._records] == [
        "dashboard", "assets", "episodes", "separator",
        "handler", "handler_episodes", "ready",
    ]
    assert [item["depth"] for item in controller.entries._records] == [
        0, 1, 1, 0, 0, 1, 2,
    ]

    controller.set_handler_only(True)
    assert controller.handlerOnly is True
    assert [item["name"] for item in controller.entries._records] == [
        "handler", "handler_episodes", "ready",
    ]
    assert [item["displayDepth"] for item in controller.entries._records] == [
        0, 1, 2,
    ]

    controller.set_handler_only(False)
    assert [item["name"] for item in controller.entries._records] == [
        "dashboard", "assets", "episodes", "separator",
        "handler", "handler_episodes", "ready",
    ]


def test_sidebar_xml_editor_targets_only_the_effective_element():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [
        {
            "search_type": "SideBarWdg",
            "view": "definition",
            "config": (
                "<config><element name='project_help' "
                "title='Project Introduction' icon='STAR' state='' "
                "is_visible='on'><display class='LinkWdg'>"
                "<widget_key>custom_layout</widget_key>"
                "<view>project_docs/project_help_layout</view>"
                "</display></element></config>"
            ),
        },
        {
            "search_type": "SideBarWdg",
            "view": "project_view",
            "config": "<config><element name='project_help'/></config>",
        },
    ]))
    controller.select_entry(0)

    xml = ElementTree.fromstring(controller.xmlText)
    assert xml.tag == "element"
    assert xml.get("name") == "project_help"
    assert xml.findtext("./display/widget_key") == "custom_layout"
    assert xml.findtext("./display/view") == (
        "project_docs/project_help_layout"
    )
    assert "<config" not in controller.xmlText


def test_sidebar_xml_apply_replaces_definition_and_keeps_reference():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Navigation:
        @staticmethod
        def _icon_name(icon, _search_type):
            return icon or "sobject"

    class Application:
        _registry = Registry()
        navigation_model = Navigation()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [
        {
            "search_type": "SideBarWdg",
            "view": "definition",
            "config": (
                "<config><element name='assets' title='Assets'>"
                "<display class='LinkWdg'><widget_key>view_panel</widget_key>"
                "</display></element></config>"
            ),
        },
        {
            "search_type": "SideBarWdg",
            "view": "project_view",
            "config": "<config><element name='assets'/></config>",
        },
    ]))
    controller.select_entry(0)
    controller.set_xml_text(
        "<element name='assets' title='Asset Cards' is_visible='off'>"
        "<display class='LinkWdg'><widget_key>tile_layout</widget_key>"
        "<view_mode>tiles</view_mode></display></element>"
    )
    controller.apply_xml()

    definition = _all_elements(controller._documents["definition"])[0]
    reference = _all_elements(controller._documents["project_view"])[0]
    assert definition.get("title") == "Asset Cards"
    assert definition.get("is_visible") == "off"
    assert _widget_type(definition) == "tile_layout"
    assert _result_view_mode(definition) == "tiles"
    assert reference.attrib == {"name": "assets"}
    assert controller.selectedRow == 0

    controller.set_mode("xml")
    controller.set_xml_text(
        "<element name='assets' title='Asset Grid' is_visible='on'>"
        "<display class='LinkWdg'><widget_key>tile_layout</widget_key>"
        "<view_mode>tiles</view_mode></display></element>"
    )
    controller.set_mode("simple")

    definition = _all_elements(controller._documents["definition"])[0]
    assert controller.mode == "simple"
    assert definition.get("title") == "Asset Grid"
    assert definition.get("is_visible") == "on"

    controller.set_mode("xml")
    controller.set_xml_text("<element name='assets'>")
    controller.set_mode("simple")

    assert controller.mode == "xml"
    assert "Invalid sidebar XML" in controller.error


def test_sidebar_simple_display_fields_write_native_xml():
    element = ElementTree.fromstring(
        "<element name='assets'><display class='LinkWdg'/></element>"
    )
    from thlib.ui.sidebar_editor import _set_display_option

    element.set("is_visible", "off")
    _set_display_option(element, "widget_key", "custom_layout")
    _set_display_option(element, "view", "project/assets")
    _set_display_option(element, "view_mode", "splitted_vertical")
    _set_display_option(
        element, "layout_preset", "workspace_layout@review",
    )

    assert element.get("is_visible") == "off"
    assert _widget_type(element) == "custom_layout"
    assert _display_option(element, "view") == "project/assets"
    assert _result_view_mode(element) == "splitted_vertical"
    assert _display_option(element, "layout_preset") == (
        "workspace_layout@review"
    )


def test_sidebar_editor_excludes_workspace_layout_config_records():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Application:
        _registry = Registry()
        navigation_model = NavigationModel()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [{
        "search_type": "SideBarWdg",
        "view": "definition",
        "config": (
            "<config><element name='assets' title='Assets'>"
            "<display class='LinkWdg'/></element></config>"
        ),
    }, {
        "search_type": "SideBarWdg",
        "category": "workspace_layout",
        "view": "workspace_layout@review",
        "config": "<config><view name='workspace_layout@review'/></config>",
    }]))

    assert set(controller._documents) == {"definition"}


def test_sidebar_entry_layout_assignment_is_native_display_data():
    class Registry:
        def register(self, _name, _callback):
            pass

    class Application:
        _registry = Registry()
        navigation_model = NavigationModel()

    class Users:
        canManageUsers = True

    controller = SidebarEditorController(Application(), Users())
    controller._loaded(("demo", "Demo", object(), [{
        "search_type": "SideBarWdg",
        "view": "definition",
        "config": (
            "<config><element name='assets' title='Assets'>"
            "<display class='LinkWdg'/><search_type>demo/assets</search_type>"
            "</element></config>"
        ),
    }]))
    controller.select_entry(0)

    controller.update_selected(
        "layoutPreset", "workspace_layout@review",
    )

    assert controller.selectedEntry["layoutPreset"] == (
        "workspace_layout@review"
    )
    assert "<layout_preset>workspace_layout@review</layout_preset>" in (
        controller.xmlText
    )
