pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property real contentWidth
    readonly property var sourceDocument: root.controller.viewerDocument || ({})
    readonly property string sourceIdentity: String(root.controller.identity || "")
    readonly property string sourceMarkdown: String(root.sourceDocument.contentMarkdown || "")
    readonly property int attachmentCount: root.controller.uploadedAttachmentModel ? root.controller.uploadedAttachmentModel.count() : 0
    readonly property var renderDependencies: [root.sourceIdentity, root.sourceMarkdown, root.attachmentCount]
    // Keep decoding independent from live dock geometry. Binding sourceSize to
    // delegate width would request another decode on every resize step, while
    // an unlimited source can create a huge scene-graph texture. The original
    // URL remains available through the full-size viewer.
    readonly property size imageDecodeBounds: Qt.size(1280, 1280)
    readonly property var blocks: {
        // Keep every source dependency explicit. The controller method also
        // resolves attachment fallbacks, but a method call alone does not
        // subscribe QML to article or attachment changes.
        const dependencies = root.renderDependencies;
        if (!dependencies[0] || !String(dependencies[1] || "").length)
            return [];
        return root.controller.viewer_blocks();
    }

    function pointSizeForHeading(level) {
        if (level === 1)
            return 24;
        if (level === 2)
            return 19;
        if (level === 3)
            return 16;
        if (level === 4)
            return 14;
        if (level === 5)
            return 12;
        if (level === 6)
            return 11;
        return Controls.Typography.body;
    }

    function scrollToHeading(heading) {
        const title = String(heading.title || "");
        if (!title.length)
            return -1;
        let remaining = Math.max(0, Number(heading.occurrence || 0));
        for (let index = 0; index < blockRepeater.count; ++index) {
            const block = blockRepeater.itemAt(index);
            // Repeater.itemAt() is statically typed as QQuickItem, while this
            // component owns the delegate API used for heading navigation.
            // qmllint disable missing-property
            if (!block || block.kind !== "html")
                continue;
            const match = block.headingPosition(title, remaining);
            if (match.count > remaining) {
                block.focusPosition(match.position);
                return block.y + match.y;
            }
            // qmllint enable missing-property
            remaining -= match.count;
        }
        return -1;
    }

    implicitWidth: root.contentWidth
    implicitHeight: blockColumn.height

    Column {
        id: blockColumn

        width: root.contentWidth
        spacing: 10

        Repeater {
            id: blockRepeater
            objectName: "knowledgeArticleBlocks"
            model: root.blocks

            delegate: Item {
                id: blockItem

                required property var modelData
                required property int index
                readonly property string kind: String(modelData.kind || "html")
                readonly property bool imageBlock: kind === "image"
                readonly property bool listItemBlock: kind === "list-item"
                readonly property int listCheckState:
                    modelData.listCheckState === undefined
                    ? -1 : Number(modelData.listCheckState)
                readonly property bool lightweightText: !imageBlock && Boolean(modelData.lightweight)
                readonly property int headingLevel: Math.max(0, Number(modelData.headingLevel || 0))
                readonly property bool imageReady: articleImage.status === Image.Ready
                readonly property string activeImageSource: articleImage.source.toString()
                readonly property var imageSources: {
                    const candidates = modelData.sources || [];
                    return candidates.length > 0 ? candidates : [String(modelData.source || "")];
                }
                property int imageSourceIndex: 0
                readonly property real requestedImageWidth: Math.max(0, Number(modelData.width || 0))
                readonly property real requestedImageHeight: Math.max(0, Number(modelData.height || 0))
                readonly property bool contentWidthImage: Boolean(modelData.contentWidth)
                readonly property real naturalImageWidth: articleImage.implicitWidth > 0 ? articleImage.implicitWidth : 0
                readonly property real naturalImageHeight: articleImage.implicitHeight > 0 ? articleImage.implicitHeight : 0
                readonly property real imageRatio: {
                    if (requestedImageWidth > 0 && requestedImageHeight > 0)
                        return requestedImageHeight / requestedImageWidth;
                    if (naturalImageWidth > 0 && naturalImageHeight > 0)
                        return naturalImageHeight / naturalImageWidth;
                    return 0;
                }
                readonly property real preferredImageWidth: {
                    if (contentWidthImage)
                        return root.contentWidth;
                    if (requestedImageWidth > 0)
                        return requestedImageWidth;
                    if (naturalImageWidth > 0)
                        return Math.min(560, naturalImageWidth);
                    return Math.min(560, root.contentWidth);
                }
                readonly property real displayedImageWidth: Math.max(24, Math.min(root.contentWidth, preferredImageWidth))
                readonly property real displayedImageHeight: imageRatio > 0 ? displayedImageWidth * imageRatio : Math.min(240, displayedImageWidth * 0.5625)

                function headingPosition(title, occurrence) {
                    if (kind !== "html")
                        return ({
                                "count": 0,
                                "position": -1,
                                "y": -1
                            });
                    const plainText = articleText.getText(0, articleText.length);
                    let offset = 0;
                    let count = 0;
                    let position = -1;
                    while (true) {
                        const found = plainText.indexOf(title, offset);
                        if (found < 0)
                            break;
                        if (count === occurrence)
                            position = found;
                        count += 1;
                        offset = found + Math.max(1, title.length);
                    }
                    const rectangle = position >= 0 ? articleText.positionToRectangle(position) : Qt.rect(0, 0, 0, 0);
                    return ({
                            "count": count,
                            "position": position,
                            "y": rectangle.y
                        });
                }

                function focusPosition(position) {
                    if (position < 0 || kind !== "html")
                        return;
                    articleText.cursorPosition = position;
                    articleText.forceActiveFocus();
                }

                objectName: imageBlock ? "knowledgeArticleImageBlock-" + index : index === 0 ? "knowledgeArticleText" : "knowledgeArticleText-" + index
                activeFocusOnTab: imageBlock
                Accessible.ignored: !imageBlock
                Accessible.role: Accessible.Button
                Accessible.name: qsTr("Open image")
                Accessible.onPressAction: {
                    if (imageBlock)
                        root.controller.open_link(String(modelData.source || ""));
                }
                width: blockColumn.width
                height: imageBlock ? Math.max(24, displayedImageHeight) : articleText.contentHeight

                Text {
                    id: listMarker
                    objectName: "knowledgeArticleListMarker-" + blockItem.index
                    visible: blockItem.listItemBlock
                    x: Math.max(
                        0, Number(blockItem.modelData.listLevel || 0)) * 22
                    width: 30
                    text: blockItem.listCheckState === 1 ? "☑"
                        : blockItem.listCheckState === 0 ? "☐"
                        : Boolean(blockItem.modelData.listOrdered)
                            ? String(blockItem.modelData.listIndex || 1) + "."
                            : "•"
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    horizontalAlignment: Text.AlignRight
                }

                Keys.onPressed: event => {
                    if (!imageBlock || (event.key !== Qt.Key_Return && event.key !== Qt.Key_Enter && event.key !== Qt.Key_Space))
                        return;
                    root.controller.open_link(String(modelData.source || ""));
                    event.accepted = true;
                }

                Controls.SelectableText {
                    id: articleText
                    objectName: "knowledgeArticleTextContent-" + blockItem.index
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: blockItem.listItemBlock
                        ? listMarker.x + listMarker.width + 8 : 0
                    visible: !blockItem.imageBlock
                    theme: root.theme
                    richText: !blockItem.lightweightText
                    text: blockItem.lightweightText ? String(blockItem.modelData.plainText || "") : String(blockItem.modelData.html || "").replace(/<a /g, "<a style=\"color:" + root.theme.action + ";\" ")
                    color: root.theme.primaryText
                    font.pointSize: root.pointSizeForHeading(blockItem.headingLevel)
                    font.weight: blockItem.headingLevel > 0 ? Font.Bold : Font.Normal
                    horizontalAlignment: {
                        const alignment = String(blockItem.modelData.alignment || "left");
                        if (alignment === "center")
                            return TextEdit.AlignHCenter;
                        if (alignment === "right")
                            return TextEdit.AlignRight;
                        if (alignment === "justify")
                            return TextEdit.AlignJustify;
                        return TextEdit.AlignLeft;
                    }
                    onLinkActivated: link => root.controller.open_link(link)
                }

                Item {
                    id: imageAction

                    visible: blockItem.imageBlock
                    anchors.left: parent.left
                    anchors.top: parent.top
                    width: blockItem.displayedImageWidth
                    height: blockItem.displayedImageHeight

                    Image {
                        id: articleImage

                        objectName: "knowledgeArticleImage-" + blockItem.index
                        anchors.fill: parent
                        visible: status !== Image.Error
                        source: blockItem.imageSources.length > 0 ? blockItem.imageSources[Math.min(blockItem.imageSourceIndex, blockItem.imageSources.length - 1)] : ""
                        asynchronous: true
                        cache: true
                        retainWhileLoading: true
                        smooth: true
                        // Smooth texture scaling is sufficient for a continuously
                        // resizable reader. A mip chain costs additional GPU memory
                        // for every embedded image and is not rebuilt for display.
                        mipmap: false
                        sourceSize: root.imageDecodeBounds
                        fillMode: Image.PreserveAspectFit

                        onStatusChanged: {
                            if (status === Image.Error && blockItem.imageSourceIndex + 1 < blockItem.imageSources.length)
                                blockItem.imageSourceIndex += 1;
                        }
                    }

                    Controls.BusyIndicator {
                        anchors.centerIn: parent
                        width: 24
                        height: 24
                        visible: articleImage.status === Image.Loading
                        running: visible
                        uiTheme: root.theme
                    }

                    Rectangle {
                        anchors.fill: parent
                        visible: articleImage.status === Image.Error && blockItem.imageSourceIndex + 1 >= blockItem.imageSources.length
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
                            Label {
                                Layout.fillWidth: true
                                text: String(blockItem.modelData.alt || blockItem.modelData.title || qsTr("Image could not be loaded"))
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        visible: blockItem.activeFocus
                        color: "transparent"
                        radius: root.theme.itemRadius
                        border.width: 2
                        border.color: root.theme.action
                    }

                    Rectangle {
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 7
                        width: 28
                        height: 28
                        visible: imageHover.hovered || blockItem.activeFocus
                        radius: 14
                        color: root.theme.surfaceContainerHigh
                        border.width: 1
                        border.color: root.theme.outlineVariant

                        Controls.MaterialIcon {
                            anchors.centerIn: parent
                            name: "open_in_new"
                            size: 15
                            color: root.theme.primaryText
                        }
                    }

                    Controls.ActivationHandler {
                        onActivated: root.controller.open_link(String(blockItem.modelData.source || ""))
                    }

                    HoverHandler {
                        id: imageHover
                        cursorShape: Qt.PointingHandCursor
                    }
                }
            }
        }
    }
}
