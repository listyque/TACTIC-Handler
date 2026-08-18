import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme

    Connections {
        target: sobjectLinkController
        function onSaved() {
            windowModel.close_window("link_sobjects")
        }
    }

    Connections {
        target: sobjectLinkController
        function onSessionStarted() {
            availableSearchDelay.stop()
            linkedSearchDelay.stop()
            availableSearch.clear()
            linkedSearch.clear()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 68
            color: root.theme.panel

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 14
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer

                    MaterialIcon {
                        anchors.centerIn: parent
                        name: "link"
                        size: 18
                        color: root.theme.action
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        Layout.fillWidth: true
                        text: {
                            const title = sobjectLinkController.target_title
                            const code = sobjectLinkController.target_code
                            if (!title)
                                return qsTr("Select an instance relation")
                            return code && code !== title
                                ? title + " (" + code + ")" : title
                        }
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }

                    Label {
                        Layout.fillWidth: true
                        text: sobjectLinkController.parent_title.length > 0
                            ? qsTr("Related to") + ": "
                                + sobjectLinkController.parent_title
                            : qsTr("Choose objects to link")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                        elide: Text.ElideRight
                    }
                }

                RefreshIconButton {
                    theme: root.theme
                    enabled: !sobjectLinkController.busy
                    toolTip: qsTr("Reload related objects")
                    onClicked: sobjectLinkController.refresh()
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        SplitView {
            id: linkSplit

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 14
            orientation: Qt.Horizontal

            handle: Item {
                implicitWidth: 54

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 1
                    color: root.theme.outlineVariant
                }

                CompactIconButton {
                    anchors.centerIn: parent
                    width: 42
                    height: 42
                    theme: root.theme
                    iconName: sobjectLinkController.transfer_direction
                        === "remove" ? "arrow-left" : "arrow-forward"
                    iconSize: 18
                    round: true
                    elevated: true
                    badgeCount: sobjectLinkController.selected_count
                    enabled: sobjectLinkController.can_transfer
                    toolTip: sobjectLinkController.transfer_direction
                        === "remove"
                        ? qsTr("Remove selected links")
                        : qsTr("Link selected objects")
                    onClicked: sobjectLinkController.transfer_selected()
                }
            }

            Rectangle {
                SplitView.preferredWidth: Math.max(280, linkSplit.width * 0.5 - 27)
                SplitView.minimumWidth: 250
                color: root.theme.panelDeep
                radius: root.theme.surfaceRadius

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Md3TextField {
                        id: availableSearch
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Search available objects")
                        onTextEdited: availableSearchDelay.restart()
                        onAccepted: {
                            availableSearchDelay.stop()
                            sobjectLinkController.search_available(text)
                        }
                    }

                    Timer {
                        id: availableSearchDelay
                        interval: 280
                        onTriggered: sobjectLinkController.search_available(
                            availableSearch.text
                        )
                    }

                    LinkList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: qsTr("Available objects")
                        emptyText: availableSearch.text.length > 0
                            ? qsTr("No matching objects")
                            : qsTr("No available objects")
                        sourceModel: linkAvailableModel
                        loading: sobjectLinkController.loading_available
                        canLoadMore: sobjectLinkController.can_load_more
                        totalCount: sobjectLinkController.available_total
                        onRowSelected: function(row, additive) {
                            sobjectLinkController.select_available(row, additive)
                        }
                        onLoadMoreRequested:
                            sobjectLinkController.load_more_available()
                    }
                }
            }

            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 250
                color: root.theme.panelDeep
                radius: root.theme.surfaceRadius

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Md3TextField {
                        id: linkedSearch
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Search linked objects")
                        onTextEdited: linkedSearchDelay.restart()
                        onAccepted: {
                            linkedSearchDelay.stop()
                            sobjectLinkController.search_linked(text)
                        }
                    }

                    Timer {
                        id: linkedSearchDelay
                        interval: 180
                        onTriggered: sobjectLinkController.search_linked(
                            linkedSearch.text
                        )
                    }

                    LinkList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: qsTr("Linked objects")
                        emptyText: linkedSearch.text.length > 0
                            ? qsTr("No matching linked objects")
                            : qsTr("No linked objects")
                        sourceModel: linkCurrentModel
                        loading: sobjectLinkController.loading_linked
                        totalCount: linkCurrentModel.count
                        onRowSelected: function(row, additive) {
                            sobjectLinkController.select_linked(row, additive)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: sobjectLinkController.error.length > 0
                ? Math.max(44, errorLabel.implicitHeight + 20) : 0
            visible: sobjectLinkController.error.length > 0
            color: root.theme.errorContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 10

                MaterialIcon {
                    name: "error"
                    size: 17
                    color: root.theme.error
                }

                Label {
                    id: errorLabel
                    Layout.fillWidth: true
                    text: sobjectLinkController.error
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: root.theme.panel

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.separator
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 9

                Label {
                    Layout.fillWidth: true
                    text: {
                        const count = sobjectLinkController.selected_count
                        if (count > 0)
                            return qsTr("Selected") + ": " + count
                        return sobjectLinkController.dirty
                            ? qsTr("Links have unsaved changes")
                            : qsTr("Select objects and use the center button")
                    }
                    color: sobjectLinkController.dirty
                        ? root.theme.action : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    elide: Text.ElideRight
                }

                Md3BusyIndicator {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    uiTheme: root.theme
                    visible: sobjectLinkController.busy
                    running: visible
                }

                Md3Button {
                    theme: root.theme
                    text: qsTr("Close")
                    enabled: !sobjectLinkController.busy
                    onClicked: windowModel.close_window("link_sobjects")
                }

                Md3Button {
                    theme: root.theme
                    text: qsTr("Save")
                    icon.name: "save"
                    highlighted: true
                    enabled: !sobjectLinkController.busy
                        && sobjectLinkController.dirty
                    onClicked: sobjectLinkController.save()
                }
            }
        }
    }
}
