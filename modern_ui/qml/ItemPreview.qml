import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    property url source: ""
    property string fallbackIcon: "image"
    property string fallbackText: ""
    property color accent: "#607d8b"
    property bool round: false
    property real cornerRadius: round ? width / 2 : 4
    property bool outlined: false
    property bool selected: false
    property color selectedBorderColor: theme.selectedText
    property real previewSize: 58
    property int fillMode: Image.PreserveAspectCrop
    property bool animateAppearance: true
    // Small delegates save memory by decoding to their rendered size.  Large
    // viewers can disable this so geometry changes only rescale the already
    // decoded texture instead of re-requesting the same source on every pixel
    // of a dock resize.
    property bool decodeAtItemSize: true
    signal appearanceCompleted()
    readonly property bool pending:
        String(root.source).indexOf("pending-preview:") === 0
    readonly property bool supportedSource: root.isSupportedSource(root.source)

    function isSupportedSource(value) {
        const text = String(value || "")
        if (!text || text.indexOf("pending-preview:") === 0)
            return false
        if (text.toLowerCase().indexOf("file:") !== 0)
            return true
        return /\.(apng|avif|bmp|gif|ico|jpe?g|png|svg|tga|tiff?|webp)(?:[?#].*)?$/i.test(text)
    }

    implicitWidth: previewSize
    implicitHeight: previewSize

    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: Qt.darker(root.accent, root.round ? 1.35 : 1.65)
        border.width: root.outlined || sourceImage.status === Image.Ready ? 1 : 0
        border.color: root.selected ? root.selectedBorderColor : root.theme.border
        antialiasing: true
    }

    Image {
        id: sourceImage
        anchors.fill: parent
        source: root.pending || !root.supportedSource ? "" : root.source
        visible: false
        fillMode: root.fillMode
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
        sourceSize: root.decodeAtItemSize
            ? Qt.size(
                Math.max(64, Math.round(root.width * Screen.devicePixelRatio)),
                Math.max(64, Math.round(root.height * Screen.devicePixelRatio))
            )
            : Qt.size(-1, -1)
        onStatusChanged: {
            if (status === Image.Ready && !root.animateAppearance)
                root.appearanceCompleted()
        }
    }

    OpacityMask {
        anchors.fill: parent
        source: sourceImage
        visible: opacity > 0
        cached: true
        maskSource: Rectangle {
            width: root.width
            height: root.height
            radius: root.cornerRadius
            antialiasing: true
        }
        opacity: sourceImage.status === Image.Ready ? 1 : 0
        Behavior on opacity {
            enabled: root.animateAppearance
            NumberAnimation {
                duration: 260
                easing.type: Easing.OutCubic
                onStopped: {
                    if (sourceImage.status === Image.Ready)
                        root.appearanceCompleted()
                }
            }
        }
    }

    MaterialIcon {
        anchors.centerIn: parent
        visible: !root.pending
            && sourceImage.status !== Image.Ready
            && root.fallbackText.length === 0
        name: root.fallbackIcon
        size: root.previewSize > 40 ? 22 : 16
        color: "#f0f3f5"
    }
    Text {
        anchors.centerIn: parent
        visible: !root.pending
            && sourceImage.status !== Image.Ready
            && root.fallbackText.length > 0
        text: root.fallbackText
        color: "#f0f3f5"
        font.family: root.theme.fontFamily
        font.pixelSize: root.previewSize > 40 ? 10 : 8
        font.weight: Font.DemiBold
    }
    Md3BusyIndicator {
        uiTheme: root.theme
        anchors.centerIn: parent
        width: Math.min(24, root.width * 0.45)
        height: width
        visible: root.pending
        running: visible
    }
}
