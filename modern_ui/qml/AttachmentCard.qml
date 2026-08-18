import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property string title
    required property string extension
    required property string previewUrl
    property string sizeText: ""
    property bool local: false
    property bool animatePreview: true
    signal activated()
    signal contextRequested(real localX, real localY)

    readonly property string extensionLabel: {
        const value = String(root.extension || "FILE").toUpperCase()
        return value.length > 5 ? value.slice(0, 5) : value
    }
    readonly property bool imageAttachment: [
        "JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP", "TIF", "TIFF",
        "TGA", "EXR", "HDR", "SVG", "HEIC", "AVIF"
    ].indexOf(String(root.extension || "").toUpperCase()) >= 0

    implicitHeight: imageAttachment
        ? Math.min(310, Math.max(220, width * 0.68))
        : 64
    radius: 14
    color: attachmentHover.hovered
        ? root.theme.surfaceContainerHighest
        : root.theme.surfaceContainerHigh
    border.width: 1
    border.color: root.theme.outlineVariant

    Behavior on color {
        ColorAnimation {
            duration: root.theme.motionFast
            easing.type: Easing.OutCubic
        }
    }

    HoverHandler {
        id: attachmentHover
        cursorShape: Qt.PointingHandCursor
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                root.contextRequested(mouse.x, mouse.y)
            else
                root.activated()
        }
    }

    RowLayout {
        visible: !root.imageAttachment
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 7
        spacing: 10

        Rectangle {
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            radius: 22
            color: root.theme.action
            clip: true

            Image {
                anchors.fill: parent
                visible: root.imageAttachment && root.previewUrl.length > 0
                source: visible ? root.previewUrl : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
                sourceSize.width: 44
                sourceSize.height: 44
            }

            Label {
                anchors.centerIn: parent
                width: parent.width - 6
                visible: root.previewUrl.length === 0
                text: root.extensionLabel
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                color: root.theme.selectedText
                font.family: root.theme.fontFamily
                font.pixelSize: root.extensionLabel.length > 4 ? 8 : 9
                font.weight: Font.Bold
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            Label {
                Layout.fillWidth: true
                text: root.title || qsTr("Attachment")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideMiddle
            }

            Label {
                Layout.fillWidth: true
                visible: root.sizeText.length > 0
                text: root.sizeText
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.label
                elide: Text.ElideRight
            }
        }

        CompactIconButton {
            theme: root.theme
            iconName: root.local ? "open_in_new" : "download"
            iconColor: root.local ? root.theme.action : root.theme.primaryText
            toolTip: root.local
                ? qsTr("Open attachment") : qsTr("Download attachment")
            onClicked: root.activated()
        }
    }

    ColumnLayout {
        visible: root.imageAttachment
        anchors.fill: parent
        anchors.margins: 8
        spacing: 7

        ItemPreview {
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            source: root.imageAttachment ? root.previewUrl : ""
            fallbackIcon: "image"
            fallbackText: root.previewUrl.length > 0 ? "" : root.extensionLabel
            accent: root.theme.action
            cornerRadius: 10
            outlined: true
            previewSize: 180
            fillMode: Image.PreserveAspectFit
            animateAppearance: root.animatePreview
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            Layout.leftMargin: 4
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    Layout.fillWidth: true
                    text: root.title || qsTr("Image attachment")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideMiddle
                }

                Label {
                    Layout.fillWidth: true
                    text: [root.extensionLabel, root.sizeText].filter(
                        value => String(value).length > 0
                    ).join("  ·  ")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    elide: Text.ElideRight
                }
            }

            CompactIconButton {
                theme: root.theme
                iconName: root.local ? "open_in_new" : "download"
                iconColor: root.local
                    ? root.theme.action : root.theme.primaryText
                toolTip: root.local
                    ? qsTr("Open image") : qsTr("Download image")
                onClicked: root.activated()
            }
        }
    }
}
