pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."

Item {
    id: root

    required property var theme
    required property var documentController
    required property var imageData
    required property real horizontalOffset
    required property real verticalOffset
    property bool interactive: false
    property string objectNamePrefix: "knowledgeEditorImage-"
    property int sourceIndex: 0
    readonly property var sources: {
        const display = String(imageData.source || "");
        const original = String(imageData.storageSource || "");
        return display === original || !original.length ? [display] : [original, display];
    }
    readonly property bool imageReady: image.status === Image.Ready
    readonly property url imageSource: image.source
    readonly property size imageSourceSize: image.sourceSize
    signal activated(string source)

    objectName: objectNamePrefix + Number(imageData.position || 0)
    x: horizontalOffset + Number(imageData.x || 0)
    y: verticalOffset + Number(imageData.y || 0)
    width: Math.max(1, Number(imageData.width || 1))
    height: Math.max(1, Number(imageData.height || 1))
    enabled: interactive
    activeFocusOnTab: interactive || activeFocus
    Accessible.ignored: !interactive
    Accessible.role: Accessible.Button
    Accessible.name: String(imageData.title || qsTr("Open image"))
    Accessible.onPressAction: root.activated(String(root.imageData.storageSource || root.imageSource))

    Image {
        id: image

        anchors.fill: parent
        visible: status !== Image.Error
        source: root.sources[Math.min(root.sourceIndex, root.sources.length - 1)]
        asynchronous: true
        cache: true
        retainWhileLoading: true
        smooth: true
        mipmap: false
        sourceSize: Qt.size(1280, 1280)
        fillMode: Image.PreserveAspectFit

        onStatusChanged: {
            if (status === Image.Ready) {
                root.documentController.set_image_natural_size(String(root.imageData.storageSource || ""), implicitWidth, implicitHeight);
            } else if (status === Image.Error && root.sourceIndex + 1 < root.sources.length) {
                root.sourceIndex += 1;
            } else if (status === Image.Error) {
                root.documentController.report_image_load_failure(String(root.imageData.storageSource || source));
            }
        }
    }

    Controls.BusyIndicator {
        anchors.centerIn: parent
        width: 24
        height: 24
        visible: image.status === Image.Loading
        running: visible
        uiTheme: root.theme
    }

    Rectangle {
        anchors.fill: parent
        visible: image.status === Image.Error
        radius: root.theme.itemRadius
        color: root.theme.surfaceContainerLow
        border.width: 1
        border.color: root.theme.outlineVariant

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Controls.MaterialIcon {
                name: "image"
                size: 18
                color: root.theme.secondaryText
            }
            Text {
                Layout.fillWidth: true
                text: String(root.imageData.title || qsTr("Image could not be loaded"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }
    }

    Controls.ActivationHandler {
        enabled: root.interactive
        onActivated: root.activated(String(root.imageData.storageSource || root.imageSource))
    }

    Component.onDestruction: image.source = ""
}
