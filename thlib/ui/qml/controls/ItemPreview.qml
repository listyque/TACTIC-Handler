import QtQuick
import Qt5Compat.GraphicalEffects
import "." as Controls

Item {
    id: root
    required property var theme
    property url source: ""
    property string fallbackIcon: "image"
    property string fallbackText: ""
    property color accent: theme.contentAccent
    readonly property color fallbackColor: theme.readableText(Qt.darker(accent, round ? 1.35 : 1.65))
    property bool round: false
    property real cornerRadius: round ? width / 2 : 4
    property bool outlined: false
    property bool readyBorderEnabled: true
    property bool selected: false
    property bool loading: false
    readonly property int previewBorderWidth: outlined || (readyBorderEnabled && sourceImage.status === Image.Ready) ? 1 : 0
    // Views explicitly deactivate pooled delegates so decoded images and
    // scene-graph textures are released instead of accumulating while the
    // user scrolls through an infinite result set.
    property bool active: true
    // Scrolling may disable decoration, but rounded clipping is geometry:
    // retain its mask for both circular and rounded-rectangle previews.
    property bool effectsEnabled: true
    property color selectedBorderColor: theme.selectedText
    property real previewSize: 58
    property int fillMode: Image.PreserveAspectCrop
    property bool animateAppearance: true
    property string _appearanceAnimationSource: ""
    readonly property bool appearanceAnimationEnabled: root.animateAppearance && !root.theme.suppressTransientMotion && root._appearanceAnimationSource === String(root.source)
    // Small delegates save memory by decoding to their rendered size.  Large
    // viewers can disable this so geometry changes only rescale the already
    // decoded texture instead of re-requesting the same source on every pixel
    // of a dock resize.
    property bool decodeAtItemSize: true
    property bool preserveDecodeAspect: false
    signal imageReady
    signal appearanceCompleted
    readonly property bool pending: root.loading || String(root.source).indexOf("pending-preview:") === 0
    readonly property bool supportedSource: root.isSupportedSource(root.source)
    readonly property bool maskEnabled: root.active && root.visible && GraphicsInfo.api !== GraphicsInfo.Software && (root.effectsEnabled || root.cornerRadius > 0)
    readonly property real sourcePixelWidth: sourceImage.status === Image.Ready ? sourceImage.sourceSize.width : 0
    readonly property real sourcePixelHeight: sourceImage.status === Image.Ready ? sourceImage.sourceSize.height : 0

    function isSupportedSource(value) {
        const text = String(value || "");
        if (!text || text.indexOf("pending-preview:") === 0)
            return false;
        if (text.toLowerCase().indexOf("file:") !== 0)
            return true;
        return /\.(apng|avif|bmp|gif|ico|jpe?g|png|svg|tga|tiff?|webp)(?:[?#].*)?$/i.test(text);
    }

    function captureAppearanceIntent() {
        const value = String(root.source || "");
        root._appearanceAnimationSource = value.length > 0 && root.animateAppearance && !root.theme.suppressTransientMotion ? value : "";
    }

    onSourceChanged: captureAppearanceIntent()
    onAnimateAppearanceChanged: {
        if (!animateAppearance)
            _appearanceAnimationSource = "";
    }
    Component.onCompleted: captureAppearanceIntent()

    implicitWidth: previewSize
    implicitHeight: previewSize

    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: Qt.darker(root.accent, root.round ? 1.35 : 1.65)
        antialiasing: true
    }

    // Mask the rendered item so Image.fillMode survives the texture-provider shortcut.
    Item {
        id: previewImageLayer
        anchors.fill: parent
        anchors.margins: root.previewBorderWidth
        visible: root.active && sourceImage.status === Image.Ready
        Image {
            id: sourceImage
            objectName: "previewSourceImage"
            anchors.fill: parent
            // Hidden layouts can probe near-DBL_MAX widths while calculating size
            // hints. A mask still renders its invisible source, and Qt's texture
            // sizing loop hangs when that width overflows. Do not load or mask a
            // preview until its presentation is visible.
            source: !root.active || !root.visible || root.pending || !root.supportedSource ? "" : root.source
            visible: root.active && status === Image.Ready
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
            sourceSize: root.decodeAtItemSize ? Qt.size(Math.max(64, Math.round(root.width * Screen.devicePixelRatio)), root.preserveDecodeAspect ? -1 : Math.max(64, Math.round(root.height * Screen.devicePixelRatio))) : Qt.size(-1, -1)
            onStatusChanged: {
                if (status !== Image.Ready)
                    return;
                // Persist first-reveal state as soon as this exact source is
                // decoded. Waiting for the fade to finish lets a recycled view
                // delegate report completion for a different model row.
                root.imageReady();
                if (!root.animateAppearance)
                    root.appearanceCompleted();
            }
        }
    }

    Loader {
        objectName: "previewMaskLoader"
        anchors.fill: previewImageLayer
        // A missing, pending, or still-decoding source is represented by the
        // fallback tree. Creating an OpacityMask before there is an image to
        // mask adds an offscreen render pass to every idle delegate for no
        // visible result.
        active: root.maskEnabled && sourceImage.status === Image.Ready
        opacity: sourceImage.status === Image.Ready ? 1 : 0
        onLoaded: {
            if (sourceImage.status === Image.Ready)
                root.appearanceCompleted();
        }
        Behavior on opacity {
            enabled: root.appearanceAnimationEnabled
            NumberAnimation {
                duration: theme.motionExtended
                easing.type: Easing.OutCubic
                onStopped: {
                    if (sourceImage.status === Image.Ready)
                        root.appearanceCompleted();
                }
            }
        }
        sourceComponent: OpacityMask {
            anchors.fill: parent
            source: ShaderEffectSource {
                sourceItem: previewImageLayer
                hideSource: true
                live: true
            }
            // Caching the effect duplicates every preview in another texture.
            // Static Image textures are already cached by Qt's image pipeline.
            cached: false
            maskSource: Rectangle {
                width: sourceImage.width
                height: sourceImage.height
                radius: Math.max(0, root.cornerRadius - root.previewBorderWidth)
                antialiasing: true
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        radius: root.cornerRadius
        border.width: root.previewBorderWidth
        border.color: root.selected ? root.selectedBorderColor : root.theme.border
        antialiasing: true
    }

    Loader {
        anchors.centerIn: parent
        anchors.alignWhenCentered: false
        active: root.active && (root.pending || sourceImage.status !== Image.Ready)
        sourceComponent: root.pending ? pendingComponent : root.fallbackText.length ? textComponent : iconComponent
    }
    Component {
        id: iconComponent
        Controls.MaterialIcon {
            name: root.fallbackIcon
            size: root.previewSize > 40 ? 22 : 16
            color: root.fallbackColor
        }
    }
    Component {
        id: textComponent
        Text {
            text: root.fallbackText
            verticalAlignment: Text.AlignVCenter
            color: root.fallbackColor
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.previewSize > 40 ? 10 : 8
            font.weight: Font.DemiBold
        }
    }
    Component {
        id: pendingComponent
        Controls.BusyIndicator {
            uiTheme: root.theme
            implicitWidth: Math.min(24, root.width * 0.45)
            implicitHeight: implicitWidth
            running: true
        }
    }
}
