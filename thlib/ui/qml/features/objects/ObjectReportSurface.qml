import "../../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/objects/report.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    property string part: "header"
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function measure(text, size, weight) {
        const metrics = size === 21 ? valueMetrics : size === 13 ? bodyMetrics : weight === 600 ? chipMetrics : captionMetrics;
        return metrics.advanceWidth(String(text));
    }
    FontMetrics {
        id: captionMetrics
        font.family: root.theme.fontFamily
        font.hintingPreference: Font.PreferVerticalHinting
        font.pixelSize: Foundation.textStyles.caption
    }
    FontMetrics {
        id: bodyMetrics
        font.family: root.theme.fontFamily
        font.hintingPreference: Font.PreferVerticalHinting
        font.pixelSize: Foundation.textStyles.body
    }
    FontMetrics {
        id: chipMetrics
        font.family: root.theme.fontFamily
        font.hintingPreference: Font.PreferVerticalHinting
        font.pixelSize: Foundation.textStyles.caption
        font.weight: Font.DemiBold
    }
    FontMetrics {
        id: valueMetrics
        font.family: root.theme.fontFamily
        font.hintingPreference: Font.PreferVerticalHinting
        font.pixelSize: Foundation.textStyles.statistic
        font.weight: Font.DemiBold
    }

    views: ({
            reportDescription: {
                component: descriptionPort,
                nodeProps: true
            }
        })
    Component {
        id: descriptionPort
        Controls.SelectableText {
            property var frameNode
            theme: root.theme
            richText: true
            text: typeof appController !== "undefined" ? appController.rich_text_html(frameNode ? frameNode.text : "") : frameNode ? frameNode.text : ""
            color: frameNode && frameNode.empty ? root.theme.secondaryText : root.theme.primaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: Foundation.textStyles.body,
                hintingPreference: Font.PreferVerticalHinting
            })
            clip: true
            onLinkActivated: link => {
                if (typeof appController !== "undefined")
                    appController.open_rich_link(link);
            }
        }
    }
    implicitHeight: scene.height
    scene: part === "header" ? UI.header(model, width, language, measure) : UI.page(model, width, language)
}
