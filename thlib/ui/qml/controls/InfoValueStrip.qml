pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "." as Controls

Item {
    id: root
    objectName: "infoValueStrip"

    required property var theme
    property var items: []
    property bool selected: false
    property int maximumItems: 0
    property real maximumItemWidth: 180
    property string separatorText: "/"
    signal externalLinkOpened(string url)

    implicitWidth: valuesRow.implicitWidth
    implicitHeight: 16
    clip: true

    Row {
        id: valuesRow
        height: parent.height
        spacing: 4

        Repeater {
            model: root.maximumItems > 0
                ? (root.items || []).slice(0, root.maximumItems)
                : root.items || []

            delegate: Row {
                id: valueDelegate
                required property int index
                required property var modelData
                height: valuesRow.height
                spacing: 4

                readonly property string displayText:
                    modelData.kind === "link"
                        ? String(modelData.text || "")
                        : modelData.text !== undefined
                        ? String(modelData.text || "")
                        : [modelData.label || "", modelData.value || ""]
                            .filter(Boolean).join(": ")
                readonly property string fullText:
                    String(modelData.tooltip || modelData.value
                        || displayText)
                readonly property string linkUrl:
                    String(modelData.url || "")
                readonly property bool isLink: linkUrl.length > 0

                Label {
                    visible: valueDelegate.index > 0
                    height: parent.height
                    text: root.separatorText
                    color: root.theme.outline
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.micro
                    verticalAlignment: Text.AlignVCenter
                }

                TextMetrics {
                    id: valueMetrics
                    text: valueDelegate.displayText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.micro
                }

                Label {
                    id: valueLabel
                    objectName: "infoValueText"
                    height: parent.height
                    width: Math.min(
                        root.maximumItemWidth,
                        Math.ceil(valueMetrics.advanceWidth)
                    )
                    text: valueDelegate.displayText
                    color: valueDelegate.isLink
                        ? root.theme.action
                        : String(valueDelegate.modelData.color || "").length
                            ? valueDelegate.modelData.color
                            : root.selected
                                ? root.theme.contentSelectionText
                                : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.micro
                    font.underline: valueDelegate.isLink
                        && valueHover.hovered
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter

                    HoverHandler {
                        id: valueHover
                        cursorShape: valueDelegate.isLink
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }
                    Controls.ActivationHandler {
                        enabled: valueDelegate.isLink
                        onActivated: {
                            Qt.openUrlExternally(valueDelegate.linkUrl)
                            root.externalLinkOpened(valueDelegate.linkUrl)
                        }
                    }
                    Controls.ToolTip {
                        theme: root.theme
                        visible: valueHover.hovered
                            && valueDelegate.fullText.length > 0
                            && !root.theme.suppressToolTips
                        text: valueDelegate.fullText
                    }
                }
            }
        }
    }
}
