pragma ComponentBehavior: Bound

import QtQuick
import "../../controls" as Controls
import "../.."

Rectangle {
    id: root

    required property var theme
    required property var controller
    required property real contentWidth
    property bool resizeActive: false
    readonly property var sourceDocument: root.controller.viewerDocument || ({})
    readonly property string sourceMarkdown: String(root.sourceDocument.contentMarkdown || "")
    readonly property var documentController: root.controller.richTextDocument
    readonly property var imageSources: root.controller.editorImageSources || ({})
    readonly property var syntaxColors: ({
            "keyword": root.theme.syntaxKeyword,
            "string": root.theme.syntaxString,
            "comment": root.theme.syntaxComment,
            "number": root.theme.syntaxNumber,
            "type": root.theme.syntaxType,
            "function": root.theme.syntaxFunction,
            "definition": root.theme.syntaxDefinition,
            "self": root.theme.syntaxSelf,
            "module": root.theme.syntaxSelf
        })
    property bool completed: false

    function scheduleLoad() {
        if (root.completed)
            loadTimer.restart();
    }

    function loadDocument() {
        root.documentController.attach(articleText.textDocument, root.syntaxColors);
        root.documentController.load_markdown(root.sourceMarkdown, root.imageSources);
        root.fitImagesToContentWidth();
    }

    function fitImagesToContentWidth() {
        if (root.documentController.attached)
            root.documentController.fit_images_to_width(Math.max(24, root.contentWidth));
    }

    function scrollToHeading(heading) {
        const title = String(heading.title || "");
        if (!title.length)
            return -1;
        const plainText = articleText.getText(0, articleText.length);
        let offset = 0;
        let occurrence = Math.max(0, Number(heading.occurrence || 0));
        while (true) {
            const position = plainText.indexOf(title, offset);
            if (position < 0)
                return -1;
            if (occurrence === 0) {
                const rectangle = articleText.positionToRectangle(position);
                articleText.select(position, position + title.length);
                return rectangle.y;
            }
            occurrence -= 1;
            offset = position + Math.max(1, title.length);
        }
    }

    objectName: "knowledgeArticleContent"
    color: root.theme.workspace
    implicitWidth: root.contentWidth
    implicitHeight: Math.max(1, articleText.contentHeight)

    Timer {
        id: loadTimer
        interval: 0
        onTriggered: root.loadDocument()
    }

    onSourceMarkdownChanged: root.scheduleLoad()
    onImageSourcesChanged: root.scheduleLoad()
    onSyntaxColorsChanged: {
        if (root.completed)
            root.documentController.attach(articleText.textDocument, root.syntaxColors);
    }
    onContentWidthChanged: {
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
            root.scheduleLoad();
        }
    }

    KnowledgeRichTextBlockDecorations {
        anchors.fill: articleText
        theme: root.theme
        editor: articleText
        documentController: root.documentController
        z: 0
    }

    Repeater {
        objectName: "knowledgeArticleImageRepeater"
        model: root.documentController.imageOverlays || []

        delegate: KnowledgeEditorImageOverlay {
            required property var modelData

            theme: root.theme
            documentController: root.documentController
            imageData: modelData
            horizontalOffset: articleText.leftPadding
            verticalOffset: articleText.topPadding
            interactive: true
            objectNamePrefix: "knowledgeArticleImage-"
            z: 2
            onActivated: source => root.controller.open_link(source)
        }
    }

    TextEdit {
        id: articleText

        objectName: "knowledgeArticleText"
        width: Math.max(1, root.contentWidth)
        height: contentHeight
        leftPadding: 0
        rightPadding: 0
        topPadding: 0
        bottomPadding: 0
        textFormat: TextEdit.RichText
        wrapMode: TextEdit.Wrap
        readOnly: true
        selectByMouse: true
        persistentSelection: true
        color: root.theme.primaryText
        selectionColor: root.theme.action
        selectedTextColor: root.theme.selectedText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
        z: 1
        onLinkActivated: link => root.controller.open_link(link)

        HoverHandler {
            cursorShape: String(articleText.hoveredLink || "").length > 0 ? Qt.PointingHandCursor : Qt.IBeamCursor
        }
    }

    Component.onCompleted: {
        root.completed = true;
        root.loadDocument();
    }
    Component.onDestruction: {
        loadTimer.stop();
        root.documentController.detach_from(articleText.textDocument);
    }
}
