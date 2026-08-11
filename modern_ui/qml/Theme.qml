import QtQuick

QtObject {
    required property bool dark
    property string styleName: "md3"
    property bool suppressToolTips: false

    readonly property string style: styleName === "material5"
        || styleName === "fluent" ? styleName : "md3"
    readonly property bool material5: style === "material5"
    readonly property bool fluent: style === "fluent"

    readonly property string fontFamily: "Segoe UI"
    readonly property real controlHeight: material5 ? 38 : fluent ? 34 : 36
    readonly property real compactControlHeight: material5 ? 34 : 32
    readonly property real fieldRadius: material5 ? 15 : fluent ? 5 : 10
    readonly property real buttonRadius: material5 ? 16 : fluent ? 5 : 18
    readonly property real itemRadius: material5 ? 13 : fluent ? 5 : 9
    readonly property real surfaceRadius: material5 ? 18 : fluent ? 7 : 12
    readonly property real sectionRadius: material5 ? 22 : fluent ? 8 : 16
    readonly property real dialogRadius: material5 ? 28 : fluent ? 8 : 20
    readonly property real menuRadius: material5 ? 20 : fluent ? 8 : 16
    readonly property real iconButtonRadius: material5 ? 9 : fluent ? 4 : 4
    readonly property real dockTitleHeight: 38
    readonly property real dockWorkspaceHeaderHeight: 96
    readonly property real dockWorkspaceFooterHeight: 58
    readonly property int motionFast: fluent ? 90 : material5 ? 150 : 120
    readonly property int motionMedium: fluent ? 120 : material5 ? 190 : 140
    readonly property int motionSlow: fluent ? 160 : material5 ? 240 : 180

    readonly property color workspace: material5
        ? (dark ? "#17151a" : "#f1edf3")
        : fluent ? (dark ? "#202020" : "#f3f3f3")
        : (dark ? "#1a1a1a" : "#edf0f2")
    readonly property color topBar: material5
        ? (dark ? "#302b35" : "#e9e1ec")
        : fluent ? (dark ? "#282828" : "#e8e8e8")
        : (dark ? "#303030" : "#e1e4e7")
    readonly property color toolBar: material5
        ? (dark ? "#3a3440" : "#ddd3e1")
        : fluent ? (dark ? "#323232" : "#dedede")
        : (dark ? "#3b3b3b" : "#d3d8dc")
    readonly property color panel: material5
        ? (dark ? "#2b272f" : "#faf7fb")
        : fluent ? (dark ? "#292929" : "#fafafa")
        : (dark ? "#2d2d2d" : "#f7f8f9")
    readonly property color panelRaised: material5
        ? (dark ? "#39323e" : "#ffffff")
        : fluent ? (dark ? "#333333" : "#ffffff")
        : (dark ? "#353535" : "#ffffff")
    readonly property color panelDeep: material5
        ? (dark ? "#201d23" : "#e9e2eb")
        : fluent ? (dark ? "#1c1c1c" : "#e5e5e5")
        : (dark ? "#202020" : "#e7ebee")
    readonly property color row: material5
        ? (dark ? "#37313c" : "#ffffff")
        : fluent ? (dark ? "#303030" : "#ffffff")
        : (dark ? "#353535" : "#ffffff")
    readonly property color rowHover: material5
        ? (dark ? "#453d4b" : "#eee6f1")
        : fluent ? (dark ? "#3c3c3c" : "#e9e9e9")
        : (dark ? "#414141" : "#e8edf1")
    readonly property color selected: material5
        ? (dark ? "#655078" : "#9f7fb5")
        : fluent ? (dark ? "#264f78" : "#70a7d0")
        : (dark ? "#4f7e9e" : "#78a6c4")
    readonly property color selectedText: "#f6f8fa"
    readonly property color primaryText: dark ? "#e2e2e2" : "#22282d"
    readonly property color secondaryText: material5
        ? (dark ? "#b5aab9" : "#706675")
        : fluent ? (dark ? "#b4b4b4" : "#616161")
        : (dark ? "#a6a6a6" : "#65717a")
    readonly property color disabledText: dark ? "#666666" : "#9ba4aa"
    readonly property color separator: material5
        ? (dark ? "#242027" : "#cbc1cf")
        : fluent ? (dark ? "#1a1a1a" : "#c8c8c8")
        : (dark ? "#1d1d1d" : "#c4cbd0")
    readonly property color border: material5
        ? (dark ? "#514858" : "#bfb2c4")
        : fluent ? (dark ? "#4b4b4b" : "#adadad")
        : (dark ? "#454545" : "#b7c0c6")
    readonly property color action: material5
        ? (dark ? "#b49ac8" : "#76558d")
        : fluent ? (dark ? "#60aee8" : "#0067c0")
        : (dark ? "#78a6c4" : "#3d7599")
    readonly property color green: "#52a86e"
    readonly property color yellow: "#d5bd51"
    readonly property color red: "#d65b67"
    readonly property color missingFile: "#d45b5b"
    readonly property color violet: "#a06bb4"
    readonly property color cyan: "#56a7b3"
    readonly property color titleGreen: dark ? "#4c8700" : "#5f970d"
    readonly property color ripple: dark ? "#34ffffff" : "#22000000"
    readonly property color rippleStrong: dark ? "#38ffffff" : "#24000000"
    readonly property color popupShadow: dark ? "#4a000000" : "#28000000"
    readonly property color dialogShadow: dark ? "#52000000" : "#30000000"
    readonly property color scrim: dark ? "#99000000" : "#73000000"
    readonly property color tooltipSurface: dark ? "#303034" : "#f5f0f5"
    readonly property color tooltipText: dark ? "#e7e1e8" : "#313034"

    // Qt Quick Controls compatibility roles.
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
    readonly property color errorContainer: rowHover
    readonly property color inverseSurface: "#eeeeee"
    readonly property color inverseOnSurface: "#202020"
    readonly property color text: primaryText
    readonly property color muted: secondaryText
    readonly property color accent: action
    readonly property color accentContainer: selected
}
