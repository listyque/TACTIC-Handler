import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    objectName: "deleteSObjectView"
    required property var theme

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Rectangle {
            id: deleteHeader
            objectName: 'deleteSObjectHeader'
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            radius: root.theme.sectionRadius
            color: root.theme.surfaceContainer
            border.width: 0

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 12
                Rectangle {
                    Layout.preferredWidth: 42
                    Layout.preferredHeight: 42
                    radius: root.theme.itemRadius
                    color: root.theme.errorContainer
                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "delete"
                        size: 22
                        color: root.theme.error
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: sobjectDeleteController.targetCount === 1 ? qsTr("Delete sObject") : qsTr("Delete sObjects")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("The selected objects and checked dependencies will be permanently removed from TACTIC.")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
                Controls.StatusChip {
                    theme: root.theme
                    text: String(sobjectDeleteController.targetCount)
                    iconName: 'sobject'
                    accentColor: root.theme.error
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "help"
                    toolTip: qsTr("Deletion help")
                    onClicked: windowModel.open_help("deleting_objects")
                }
            }
        }

        Rectangle {
            objectName: 'deleteSObjectTargetCard'
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(132, Math.max(56, targetsList.contentHeight + 20))
            radius: root.theme.sectionRadius
            color: root.theme.surfaceContainerHigh
            border.width: 0

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 1
                anchors.topMargin: root.theme.sectionRadius / 2
                anchors.bottomMargin: root.theme.sectionRadius / 2
                width: 3
                radius: width / 2
                color: root.theme.error
            }

            ListView {
                id: targetsList
                objectName: "deleteSObjectTargets"
                anchors.fill: parent
                anchors.margins: 10
                anchors.leftMargin: 14
                clip: true
                spacing: 2
                model: sobjectDeleteController.targets
                delegate: RowLayout {
                    required property var modelData
                    width: ListView.view.width
                    height: 28
                    spacing: 8
                    Controls.MaterialIcon {
                        name: "sobject"
                        size: 14
                        color: root.theme.error
                    }
                    Label {
                        Layout.fillWidth: true
                        text: modelData.title
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideRight
                    }
                }
                footer: Label {
                    width: targetsList.width
                    height: sobjectDeleteController.remainingTargetCount > 0 ? 26 : 0
                    visible: height > 0
                    text: qsTr("and %1 more sObjects").arg(sobjectDeleteController.remainingTargetCount)
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    verticalAlignment: Text.AlignVCenter
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: sobjectDeleteController.ready && sobjectDependencyModel.count() > 0
            spacing: 8
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Dependencies")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Choose related records to remove with the selected objects.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideRight
                }
            }
            Controls.StatusChip {
                theme: root.theme
                text: qsTr("%1 of %2 selected").arg(sobjectDeleteController.selectedDependencyCount).arg(sobjectDeleteController.dependencyCount)
                iconName: "check"
                accentColor: root.theme.secondaryText
            }
        }

        ScrollView {
            id: dependenciesScroll
            objectName: "deleteSObjectDependencies"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            visible: sobjectDeleteController.ready && sobjectDependencyModel.count() > 0
            leftPadding: 6
            rightPadding: 6
            topPadding: 6
            bottomPadding: 6
            background: Rectangle {
                radius: root.theme.sectionRadius
                color: root.theme.surfaceContainerLow
                border.width: 0
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }

            ColumnLayout {
                width: dependenciesScroll.availableWidth
                spacing: 8

                Repeater {
                    objectName: "deleteDependencyRepeater"
                    model: sobjectDependencyModel
                    delegate: Rectangle {
                        id: dependencyGroup
                        objectName: "deleteDependencyGroup_" + index
                        required property int index
                        required property string searchType
                        required property string searchTypeTitle
                        required property string iconName
                        required property int count
                        required property bool checked
                        required property bool defaultChecked
                        required property bool expanded
                        required property var items
                        Layout.fillWidth: true
                        implicitHeight: groupColumn.implicitHeight + 4
                        radius: root.theme.sectionRadius
                        color: dependencyGroup.checked ? root.theme.surfaceContainerHighest : root.theme.surfaceContainerHigh
                        border.width: 0
                        clip: true

                        ColumnLayout {
                            id: groupColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 1
                            spacing: 0

                            RowLayout {
                                objectName: "deleteDependencyHeader_" + dependencyGroup.index
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                spacing: 8
                                Controls.CheckBox {
                                    objectName: "deleteDependencyCheck_" + dependencyGroup.index
                                    theme: root.theme
                                    Layout.leftMargin: 7
                                    Layout.preferredWidth: 24
                                    Layout.preferredHeight: 24
                                    Layout.alignment: Qt.AlignVCenter
                                    leftPadding: 0
                                    rightPadding: 0
                                    spacing: 0
                                    checked: dependencyGroup.checked
                                    prominent: dependencyGroup.defaultChecked
                                    onClicked: sobjectDeleteController.set_group_checked(dependencyGroup.index, checked)
                                }
                                Controls.CompactIconButton {
                                    objectName: "deleteDependencyExpand_" + dependencyGroup.index
                                    theme: root.theme
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    Layout.alignment: Qt.AlignVCenter
                                    iconName: dependencyGroup.expanded ? "expand-less" : "expand-more"
                                    iconSize: 14
                                    toolTip: dependencyGroup.expanded ? qsTr("Hide dependencies") : qsTr("Show dependencies")
                                    onClicked: sobjectDeleteController.toggle_group(dependencyGroup.index)
                                }
                                Controls.MaterialIcon {
                                    Layout.preferredWidth: 18
                                    Layout.preferredHeight: 18
                                    Layout.alignment: Qt.AlignVCenter
                                    name: dependencyGroup.iconName
                                    size: 18
                                    color: root.theme.secondaryText
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    Layout.alignment: Qt.AlignVCenter
                                    spacing: 0
                                    Label {
                                        Layout.fillWidth: true
                                        text: dependencyGroup.searchTypeTitle
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: qsTr("%1 related items").arg(dependencyGroup.count)
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }

                            Loader {
                                Layout.fillWidth: true
                                Layout.leftMargin: 4
                                Layout.rightMargin: 4
                                Layout.bottomMargin: 4
                                active: dependencyGroup.expanded
                                visible: active
                                sourceComponent: Component {
                                    ColumnLayout {
                                        spacing: 0
                                        ListView {
                                            id: dependencyItems
                                            objectName: "deleteDependencyItems_" + dependencyGroup.index
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: Math.min(320, Math.max(44, contentHeight))
                                            clip: true
                                            model: dependencyGroup.items
                                            boundsBehavior: Flickable.StopAtBounds
                                            delegate: Rectangle {
                                                objectName: "deleteDependencyItem_" + index
                                                required property int index
                                                required property var modelData
                                                width: ListView.view.width
                                                height: String(modelData.details || "").length > 0 ? 52 : 44
                                                bottomLeftRadius: index === ListView.view.count - 1
                                                    ? Math.max(0, dependencyGroup.radius - 4) : 0
                                                bottomRightRadius: bottomLeftRadius
                                                color: index % 2 ? root.theme.surfaceContainerLow : root.theme.surfaceContainer
                                                antialiasing: bottomLeftRadius > 0
                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 14
                                                    anchors.rightMargin: 14
                                                    spacing: 10
                                                    Controls.MaterialIcon {
                                                        name: dependencyGroup.iconName
                                                        size: 17
                                                        color: root.theme.secondaryText
                                                    }
                                                    ColumnLayout {
                                                        Layout.fillWidth: true
                                                        spacing: 1
                                                        Label {
                                                            objectName: "deleteDependencyItemTitle"
                                                            Layout.fillWidth: true
                                                            text: modelData.title
                                                            color: root.theme.primaryText
                                                            font.family: root.theme.fontFamily
                                                            font.pointSize: Controls.Typography.body
                                                            font.weight: Font.Medium
                                                            elide: Text.ElideRight
                                                        }
                                                        Label {
                                                            objectName: "deleteDependencyItemDetails"
                                                            Layout.fillWidth: true
                                                            visible: text.length > 0
                                                            text: String(modelData.details || "")
                                                            color: root.theme.secondaryText
                                                            font.family: root.theme.fontFamily
                                                            font.pointSize: Controls.Typography.caption
                                                            elide: Text.ElideRight
                                                        }
                                                    }
                                                }
                                            }
                                            ScrollBar.vertical: Controls.ScrollBar {
                                                theme: root.theme
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            objectName: 'deleteSObjectEmptyState'
            Layout.fillWidth: true
            Layout.fillHeight: sobjectDeleteController.ready && sobjectDependencyModel.count() === 0
            visible: sobjectDeleteController.ready && sobjectDependencyModel.count() === 0
            radius: root.theme.sectionRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - 40, 420)
                spacing: 8
                Controls.MaterialIcon {
                    Layout.alignment: Qt.AlignHCenter
                    name: "check-circle"
                    size: 28
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No dependencies were found. Only the selected objects will be deleted.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        Rectangle {
            objectName: 'deleteSObjectErrorBanner'
            Layout.fillWidth: true
            Layout.preferredHeight: errorMessage.implicitHeight + 20
            visible: sobjectDeleteController.error.length > 0
            radius: root.theme.itemRadius
            color: root.theme.errorContainer
            border.width: 1
            border.color: root.theme.error

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8
                Controls.MaterialIcon {
                    name: "warning"
                    size: 18
                    color: root.theme.error
                }
                Label {
                    id: errorMessage
                    Layout.fillWidth: true
                    text: sobjectDeleteController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
            }
        }

        Controls.DockWorkspaceFooter {
            id: deleteFooter
            objectName: 'deleteSObjectFooter'
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            roundTopLeft: true
            roundTopRight: true

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8
                Label {
                    Layout.fillWidth: true
                    text: sobjectDeleteController.ready ? qsTr("%1 dependencies selected").arg(sobjectDeleteController.selectedDependencyCount) : qsTr("Reviewing selected objects")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                }
                Controls.Button {
                    visible: sobjectDeleteController.error.length > 0 && !sobjectDeleteController.ready
                    theme: root.theme
                    text: qsTr("Retry")
                    icon.name: "refresh"
                    onClicked: sobjectDeleteController.retry()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: sobjectDeleteController.cancel()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Delete")
                    icon.name: "delete"
                    destructive: true
                    highlighted: true
                    enabled: sobjectDeleteController.ready && !sobjectDeleteController.busy && !sobjectDeleteController.deleting
                    onClicked: sobjectDeleteController.confirm_delete()
                }
            }
        }
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        anchors.margins: 12
        anchors.topMargin: deleteHeader.height + 22
        anchors.bottomMargin: deleteFooter.height + 22
        visible: sobjectDeleteController.busy || sobjectDeleteController.deleting
        theme: root.theme
        message: sobjectDeleteController.deleting ? qsTr("Deleting selected objects…") : qsTr("Discovering dependencies…")
        cancellable: true
        onCancelRequested: sobjectDeleteController.cancel()
    }
}
