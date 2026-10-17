import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "tactic_frame" as Frame
import "tactic_frame/features/objects/snapshot.ui.mjs" as UI

Item {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property string version: ""
    property string revision: ""
    property string repository: ""
    property string repositoryColor: ""
    property string fileSize: ""
    property string author: ""
    property string timestamp: ""
    property bool fileExists: true
    property bool isLatest: false
    property var infoChips: []
    property bool selected: false

    implicitHeight: 59

    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function measure(text, size, weight) {
        const metrics = size === 14 ? titleMetrics : size === 12 ? weight === 600 ? versionMetrics : secondaryMetrics : weight === 700 ? badgeMetrics : captionMetrics;
        return metrics.advanceWidth(String(text));
    }
    FontMetrics {
        id: captionMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: 11
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: badgeMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: 11
        font.weight: Font.Bold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: secondaryMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: 12
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: versionMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: 12
        font.weight: Font.DemiBold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: titleMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: 14
        font.weight: Font.DemiBold
        font.hintingPreference: Font.PreferVerticalHinting
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.summary({
            title: root.title,
            description: root.description,
            version: root.version,
            revision: root.revision,
            repository: root.repository,
            repositoryColor: root.repositoryColor,
            fileSize: root.fileSize,
            author: root.author,
            timestamp: root.timestamp,
            fileExists: root.fileExists,
            isLatest: root.isLatest,
            infoChips: root.infoChips,
            selected: root.selected
        }, width, root.language, root.measure)
    }
}
