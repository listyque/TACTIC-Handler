import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    readonly property bool presentationActive:
        parent ? parent.visible : visible
    property int activeIndex: 0
    property var activeRecord: ({})
    property var fieldRows: []
    property var pendingChanges: ({})
    property int dirtyCount: 0
    property bool sessionInitialized: false
    property string sessionContextFingerprint: ""

    function currentContextFingerprint() {
        const nodeIds = appController.selected_result_node_ids || []
        const selected = []
        for (let index = 0; index < nodeIds.length; ++index)
            selected.push(String(nodeIds[index] || ""))
        return [
            String(appController.current_project_code || ""),
            String(appController.current_section_key || ""),
            String(appController.current_page_key || ""),
            selected.join("\u001f")
        ].join("\u001e")
    }

    function beginSessionForCurrentContext(forceRefresh) {
        if (!root.presentationActive)
            return
        const fingerprint = root.currentContextFingerprint()
        if (!forceRefresh && root.sessionInitialized
                && fingerprint === root.sessionContextFingerprint)
            return
        columnsEditorController.begin_session()
        root.sessionContextFingerprint = fingerprint
        root.sessionInitialized = true
        root.rebuildProperties()
    }

    function rebuildProperties() {
        const records = appController.selected_result_records
        if (!records || records.length === 0) {
            activeIndex = 0
            activeRecord = ({})
            fieldRows = []
            pendingChanges = ({})
            dirtyCount = 0
            return
        }
        activeIndex = Math.max(0, Math.min(activeIndex, records.length - 1))
        activeRecord = records[activeIndex]
        fieldRows = columnsEditorController.order_field_records(
            appController.editable_result_field_records(
                String(activeRecord.nodeId || "")
            )
        )
        pendingChanges = ({})
        dirtyCount = 0
    }

    function saveChanges() {
        appController.update_selected_item_fields(
            String(activeRecord.nodeId || ""), pendingChanges
        )
    }

    function markChanged(fieldName, originalValue, value) {
        const changes = Object.assign({}, pendingChanges)
        if (String(value) === String(originalValue))
            delete changes[fieldName]
        else
            changes[fieldName] = String(value)
        pendingChanges = changes
        dirtyCount = Object.keys(changes).length
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    Connections {
        target: appController
        enabled: root.presentationActive
        function onSelected_node_changed() {
            root.beginSessionForCurrentContext(true)
        }
        function onProject_changed() {
            root.beginSessionForCurrentContext(false)
        }
        function onSection_state_changed() {
            root.beginSessionForCurrentContext(false)
        }
    }
    Connections {
        target: columnsEditorController
        enabled: root.presentationActive
        function onApplied() { root.rebuildProperties() }
    }
    Component.onCompleted: root.beginSessionForCurrentContext(false)
    onPresentationActiveChanged:
        root.beginSessionForCurrentContext(false)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            spacing: 8
            Controls.MaterialIcon { name: "table"; size: 16; color: root.theme.action }
            Label {
                text: qsTr("Database Editor")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
            }
            Rectangle {
                Layout.preferredWidth: selectionLabel.implicitWidth + 18
                Layout.preferredHeight: 24
                radius: 8
                color: root.theme.secondaryContainer
                Label {
                    id: selectionLabel
                    anchors.centerIn: parent
                    text: appController.selected_result_count
                        + qsTr(" selected")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
            }
            Item { Layout.fillWidth: true }
            Label {
                visible: root.dirtyCount > 0
                text: root.dirtyCount + qsTr(" unsaved")
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            }
            Controls.Button {
                id: saveButton
                theme: root.theme
                Layout.preferredHeight: 30
                text: qsTr("Save changes")
                highlighted: true
                enabled: root.dirtyCount > 0 && !appController.loading
                onClicked: root.saveChanges()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: visible
            visible: appController.selected_result_count > 0
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.border
            clip: true

            RowLayout {
                anchors.fill: parent
                spacing: 0

                Item {
                    Layout.preferredWidth: appController.selected_result_count > 1
                        ? Math.min(250, parent.width * 0.32) : 0
                    Layout.fillHeight: true
                    visible: width > 0

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            color: root.theme.surfaceContainerHigh
                            Label {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                text: qsTr("SELECTED OBJECTS")
                                verticalAlignment: Text.AlignVCenter
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                        }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: appController.selected_result_records
                            delegate: Rectangle {
                                required property var modelData
                                required property int index
                                width: ListView.view.width
                                height: 48
                                color: index === root.activeIndex
                                    ? root.theme.selected
                                    : objectMouse.containsMouse
                                      ? root.theme.rowHover
                                      : index % 2 ? root.theme.row : root.theme.panel
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 8
                                    spacing: 8
                                    Rectangle {
                                        Layout.preferredWidth: 28
                                        Layout.preferredHeight: 28
                                        radius: 9
                                        color: root.theme.secondaryContainer
                                        Label {
                                            anchors.centerIn: parent
                                            text: String(modelData.title || "?")
                                                .slice(0, 2).toUpperCase()
                                            color: root.theme.primaryText
                                            font.pointSize: Controls.Typography.label
                                            font.weight: Font.Bold
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 1
                                        Label {
                                            Layout.fillWidth: true
                                            text: modelData.title || modelData.code
                                            elide: Text.ElideRight
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            font.weight: Font.Medium
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: modelData.code || modelData.type
                                            elide: Text.ElideRight
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                        }
                                    }
                                }
                                MouseArea {
                                    id: objectMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.activeIndex = index
                                        root.rebuildProperties()
                                    }
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                        }
                    }
                    Rectangle {
                        anchors.right: parent.right
                        width: 1
                        height: parent.height
                        color: root.theme.separator
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        color: root.theme.surfaceContainerHigh
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 12
                            Label {
                                text: qsTr("FIELD")
                                Layout.preferredWidth: Math.min(210, parent.width * 0.34)
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                            Label {
                                text: root.activeRecord.title || "VALUE"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                            }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 1
                        model: root.fieldRows
                        delegate: Rectangle {
                            id: propertyRow
                            required property var modelData
                            required property int index
                            property string fieldName: String(
                                modelData.fieldName || ""
                            )
                            property string fieldLabel: String(
                                modelData.fieldLabel || fieldName
                            )
                            property string originalValue:
                                modelData.fieldValue === undefined
                                ? "" : String(modelData.fieldValue)
                            property bool changed:
                                root.pendingChanges[fieldName] !== undefined
                            width: ListView.view.width
                            height: 40
                            color: changed
                                ? root.theme.secondaryContainer
                                : index % 2 ? root.theme.row : root.theme.panel

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 8
                                spacing: 12
                                Label {
                                    Layout.preferredWidth: Math.min(
                                        210, propertyRow.width * 0.34
                                    )
                                    text: propertyRow.fieldLabel
                                    elide: Text.ElideRight
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                }
                                Controls.TextField {
                                    id: valueEditor
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    text: propertyRow.originalValue
                                    selectByMouse: true
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    leftPadding: 9
                                    rightPadding: 9
                                    onTextEdited: root.markChanged(
                                        propertyRow.fieldName,
                                        propertyRow.originalValue,
                                        text
                                    )
                                    background: Rectangle {
                                        radius: 8
                                        color: valueEditor.activeFocus
                                            ? root.theme.surfaceContainerLow
                                            : "transparent"
                                        border.width: valueEditor.activeFocus ? 1 : 0
                                        border.color: root.theme.action
                                    }
                                }
                                Controls.MaterialIcon {
                                    visible: propertyRow.changed
                                    name: "edit"
                                    size: 13
                                    color: root.theme.action
                                }
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: appController.selected_result_count > 1
                ? 62 : 0
            visible: height > 0
            radius: 12
            color: root.theme.surfaceContainerHigh

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8
                ColumnLayout {
                    Layout.preferredWidth: 190
                    spacing: 2
                    Label {
                        text: qsTr("APPLY TO ALL SELECTED")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }
                    Controls.ComboBox {
                        id: bulkColumn
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        model: appController.selected_result_fields
                        enabled: count > 0
                        displayText: currentText || "Choose field"
                        font.pointSize: Controls.Typography.label
                    }
                }
                Controls.TextField {
                    id: bulkValue
                    theme: root.theme
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredHeight: 30
                    placeholderText: qsTr("New value for all selected objects")
                    color: root.theme.primaryText
                    selectByMouse: true
                    background: Rectangle {
                        radius: 9
                        color: root.theme.surfaceContainerLow
                        border.width: bulkValue.activeFocus ? 1 : 0
                        border.color: root.theme.action
                    }
                    onAccepted: bulkApply.clicked()
                }
                Controls.Button {
                    id: bulkApply
                    theme: root.theme
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredHeight: 30
                    text: qsTr("Apply to ") + appController.selected_result_count
                    enabled: bulkColumn.currentText.length > 0
                        && appController.selected_result_count > 1
                        && !appController.loading
                    onClicked: appController.update_selected_items(
                        bulkColumn.currentText, bulkValue.text
                    )
                }
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.fillHeight: appController.selected_result_count === 0
            visible: appController.selected_result_count === 0
            text: qsTr("Select one or more objects to edit database fields")
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
        }
    }
}
