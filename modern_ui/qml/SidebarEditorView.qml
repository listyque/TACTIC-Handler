import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    readonly property var controller: sidebarEditorController
    readonly property int scrollContentGap: 10
    readonly property string presetContextKey:
        String(controller.selectedRow) + "|"
        + String(controller.selectedEntry.searchType || "")

    function optionIndex(options, value) {
        const expected = String(value || "")
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === expected)
                return index
        }
        return 0
    }

    function switchEditorMode(value) {
        // Commit the currently focused Simple editor before its Loader is
        // replaced. Text fields write their value on editingFinished.
        root.forceActiveFocus(Qt.MouseFocusReason)
        Qt.callLater(function() {
            root.controller.set_mode(value)
        })
    }

    Component.onCompleted: controller.begin_session()
    onPresetContextKeyChanged: Qt.callLater(
        controller.refresh_search_presets
    )

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainer
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 10

                MaterialIcon {
                    name: "account_tree"
                    size: 20
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Sidebar Editor")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Project") + ": " + root.controller.projectTitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                        elide: Text.ElideRight
                    }
                }
                Md3SegmentedButton {
                    theme: root.theme
                    currentValue: root.controller.mode
                    segmentWidth: 94
                    model: [
                        {"value": "simple", "label": "Simple", "icon": "view_list"},
                        {"value": "xml", "label": "XML", "icon": "code"}
                    ]
                    onActivated: value => root.switchEditorMode(value)
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "refresh"
                    round: true
                    toolTip: qsTr("Reload sidebar")
                    enabled: !root.controller.busy
                    onClicked: root.controller.reload()
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: root.controller.error.length > 0
            text: root.controller.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Typography.body
            wrapMode: Text.WordWrap
        }

        SplitView {
            id: editorSplit
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal
            handle: Rectangle {
                implicitWidth: 10
                color: "transparent"

                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                SplitView.preferredWidth: Math.max(300, root.width * 0.36)
                SplitView.minimumWidth: 260
                SplitView.maximumWidth: Math.max(360, root.width * 0.54)
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 52
                        Layout.leftMargin: 14
                        Layout.rightMargin: 8
                        spacing: 6

                        MaterialIcon {
                            name: "view_list"
                            size: 17
                            color: root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Project Views")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "filter-alt"
                            iconColor: root.controller.handlerOnly
                                ? root.theme.action : root.theme.secondaryText
                            backgroundColor: root.controller.handlerOnly
                                ? root.theme.secondaryContainer : "transparent"
                            toolTip: root.controller.handlerOnly
                                ? qsTr("Show all project views")
                                : qsTr("Show only TACTIC Handler")
                            onClicked: root.controller.set_handler_only(
                                !root.controller.handlerOnly
                            )
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "add"
                            toolTip: qsTr("Add link")
                            onClicked: root.controller.add_entry("link")
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "create-new-folder"
                            toolTip: qsTr("Add section")
                            onClicked: root.controller.add_entry("section")
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "remove"
                            toolTip: qsTr("Add separator")
                            onClicked: root.controller.add_entry("separator")
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.theme.separator
                    }

                    ListView {
                        id: previewList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.topMargin: 8
                        Layout.bottomMargin: 8
                        clip: true
                        spacing: 0
                        rightMargin: root.scrollContentGap
                        model: sidebarEntryModel
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Item {
                            id: previewEntry
                            required property int index
                            required property string title
                            required property string entryType
                            required property string glyph
                            required property string accent
                            required property string searchType
                            required property int depth
                            required property int displayDepth
                            required property bool selected
                            required property bool included
                            required property bool expanded
                            required property bool entryVisible
                            required property bool hasChildren

                            width: Math.max(
                                0,
                                previewList.width - previewList.rightMargin
                            )
                            height: !entryVisible ? 0
                                : editorSidebarRow.implicitHeight
                            visible: entryVisible

                            SidebarTreeRow {
                                id: editorSidebarRow
                                anchors.fill: parent
                                theme: root.theme
                                rowType: previewEntry.entryType
                                title: previewEntry.title
                                glyph: previewEntry.glyph
                                depth: previewEntry.displayDepth
                                accent: previewEntry.accent
                                expanded: previewEntry.expanded
                                selected: previewEntry.selected
                                dimmed: !previewEntry.included
                                interactive: true
                                onActivated: root.controller.activate_entry(
                                    previewEntry.index
                                )
                            }
                        }

                        ScrollBar.vertical: Md3ScrollBar {
                            theme: root.theme
                            flickableTarget: previewList
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: previewList.count === 0 && !root.controller.busy
                            text: root.controller.handlerOnly
                                ? qsTr("TACTIC Handler branch was not found")
                                : qsTr("This sidebar has no items")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
                        }
                    }
                }
            }

            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 390
                color: root.theme.surfaceContainerLow
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                Loader {
                    anchors.fill: parent
                    anchors.margins: 14
                    sourceComponent: root.controller.mode === "xml"
                        ? xmlEditor : simpleEditor
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.controller.dirty
                        ? qsTr("Sidebar has unsaved changes")
                        : qsTr("Sidebar is up to date")
                    color: root.controller.dirty
                        ? root.theme.action : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("DISCARD")
                    icon.name: "undo"
                    enabled: root.controller.dirty && !root.controller.busy
                    onClicked: root.controller.discard()
                }
                Md3Button {
                    theme: root.theme
                    text: root.controller.busy ? qsTr("Saving...") : qsTr("SAVE")
                    icon.name: "save"
                    highlighted: true
                    enabled: root.controller.dirty && !root.controller.busy
                    onClicked: root.controller.save()
                }
            }
        }
    }

    Component {
        id: simpleEditor

        Flickable {
            id: simpleFlick
            clip: true
            contentWidth: width
            contentHeight: simpleColumn.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick
            rightMargin: root.scrollContentGap

            ColumnLayout {
                id: simpleColumn
                width: Math.max(
                    0,
                    simpleFlick.width - simpleFlick.rightMargin
                )
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Link details")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_upward"
                        toolTip: qsTr("Move up")
                        enabled: root.controller.selectedRow >= 0
                            && Boolean(root.controller.selectedEntry.included)
                        onClicked: root.controller.move_selected(-1)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "arrow_downward"
                        toolTip: qsTr("Move down")
                        enabled: root.controller.selectedRow >= 0
                            && Boolean(root.controller.selectedEntry.included)
                        onClicked: root.controller.move_selected(1)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        toolTip: qsTr("Delete item")
                        enabled: root.controller.selectedRow >= 0
                        onClicked: root.controller.delete_selected()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.controller.selectedRow < 0
                    text: qsTr("Select an item in the preview to edit it, or add a new link or section.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    wrapMode: Text.WordWrap
                }

                Rectangle {
                    Layout.fillWidth: true
                    visible: root.controller.selectedRow >= 0
                    implicitHeight: detailsGrid.implicitHeight + 28
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainer
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    GridLayout {
                        id: detailsGrid
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        columns: width >= 620 ? 2 : 1
                        columnSpacing: 12
                        rowSpacing: 10

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: qsTr("Item type"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            Md3ComboBox {
                                Layout.fillWidth: true
                                theme: root.theme
                                textRole: "label"
                                valueRole: "value"
                                iconRole: "icon"
                                model: [
                                    {
                                        "value": "link",
                                        "label": qsTr("Link"),
                                        "icon": "sidebar-link"
                                    },
                                    {
                                        "value": "section",
                                        "label": qsTr("Section"),
                                        "icon": "sidebar-section"
                                    },
                                    {
                                        "value": "separator",
                                        "label": qsTr("Separator"),
                                        "icon": "sidebar-separator"
                                    }
                                ]
                                currentIndex: root.optionIndex(model, root.controller.selectedEntry.entryType)
                                onActivated: root.controller.update_selected("entryType", currentValue)
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: qsTr("Title"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            Md3TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                text: String(root.controller.selectedEntry.title || "")
                                placeholderText: qsTr("Sidebar title")
                                onEditingFinished: root.controller.update_selected("title", text)
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: qsTr("Name"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            Md3TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                text: String(root.controller.selectedEntry.name || "")
                                placeholderText: qsTr("Stable item name")
                                onEditingFinished: root.controller.update_selected("name", text)
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: qsTr("Icon"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                Md3TextField {
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    text: String(root.controller.selectedEntry.icon || "")
                                    placeholderText: qsTr("Semantic icon name")
                                    onEditingFinished: root.controller.update_selected("icon", text)
                                }
                                IconPickerButton {
                                    Layout.preferredWidth: 44
                                    Layout.preferredHeight: 44
                                    theme: root.theme
                                    // The XML keeps TACTIC's legacy FAS_ name;
                                    // the picker and MaterialIcon use the
                                    // already decoded runtime glyph.
                                    iconName: String(root.controller.selectedEntry.glyph || "")
                                    onIconSelected: name => root.controller.update_selected("icon", name)
                                }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label {
                                text: qsTr("Visibility")
                                color: root.theme.secondaryText
                                font.pointSize: Typography.label
                            }
                            Md3CheckBox {
                                Layout.fillWidth: true
                                theme: root.theme
                                text: qsTr("Is visible")
                                checked: Boolean(
                                    root.controller.selectedEntry.isVisible
                                )
                                onToggled: root.controller.update_selected(
                                    "isVisible", checked
                                )
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.controller.selectedEntry.entryType === "link"
                            spacing: 4
                            Label { text: qsTr("Search Type"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            Md3ComboBox {
                                Layout.fillWidth: true
                                theme: root.theme
                                textRole: "label"
                                valueRole: "value"
                                translateDisplayText: false
                                model: root.controller.searchTypes
                                currentIndex: root.optionIndex(model, root.controller.selectedEntry.searchType)
                                onActivated: root.controller.update_selected("searchType", currentValue)
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.controller.selectedEntry.entryType === "link"
                            spacing: 4
                            Label { text: qsTr("Predefined search"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6

                                Md3ComboBox {
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    textRole: "label"
                                    valueRole: "value"
                                    translateDisplayText: false
                                    model: root.controller.searchPresetOptions
                                    currentIndex: root.optionIndex(
                                        model,
                                        root.controller.selectedEntry.searchView
                                    )
                                    enabled: !root.controller.searchPresetsBusy
                                        && String(root.controller.selectedEntry.searchType || "").length > 0
                                    onActivated: root.controller.update_selected(
                                        "searchView", currentValue
                                    )
                                }
                                Md3BusyIndicator {
                                    uiTheme: root.theme
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    running: root.controller.searchPresetsBusy
                                    visible: running
                                }
                                Md3Button {
                                    theme: root.theme
                                    text: qsTr("Edit searches")
                                    icon.name: "edit"
                                    flat: true
                                    enabled: String(
                                        root.controller.selectedEntry.searchType || ""
                                    ).length > 0
                                    onClicked: root.controller.edit_search_presets()
                                }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.controller.selectedEntry.entryType === "section"
                            spacing: 4
                            Label { text: qsTr("Child view"); color: root.theme.secondaryText; font.pointSize: Typography.label }
                            Md3TextField {
                                Layout.fillWidth: true
                                theme: root.theme
                                text: String(root.controller.selectedEntry.targetView || "")
                                placeholderText: qsTr("Referenced SideBarWdg view")
                                onEditingFinished: root.controller.update_selected("targetView", text)
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.columnSpan: detailsGrid.columns
                            visible: root.controller.selectedEntry.entryType === "link"
                            implicitHeight: displayDefinition.implicitHeight + 24
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainerHigh
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            GridLayout {
                                id: displayDefinition
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 12
                                columns: width >= 570 ? 2 : 1
                                columnSpacing: 12
                                rowSpacing: 9

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.columnSpan: displayDefinition.columns
                                    spacing: 8
                                    MaterialIcon {
                                        name: "dashboard_customize"
                                        size: 17
                                        color: root.theme.action
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: qsTr("Display definition")
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.bodyLarge
                                        font.weight: Font.DemiBold
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: qsTr("Widget Type")
                                        color: root.theme.secondaryText
                                        font.pointSize: Typography.label
                                    }
                                    Md3ComboBox {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        textRole: "label"
                                        valueRole: "value"
                                        iconRole: "icon"
                                        model: root.controller.widgetTypeOptions
                                        currentIndex: root.optionIndex(
                                            model,
                                            root.controller.selectedEntry.widgetType
                                        )
                                        onActivated: root.controller.update_selected(
                                            "widgetType", currentValue
                                        )
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: root.controller.selectedEntry.widgetType
                                        === "__class__"
                                    spacing: 4
                                    Label {
                                        text: qsTr("Class Path")
                                        color: root.theme.secondaryText
                                        font.pointSize: Typography.label
                                    }
                                    Md3TextField {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        text: String(
                                            root.controller.selectedEntry.displayClassName
                                            || ""
                                        )
                                        placeholderText: qsTr("Python widget class path")
                                        onEditingFinished: root.controller.update_selected(
                                            "displayClassName", text
                                        )
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: [
                                        "custom_layout", "edit_layout",
                                        "tile_layout", "fast_layout"
                                    ].indexOf(String(
                                        root.controller.selectedEntry.widgetType
                                    )) >= 0
                                    spacing: 4
                                    Label {
                                        text: qsTr("View")
                                        color: root.theme.secondaryText
                                        font.pointSize: Typography.label
                                    }
                                    Md3TextField {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        text: String(
                                            root.controller.selectedEntry.displayView
                                            || ""
                                        )
                                        placeholderText: qsTr("TACTIC view name")
                                        onEditingFinished: root.controller.update_selected(
                                            "displayView", text
                                        )
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: String(
                                        root.controller.selectedEntry.searchType || ""
                                    ).length > 0
                                    spacing: 4
                                    Label {
                                        text: qsTr("Default item view")
                                        color: root.theme.secondaryText
                                        font.pointSize: Typography.label
                                    }
                                    Md3ComboBox {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        textRole: "label"
                                        valueRole: "value"
                                        iconRole: "icon"
                                        model: root.controller.resultViewOptions
                                        currentIndex: root.optionIndex(
                                            model,
                                            root.controller.selectedEntry.resultViewMode
                                        )
                                        onActivated: root.controller.update_selected(
                                            "resultViewMode", currentValue
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 260
                    visible: root.controller.selectedRow >= 0
                    implicitHeight: Math.max(
                        260,
                        securityColumn.implicitHeight + 20,
                        simpleFlick.height - y
                    )
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainer
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        id: securityColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.margins: 10
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            MaterialIcon {
                                name: "groups"
                                size: 18
                                color: root.theme.action
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("Security Settings")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.bodyLarge
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("Groups that can see this sidebar element")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.label
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: root.theme.separator
                        }

                        ListView {
                            id: securityList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumHeight: 170
                            clip: true
                            spacing: 0
                            rightMargin: root.scrollContentGap
                            model: sidebarSecurityGroupModel
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                id: securityRow
                                required property string code
                                required property string groupName
                                required property string label
                                required property bool allowed
                                required property bool changed
                                width: Math.max(
                                    0,
                                    securityList.width - securityList.rightMargin
                                )
                                height: 34
                                radius: root.theme.itemRadius
                                color: groupMouse.hovered
                                    ? root.theme.rowHover : "transparent"

                                Md3CheckBox {
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6
                                    theme: root.theme
                                    checked: securityRow.allowed
                                    text: securityRow.label
                                        + (securityRow.groupName !== securityRow.label
                                            ? " (" + securityRow.groupName + ")" : "")
                                    font.weight: securityRow.changed
                                        ? Font.DemiBold : Font.Normal
                                    onToggled: root.controller.set_group_allowed(
                                        securityRow.code, checked
                                    )
                                }
                                HoverHandler {
                                    id: groupMouse
                                    acceptedDevices: PointerDevice.Mouse
                                }
                            }

                            ScrollBar.vertical: Md3ScrollBar {
                                theme: root.theme
                                flickableTarget: securityList
                            }

                            Label {
                                anchors.centerIn: parent
                                visible: securityList.count === 0
                                text: qsTr("No login groups available")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                            }
                        }
                    }
                }
            }

            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: simpleFlick
            }
        }
    }

    Component {
        id: xmlEditor

        ColumnLayout {
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        text: qsTr("Advanced XML")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: root.controller.selectedRow >= 0
                            ? qsTr("Selected element") + ": "
                                + String(root.controller.selectedEntry.name || "")
                            : qsTr("Select a sidebar element first")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("APPLY XML")
                    icon.name: "code"
                    enabled: root.controller.selectedRow >= 0
                    onClicked: root.controller.apply_xml()
                }
            }

            Md3TextArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                text: root.controller.xmlText
                enabled: root.controller.selectedRow >= 0
                wrapMode: TextEdit.NoWrap
                font.family: "Consolas"
                font.pointSize: Typography.body
                onTextChanged: root.controller.set_xml_text(text)
            }
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        visible: root.controller.busy
        theme: root.theme
        message: qsTr("Loading sidebar configuration...")
        cancellable: false
    }
}
