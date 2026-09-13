pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property int selectedRow: -1
    property string selectedName: ""
    property int modelRevision: 0
    property string definitionTarget: "definition"
    property string editorMode: "simple"
    property string workspaceMode: "current"
    property string catalogScope: "current"
    property string catalogFilter: ""
    property string catalogSearchType: ""
    property string catalogEditorMode: "simple"
    property string selectedCatalogIdentity: ""
    property string catalogXmlText: ""
    property string catalogXmlOriginal: ""
    property var catalogSimpleRows: []
    property bool catalogSaving: false
    property var selectedColumn: {
        const revision = modelRevision
        return selectedRow >= 0
            ? columnsEditorModel.get(selectedRow) : ({})
    }
    readonly property bool catalogDirty:
        catalogXmlText !== catalogXmlOriginal
    readonly property var catalogRows: {
        const needle = catalogFilter.trim().toLowerCase()
        return columnsEditorController.definitionCatalog.filter(record => {
            if (catalogScope === "current" && !record.current)
                return false
            if (catalogScope === "all" && catalogSearchType
                    && record.searchType !== catalogSearchType)
                return false
            return !needle || [
                record.view, record.searchType, record.code,
                record.login, record.category, record.widgetType
            ].join(" ").toLowerCase().includes(needle)
        })
    }
    readonly property var selectedCatalog: {
        for (let row = 0; row < catalogRows.length; ++row) {
            if (String(catalogRows[row].identity || "")
                    === selectedCatalogIdentity)
                return catalogRows[row]
        }
        return ({})
    }
    readonly property var catalogSearchTypeOptions: {
        return [{value: "", label: qsTr("All Search Types")}].concat(
            columnsEditorController.definitionCatalogSearchTypes
        )
    }

    function loadDefinition() {
        definitionEditor.reload()
    }

    function switchEditorMode(value) {
        root.forceActiveFocus(Qt.MouseFocusReason)
        Qt.callLater(function() {
            root.editorMode = value
        })
    }

    function switchWorkspaceMode(value) {
        if (catalogDirty)
            return
        workspaceMode = value
        if (value === "catalog")
            columnsEditorController.load_definition_catalog()
    }

    function optionIndex(options, value) {
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === String(value || ""))
                return index
        }
        return 0
    }

    function reloadCatalogSimpleRows() {
        catalogSimpleRows = columnsEditorController.catalog_simple_rows(
            catalogXmlText
        )
    }

    function switchCatalogEditorMode(value) {
        root.forceActiveFocus(Qt.MouseFocusReason)
        Qt.callLater(function() {
            root.catalogEditorMode = value
            if (value === "simple")
                root.reloadCatalogSimpleRows()
        })
    }

    function updateCatalogSimpleValue(path, kind, name, value) {
        const updated = columnsEditorController.update_catalog_simple_value(
            catalogXmlText, path, kind, name, value
        )
        if (!updated)
            return
        catalogXmlText = updated
        reloadCatalogSimpleRows()
    }

    function selectCatalog(record, force) {
        if (!force && catalogDirty)
            return
        if (!record) {
            selectedCatalogIdentity = ""
            catalogXmlText = ""
            catalogXmlOriginal = ""
            catalogSimpleRows = []
            return
        }
        selectedCatalogIdentity = String(record.identity || "")
        catalogXmlText = String(record.config || "")
        catalogXmlOriginal = catalogXmlText
        reloadCatalogSimpleRows()
    }

    function refreshCatalogSelection(force) {
        for (let row = 0; row < catalogRows.length; ++row) {
            if (String(catalogRows[row].identity || "")
                    === selectedCatalogIdentity) {
                selectCatalog(catalogRows[row], force)
                return
            }
        }
        selectCatalog(
            catalogRows.length > 0 ? catalogRows[0] : null, force
        )
    }

    function rowForName(name) {
        for (let row = 0; row < columnsEditorModel.count(); ++row) {
            if (String(columnsEditorModel.get(row).name || "") === name)
                return row
        }
        return -1
    }

    function selectColumn(row, target) {
        if (columnsEditorModel.count() === 0) {
            selectedRow = -1
            selectedName = ""
            return
        }
        const bounded = Math.max(0, Math.min(
            columnsEditorModel.count() - 1, Number(row)
        ))
        selectedName = String(columnsEditorModel.get(bounded).name || "")
        selectedRow = bounded
        if (target === "definition" || target === "edit_definition")
            definitionTarget = target
        loadDefinition()
    }

    onSelectedRowChanged: loadDefinition()
    onDefinitionTargetChanged: loadDefinition()
    onCatalogRowsChanged: if (!catalogDirty)
        root.refreshCatalogSelection()
    Component.onCompleted: {
        if (columnsEditorModel.count() > 0) {
            const requested = root.rowForName(
                String(columnsEditorController.requestedName || "")
            )
            selectColumn(
                requested >= 0 ? requested
                    : columnsEditorController.requestedRow,
                columnsEditorController.requestedDefinitionTarget
            )
        }
        columnsEditorController.begin_session()
    }

    Connections {
        target: columnsEditorModel
        function onContentReplaced() {
            root.modelRevision += 1
            if (columnsEditorModel.count() === 0)
                root.selectColumn(-1)
            else {
                const restored = root.rowForName(root.selectedName)
                root.selectColumn(restored >= 0 ? restored : 0)
            }
        }
    }
    Connections {
        target: columnsEditorController
        function onFocusRequested() {
            const requested = root.rowForName(
                String(columnsEditorController.requestedName || "")
            )
            root.selectColumn(
                requested >= 0 ? requested
                    : columnsEditorController.requestedRow,
                columnsEditorController.requestedDefinitionTarget
            )
        }
        function onStateChanged() {
            if (root.workspaceMode !== "catalog"
                    || columnsEditorController.busy)
                return
            if (root.catalogSaving) {
                root.catalogSaving = false
                if (columnsEditorController.error.length === 0)
                    root.refreshCatalogSelection(true)
            } else if (!root.catalogDirty) {
                root.refreshCatalogSelection()
            }
        }
    }

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10
        enabled: !columnsEditorController.busy

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: root.workspaceMode === "catalog"
                    ? qsTr("TACTIC definitions")
                    : qsTr("TACTIC table · ") + columnsEditorController.title
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 15
                font.weight: Font.DemiBold
            }
            Controls.SegmentedButton {
                theme: root.theme
                currentValue: root.workspaceMode
                segmentWidth: 112
                model: [
                    {value: "current", label: "Current", icon: "table-view"},
                    {value: "catalog", label: "Advanced", icon: "schema"}
                ]
                onActivated: value => root.switchWorkspaceMode(value)
            }
            Controls.SegmentedButton {
                visible: root.workspaceMode === "current"
                theme: root.theme
                currentValue: root.editorMode
                segmentWidth: 94
                model: [
                    {value: "simple", label: "Simple", icon: "view_list"},
                    {value: "xml", label: "XML", icon: "code"}
                ]
                onActivated: value => root.switchEditorMode(value)
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                running: columnsEditorController.busy
                visible: running
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Resolve the native TACTIC view again")
                onClicked: root.workspaceMode === "catalog"
                    ? columnsEditorController.reload_definition_catalog()
                    : columnsEditorController.reload()
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.workspaceMode === "current"
            orientation: root.width >= 660 ? Qt.Horizontal : Qt.Vertical

            Rectangle {
                objectName: "tableViewSelectorPanel"
                SplitView.preferredWidth: root.width >= 1000 ? 430 : 330
                SplitView.minimumWidth: root.width >= 660 ? 300 : 0
                SplitView.preferredHeight: root.width >= 660 ? -1 : 220
                SplitView.minimumHeight: root.width >= 660 ? 0 : 140
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 5

                    Label {
                        Layout.fillWidth: true
                        text: root.definitionTarget === "edit_definition"
                            ? qsTr("EDITSOBJECT FIELDS")
                            : qsTr("TABLE VIEW SELECTOR")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.definitionTarget === "edit_definition"
                            ? qsTr("Select a field to configure its input widget and view=edit membership.")
                            : qsTr("Order and width are stored in view=table. Widget behavior comes from the definition stack.")
                        color: root.theme.secondaryText
                        wrapMode: Text.WordWrap
                        font.pointSize: Controls.Typography.label
                    }
                    ListView {
                        id: columnsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.rightMargin: columnsBar.reservedExtent + 4
                        model: columnsEditorModel
                        clip: true
                        spacing: 3
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Rectangle {
                            id: columnRow
                            objectName: "tacticColumnRow_" + name
                            required property int index
                            required property string name
                            required property string label
                            required property string dataType
                            required property bool displayVisible
                            required property int displayWidth
                            required property string widgetClass
                            required property string widgetKey
                            required property bool editVisible
                            required property string editClass
                            required property string editWidget
                            width: columnsList.width
                            height: 54
                            radius: 10
                            color: root.selectedRow === index
                                ? root.theme.selected
                                : rowHover.hovered
                                  ? root.theme.rowHover : root.theme.row

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 7
                                anchors.rightMargin: 5
                                spacing: 6
                                Controls.CheckBox {
                                    theme: root.theme
                                    visible: root.definitionTarget
                                        !== "edit_definition"
                                    checked: columnRow.displayVisible
                                    Accessible.name: qsTr("Show column")
                                    onToggled: columnsEditorController
                                        .set_visible(columnRow.index, checked)
                                }
                                Controls.MaterialIcon {
                                    visible: root.definitionTarget
                                        === "edit_definition"
                                    name: columnRow.editVisible
                                        ? "check_circle" : "circle"
                                    size: 18
                                    color: columnRow.editVisible
                                        ? root.theme.action
                                        : root.theme.disabledText
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
                                    Label {
                                        Layout.fillWidth: true
                                        text: columnRow.label
                                        color: root.theme.primaryText
                                        elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.body
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: columnRow.name + " · "
                                            + (root.definitionTarget
                                                === "edit_definition"
                                                ? columnRow.editWidget
                                                    || columnRow.editClass
                                                    || columnRow.dataType
                                                : columnRow.widgetKey
                                                    || columnRow.widgetClass
                                                    || columnRow.dataType)
                                        color: root.theme.secondaryText
                                        elide: Text.ElideMiddle
                                        font.pointSize: Controls.Typography.label
                                    }
                                }
                                Controls.SpinBox {
                                    visible: root.definitionTarget
                                        !== "edit_definition"
                                    Layout.preferredWidth: 96
                                    theme: root.theme
                                    from: 48
                                    to: 640
                                    stepSize: 8
                                    value: columnRow.displayWidth
                                    Accessible.name: qsTr("Column width")
                                    onValueModified: columnsEditorController
                                        .set_width(columnRow.index, value)
                                }
                                Controls.CompactIconButton {
                                    visible: root.definitionTarget
                                        !== "edit_definition"
                                    theme: root.theme
                                    iconName: "arrow_upward"
                                    toolTip: qsTr("Move up")
                                    enabled: columnRow.index > 0
                                    onClicked: {
                                        columnsEditorController.move(
                                            columnRow.index, -1)
                                        root.selectColumn(columnRow.index - 1)
                                    }
                                }
                                Controls.CompactIconButton {
                                    visible: root.definitionTarget
                                        !== "edit_definition"
                                    theme: root.theme
                                    iconName: "arrow_downward"
                                    toolTip: qsTr("Move down")
                                    enabled: columnRow.index
                                        < columnsEditorModel.count() - 1
                                    onClicked: {
                                        columnsEditorController.move(
                                            columnRow.index, 1)
                                        root.selectColumn(columnRow.index + 1)
                                    }
                                }
                            }
                            HoverHandler {
                                id: rowHover
                                cursorShape: Qt.PointingHandCursor
                            }
                            Controls.ActivationHandler {
                                onActivated: root.selectColumn(columnRow.index)
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: columnsBar
                            theme: root.theme
                            flickableTarget: columnsList
                        }
                    }
                }
            }

            Rectangle {
                objectName: "elementDefinitionPanel"
                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: root.width >= 660 ? 300 : 0
                SplitView.minimumHeight: root.width >= 660 ? 0 : 220
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                TacticElementDefinitionEditor {
                    id: definitionEditor
                    anchors.fill: parent
                    anchors.margins: 12
                    theme: root.theme
                    controller: columnsEditorController
                    selectedRow: root.selectedRow
                    selectedColumn: root.selectedColumn
                    modelRevision: root.modelRevision
                    target: root.definitionTarget
                    editorMode: root.editorMode
                    onTargetRequested: value => root.definitionTarget = value
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.workspaceMode === "catalog"
            orientation: root.width >= 660 ? Qt.Horizontal : Qt.Vertical

            Rectangle {
                objectName: "definitionCatalogPanel"
                SplitView.preferredWidth: root.width >= 1000 ? 410 : 330
                SplitView.minimumWidth: root.width >= 660 ? 300 : 0
                SplitView.preferredHeight: root.width >= 660 ? -1 : 240
                SplitView.minimumHeight: root.width >= 660 ? 0 : 170
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 7

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("SAVED DEFINITIONS")
                            color: root.theme.secondaryText
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: root.catalogRows.length
                            color: root.theme.secondaryText
                            font.pointSize: Controls.Typography.label
                        }
                    }
                    Controls.SegmentedButton {
                        Layout.fillWidth: true
                        theme: root.theme
                        enabled: !root.catalogDirty
                        currentValue: root.catalogScope
                        segmentWidth: 138
                        model: [
                            {
                                value: "current", label: "Current type",
                                icon: "filter_alt"
                            },
                            {value: "all", label: "All types", icon: "schema"}
                        ]
                        onActivated: value => root.catalogScope = value
                    }
                    Controls.ComboBox {
                        objectName: "definitionCatalogSearchTypeFilter"
                        Layout.fillWidth: true
                        visible: root.catalogScope === "all"
                        theme: root.theme
                        enabled: !root.catalogDirty
                        leadingIcon: "schema"
                        model: root.catalogSearchTypeOptions
                        textRole: "label"
                        valueRole: "value"
                        translateDisplayText: false
                        currentIndex: root.optionIndex(
                            model, root.catalogSearchType
                        )
                        Accessible.name: qsTr("Filter by Search Type")
                        onActivated: root.catalogSearchType = String(
                            currentValue || ""
                        )
                    }
                    Controls.SearchField {
                        objectName: "definitionCatalogFilter"
                        Layout.fillWidth: true
                        theme: root.theme
                        enabled: !root.catalogDirty
                        placeholderText: qsTr("Filter saved views")
                        text: root.catalogFilter
                        onSearchEdited: query => root.catalogFilter = query
                    }
                    ListView {
                        id: definitionCatalogList
                        objectName: "definitionCatalogList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.rightMargin: definitionCatalogBar.reservedExtent + 4
                        model: root.catalogRows
                        enabled: !root.catalogDirty
                        clip: true
                        spacing: 3
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Rectangle {
                            id: catalogRow
                            required property int index
                            required property var modelData
                            objectName: "definitionCatalogRow_" + index
                            width: definitionCatalogList.width
                            height: 58
                            radius: 10
                            color: root.selectedCatalogIdentity
                                    === String(modelData.identity || "")
                                ? root.theme.selected
                                : catalogHover.hovered
                                    ? root.theme.rowHover : root.theme.row

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 8
                                spacing: 8
                                Controls.MaterialIcon {
                                    name: catalogRow.modelData.current
                                        ? "table-view" : "schema"
                                    size: 18
                                    color: catalogRow.modelData.current
                                        ? root.theme.action
                                        : root.theme.secondaryText
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
                                    Label {
                                        Layout.fillWidth: true
                                        text: String(catalogRow.modelData.view)
                                        color: root.theme.primaryText
                                        elide: Text.ElideMiddle
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: String(
                                            catalogRow.modelData.searchType
                                        ) + (catalogRow.modelData.login
                                            ? " · " + catalogRow.modelData.login
                                            : "")
                                        color: root.theme.secondaryText
                                        elide: Text.ElideMiddle
                                        font.pointSize: Controls.Typography.label
                                    }
                                }
                            }
                            HoverHandler {
                                id: catalogHover
                                cursorShape: root.catalogDirty
                                    ? Qt.ArrowCursor : Qt.PointingHandCursor
                            }
                            Controls.ActivationHandler {
                                enabled: !root.catalogDirty
                                onActivated:
                                    root.selectCatalog(catalogRow.modelData)
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: definitionCatalogBar
                            theme: root.theme
                            flickableTarget: definitionCatalogList
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: columnsEditorController.definitionCatalogLoaded
                            && root.catalogRows.length === 0
                        text: root.catalogScope === "current"
                            ? qsTr("No saved definitions for this Search Type")
                            : qsTr("No saved definitions match the filter")
                        color: root.theme.secondaryText
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        font.pointSize: Controls.Typography.label
                    }
                }
            }

            Rectangle {
                objectName: "definitionCatalogXmlPanel"
                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: root.width >= 660 ? 300 : 0
                SplitView.minimumHeight: root.width >= 660 ? 0 : 240
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            text: String(root.selectedCatalog.view
                                || qsTr("Select a definition"))
                            color: root.theme.primaryText
                            elide: Text.ElideMiddle
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Controls.SegmentedButton {
                            theme: root.theme
                            currentValue: root.catalogEditorMode
                            segmentWidth: 88
                            segmentObjectNamePrefix: "catalogEditorMode_"
                            model: [
                                {
                                    value: "simple", label: "Simple",
                                    icon: "view_list"
                                },
                                {value: "xml", label: "XML", icon: "code"}
                            ]
                            onActivated: value =>
                                root.switchCatalogEditorMode(value)
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.selectedCatalog.searchType
                            ? qsTr("Search Type: ")
                                + root.selectedCatalog.searchType
                                + (root.selectedCatalog.login
                                    ? qsTr(" · Login: ")
                                        + root.selectedCatalog.login : "")
                            : ""
                        color: root.theme.secondaryText
                        elide: Text.ElideMiddle
                        font.pointSize: Controls.Typography.label
                    }
                    Loader {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        sourceComponent: root.catalogEditorMode === "xml"
                            ? catalogXmlEditor : catalogSimpleEditor
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            text: root.catalogDirty
                                ? qsTr("Save or revert changes before selecting another definition.")
                                : String(root.selectedCatalog.code || "")
                            color: root.catalogDirty
                                ? root.theme.yellow : root.theme.secondaryText
                            elide: Text.ElideMiddle
                            font.pointSize: Controls.Typography.label
                        }
                        Controls.Button {
                            theme: root.theme
                            text: root.catalogEditorMode === "xml"
                                ? qsTr("REVERT XML") : qsTr("REVERT")
                            enabled: root.catalogDirty
                            onClicked: {
                                root.catalogXmlText = root.catalogXmlOriginal
                                root.reloadCatalogSimpleRows()
                            }
                        }
                        Controls.Button {
                            objectName: "saveDefinitionCatalogXml"
                            theme: root.theme
                            text: root.catalogEditorMode === "xml"
                                ? qsTr("SAVE XML") : qsTr("SAVE")
                            highlighted: true
                            enabled: root.catalogDirty
                                && Boolean(root.selectedCatalog.identity)
                            onClicked: {
                                root.catalogSaving = true
                                if (!columnsEditorController.save_catalog_xml(
                                        Number(root.selectedCatalog.row),
                                        root.catalogXmlText))
                                    root.catalogSaving = false
                            }
                        }
                    }
                }

                Component {
                    id: catalogSimpleEditor

                    ColumnLayout {
                        spacing: 7

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Edit existing XML values visually. Use XML mode to change the structure.")
                            color: root.theme.secondaryText
                            wrapMode: Text.WordWrap
                            font.pointSize: Controls.Typography.label
                        }
                        ListView {
                            id: catalogSimpleList
                            objectName: "definitionCatalogSimpleList"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            rightMargin: catalogSimpleBar.reservedExtent + 4
                            model: root.catalogSimpleRows
                            clip: true
                            spacing: 3
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                id: catalogSimpleRow
                                required property int index
                                required property var modelData
                                readonly property bool elementRow:
                                    modelData.kind === "element"
                                readonly property bool textRow:
                                    modelData.kind === "text"

                                width: Math.max(
                                    0, catalogSimpleList.width
                                        - catalogSimpleList.rightMargin
                                )
                                height: elementRow ? 36 : textRow ? 100 : 68
                                radius: 8
                                color: elementRow
                                    ? root.theme.row : root.theme.panelDeep
                                border.width: elementRow ? 0 : 1
                                border.color: root.theme.border

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8 + Math.min(
                                        72, Number(
                                            catalogSimpleRow.modelData.depth
                                                || 0
                                        ) * 14
                                    )
                                    anchors.rightMargin: 8
                                    visible: catalogSimpleRow.elementRow
                                    spacing: 7
                                    Controls.MaterialIcon {
                                        name: "account_tree"
                                        size: 16
                                        color: root.theme.action
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: "<" + String(
                                            catalogSimpleRow.modelData.name
                                                || ""
                                        ) + ">" + (
                                            catalogSimpleRow.modelData.detail
                                                ? "  " + String(
                                                    catalogSimpleRow.modelData
                                                        .detail
                                                ) : ""
                                        )
                                        color: root.theme.primaryText
                                        elide: Text.ElideMiddle
                                        font.family: root.theme.fontFamily
                                        font.pointSize:
                                            Controls.Typography.body
                                        font.weight: Font.DemiBold
                                    }
                                }

                                Column {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    anchors.leftMargin: 8 + Math.min(
                                        72, Number(
                                            catalogSimpleRow.modelData.depth
                                                || 0
                                        ) * 14
                                    )
                                    anchors.rightMargin: 8
                                    anchors.topMargin: 5
                                    anchors.bottomMargin: 5
                                    visible: !catalogSimpleRow.elementRow
                                    spacing: 3

                                    Label {
                                        width: parent.width
                                        text: catalogSimpleRow.textRow
                                            ? qsTr("Text value")
                                            : "@" + String(
                                                catalogSimpleRow.modelData.name
                                                    || ""
                                            )
                                        color: root.theme.secondaryText
                                        elide: Text.ElideRight
                                        font.pointSize:
                                            Controls.Typography.label
                                    }
                                    Controls.TextArea {
                                        width: parent.width
                                        height: catalogSimpleRow.textRow
                                            ? 70 : 38
                                        theme: root.theme
                                        enabled: Boolean(
                                            root.selectedCatalog.identity
                                        )
                                        text: String(
                                            catalogSimpleRow.modelData.value
                                                || ""
                                        )
                                        wrapMode: TextEdit.Wrap
                                        font.family: catalogSimpleRow.textRow
                                            ? "Consolas"
                                            : root.theme.fontFamily
                                        onActiveFocusChanged: {
                                            if (!activeFocus && text !== String(
                                                    catalogSimpleRow.modelData
                                                        .value || "")) {
                                                root.updateCatalogSimpleValue(
                                                    String(
                                                        catalogSimpleRow
                                                            .modelData.path
                                                            || ""
                                                    ),
                                                    String(
                                                        catalogSimpleRow
                                                            .modelData.kind
                                                            || ""
                                                    ),
                                                    String(
                                                        catalogSimpleRow
                                                            .modelData.name
                                                            || ""
                                                    ),
                                                    text
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                id: catalogSimpleBar
                                theme: root.theme
                                flickableTarget: catalogSimpleList
                            }
                        }
                    }
                }

                Component {
                    id: catalogXmlEditor

                    Flickable {
                        id: catalogXmlViewport
                        clip: true
                        contentWidth: width
                        contentHeight: catalogXml.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds

                        Controls.TextArea {
                            id: catalogXml
                            objectName: "definitionCatalogXml"
                            width: Math.max(
                                0, catalogXmlViewport.width
                                    - catalogXmlBar.reservedExtent - 4
                            )
                            height: Math.max(
                                catalogXmlViewport.height, implicitHeight
                            )
                            theme: root.theme
                            enabled: Boolean(root.selectedCatalog.identity)
                            text: root.catalogXmlText
                            wrapMode: TextEdit.Wrap
                            font.family: "Consolas"
                            onTextChanged: if (root.catalogXmlText !== text)
                                root.catalogXmlText = text
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: catalogXmlBar
                            theme: root.theme
                            flickableTarget: catalogXmlViewport
                        }
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: columnsEditorController.error.length > 0
            text: columnsEditorController.error
            color: root.theme.red
            wrapMode: Text.WordWrap
            font.pointSize: Controls.Typography.label
        }
        RowLayout {
            Layout.fillWidth: true
            visible: root.workspaceMode === "current"
                && root.definitionTarget !== "edit_definition"
            Controls.Button {
                theme: root.theme
                text: qsTr("REVERT TABLE")
                enabled: columnsEditorController.dirty
                onClicked: columnsEditorController.cancel()
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("SAVE TABLE VIEW")
                highlighted: true
                enabled: columnsEditorController.dirty
                onClicked: columnsEditorController.apply()
            }
        }
    }
}
