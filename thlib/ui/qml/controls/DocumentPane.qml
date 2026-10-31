import QtQuick
import QtQuick.Controls
import "." as Controls
import "../tactic_frame/core/foundation.mjs" as Foundation

// Neutral Markdown reader; its owner supplies content and handles links/files.
ScrollView {
    id: root
    required property var theme
    property string documentKey: ""
    property url baseUrl: ""
    property string text: ""
    property string summary: ""
    property string notice: ""
    property string error: ""
    property real scrollOffset: 0
    property bool presented: true
    property real contentInset: theme.spacing.content
    property bool restoring: false
    property int restoreEpoch: 0
    signal linkActivated(string link)
    signal scrollChanged(string documentKey, real offset)
    signal formatRequested(var document, var style)
    padding: 0
    clip: true
    contentWidth: width
    contentHeight: documentColumn.height + contentInset * 2

    function prepare() {
        restoreEpoch++;
        restoring = true;
    }
    function restore() {
        if (!presented || !visible || height <= 0 || !contentItem)
            return;
        restoring = true;
        contentItem.contentY = Math.max(0, Math.min(scrollOffset, Math.max(0, contentHeight - height)));
        const epoch = restoreEpoch;
        Qt.callLater(function () {
            if (root && root.restoreEpoch === epoch)
                root.restoring = false;
        });
    }
    function capture() {
        if (!restoring && presented && visible && contentItem)
            scrollChanged(documentKey, contentItem.contentY);
    }
    function focusArticle() {
        documentBody.forceActiveFocus();
    }
    onDocumentKeyChanged: {
        prepare();
        Qt.callLater(restore);
    }
    onScrollOffsetChanged: Qt.callLater(restore)
    onPresentedChanged: if (presented)
        Qt.callLater(restore)
    onContentHeightChanged: Qt.callLater(restore)
    onHeightChanged: Qt.callLater(restore)
    Component.onCompleted: Qt.callLater(restore)
    Connections {
        target: root.contentItem
        ignoreUnknownSignals: true
        function onContentYChanged() {
            root.capture();
        }
    }
    Column {
        id: documentColumn
        x: root.contentInset
        y: root.contentInset
        width: Math.max(0, root.width - root.contentInset * 2 - 12)
        spacing: root.theme.spacing.section
        Controls.SelectableText {
            width: documentColumn.width
            height: contentHeight
            theme: root.theme
            visible: root.notice.length > 0
            text: root.notice
            color: root.theme.secondaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 11,
                hintingPreference: Font.PreferVerticalHinting
            })
        }
        Rectangle {
            objectName: "documentSummary"
            width: documentColumn.width
            height: summaryText.contentHeight + 24
            visible: root.summary.length > 0 && !root.error.length
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant
            Controls.MaterialIcon {
                x: 12
                y: 12
                size: 18
                name: "info"
                color: root.theme.action
            }
            Controls.SelectableText {
                id: summaryText
                objectName: "documentSummaryText"
                x: 12 + 18 + root.theme.spacing.compact
                y: 12
                width: Math.max(0, parent.width - x - root.theme.spacing.content)
                height: contentHeight
                theme: root.theme
                text: root.summary
                baseUrl: root.baseUrl
                textFormat: TextEdit.MarkdownText
                font: Qt.font({
                    family: root.theme.fontFamily,
                    pixelSize: 12,
                    hintingPreference: Font.PreferVerticalHinting
                })
                onLinkActivated: link => root.linkActivated(link)
                onTextChanged: Qt.callLater(function () {
                    if (!root || !summaryText)
                        return;
                    root.formatRequested(summaryText.textDocument, Object.assign({}, Foundation.controls.document, {
                        borderColor: String(root.theme.outlineVariant)
                    }));
                })
            }
        }
        Controls.SelectableText {
            id: documentBody
            objectName: "documentBody"
            width: documentColumn.width
            height: contentHeight
            theme: root.theme
            text: root.error.length ? root.error : root.text
            baseUrl: root.baseUrl
            textFormat: root.error.length ? TextEdit.PlainText : TextEdit.MarkdownText
            color: root.error.length ? root.theme.error : root.theme.primaryText
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 12,
                hintingPreference: Font.PreferVerticalHinting
            })
            onLinkActivated: link => root.linkActivated(link)
            onTextChanged: Qt.callLater(function () {
                if (!root || !documentBody)
                    return;
                root.formatRequested(documentBody.textDocument, Object.assign({}, Foundation.controls.document, {
                    borderColor: String(root.theme.outlineVariant)
                }));
            })
        }
    }
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical: Controls.ScrollBar {
        objectName: "documentScrollbar"
        theme: root.theme
        flickableTarget: root
    }
}
