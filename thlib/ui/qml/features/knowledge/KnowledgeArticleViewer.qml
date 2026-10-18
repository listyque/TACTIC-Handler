pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/commands.ui.mjs" as Commands

Rectangle {
    id: root
    required property var theme
    required property var controller
    signal backRequested
    property bool resizeActive: false
    property bool tableOfContentsVisible: true
    property bool resourcesVisible: false
    readonly property bool narrow: width < 720
    property bool backNavigationAvailable: root.narrow
    readonly property bool sideTableOfContents: !root.narrow
    readonly property var viewerDocument: root.controller.viewerDocument || ({})
    readonly property var articleMetadata: root.controller.viewerArticleMetadata || ({})
    readonly property var viewerTableOfContents: root.controller.viewerTableOfContents || []
    readonly property string viewerIdentity: String(root.controller.identity || "")
    readonly property int resourceCount: root.controller.references.length + (root.controller.uploadedAttachmentModel ? root.controller.uploadedAttachmentModel.count() : 0)
    readonly property string articleAuthor: String(root.articleMetadata.authorDisplay || root.articleMetadata.author || "")
    readonly property bool articleMetadataVisible: root.viewerDocument.kind === "article" && (root.articleAuthor.length > 0 || String(root.articleMetadata.createdLabel || "").length > 0 || String(root.articleMetadata.updatedLabel || "").length > 0)
    readonly property var sectionEntries: {
        if (root.viewerDocument.kind !== "section" || root.controller.historyPreviewActive)
            return [];
        return root.viewerTableOfContents || [];
    }

    color: root.theme.workspace

    onViewerIdentityChanged: root.resourcesVisible = false

    function scrollToHeading(heading) {
        const headingY = articleContent.scrollToHeading(heading);
        if (headingY < 0)
            return;
        articleFlickable.contentY = Math.max(0, Math.min(articleContent.y + headingY, articleFlickable.contentHeight - articleFlickable.height));
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 7

        Frame.FrameView {
            id: viewerHeader
            Layout.fillWidth: true
            Layout.preferredHeight: Commands.viewerHeight(width)
            theme: root.theme
            readonly property var presentation: ({
                    kind: root.viewerDocument.kind,
                    title: root.viewerDocument.title,
                    description: root.viewerDocument.description,
                    minutes: root.controller.viewerReadingMinutes,
                    back: root.backNavigationAvailable,
                    localDraft: root.controller.localDraft,
                    history: root.controller.historyPreviewActive,
                    canEdit: root.controller.canEdit,
                    busy: root.controller.busy,
                    tocCount: root.viewerTableOfContents.length,
                    tocVisible: root.tableOfContentsVisible,
                    resourceCount: root.resourceCount,
                    resourcesVisible: root.resourcesVisible
                })
            scene: Commands.viewer(presentation, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
            onEvent: (action, source) => {
                if (action.type === "back")
                    root.backRequested();
                else if (action.type === "copy")
                    root.controller.copy_search_key();
                else if (action.type === "history")
                    historyPopup.toggleBelow(source);
                else if (action.type === "toc")
                    root.tableOfContentsVisible = !root.tableOfContentsVisible;
                else if (action.type === "resources")
                    root.resourcesVisible = !root.resourcesVisible;
                else if (action.type === "delete")
                    root.controller.delete_selected();
                else if (action.type === "edit")
                    root.controller.begin_edit();
            }
        }

        Rectangle {
            objectName: "knowledgeRevisionPreviewBanner"
            Layout.fillWidth: true
            implicitHeight: revisionBannerRow.implicitHeight + 14
            visible: root.controller.historyPreviewActive
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                id: revisionBannerRow
                anchors.fill: parent
                anchors.margins: 7
                spacing: 8

                Controls.MaterialIcon {
                    name: "history"
                    size: 17
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Viewing revision from %1 by %2").arg(String(root.controller.historyPreview.timestampFull || root.controller.historyPreview.timestampPretty || "")).arg(String(root.controller.historyPreview.actorDisplay || ""))
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideRight
                }
                Controls.Button {
                    objectName: "knowledgeBackToCurrentRevision"
                    theme: root.theme
                    text: qsTr("Back to current")
                    icon.name: "undo"
                    compact: root.narrow
                    tonal: true
                    onClicked: root.controller.clear_history_preview()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.viewerDocument.kind === "article"
            spacing: 10

            Flickable {
                id: articleFlickable
                objectName: "knowledgeArticleScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: Math.max(0, width - (articleScrollBar.visible ? articleScrollBar.reservedExtent : 0))
                contentHeight: articleBody.implicitHeight
                boundsBehavior: Flickable.StopAtBounds

                Controls.ScrollBar.vertical: Controls.ScrollBar {
                    id: articleScrollBar
                    objectName: "knowledgeArticleScrollBar"
                    theme: root.theme
                    flickableTarget: articleFlickable
                }

                ColumnLayout {
                    id: articleBody
                    width: articleFlickable.contentWidth
                    height: implicitHeight
                    spacing: 12

                    KnowledgeLinkedObjectHeader {
                        Layout.fillWidth: true
                        visible: !root.controller.historyPreviewActive && count > 0
                        theme: root.theme
                        controller: root.controller
                    }

                    KnowledgeTableOfContents {
                        objectName: "knowledgeInlineTableOfContents"
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        visible: root.tableOfContentsVisible && !root.sideTableOfContents && root.viewerTableOfContents.length > 0
                        theme: root.theme
                        compact: true
                        entries: root.viewerTableOfContents
                        onHeadingRequested: heading => root.scrollToHeading(heading)
                    }

                    KnowledgeArticleContent {
                        id: articleContent
                        Layout.fillWidth: true
                        theme: root.theme
                        controller: root.controller
                        contentWidth: articleFlickable.contentWidth
                        resizeActive: root.resizeActive
                    }

                    Item {
                        id: resourcePanel

                        objectName: "knowledgeViewerResources"
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.resourcesVisible ? resourceContents.implicitHeight : 0
                        Layout.maximumHeight: Layout.preferredHeight
                        visible: !root.controller.historyPreviewActive && root.resourceCount > 0
                        opacity: root.resourcesVisible ? 1 : 0
                        enabled: root.resourcesVisible
                        clip: true
                        Accessible.ignored: !root.resourcesVisible

                        ColumnLayout {
                            id: resourceContents

                            width: parent.width
                            height: implicitHeight
                            spacing: 12

                            ColumnLayout {
                                objectName: "knowledgeViewerReferences"
                                Layout.fillWidth: true
                                visible: root.controller.references.length > 0
                                spacing: 7
                                Label {
                                    text: qsTr("Linked objects and files")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                }
                                Repeater {
                                    model: root.controller.references
                                    delegate: SKeyPreviewCard {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        preview: modelData
                                        animatePreview: false
                                        onActivated: root.controller.open_reference(modelData.searchKey)
                                        onRetryRequested: skeyPreviewResolver.retry(modelData.searchKey)
                                    }
                                }
                            }

                            KnowledgeArticleAttachments {
                                Layout.fillWidth: true
                                visible: uploadedModel.count() > 0
                                theme: root.theme
                                controller: root.controller
                                uploadedModel: root.controller.uploadedAttachmentModel
                            }
                        }
                    }

                    ColumnLayout {
                        objectName: "knowledgeArticleMetadataFooter"
                        Layout.fillWidth: true
                        visible: root.articleMetadataVisible
                        spacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 1
                            color: root.theme.separator
                        }

                        Flow {
                            Layout.fillWidth: true
                            spacing: 16

                            Label {
                                objectName: "knowledgeArticleAuthor"
                                visible: root.articleAuthor.length > 0
                                text: qsTr("Author: %1").arg(root.articleAuthor)
                                color: root.theme.disabledText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                            Label {
                                objectName: "knowledgeArticleCreated"
                                visible: String(root.articleMetadata.createdLabel || "").length > 0
                                text: qsTr("Created: %1").arg(String(root.articleMetadata.createdLabel || ""))
                                color: root.theme.disabledText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                            Label {
                                objectName: "knowledgeArticleUpdated"
                                visible: String(root.articleMetadata.updatedLabel || "").length > 0
                                text: qsTr("Updated: %1").arg(String(root.articleMetadata.updatedLabel || ""))
                                color: root.theme.disabledText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                    }
                }
            }

            KnowledgeTableOfContents {
                objectName: "knowledgeSideTableOfContents"
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                visible: root.tableOfContentsVisible && root.sideTableOfContents && root.viewerTableOfContents.length > 0
                theme: root.theme
                entries: root.viewerTableOfContents
                onHeadingRequested: heading => root.scrollToHeading(heading)
            }
        }

        Flickable {
            id: sectionFlickable
            objectName: "knowledgeSectionOverview"
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.viewerDocument.kind === "section"
            clip: true
            contentWidth: Math.max(0, width - 12)
            contentHeight: sectionOverview.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            Controls.ScrollBar.vertical: Controls.ScrollBar {
                objectName: "knowledgeSectionScrollBar"
                theme: root.theme
                flickableTarget: sectionFlickable
            }

            ColumnLayout {
                id: sectionOverview
                width: sectionFlickable.contentWidth
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Section contents")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.title
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Open a page or continue into a subsection.")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.Wrap
                        }
                    }
                    Label {
                        visible: root.sectionEntries.length > 0
                        text: String(root.sectionEntries.length)
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                }

                ColumnLayout {
                    id: sectionList
                    objectName: "knowledgeSectionList"
                    Layout.fillWidth: true
                    spacing: 4

                    Repeater {
                        model: root.sectionEntries
                        delegate: Controls.Button {
                            id: sectionEntry
                            required property var modelData
                            required property int index
                            objectName: "knowledgeSectionEntry-" + String(modelData.identity || index)
                            readonly property int outlineLevel: Math.max(1, Number(modelData.level || 1))
                            readonly property bool section: modelData.kind === "section"
                            readonly property int visualDepth: section || outlineLevel > 1 ? outlineLevel : 0
                            Layout.fillWidth: true
                            Layout.leftMargin: visualDepth * 20
                            Layout.preferredHeight: 48
                            theme: root.theme
                            text: String(modelData.title || "")
                            leftPadding: 8
                            rightPadding: 8
                            topPadding: 4
                            bottomPadding: 4
                            Accessible.name: text
                            onClicked: root.controller.select(String(modelData.identity || ""))

                            background: Controls.ItemSurface {
                                objectName: "knowledgeSectionEntrySurface-" + String(sectionEntry.modelData.identity || sectionEntry.index)
                                theme: root.theme
                                hovered: sectionEntry.hovered
                                pressed: sectionEntry.down
                                normalColor: "transparent"
                                cornerRadius: root.theme.itemRadius
                                borderWidth: 0
                                railVisible: false
                                separatorVisible: false
                            }

                            contentItem: RowLayout {
                                spacing: 8
                                Controls.MaterialIcon {
                                    objectName: "knowledgeSectionEntryIcon-" + String(sectionEntry.modelData.identity || sectionEntry.index)
                                    Layout.preferredWidth: 20
                                    name: sectionEntry.section ? "folder-open" : "file"
                                    size: 17
                                    color: sectionEntry.section ? root.theme.tertiary : root.theme.action
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0
                                    Label {
                                        Layout.fillWidth: true
                                        text: sectionEntry.text
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        objectName: "knowledgeSectionEntrySubtitle-" + String(sectionEntry.modelData.identity || sectionEntry.index)
                                        Layout.fillWidth: true
                                        text: sectionEntry.section ? qsTr("Section") + (String(sectionEntry.modelData.description || "").length > 0 ? "  ·  " + String(sectionEntry.modelData.description || "") : "") : String(sectionEntry.modelData.description || "")
                                        visible: text.length > 0
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 220
                    visible: root.sectionEntries.length === 0
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant
                    Controls.EmptyState {
                        anchors.fill: parent
                        anchors.margins: 12
                        theme: root.theme
                        iconName: "folder-open"
                        title: qsTr("Empty section")
                        message: qsTr("This section does not contain any pages yet.")
                    }
                }
            }
        }
    }

    KnowledgeRevisionHistoryPopup {
        id: historyPopup
        theme: root.theme
        controller: root.controller
    }
}
