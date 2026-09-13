import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Item {
    id: root

    required property var theme
    property string iconName: "info"
    property string title: ""
    property string message: ""
    property real preferredHeight: 140
    property real maximumContentWidth: 440
    property real horizontalViewportMargin: 24
    readonly property real availableViewportWidth:
        parent && parent.width > 0
            ? Math.max(0, parent.width - horizontalViewportMargin * 2)
            : maximumContentWidth

    implicitWidth: maximumContentWidth
    implicitHeight: preferredHeight
    Layout.fillWidth: true
    Layout.minimumWidth: 0
    Layout.preferredHeight: preferredHeight

    // The outer Item owns a stable intrinsic size.  Making the root itself a
    // ColumnLayout would derive its implicit width from labels whose width is
    // constrained by that same parent, collapsing nested layouts to the
    // icon's width.
    ColumnLayout {
        anchors.centerIn: parent
        width: root.width
        spacing: 8

        Controls.MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            name: root.iconName
            size: 30
            color: root.theme.secondaryText
        }

        Label {
            id: titleLabel
            objectName: "emptyStateTitle"
            visible: root.title.length > 0
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.maximumWidth: Math.min(
                root.maximumContentWidth, Math.max(0, root.width)
            )
            text: root.title
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }

        Label {
            id: messageLabel
            objectName: "emptyStateMessage"
            visible: root.message.length > 0
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.maximumWidth: Math.min(
                root.maximumContentWidth, Math.max(0, root.width)
            )
            text: root.message
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
    }
}
