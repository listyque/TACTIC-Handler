import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property string iconName: ""
    property int popupWidth: 560
    property int popupHeight: 440
    signal iconSelected(string name)

    implicitWidth: 44
    implicitHeight: 44

    function rebuildIcons() {
        const names = ({})
        Object.keys(iconSource.solidGlyphs || {}).forEach(function(name) {
            names[String(name)] = true
        })
        Object.keys(iconSource.regularGlyphs || {}).forEach(function(name) {
            names[String(name)] = true
        })
        allIcons = Object.keys(names).sort()
        applyFilter()
    }

    function applyFilter() {
        const query = String(searchField.text || "").trim().toLowerCase()
        filteredIcons = query.length === 0
            ? allIcons
            : allIcons.filter(function(name) {
                return String(name).toLowerCase().indexOf(query) >= 0
            })
    }

    property var allIcons: []
    property var filteredIcons: []

    MaterialIcon {
        id: iconSource
        visible: false
    }

    CompactIconButton {
        id: pickerButton
        anchors.fill: parent
        theme: root.theme
        iconName: root.iconName.length > 0 ? root.iconName : "image"
        toolTip: qsTr("Choose icon")
        onClicked: pickerPopup.opened ? pickerPopup.close() : pickerPopup.open()
    }

    Md3Popup {
        id: pickerPopup
        theme: root.theme
        x: pickerButton.width - width
        y: pickerButton.height + 6
        width: root.popupWidth
        height: root.popupHeight
        padding: 10

        onOpened: {
            root.rebuildIcons()
            searchField.forceActiveFocus()
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                MaterialIcon {
                    name: "shapes"
                    size: 19
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Icon library")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                Label {
                    text: String(root.filteredIcons.length)
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                }
            }

            Md3TextField {
                id: searchField
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Search icons")
                onTextChanged: root.applyFilter()
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: root.theme.surfaceRadius
                color: root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                GridView {
                    id: iconGrid
                    anchors.fill: parent
                    anchors.margins: 6
                    clip: true
                    cellWidth: 104
                    cellHeight: 76
                    model: root.filteredIcons
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Item {
                        id: iconDelegate
                        required property string modelData
                        width: iconGrid.cellWidth
                        height: iconGrid.cellHeight

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 3
                            radius: root.theme.itemRadius
                            color: root.iconName === iconDelegate.modelData
                                ? root.theme.selected
                                : iconMouse.containsMouse
                                    ? root.theme.rowHover : "transparent"
                            border.width: root.iconName === iconDelegate.modelData ? 1 : 0
                            border.color: root.theme.action

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 3

                                MaterialIcon {
                                    Layout.alignment: Qt.AlignHCenter
                                    name: iconDelegate.modelData
                                    size: 28
                                    color: root.iconName === iconDelegate.modelData
                                        ? root.theme.selectedText
                                        : root.theme.primaryText
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: iconDelegate.modelData
                                    color: root.iconName === iconDelegate.modelData
                                        ? root.theme.selectedText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.caption
                                    horizontalAlignment: Text.AlignHCenter
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                id: iconMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.iconSelected(iconDelegate.modelData)
                                    pickerPopup.close()
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: iconGrid
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: root.filteredIcons.length === 0
                    text: qsTr("No matching icons")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                }
            }
        }
    }
}
