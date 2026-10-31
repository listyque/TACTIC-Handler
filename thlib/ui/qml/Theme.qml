import QtQuick
import "tactic_frame/core/foundation.mjs" as Foundation

QtObject {
    id: root
    readonly property var frameMotion: Foundation.motion(style, {
        click: clickAnimationsEnabled,
        hover: hoverAnimationsEnabled,
        fade: fadeAnimationsEnabled,
        popup: popupAnimationsEnabled
    })
    readonly property var frameMetrics: Foundation.metrics(style)
    readonly property var framePalette: Foundation.palette(style, dark, [baseColor.r * 255, baseColor.g * 255, baseColor.b * 255], [accentColor.r * 255, accentColor.g * 255, accentColor.b * 255])

    function frameColor(name) {
        const channels = framePalette[name];
        return Qt.rgba(channels[0] / 255, channels[1] / 255, channels[2] / 255, channels.length === 4 ? channels[3] : 1);
    }

    required property bool dark
    property string styleName: "md3"
    property color accentColor: dark ? "#78a6c4" : "#3d7599"
    property color baseColor: dark ? "#292d30" : "#d4dce1"
    property bool suppressToolTips: false
    property bool clickAnimationsEnabled: true
    property bool hoverAnimationsEnabled: true
    property bool fadeAnimationsEnabled: true
    property bool popupAnimationsEnabled: true
    // A local presenter may suppress motion while applying a batched state.
    // Never bind this to global navigation: that would invalidate animation
    // bindings in every delegate when one Search tab changes.
    property bool suppressTransientMotion: false

    function blend(first, second, secondWeight) {
        const channels = Foundation.blend([first.r, first.g, first.b], [second.r, second.g, second.b], secondWeight);
        return Qt.rgba(channels[0], channels[1], channels[2], 1);
    }

    function overlay(base, foreground, foregroundOpacity) {
        const foregroundAlpha = Math.max(0, Math.min(1, foregroundOpacity * foreground.a));
        const outputAlpha = foregroundAlpha + base.a * (1 - foregroundAlpha);
        if (outputAlpha <= 0)
            return Qt.rgba(0, 0, 0, 0);
        return Qt.rgba((foreground.r * foregroundAlpha + base.r * base.a * (1 - foregroundAlpha)) / outputAlpha, (foreground.g * foregroundAlpha + base.g * base.a * (1 - foregroundAlpha)) / outputAlpha, (foreground.b * foregroundAlpha + base.b * base.a * (1 - foregroundAlpha)) / outputAlpha, outputAlpha);
    }

    function readableText(backgroundColor) {
        const channels = Foundation.readableText([backgroundColor.r * 255, backgroundColor.g * 255, backgroundColor.b * 255]);
        return "#" + channels.map(channel => channel.toString(16).padStart(2, "0")).join("");
    }

    readonly property string style: styleName === "material5" || styleName === "fluent" ? styleName : "md3"
    readonly property bool material5: style === "material5"
    readonly property bool fluent: style === "fluent"
    readonly property color blackMix: frameColor("blackMix")
    readonly property color whiteMix: frameColor("whiteMix")
    readonly property color paletteBase: frameColor("paletteBase")
    readonly property string fontFamily: Foundation.fontFamily
    readonly property var spacing: Foundation.spacing
    readonly property string emojiFontFamily: typeof emojiCatalog !== "undefined" ? String(emojiCatalog.fontFamily || "Segoe UI Emoji") : "Segoe UI Emoji"
    readonly property real controlHeight: frameMetrics.controlHeight
    readonly property real compactControlHeight: frameMetrics.compactControlHeight
    readonly property real fieldRadius: frameMetrics.fieldRadius
    readonly property real buttonRadius: frameMetrics.buttonRadius
    readonly property real itemRadius: frameMetrics.itemRadius
    readonly property real snapshotRadius: frameMetrics.snapshotRadius
    readonly property real surfaceRadius: frameMetrics.surfaceRadius
    readonly property real sectionRadius: frameMetrics.sectionRadius
    readonly property real dialogRadius: frameMetrics.dialogRadius
    readonly property real menuRadius: frameMetrics.menuRadius
    readonly property real iconButtonRadius: frameMetrics.iconButtonRadius
    readonly property real dockTitleHeight: frameMetrics.dockTitleHeight
    readonly property real dockWorkspaceHeaderHeight: frameMetrics.dockWorkspaceHeaderHeight
    readonly property real dockWorkspaceFooterHeight: frameMetrics.dockWorkspaceFooterHeight
    readonly property real communicationListSpacing: frameMetrics.communicationListSpacing
    readonly property real communicationBubblePadding: frameMetrics.communicationBubblePadding
    readonly property real communicationContentSpacing: frameMetrics.communicationContentSpacing
    readonly property real communicationAvatarSpacing: frameMetrics.communicationAvatarSpacing
    readonly property real communicationGroupedSpacing: frameMetrics.communicationGroupedSpacing
    readonly property real communicationGroupTailSize: frameMetrics.communicationGroupTailSize
    readonly property real communicationBubbleRadius: frameMetrics.communicationBubbleRadius
    readonly property real communicationGroupedBubbleRadius: frameMetrics.communicationGroupedBubbleRadius
    readonly property int baseMotionInstant: frameMetrics.baseMotionInstant
    readonly property int baseMotionFast: frameMetrics.baseMotionFast
    readonly property int baseMotionMedium: frameMetrics.baseMotionMedium
    readonly property int baseMotionSlow: frameMetrics.baseMotionSlow
    readonly property int baseMotionExtended: frameMetrics.baseMotionExtended
    readonly property int motionInstant: frameMotion.motionInstant
    readonly property int motionFast: frameMotion.motionFast
    readonly property int motionMedium: frameMotion.motionMedium
    readonly property int motionSlow: frameMotion.motionSlow
    readonly property int motionExtended: frameMotion.motionExtended
    readonly property int scrollMotion: frameMotion.scrollMotion
    readonly property int clickMotionFast: frameMotion.clickMotionFast
    readonly property int clickMotionInstant: frameMotion.clickMotionInstant
    readonly property int clickMotionMedium: frameMotion.clickMotionMedium
    readonly property int clickMotionSlow: frameMotion.clickMotionSlow
    readonly property int clickMotionExtended: frameMotion.clickMotionExtended
    readonly property int hoverMotionFast: frameMotion.hoverMotionFast
    readonly property int hoverMotionMedium: frameMotion.hoverMotionMedium
    readonly property int popupMotionFast: frameMotion.popupMotionFast
    readonly property int popupMotionMedium: frameMotion.popupMotionMedium
    readonly property int popupMotionSlow: frameMotion.popupMotionSlow
    readonly property color workspace: frameColor("workspace")
    readonly property color topBar: frameColor("topBar")
    readonly property color toolBar: frameColor("toolBar")
    readonly property color tableHeader: frameColor("tableHeader")
    readonly property color tableAlternateRow: frameColor("tableAlternateRow")
    readonly property color tableDivider: frameColor("tableDivider")
    readonly property color panel: frameColor("panel")
    readonly property color surfaceContainerLowest: frameColor("surfaceContainerLowest")
    readonly property color panelRaised: frameColor("panelRaised")
    readonly property color panelDeep: frameColor("panelDeep")
    readonly property color row: frameColor("row")
    readonly property color rowHover: frameColor("rowHover")
    readonly property color selected: frameColor("selected")
    readonly property color contentSelection: frameColor("contentSelection")
    readonly property color contentAccent: frameColor("contentAccent")
    readonly property color selectedText: frameColor("selectedText")
    readonly property color contentSelectionText: frameColor("contentSelectionText")
    readonly property color primaryText: frameColor("primaryText")
    readonly property color secondaryText: frameColor("secondaryText")
    readonly property color disabledText: frameColor("disabledText")
    readonly property color separator: frameColor("separator")
    readonly property color border: frameColor("border")
    readonly property color action: frameColor("action")
    readonly property color green: frameColor("green")
    readonly property color yellow: frameColor("yellow")
    readonly property color red: frameColor("red")
    readonly property color missingFile: frameColor("missingFile")
    readonly property color violet: frameColor("violet")
    readonly property color cyan: frameColor("cyan")
    readonly property color syntaxKeyword: frameColor("syntaxKeyword")
    readonly property color syntaxString: frameColor("syntaxString")
    readonly property color syntaxComment: frameColor("syntaxComment")
    readonly property color syntaxNumber: frameColor("syntaxNumber")
    readonly property color syntaxType: frameColor("syntaxType")
    readonly property color syntaxFunction: frameColor("syntaxFunction")
    readonly property color syntaxDefinition: frameColor("syntaxDefinition")
    readonly property color syntaxSelf: frameColor("syntaxSelf")
    readonly property color syntaxOccurrence: frameColor("syntaxOccurrence")
    readonly property color syntaxSearch: frameColor("syntaxSearch")
    readonly property color titleGreen: frameColor("titleGreen")
    readonly property color ripple: frameColor("ripple")
    readonly property color rippleStrong: frameColor("rippleStrong")
    readonly property color popupShadow: frameColor("popupShadow")
    readonly property color dialogShadow: frameColor("dialogShadow")
    readonly property color scrim: frameColor("scrim")
    readonly property color tooltipSurface: frameColor("tooltipSurface")
    readonly property color tooltipText: frameColor("tooltipText")
    readonly property color background: frameColor("background")
    readonly property color surface: frameColor("surface")
    readonly property color surfaceContainerLow: frameColor("surfaceContainerLow")
    readonly property color surfaceContainer: frameColor("surfaceContainer")
    readonly property color surfaceContainerHigh: frameColor("surfaceContainerHigh")
    readonly property color surfaceContainerHighest: frameColor("surfaceContainerHighest")
    readonly property color surfaceVariant: frameColor("surfaceVariant")
    readonly property color outline: frameColor("outline")
    readonly property color outlineVariant: frameColor("outlineVariant")
    readonly property color primary: frameColor("primary")
    readonly property color primaryContainer: frameColor("primaryContainer")
    readonly property color secondary: frameColor("secondary")
    readonly property color secondaryContainer: frameColor("secondaryContainer")
    readonly property color tertiary: frameColor("tertiary")
    readonly property color tertiaryContainer: frameColor("tertiaryContainer")
    readonly property color error: frameColor("error")
    readonly property color errorText: frameColor("onError")
    readonly property alias onError: root.errorText
    readonly property color errorContainer: frameColor("errorContainer")
    readonly property color inverseSurface: frameColor("inverseSurface")
    readonly property color inverseOnSurface: frameColor("inverseOnSurface")
    readonly property color text: frameColor("text")
    readonly property color muted: frameColor("muted")
    readonly property color accent: frameColor("accent")
    readonly property color accentContainer: frameColor("accentContainer")
}
