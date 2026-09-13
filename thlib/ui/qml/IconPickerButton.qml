import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string iconName: ""
    property bool tacticCompatibleOnly: false
    property int popupWidth: 560
    property int popupHeight: 440
    signal iconSelected(string name)

    implicitWidth: 44
    implicitHeight: 44

    function fallbackFontAwesomeNames() {
        const names = ({})
        Object.keys(iconSource.solidGlyphs || {}).forEach(function(name) {
            names[String(name)] = true
        })
        return Object.keys(names).sort()
    }

    function rebuildSets() {
        if (tacticCompatibleOnly
                || typeof iconFontCatalog === "undefined") {
            setOptions = [{
                "value": "fontawesome-solid",
                "label": qsTr("TACTIC / Font Awesome")
            }]
        } else {
            setOptions = iconFontCatalog.sets.map(function(record) {
                return {
                    "value": String(record.value),
                    "label": qsTr(String(record.label))
                }
            })
        }
        const separator = iconName.indexOf(":")
        const explicitSet = separator > 0
            ? iconName.slice(0, separator) : ""
        const configuredSet = typeof appController !== "undefined"
            ? String(appController.icon_set || "material-design")
            : "material-design"
        const preferredSet = tacticCompatibleOnly
            ? "fontawesome-solid"
            : explicitSet.length > 0
                ? explicitSet
                : configuredSet === "automatic"
                    ? "material-design" : configuredSet
        activeSet = setOptions.some(function(record) {
            return record.value === preferredSet
        }) ? preferredSet : setOptions[0].value
        for (let index = 0; index < setOptions.length; ++index) {
            if (setOptions[index].value === activeSet) {
                setSelector.currentIndex = index
                break
            }
        }
    }

    function applyFilter() {
        const query = String(searchField.text || "").trim().toLowerCase()
        if (typeof iconFontCatalog !== "undefined") {
            filteredIcons = iconFontCatalog.search(activeSet, query)
            return
        }
        const icons = fallbackFontAwesomeNames()
        filteredIcons = query.length === 0 ? icons : icons.filter(
            function(name) {
                return String(name).toLowerCase().indexOf(query) >= 0
            }
        )
    }

    function storedIconName(name) {
        return tacticCompatibleOnly ? name : activeSet + ":" + name
    }

    function iconIsSelected(name) {
        return iconName === storedIconName(name)
            || (iconName.indexOf(":") < 0 && iconName === name)
    }

    property string activeSet: "material-design"
    property var setOptions: []
    property var filteredIcons: []

    Controls.MaterialIcon {
        id: iconSource
        visible: false
        color: root.theme.primaryText
    }

    Controls.CompactIconButton {
        id: pickerButton
        anchors.fill: parent
        theme: root.theme
        iconName: root.iconName.length > 0 ? root.iconName : "image"
        toolTip: qsTr("Choose icon")
        onPressed: pickerPopup.rememberSourceOpen()
        onClicked: pickerPopup.toggleBelowItem(pickerButton, true, 6)
    }

    Controls.Popup {
        id: pickerPopup
        objectName: "sidebarIconPopup"
        parent: Overlay.overlay
        theme: root.theme
        // Native popups re-evaluate their implicit size when the grid fills.
        // Keep the library width independent of the narrow invocation button.
        implicitWidth: Math.min(root.popupWidth, maximumAvailableWidth)
        implicitHeight: Math.min(root.popupHeight, maximumAvailableHeight)
        width: implicitWidth
        height: implicitHeight
        focus: true
        padding: 10

        onOpened: {
            root.rebuildSets()
            root.applyFilter()
            searchField.forceActiveFocus()
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Controls.MaterialIcon {
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
                    font.pointSize: Controls.Typography.label
                }
                Controls.ComboBox {
                    id: setSelector
                    objectName: "iconLibrarySetSelector"
                    visible: count > 1
                    Layout.preferredWidth: 190
                    theme: root.theme
                    model: root.setOptions
                    textRole: "label"
                    valueRole: "value"
                    onActivated: {
                        root.activeSet = String(currentValue)
                        root.applyFilter()
                    }
                }
            }

            Controls.TextField {
                id: searchField
                objectName: "sidebarIconSearch"
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
                    objectName: "sidebarIconGrid"
                    anchors.fill: parent
                    anchors.margins: 6
                    clip: true
                    readonly property real gridWidth: Math.max(1, width - rightMargin)
                    rightMargin: iconScrollBar.reservedExtent + 4
                    cellWidth: gridWidth / Math.max(1, Math.floor(gridWidth / 96))
                    cellHeight: 76
                    model: root.filteredIcons
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Controls.PopupAction {
                        id: iconDelegate
                        required property string modelData
                        width: iconGrid.cellWidth
                        height: iconGrid.cellHeight
                        hoverEnabled: true
                        padding: 3
                        Accessible.name: modelData
                        background: null
                        contentItem: Rectangle {
                            radius: root.theme.itemRadius
                            color: root.iconIsSelected(
                                    iconDelegate.modelData)
                                ? root.theme.selected
                                : iconDelegate.down
                                    ? root.theme.surfaceContainerHighest
                                    : iconDelegate.hovered
                                        ? root.theme.rowHover : "transparent"
                            border.width:
                                root.iconIsSelected(iconDelegate.modelData)
                                    ? 1 : 0
                            border.color: root.theme.action

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 3

                                Controls.MaterialIcon {
                                    Layout.alignment: Qt.AlignHCenter
                                    name: root.activeSet + ":"
                                        + iconDelegate.modelData
                                    size: 28
                                    color: root.iconIsSelected(
                                            iconDelegate.modelData)
                                        ? root.theme.selectedText
                                        : root.theme.primaryText
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: iconDelegate.modelData
                                    color: root.iconIsSelected(
                                            iconDelegate.modelData)
                                        ? root.theme.selectedText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    horizontalAlignment: Text.AlignHCenter
                                    elide: Text.ElideRight
                                }
                            }
                        }
                        onClicked: {
                            root.iconSelected(root.storedIconName(
                                iconDelegate.modelData
                            ))
                            pickerPopup.close()
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
                        id: iconScrollBar
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
                    font.pointSize: Controls.Typography.body
                }
            }
        }
    }
}
