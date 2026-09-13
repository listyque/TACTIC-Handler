pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    objectName: "knowledgeArticleEditor"
    required property var theme
    required property var controller
    readonly property var richTextDocument: knowledgeRichText
    signal backRequested
    property bool resizeActive: false
    readonly property bool narrow: width < 720
    readonly property bool compactHeader: width < 1180
    readonly property bool minimalHeader: width < 640
    property bool backNavigationAvailable: root.narrow
    readonly property bool article: root.controller.document.kind === "article"
    readonly property var parentSection: root.controller ? root.controller.parentSection || ({}) : ({})
    property bool contentDirty: false
    property int editorStep: root.article && root.controller.creating ? 0 : 1
    property bool metadataExpanded: !root.article || root.editorStep === 0
    property bool attachmentsVisible: false
    property bool fittingImages: false
    property int imageDropPosition: -1
    property bool movingImage: false
    property var hoveredLink: ({})
    property string contentMode: "visual"
    property bool loadingSource: false
    readonly property bool contentStep: root.article && root.editorStep === 1
    readonly property bool hoveredLinkActive: String(root.hoveredLink.target || "").length > 0
    readonly property real imageMaximumWidth: Math.max(24, documentFlickable.width - 40)
    readonly property real imageInitialWidth: Math.min(560, root.imageMaximumWidth)
    readonly property int imageWidthBucket: Math.floor(root.imageMaximumWidth / 64)

    color: root.theme.workspace

    function syncSelection() {
        knowledgeRichText.sync_selection(articleEditor.cursorPosition, articleEditor.selectionStart, articleEditor.selectionEnd);
    }

    function scheduleSelectionSync() {
        if (articleEditor.activeFocus)
            selectionSync.restart();
    }

    Timer {
        id: selectionSync
        interval: 100
        onTriggered: {
            if (!knowledgeRichText.imageSelected)
                root.syncSelection();
        }
    }

    Timer {
        id: draftCheckpoint
        interval: 350
        onTriggered: root.checkpointDraft()
    }

    function selectEditorImage(position) {
        if (!knowledgeRichText.select_image_at(position, root.imageMaximumWidth))
            return false;
        const imagePosition = knowledgeRichText.selectedImagePosition;
        articleEditor.select(imagePosition, imagePosition + 1);
        knowledgeRichText.select_image_at(imagePosition, root.imageMaximumWidth);
        root.syncSelection();
        return true;
    }

    function selectEditorImageAtPoint(x, y) {
        if (!root.richTextDocument.select_image_at_point(
                x - articleEditor.leftPadding,
                y - articleEditor.topPadding,
                root.imageMaximumWidth)
                && !root.richTextDocument.try_select_image_at(
                    articleEditor.positionAt(x, y),
                    root.imageMaximumWidth)) {
            return false;
        }
        const imagePosition = root.richTextDocument.selectedImagePosition;
        articleEditor.select(imagePosition, imagePosition + 1);
        root.richTextDocument.select_image_at(
            imagePosition, root.imageMaximumWidth);
        root.syncSelection();
        return true;
    }

    function saveDocument() {
        root.syncContent();
        root.contentDirty = false;
        root.controller.save();
    }

    function saveDraftDocument() {
        root.syncContent();
        root.contentDirty = false;
        root.controller.save_draft();
    }

    function syncContent() {
        if (!root.article || !root.contentDirty)
            return;
        if (root.contentMode === "markdown")
            root.controller.set_content(markdownEditor.text);
        else if (knowledgeRichText.attached)
            root.controller.set_content(knowledgeRichText.markdown());
    }

    function checkpointDraft() {
        if (!root.article || !root.contentDirty)
            return;
        root.syncContent();
        root.controller.checkpoint_current_draft();
        root.contentDirty = false;
    }

    function returnToArticles() {
        root.syncContent();
        root.controller.stash_current_draft();
        root.backRequested();
    }

    function attachEditorDocument() {
        knowledgeRichText.attach(articleEditor.textDocument);
        root.loadEditorDocument();
    }

    function loadEditorDocument() {
        if (root.contentMode === "markdown") {
            root.loadingSource = true;
            markdownEditor.text = String(root.controller.editorMarkdown || "");
            root.loadingSource = false;
            root.contentDirty = false;
            return;
        }
        root.fittingImages = true;
        articleEditor.text = String(root.controller.editorHtml || "<p></p>");
        knowledgeRichText.apply_image_storage_sources(
            root.controller.editorImageStorageSources || []);
        root.fitImagesToContentWidth();
        root.fittingImages = false;
        root.syncSelection();
        root.contentDirty = false;
    }

    function setContentMode(mode) {
        mode = String(mode || "visual");
        if (mode === root.contentMode)
            return;
        root.syncContent();
        root.contentMode = mode;
        root.loadEditorDocument();
        if (mode === "markdown")
            markdownEditor.forceActiveFocus();
        else
            articleEditor.forceActiveFocus();
    }

    function fitImagesToContentWidth() {
        if (!knowledgeRichText.attached)
            return;
        const wasDirty = root.contentDirty;
        root.fittingImages = true;
        knowledgeRichText.fit_images_to_width(root.imageMaximumWidth);
        root.fittingImages = false;
        root.contentDirty = wasDirty;
    }

    function imageSizeText(width, height) {
        return qsTr("%1 × %2 px").arg(Math.max(0, Math.round(width))).arg(Math.max(0, Math.round(height)));
    }

    function selectedImageMetricsText() {
        const displayedHeight = knowledgeRichText.selectedImageHeight > 0 ? knowledgeRichText.selectedImageHeight : imageSelectionFrame.selectedImageRect.height;
        let values = [qsTr("Displayed: %1").arg(root.imageSizeText(knowledgeRichText.selectedImageWidth, displayedHeight))];
        if (knowledgeRichText.selectedImageNaturalWidth > 0 && knowledgeRichText.selectedImageNaturalHeight > 0) {
            values.push(qsTr("Original: %1").arg(root.imageSizeText(knowledgeRichText.selectedImageNaturalWidth, knowledgeRichText.selectedImageNaturalHeight)));
        }
        if (Math.abs(knowledgeRichText.selectedImageConfiguredWidth - knowledgeRichText.selectedImageWidth) > 1) {
            values.push(qsTr("Article size: %1").arg(root.imageSizeText(knowledgeRichText.selectedImageConfiguredWidth, knowledgeRichText.selectedImageConfiguredHeight)));
        }
        return values.join("  ·  ");
    }

    function updateHoveredLink(target, x, y) {
        target = String(target || "");
        if (target.length === 0)
            return;
        if (String(root.hoveredLink.target || "") === target)
            return;
        const position = articleEditor.positionAt(x, y);
        const details = root.richTextDocument.link_at(position, target);
        root.hoveredLink = String(details.target || "").length > 0 ? details : ({});
    }

    function clearHoveredLink() {
        root.hoveredLink = ({});
    }

    function editLinkButtonContains(x, y) {
        if (!editHoveredLink.visible)
            return false;
        const point = editHoveredLink.mapFromItem(articleEditor, x, y);
        return point.x >= 0 && point.y >= 0 && point.x <= editHoveredLink.width && point.y <= editHoveredLink.height;
    }

    function imageControlsContain(x, y) {
        if (!imageMetricsPanel.visible)
            return false;
        const point = imageMetricsPanel.mapFromItem(articleEditor, x, y);
        return point.x >= 0 && point.y >= 0
            && point.x <= imageMetricsPanel.width
            && point.y <= imageMetricsPanel.height;
    }

    function continueToContent() {
        if (String(root.controller.document.title || "").trim().length === 0)
            return;
        root.editorStep = 1;
        root.metadataExpanded = false;
        root.attachmentsVisible = false;
    }

    function toggleMetadata() {
        if (root.controller.creating) {
            root.syncContent();
            root.editorStep = 0;
            root.metadataExpanded = true;
            root.attachmentsVisible = false;
            return;
        }
        root.metadataExpanded = !root.metadataExpanded;
    }

    Component.onDestruction: {
        selectionSync.stop();
        draftCheckpoint.stop();
        root.checkpointDraft();
        knowledgeRichText.detach();
    }
    onContentDirtyChanged: {
        if (root.contentDirty)
            draftCheckpoint.restart();
        else
            draftCheckpoint.stop();
    }
    onImageWidthBucketChanged: {
        if (!root.resizeActive)
            root.fitImagesToContentWidth();
    }
    onResizeActiveChanged: {
        if (!root.resizeActive)
            root.fitImagesToContentWidth();
    }
    Connections {
        target: root.controller

        function onEditorDocumentChanged() {
            root.loadEditorDocument();
        }
    }

    Shortcut {
        sequence: StandardKey.Bold
        enabled: root.visible && root.article && root.contentMode === "visual"
        onActivated: {
            root.syncSelection();
            knowledgeRichText.toggle_bold();
        }
    }
    Shortcut {
        sequence: StandardKey.Italic
        enabled: root.visible && root.article && root.contentMode === "visual"
        onActivated: {
            root.syncSelection();
            knowledgeRichText.toggle_italic();
        }
    }
    Shortcut {
        sequence: StandardKey.Underline
        enabled: root.visible && root.article && root.contentMode === "visual"
        onActivated: {
            root.syncSelection();
            knowledgeRichText.toggle_underline();
        }
    }
    Shortcut {
        sequence: "Ctrl+K"
        enabled: root.visible && root.article && root.contentMode === "visual"
        onActivated: {
            root.syncSelection();
            toolbar.insertPanelVisible = true;
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            id: editorHeader
            objectName: "knowledgeEditorHeader"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 7

            Controls.CompactIconButton {
                objectName: "knowledgeEditorBack"
                visible: root.backNavigationAvailable
                theme: root.theme
                iconName: "arrow-left"
                toolTip: qsTr("Back to articles")
                enabled: !root.controller.busy
                onClicked: root.returnToArticles()
            }

            Controls.MaterialIcon {
                objectName: "knowledgeEditorKindIcon"
                name: root.article ? "file" : "folder"
                size: 20
                color: root.theme.action
            }
            Label {
                objectName: "knowledgeEditorTitle"
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: root.article ? qsTr("Edit article") : qsTr("Edit section")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.title
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                objectName: "knowledgeCreationStep"
                visible: root.article && root.controller.creating
                text: qsTr("Step %1 of 2").arg(root.editorStep + 1)
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
            }
            Controls.Button {
                objectName: "knowledgeMetadataToggle"
                visible: root.contentStep
                theme: root.theme
                compact: root.compactHeader
                tonal: root.metadataExpanded
                text: root.controller.creating ? qsTr("Back to title and summary") : root.metadataExpanded ? qsTr("Hide title and summary") : qsTr("Show title and summary")
                icon.name: root.controller.creating ? "arrow-left" : root.metadataExpanded ? "chevron-up" : "chevron-down"
                toolTip: text
                onClicked: root.toggleMetadata()
            }
            Controls.Button {
                objectName: "knowledgeLinkSelectedObjects"
                visible: root.article && root.controller.linkableSelectedObjects.length > 0
                theme: root.theme
                compact: root.compactHeader
                tonal: true
                text: root.controller.linkableSelectedObjects.length === 1 ? qsTr("Link selected object to article") : qsTr("Link %1 selected objects to article").arg(root.controller.linkableSelectedObjects.length)
                toolTip: text
                icon.name: "link"
                enabled: !root.controller.busy
                onClicked: root.controller.link_selected_objects()
            }
            Controls.Button {
                objectName: "knowledgeCancelAction"
                theme: root.theme
                text: qsTr("Cancel")
                compact: root.compactHeader
                icon.name: root.compactHeader ? "close" : ""
                toolTip: qsTr("Cancel")
                enabled: !root.controller.busy
                onClicked: root.controller.discard()
            }
            Controls.Button {
                objectName: "knowledgeArchiveAction"
                visible: !root.controller.creating
                theme: root.theme
                text: root.article ? qsTr("Delete article") : qsTr("Delete section")
                compact: root.compactHeader
                icon.name: "delete"
                toolTip: text
                destructive: true
                enabled: !root.controller.busy
                onClicked: root.controller.delete_selected()
            }
            Controls.Button {
                objectName: "knowledgeSaveDraft"
                visible: root.controller.creating || root.controller.draft
                theme: root.theme
                text: qsTr("Save as draft")
                icon.name: "save"
                compact: root.minimalHeader
                tonal: true
                toolTip: qsTr("Save as draft")
                enabled: (root.controller.dirty || root.controller.localDraft || root.contentDirty) && !root.controller.busy
                onClicked: root.saveDraftDocument()
            }
            Controls.Button {
                objectName: "knowledgeSave"
                visible: !root.article || !root.controller.creating || root.contentStep
                theme: root.theme
                text: root.controller.creating || root.controller.draft ? qsTr("Publish") : qsTr("Save")
                icon.name: root.controller.creating || root.controller.draft ? "send" : "save"
                compact: root.minimalHeader
                toolTip: text
                highlighted: true
                enabled: (root.controller.dirty || root.controller.draft || root.controller.localDraft || root.contentDirty) && !root.controller.busy
                onClicked: root.saveDocument()
            }
        }

        Rectangle {
            objectName: "knowledgeCreationParent"
            Layout.fillWidth: true
            implicitHeight: creationParentRow.implicitHeight + 16
            visible: root.controller.creating && root.metadataExpanded
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                id: creationParentRow
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                Controls.MaterialIcon {
                    name: "folder"
                    size: 18
                    color: root.theme.tertiary
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        text: qsTr("Parent section")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    Label {
                        objectName: "knowledgeCreationParentTitle"
                        Layout.fillWidth: true
                        text: String(root.parentSection.title || "").length > 0 ? String(root.parentSection.title) : qsTr("Knowledge Base root")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                }
            }
        }

        KnowledgeLinkedObjectHeader {
            id: linkedObjectHeader
            Layout.fillWidth: true
            visible: count > 0
            theme: root.theme
            controller: root.controller
        }

        Flickable {
            id: formFlickable
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width - 12
            contentHeight: editForm.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            Controls.ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: formFlickable
            }

            ColumnLayout {
                id: editForm
                width: formFlickable.contentWidth
                spacing: 9

                Label {
                    visible: root.metadataExpanded
                    text: qsTr("Title")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextField {
                    objectName: "knowledgeTitleField"
                    visible: root.metadataExpanded
                    Layout.fillWidth: true
                    theme: root.theme
                    text: String(root.controller.document.title || "")
                    placeholderText: qsTr("A short, recognizable title")
                    onTextEdited: root.controller.set_field("title", text)
                }
                Label {
                    visible: root.metadataExpanded
                    text: qsTr("Summary")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextArea {
                    objectName: "knowledgeSummaryField"
                    visible: root.metadataExpanded
                    Layout.fillWidth: true
                    Layout.preferredHeight: 76
                    theme: root.theme
                    text: String(root.controller.document.description || "")
                    placeholderText: qsTr("What this page is about")
                    onTextChanged: {
                        if (activeFocus)
                            root.controller.set_field("description", text);
                    }
                }

                RowLayout {
                    objectName: "knowledgeCreationNavigation"
                    Layout.fillWidth: true
                    visible: root.article && root.controller.creating && root.editorStep === 0
                    Item {
                        Layout.fillWidth: true
                    }
                    Controls.Button {
                        objectName: "knowledgeCreationNext"
                        theme: root.theme
                        text: qsTr("Continue to content")
                        icon.name: "arrow-right"
                        highlighted: true
                        enabled: String(root.controller.document.title || "").trim().length > 0
                        onClicked: root.continueToContent()
                    }
                }

                KnowledgeRichTextToolbar {
                    id: toolbar
                    Layout.fillWidth: true
                    visible: root.contentStep
                    theme: root.theme
                    documentController: knowledgeRichText
                    maximumImageWidth: root.imageInitialWidth
                    contentMode: root.contentMode
                    onContentModeRequested: mode => root.setContentMode(mode)
                    onEditorActionRequested: {
                        root.syncSelection();
                        articleEditor.forceActiveFocus();
                    }
                    onAttachRequested: root.attachmentsVisible = !root.attachmentsVisible
                    onImageInserted: root.selectEditorImage(
                        root.richTextDocument.selectedImagePosition)
                }

                KnowledgeAttachmentLibrary {
                    id: attachmentLibrary
                    Layout.fillWidth: true
                    visible: root.contentStep && root.contentMode === "visual" && root.attachmentsVisible
                    theme: root.theme
                    controller: root.controller
                    uploadController: knowledgeAttachments
                    stagingModel: knowledgeAttachmentDraftModel
                    uploadedModel: root.controller.uploadedAttachmentModel
                    documentController: knowledgeRichText
                    maximumImageWidth: root.imageInitialWidth
                    onInsertionRequested: root.syncSelection()
                    onImageInserted: root.selectEditorImage(
                        root.richTextDocument.selectedImagePosition)
                    onCloseRequested: root.attachmentsVisible = false
                    onContentChanged: {
                        root.controller.set_content(knowledgeRichText.markdown());
                    }
                }

                Rectangle {
                    objectName: "knowledgeEditorSurface"
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.contentStep ? Math.max(360, formFlickable.height - toolbar.implicitHeight - 18) : 0
                    visible: root.contentStep
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainerHigh
                    border.width: articleEditor.activeFocus || markdownEditor.activeFocus ? 2 : 1
                    border.color: articleEditor.activeFocus || markdownEditor.activeFocus ? root.theme.action : root.theme.outline

                    Flickable {
                        id: documentFlickable
                        visible: root.contentMode === "visual"
                        anchors.fill: parent
                        anchors.margins: 2
                        clip: true
                        contentWidth: width - 12
                        contentHeight: Math.max(height, articleEditor.contentHeight + 24)
                        boundsBehavior: Flickable.StopAtBounds

                        Controls.ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                            flickableTarget: documentFlickable
                        }

                        TextEdit {
                            id: articleEditor
                            objectName: "knowledgeRichTextEditor"
                            width: documentFlickable.contentWidth
                            height: Math.max(documentFlickable.height, contentHeight + 24)
                            leftPadding: 13
                            rightPadding: 13
                            topPadding: 12
                            bottomPadding: 12
                            text: "<p></p>"
                            textFormat: TextEdit.RichText
                            wrapMode: TextEdit.Wrap
                            selectByMouse: true
                            persistentSelection: true
                            color: root.theme.primaryText
                            selectionColor: root.theme.action
                            selectedTextColor: root.theme.selectedText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            onCursorPositionChanged: root.scheduleSelectionSync()
                            onSelectionStartChanged: root.scheduleSelectionSync()
                            onSelectionEndChanged: root.scheduleSelectionSync()
                            onTextChanged: {
                                if (!root.fittingImages
                                        && root.contentDirty !== true
                                        && knowledgeRichText.attached)
                                    root.contentDirty = true;
                            }
                            onActiveFocusChanged: {
                                if (!activeFocus) {
                                    root.syncSelection();
                                    if (root.contentDirty)
                                        root.syncContent();
                                }
                            }
                            Component.onCompleted: {
                                root.attachEditorDocument();
                            }

                            onLinkHovered: link => root.updateHoveredLink(link, editorHover.point.position.x, editorHover.point.position.y)

                            HoverHandler {
                                id: editorHover
                                cursorShape: root.movingImage ? Qt.ClosedHandCursor : String(articleEditor.hoveredLink || "").length > 0 ? Qt.PointingHandCursor : Qt.IBeamCursor
                                onPointChanged: {
                                    if (root.hoveredLinkActive && String(articleEditor.hoveredLink || "").length === 0 && !root.editLinkButtonContains(point.position.x, point.position.y))
                                        root.clearHoveredLink();
                                }
                            }

                            TapHandler {
                                acceptedButtons: Qt.LeftButton
                                gesturePolicy: TapHandler.DragThreshold
                                onTapped: (eventPoint, button) => {
                                    root.clearHoveredLink();
                                    if (!root.selectEditorImageAtPoint(
                                        eventPoint.position.x,
                                        eventPoint.position.y)
                                            && !root.imageControlsContain(
                                                eventPoint.position.x,
                                                eventPoint.position.y)) {
                                        root.richTextDocument.clear_image_selection();
                                    }
                                }
                                onCanceled: {
                                    if (root.richTextDocument.imageSelected)
                                        root.richTextDocument.clear_image_selection();
                                }
                            }

                            TapHandler {
                                acceptedButtons: Qt.RightButton
                                gesturePolicy: TapHandler.DragThreshold
                                onTapped: (eventPoint, button) => {
                                    const position = articleEditor.positionAt(
                                        eventPoint.position.x,
                                        eventPoint.position.y);
                                    richTextContextMenu.openForEditor(
                                        articleEditor,
                                        eventPoint.position.x,
                                        eventPoint.position.y,
                                        position);
                                }
                            }

                            KnowledgeImageSelectionOverlay {
                                id: imageSelectionFrame
                                theme: root.theme
                                editor: articleEditor
                                documentController: knowledgeRichText
                                maximumWidth: root.imageMaximumWidth
                                active: root.contentStep
                                moving: root.movingImage
                                dropPosition: root.imageDropPosition
                                onContentChanged: root.syncContent()
                                onMoveStarted: {
                                    root.clearHoveredLink();
                                    root.movingImage = true;
                                    root.imageDropPosition = root.richTextDocument.selectedImagePosition;
                                }
                                onMoveUpdated: position => root.imageDropPosition = position
                                onMoveFinished: position => {
                                    if (position >= 0 && root.richTextDocument.move_selected_image(position)) {
                                        root.selectEditorImage(root.richTextDocument.selectedImagePosition);
                                        root.contentDirty = true;
                                        root.syncContent();
                                    }
                                    root.imageDropPosition = -1;
                                    root.movingImage = false;
                                }
                                onMoveCanceled: {
                                    root.imageDropPosition = -1;
                                    root.movingImage = false;
                                }
                            }

                            Controls.CompactIconButton {
                                id: editHoveredLink
                                objectName: "knowledgeEditHoveredLink"
                                readonly property rect linkEndRect: root.hoveredLinkActive ? articleEditor.positionToRectangle(Number(root.hoveredLink.end)) : Qt.rect(0, 0, 0, 0)
                                visible: root.contentStep && root.hoveredLinkActive && !root.movingImage
                                x: Math.max(4, Math.min(articleEditor.width - width - 4, linkEndRect.x + 5))
                                y: linkEndRect.y >= height + 4 ? linkEndRect.y - height - 3 : linkEndRect.y + linkEndRect.height + 3
                                width: 30
                                height: 30
                                z: 7
                                theme: root.theme
                                iconName: "edit"
                                forceSolidIcon: true
                                toolTip: qsTr("Edit link")
                                onPointerHoveredChanged: {
                                    if (!pointerHovered && String(articleEditor.hoveredLink || "").length === 0)
                                        root.clearHoveredLink();
                                }
                                onClicked: {
                                    toolbar.editLink(root.hoveredLink);
                                    root.clearHoveredLink();
                                }
                            }
                        }
                    }

                    Flickable {
                        id: markdownFlickable
                        visible: root.contentMode === "markdown"
                        anchors.fill: parent
                        anchors.margins: 2
                        clip: true
                        contentWidth: width - 12
                        contentHeight: Math.max(
                            height, markdownEditor.contentHeight + 24)
                        boundsBehavior: Flickable.StopAtBounds

                        Controls.ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                            flickableTarget: markdownFlickable
                        }

                        TextEdit {
                            id: markdownEditor
                            objectName: "knowledgeMarkdownEditor"
                            width: markdownFlickable.contentWidth
                            height: Math.max(
                                markdownFlickable.height, contentHeight + 24)
                            leftPadding: 13
                            rightPadding: 13
                            topPadding: 12
                            bottomPadding: 12
                            textFormat: TextEdit.PlainText
                            wrapMode: TextEdit.Wrap
                            selectByMouse: true
                            persistentSelection: true
                            color: root.theme.primaryText
                            selectionColor: root.theme.action
                            selectedTextColor: root.theme.selectedText
                            font.family: "Consolas"
                            font.pointSize: Controls.Typography.body
                            onTextChanged: {
                                if (!root.loadingSource)
                                    root.contentDirty = true;
                            }

                            TapHandler {
                                acceptedButtons: Qt.RightButton
                                gesturePolicy: TapHandler.DragThreshold
                                onTapped: (eventPoint, button) => {
                                    markdownContextMenu.openForEditor(
                                        markdownEditor,
                                        eventPoint.position.x,
                                        eventPoint.position.y,
                                        markdownEditor.positionAt(
                                            eventPoint.position.x,
                                            eventPoint.position.y));
                                }
                            }
                        }

                        Controls.TextContextMenu {
                            id: markdownContextMenu
                            theme: root.theme
                            editor: markdownEditor
                            readOnly: false
                        }
                    }

                    Rectangle {
                        id: imageMetricsPanel
                        objectName: "knowledgeSelectedImageMetrics"
                        visible: root.contentStep && root.contentMode === "visual" && knowledgeRichText.imageSelected
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 10
                        width: Math.min(Math.max(270, imageMetricsColumn.implicitWidth + 20), Math.max(160, parent.width - 20))
                        height: imageMetricsColumn.implicitHeight + 12
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerHighest
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        z: 8

                        ColumnLayout {
                            id: imageMetricsColumn
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 2

                            Label {
                                objectName: "knowledgeSelectedImageSize"
                                Layout.maximumWidth: Math.max(100, documentFlickable.width - 40)
                                text: root.selectedImageMetricsText()
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                            Controls.CheckBox {
                                objectName: "knowledgeImageContentWidth"
                                Layout.fillWidth: true
                                theme: root.theme
                                compact: true
                                text: qsTr("Stretch to content width")
                                checked: root.richTextDocument.selectedImageContentWidth
                                onToggled: {
                                    if (root.richTextDocument.set_selected_image_content_width(checked, root.imageMaximumWidth)) {
                                        root.contentDirty = true;
                                        root.syncContent();
                                    }
                                }
                            }
                            RowLayout {
                                objectName: "knowledgeImageFixedWidth"
                                Layout.fillWidth: true
                                spacing: 7
                                visible: !root.richTextDocument.selectedImageContentWidth

                                Controls.MaterialIcon {
                                    name: "image"
                                    size: 14
                                    color: root.theme.secondaryText
                                }
                                Controls.Slider {
                                    id: imageWidthSlider
                                    objectName: "knowledgeImageWidthSlider"
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    from: 24
                                    to: Math.max(24, root.imageMaximumWidth)
                                    stepSize: 1
                                    live: true
                                    value: Math.max(24, knowledgeRichText.selectedImageWidth)
                                    Accessible.name: qsTr("Fixed image width")
                                    onMoved: {
                                        knowledgeRichText.resize_selected_image(value, root.imageMaximumWidth);
                                        root.contentDirty = true;
                                    }
                                    onPressedChanged: {
                                        if (!pressed && root.contentDirty)
                                            root.syncContent();
                                    }
                                }
                                Label {
                                    text: qsTr("%1 px").arg(Math.round(knowledgeRichText.selectedImageWidth))
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                }
                            }
                        }
                    }

                    Controls.TextContextMenu {
                        id: richTextContextMenu
                        theme: root.theme
                        editor: articleEditor
                        readOnly: false
                    }
                }
            }
        }
    }

}
