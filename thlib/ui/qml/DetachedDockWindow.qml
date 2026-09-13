import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

Window {
    id: root

    required property var ownerWindow
    required property var theme
    required property string panelId
    required property string panelTitle
    required property string kind
    required property real panelX
    required property real panelY
    required property real panelWidth
    required property real panelHeight
    required property bool panelVisible
    required property bool detached
    required property bool closable
    required property Component contentComponent
    property string titleOverride: ""
    property bool nativeClosePending: false
    readonly property string displayTitle: titleOverride.length
        ? titleOverride : panelTitle

    function syncContent() {
        if (root.visible) {
            contentRelease.stop()
            dockContentLoader.active = true
        } else if (dockContentLoader.active) {
            contentRelease.restart()
        }
    }

    WindowSizing { id: sizing }

    transientParent: ownerWindow
    modality: Qt.NonModal
    flags: Qt.Window
        | Qt.WindowTitleHint
        | Qt.WindowSystemMenuHint
        | Qt.WindowMinMaxButtonsHint
        | Qt.WindowCloseButtonHint
    visible: panelVisible && detached
    title: qsTr(displayTitle)
    color: theme.workspace
    minimumWidth: sizing.dockMinimumWidth(root.kind)
    minimumHeight: sizing.dockMinimumHeight(root.kind)
    width: Math.max(
        minimumWidth,
        panelWidth * (ownerWindow ? ownerWindow.width : 1000)
    )
    height: Math.max(
        minimumHeight,
        panelHeight * (ownerWindow ? ownerWindow.height : 760)
    )
    x: (ownerWindow ? ownerWindow.x : 0)
        + panelX * (ownerWindow ? ownerWindow.width : 1000)
    y: (ownerWindow ? ownerWindow.y : 0)
        + panelY * (ownerWindow ? ownerWindow.height : 760)

    onVisibleChanged: {
        syncContent()
        if (visible) {
            nativeClosePending = false
            Qt.callLater(function() {
                root.requestActivate()
                root.raise()
            })
        } else if (
            !nativeClosePending
            && root.detached
            && root.panelVisible
        ) {
            nativeClosePending = true
            Qt.callLater(function() {
                dockModel.close_detached_panel(root.panelId)
            })
        }
    }
    Component.onCompleted: syncContent()
    onClosing: function(close) {
        close.accepted = false
        if (nativeClosePending)
            return
        nativeClosePending = true
        Qt.callLater(function() {
            dockModel.close_detached_panel(root.panelId)
        })
    }
    onXChanged: if (visible && visibility === Window.Windowed)
        geometrySave.restart()
    onYChanged: if (visible && visibility === Window.Windowed)
        geometrySave.restart()
    onWidthChanged: if (visible && visibility === Window.Windowed)
        geometrySave.restart()
    onHeightChanged: if (visible && visibility === Window.Windowed)
        geometrySave.restart()

    Timer {
        id: geometrySave
        interval: 180
        onTriggered: {
            if (!root.ownerWindow || root.ownerWindow.width <= 0
                    || root.ownerWindow.height <= 0)
                return
            dockModel.set_geometry(
                root.panelId,
                (root.x - root.ownerWindow.x) / root.ownerWindow.width,
                (root.y - root.ownerWindow.y) / root.ownerWindow.height,
                root.width / root.ownerWindow.width,
                root.height / root.ownerWindow.height
            )
        }
    }

    Timer {
        id: contentRelease
        interval: 500
        onTriggered: {
            if (!root.visible)
                dockContentLoader.active = false
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            color: root.theme.panel

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 6
                spacing: 8

                Controls.MaterialIcon {
                    name: "window-restore"
                    size: 16
                    color: root.theme.action
                }
                DockTitleLabel {
                    Layout.fillWidth: true
                    theme: root.theme
                    titleText: qsTr(root.displayTitle)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    round: true
                    iconName: "help"
                    iconSize: 14
                    iconColor: root.theme.secondaryText
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Help for this dock")
                    onClicked: windowModel.open_help("dock." + root.kind)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    round: true
                    iconName: "picture-in-picture"
                    iconSize: 14
                    iconColor: root.theme.secondaryText
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Float ") + qsTr(root.displayTitle)
                        + qsTr(" inside workspace")
                    onClicked:
                        dockModel.attach_panel_floating(root.panelId)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    round: true
                    iconName: "window-restore"
                    iconSize: 14
                    iconColor: root.theme.secondaryText
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Dock ") + qsTr(root.displayTitle)
                    onClicked: dockModel.dock_panel(root.panelId)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }

        Loader {
            id: dockContentLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: false
            sourceComponent: root.contentComponent
        }
    }
}
