import QtQuick

QtObject {
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
        const weight = Math.max(0, Math.min(1, secondWeight))
        return Qt.rgba(
            first.r * (1 - weight) + second.r * weight,
            first.g * (1 - weight) + second.g * weight,
            first.b * (1 - weight) + second.b * weight,
            1
        )
    }

    function overlay(base, foreground, foregroundOpacity) {
        const foregroundAlpha = Math.max(
            0,
            Math.min(1, foregroundOpacity * foreground.a)
        )
        const outputAlpha = foregroundAlpha
            + base.a * (1 - foregroundAlpha)
        if (outputAlpha <= 0)
            return Qt.rgba(0, 0, 0, 0)
        return Qt.rgba(
            (foreground.r * foregroundAlpha
                + base.r * base.a * (1 - foregroundAlpha)) / outputAlpha,
            (foreground.g * foregroundAlpha
                + base.g * base.a * (1 - foregroundAlpha)) / outputAlpha,
            (foreground.b * foregroundAlpha
                + base.b * base.a * (1 - foregroundAlpha)) / outputAlpha,
            outputAlpha
        )
    }

    function readableText(backgroundColor) {
        const luminance = backgroundColor.r * 0.2126
            + backgroundColor.g * 0.7152
            + backgroundColor.b * 0.0722
        return luminance > 0.56 ? "#172027" : "#f6f8fa"
    }

    readonly property string style: styleName === "material5"
        || styleName === "fluent" ? styleName : "md3"
    readonly property bool material5: style === "material5"
    readonly property bool fluent: style === "fluent"
    readonly property color blackMix: "#000000"
    readonly property color whiteMix: "#ffffff"
    readonly property color paletteBase: material5
        ? blend(baseColor, action, dark ? 0.07 : 0.05)
        : baseColor

    readonly property string fontFamily: "Segoe UI"
    readonly property string emojiFontFamily:
        typeof emojiCatalog !== "undefined"
            ? String(emojiCatalog.fontFamily || "Segoe UI Emoji")
            : "Segoe UI Emoji"
    readonly property real controlHeight: material5 ? 38 : fluent ? 34 : 36
    readonly property real compactControlHeight: material5 ? 34 : 32
    readonly property real fieldRadius: material5 ? 15 : fluent ? 5 : 10
    readonly property real buttonRadius: material5 ? 16 : fluent ? 5 : 18
    readonly property real itemRadius: material5 ? 13 : fluent ? 5 : 9
    readonly property real snapshotRadius: material5 ? 10 : fluent ? 3 : 5
    readonly property real surfaceRadius: material5 ? 18 : fluent ? 7 : 12
    readonly property real sectionRadius: material5 ? 22 : fluent ? 8 : 16
    readonly property real dialogRadius: material5 ? 28 : fluent ? 8 : 20
    readonly property real menuRadius: material5 ? 20 : fluent ? 8 : 16
    readonly property real iconButtonRadius: material5 ? 9 : fluent ? 4 : 4
    readonly property real dockTitleHeight: 38
    readonly property real dockWorkspaceHeaderHeight: 96
    readonly property real dockWorkspaceFooterHeight: 58
    readonly property real communicationListSpacing: 10
    readonly property real communicationBubblePadding: 10
    readonly property real communicationContentSpacing: 6
    readonly property real communicationAvatarSpacing: 8
    readonly property real communicationGroupedSpacing: material5 ? 3 : 2
    readonly property real communicationGroupTailSize: material5 ? 11 : 10
    readonly property real communicationBubbleRadius: material5
        ? 16 : fluent ? 7 : 14
    readonly property real communicationGroupedBubbleRadius: material5
        ? 10 : fluent ? 4 : 8
    readonly property int baseMotionInstant:
        fluent ? 60 : material5 ? 90 : 70
    readonly property int baseMotionFast:
        fluent ? 90 : material5 ? 150 : 120
    readonly property int baseMotionMedium:
        fluent ? 120 : material5 ? 190 : 140
    readonly property int baseMotionSlow:
        fluent ? 160 : material5 ? 240 : 180
    readonly property int baseMotionExtended:
        fluent ? 220 : material5 ? 320 : 260

    // Existing motion tokens represent view transitions and fades. Pointer
    // feedback has dedicated tokens so each preference stays independent.
    readonly property int motionInstant:
        fadeAnimationsEnabled ? baseMotionInstant : 0
    readonly property int motionFast:
        fadeAnimationsEnabled ? baseMotionFast : 0
    readonly property int motionMedium:
        fadeAnimationsEnabled ? baseMotionMedium : 0
    readonly property int motionSlow:
        fadeAnimationsEnabled ? baseMotionSlow : 0
    readonly property int motionExtended:
        fadeAnimationsEnabled ? baseMotionExtended : 0
    // Wheel input is direct manipulation. It should settle faster than a
    // view fade while still smoothing discrete mouse-wheel steps.
    readonly property int scrollMotion:
        fadeAnimationsEnabled ? baseMotionInstant : 0
    readonly property int clickMotionFast:
        clickAnimationsEnabled ? baseMotionFast : 0
    readonly property int clickMotionInstant:
        clickAnimationsEnabled ? baseMotionInstant : 0
    readonly property int clickMotionMedium:
        clickAnimationsEnabled ? baseMotionMedium : 0
    readonly property int clickMotionSlow:
        clickAnimationsEnabled ? baseMotionSlow : 0
    readonly property int clickMotionExtended:
        clickAnimationsEnabled ? baseMotionExtended : 0
    readonly property int hoverMotionFast:
        hoverAnimationsEnabled ? baseMotionFast : 0
    readonly property int hoverMotionMedium:
        hoverAnimationsEnabled ? baseMotionMedium : 0
    readonly property int popupMotionFast:
        popupAnimationsEnabled ? baseMotionFast : 0
    readonly property int popupMotionMedium:
        popupAnimationsEnabled ? baseMotionMedium : 0
    readonly property int popupMotionSlow:
        popupAnimationsEnabled ? baseMotionSlow : 0

    // Every preset supplies a base surface and an accent. All containers are
    // derived here so changing a palette affects the whole interface instead
    // of only buttons and selection states.
    readonly property color workspace: blend(
        paletteBase, dark ? blackMix : whiteMix,
        dark ? (fluent ? 0.23 : 0.34) : (fluent ? 0.12 : 0.08)
    )
    readonly property color topBar: blend(
        paletteBase, dark ? whiteMix : blackMix,
        dark ? (material5 ? 0.05 : 0.03) : 0.03
    )
    readonly property color toolBar: blend(
        paletteBase, dark ? whiteMix : blackMix,
        dark ? (material5 ? 0.11 : 0.08) : 0.07
    )
    readonly property color panel: blend(
        paletteBase, dark ? blackMix : whiteMix,
        dark ? 0.04 : 0.22
    )
    readonly property color panelRaised: blend(
        paletteBase, whiteMix, dark ? 0.08 : 0.38
    )
    readonly property color panelDeep: blend(
        paletteBase, blackMix, dark ? 0.19 : 0.08
    )
    readonly property color row: blend(
        paletteBase, whiteMix, dark ? 0.07 : 0.32
    )
    readonly property color rowHover: blend(
        row, action, dark ? 0.10 : 0.08
    )
    readonly property color selected: blend(
        action, panelRaised, dark ? 0.28 : 0.30
    )
    // A quieter slate selection intended for content entities.  Keep this
    // separate from `selected`: tabs and primary controls still need the
    // stronger interactive accent, while dense result lists should not turn
    // into large bright blocks when several sObjects are selected.
    readonly property color contentSelection: blend(
        action, workspace, dark ? 0.68 : 0.72
    )
    readonly property color contentAccent: blend(
        action, primaryText, dark ? 0.12 : 0.08
    )
    readonly property color selectedText: readableText(selected)
    readonly property color contentSelectionText:
        readableText(contentSelection)
    readonly property color primaryText: readableText(workspace)
    readonly property color secondaryText: blend(
        primaryText, paletteBase, dark ? 0.35 : 0.42
    )
    readonly property color disabledText: blend(
        secondaryText, paletteBase, 0.42
    )
    readonly property color separator: blend(
        paletteBase, primaryText, dark ? 0.11 : 0.18
    )
    readonly property color border: blend(
        paletteBase, primaryText, dark ? 0.24 : 0.30
    )
    readonly property color action: accentColor
    readonly property color green: "#52a86e"
    readonly property color yellow: "#d5bd51"
    readonly property color red: "#d65b67"
    readonly property color missingFile: "#d45b5b"
    readonly property color violet: "#a06bb4"
    readonly property color cyan: "#56a7b3"
    // Script-editor roles follow the established Python palette while preserving
    // contrast in both application themes.
    readonly property color syntaxKeyword: dark ? "#d5bd51" : "#808000"
    readonly property color syntaxString: dark ? "#69b77d" : "#008000"
    readonly property color syntaxComment: dark ? "#70a87a" : "#008000"
    readonly property color syntaxNumber: dark ? "#66b8c4" : "#000080"
    readonly property color syntaxType: dark ? "#bc84cf" : "#800080"
    readonly property color syntaxFunction: dark ? "#66b8c4" : "#00677c"
    readonly property color syntaxDefinition: dark ? "#d39562" : "#7c4800"
    readonly property color syntaxSelf: dark ? "#88aac4" : "#092e64"
    readonly property color syntaxOccurrence: dark ? "#55545a" : "#b4b4b4"
    readonly property color syntaxSearch: dark ? "#75651f" : "#ffef0b"
    readonly property color titleGreen: dark ? "#4c8700" : "#5f970d"
    readonly property color ripple: dark ? "#34ffffff" : "#22000000"
    readonly property color rippleStrong: dark ? "#38ffffff" : "#24000000"
    readonly property color popupShadow: dark ? "#4a000000" : "#28000000"
    readonly property color dialogShadow: dark ? "#52000000" : "#30000000"
    readonly property color scrim: dark ? "#99000000" : "#73000000"
    readonly property color tooltipSurface: panelRaised
    readonly property color tooltipText: primaryText

    // Shared Qt Quick Controls semantic roles.
    readonly property color background: workspace
    readonly property color surface: panel
    readonly property color surfaceContainerLow: panel
    readonly property color surfaceContainer: toolBar
    readonly property color surfaceContainerHigh: panelRaised
    readonly property color surfaceContainerHighest: rowHover
    readonly property color surfaceVariant: toolBar
    readonly property color outline: border
    readonly property color outlineVariant: separator
    readonly property color primary: action
    readonly property color primaryContainer: selected
    readonly property color secondary: secondaryText
    readonly property color secondaryContainer: rowHover
    readonly property color tertiary: violet
    readonly property color tertiaryContainer: rowHover
    readonly property color error: red
    readonly property color onError: readableText(error)
    readonly property color errorContainer: rowHover
    readonly property color inverseSurface: "#eeeeee"
    readonly property color inverseOnSurface: "#202020"
    readonly property color text: primaryText
    readonly property color muted: secondaryText
    readonly property color accent: action
    readonly property color accentContainer: selected
}
