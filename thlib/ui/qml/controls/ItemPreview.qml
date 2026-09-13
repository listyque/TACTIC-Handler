import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import "." as Controls

Item {
    id: root
    required property var theme
    property url source: ""
    property string fallbackIcon: "image"
    property string fallbackText: ""
    property color accent: theme.contentAccent
    readonly property color fallbackColor:
        theme.readableText(Qt.darker(accent, round ? 1.35 : 1.65))
    property bool round: false
    property real cornerRadius: round ? width / 2 : 4
    property bool outlined: false
    property bool selected: false
    // Views explicitly deactivate pooled delegates so decoded images and
    // scene-graph textures are released instead of accumulating while the
    // user scrolls through an infinite result set.
    property bool active: true
    // Moving views may render non-round images directly. Circular sObject
    // previews keep their mask alive so scrolling never changes their shape
    // or repeatedly destroys and recreates the effect item.
    property bool effectsEnabled: true
    property color selectedBorderColor: theme.selectedText
    property real previewSize: 58
    property int fillMode: Image.PreserveAspectCrop
    property bool animateAppearance: true
    property string _appearanceAnimationSource: ""
    readonly property bool appearanceAnimationEnabled:
        root.animateAppearance
        && !root.theme.suppressTransientMotion
        && root._appearanceAnimationSource === String(root.source)
    // Small delegates save memory by decoding to their rendered size.  Large
    // viewers can disable this so geometry changes only rescale the already
    // decoded texture instead of re-requesting the same source on every pixel
    // of a dock resize.
    property bool decodeAtItemSize: true
    signal imageReady()
    signal appearanceCompleted()
    readonly property bool pending:
        String(root.source).indexOf("pending-preview:") === 0
    readonly property bool supportedSource: root.isSupportedSource(root.source)
    readonly property bool maskEnabled:
        root.active && (root.effectsEnabled || root.round)

    function isSupportedSource(value) {
        const text = String(value || "")
        if (!text || text.indexOf("pending-preview:") === 0)
            return false
        if (text.toLowerCase().indexOf("file:") !== 0)
            return true
        return /\.(apng|avif|bmp|gif|ico|jpe?g|png|svg|tga|tiff?|webp)(?:[?#].*)?$/i.test(text)
    }

    function captureAppearanceIntent() {
        const value = String(root.source || "")
        root._appearanceAnimationSource = value.length > 0
            && root.animateAppearance
            && !root.theme.suppressTransientMotion
            ? value : ""
    }

    onSourceChanged: captureAppearanceIntent()
    onAnimateAppearanceChanged: {
        if (!animateAppearance)
            _appearanceAnimationSource = ""
    }
    Component.onCompleted: captureAppearanceIntent()

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
        objectName: "previewSourceImage"
        anchors.fill: parent
        source: !root.active || root.pending || !root.supportedSource
            ? "" : root.source
        visible: root.active && !root.maskEnabled
            && status === Image.Ready
        fillMode: root.fillMode
        asynchronous: true
        cache: true
        // Search Tabs reuse delegate slots. Keep the already rendered texture
        // until the cached replacement is ready instead of flashing the
        // fallback between two local preview sources.
        retainWhileLoading: true
        smooth: true
        // The image is already decoded at its render size. A mip chain adds
        // roughly one third more texture memory without improving thumbnails.
        mipmap: false
        sourceSize: root.decodeAtItemSize
            ? Qt.size(
                Math.max(64, Math.round(root.width * Screen.devicePixelRatio)),
                Math.max(64, Math.round(root.height * Screen.devicePixelRatio))
            )
            : Qt.size(-1, -1)
        onStatusChanged: {
            if (status !== Image.Ready)
                return
            // Persist first-reveal state as soon as this exact source is
            // decoded. Waiting for the fade to finish lets a recycled view
            // delegate report completion for a different model row.
            root.imageReady()
            if (!root.animateAppearance)
                root.appearanceCompleted()
        }
    }

    Loader {
        objectName: "previewMaskLoader"
        anchors.fill: parent
        // A missing, pending, or still-decoding source is represented by the
        // fallback tree. Creating an OpacityMask before there is an image to
        // mask adds an offscreen render pass to every idle delegate for no
        // visible result.
        active: root.maskEnabled && sourceImage.status === Image.Ready
        opacity: sourceImage.status === Image.Ready ? 1 : 0
        onLoaded: {
            if (sourceImage.status === Image.Ready)
                root.appearanceCompleted()
        }
        Behavior on opacity {
            enabled: root.appearanceAnimationEnabled
            NumberAnimation {
                duration: theme.motionExtended
                easing.type: Easing.OutCubic
                onStopped: {
                    if (sourceImage.status === Image.Ready)
                        root.appearanceCompleted()
                }
            }
        }
        sourceComponent: OpacityMask {
            anchors.fill: parent
            source: sourceImage
            // Caching the effect duplicates every preview in another texture.
            // Static Image textures are already cached by Qt's image pipeline.
            cached: false
            maskSource: Rectangle {
                width: root.width
                height: root.height
                radius: root.cornerRadius
                antialiasing: true
            }
        }
    }

    Loader {
        anchors.centerIn: parent
        active: root.active && !root.pending
            && sourceImage.status !== Image.Ready
            && root.fallbackText.length === 0
        sourceComponent: Controls.MaterialIcon {
            name: root.fallbackIcon
            size: root.previewSize > 40 ? 22 : 16
            color: root.fallbackColor
        }
    }
    Loader {
        anchors.centerIn: parent
        active: root.active && !root.pending
            && sourceImage.status !== Image.Ready
            && root.fallbackText.length > 0
        sourceComponent: Text {
            text: root.fallbackText
            color: root.fallbackColor
            font.family: root.theme.fontFamily
            font.pixelSize: root.previewSize > 40 ? 10 : 8
            font.weight: Font.DemiBold
        }
    }
    Loader {
        anchors.centerIn: parent
        width: Math.min(24, root.width * 0.45)
        height: width
        active: root.active && root.pending
        sourceComponent: Controls.BusyIndicator {
            uiTheme: root.theme
            running: true
        }
    }
}
