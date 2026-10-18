pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/format.ui.mjs" as UI

Rectangle {
    id: root
    objectName: "knowledgeRichTextToolbar"
    required property var theme
    required property var documentController
    property real maximumImageWidth: 560
    property string contentMode: "visual"
    property bool insertPanelVisible: false
    property string blockPanelMode: ""
    property int editLinkStart: -1
    property int editLinkEnd: -1
    signal attachRequested
    signal editorActionRequested
    signal imageInserted
    signal contentModeRequested(string mode)

    readonly property bool compactToolbar: width < 760
    readonly property bool minimalToolbar: width < 640
    readonly property bool showAlignmentActions: width >= 1000
    readonly property bool editingLink: editLinkStart >= 0 && editLinkEnd > editLinkStart
    readonly property bool blockPanelVisible: blockPanelMode === "quote" || blockPanelMode === "pullquote" || blockPanelMode === "code-block"
    readonly property var formatState: documentController.formatState || ({})
    readonly property var historyActions: UI.historyActions
    readonly property var textActions: UI.textActions.map(record => Object.assign({}, record, {
            tip: qsTr(record.tip)
        }))
    readonly property var insertActions: UI.insertActions.map(record => Object.assign({}, record, {
            tip: qsTr(record.tip)
        }))
    readonly property var alignmentActions: UI.alignmentActions.map(record => Object.assign({}, record, {
            tip: qsTr(record.tip)
        }))

    function checkedActions() {
        const result = {};
        for (const record of UI.textActions.concat(UI.insertActions, UI.alignmentActions))
            result[record.action] = root.actionChecked(record.action);
        return result;
    }

    function actionChecked(action) {
        if (action === "bold")
            return !!root.formatState.bold;
        if (action === "italic")
            return !!root.formatState.italic;
        if (action === "underline")
            return !!root.formatState.underline;
        if (action === "strike")
            return !!root.formatState.strike;
        if (action === "bullet")
            return root.formatState.listStyle === "bullet";
        if (action === "number")
            return root.formatState.listStyle === "ordered";
        if (action === "checklist")
            return root.formatState.listStyle === "checklist";
        if (action === "quote")
            return !!root.formatState.quote;
        if (action === "pullquote")
            return !!root.formatState.pullQuote;
        if (action === "code-block")
            return !!root.formatState.codeBlock;
        if (action === "small-text")
            return !!root.formatState.smallText;
        if (action.indexOf("heading:") === 0) {
            const level = Number(action.slice(8));
            return level === Number(root.formatState.heading || 0) && (level > 0 || !root.formatState.quote && !root.formatState.pullQuote && !root.formatState.codeBlock && !root.formatState.smallText);
        }
        return root.formatState.alignment === action;
    }

    function runAction(action) {
        root.editorActionRequested();
        if (action === "undo")
            root.documentController.undo();
        else if (action === "redo")
            root.documentController.redo();
        else if (action === "bold")
            root.documentController.toggle_bold();
        else if (action === "italic")
            root.documentController.toggle_italic();
        else if (action === "underline")
            root.documentController.toggle_underline();
        else if (action === "strike")
            root.documentController.toggle_strike();
        else if (action === "bullet")
            root.documentController.toggle_list("bullet");
        else if (action === "number")
            root.documentController.toggle_list("ordered");
        else if (action === "checklist")
            root.documentController.toggle_check_list();
        else if (action === "table")
            root.documentController.insert_table();
        else if (action === "quote" || action === "pullquote" || action === "code-block")
            root.openBlockPanel(action);
        else if (action === "small-text")
            root.documentController.set_small_text();
        else if (action === "divider")
            root.documentController.insert_divider();
        else if (action === "left")
            root.documentController.set_alignment("left");
        else if (action === "center")
            root.documentController.set_alignment("center");
        else if (action === "right")
            root.documentController.set_alignment("right");
        else if (action === "link") {
            root.closeBlockPanel();
            if (root.insertPanelVisible) {
                root.closeLinkPanel();
            } else {
                root.editLinkStart = -1;
                root.editLinkEnd = -1;
                targetField.clear();
                labelField.clear();
                root.insertPanelVisible = true;
                targetField.forceActiveFocus();
            }
        } else if (action === "attach")
            root.attachRequested();
        else if (action === "clear")
            root.documentController.clear_format();
        else if (action.indexOf("heading:") === 0)
            root.documentController.set_heading(Number(action.slice(8)));
    }

    function closeLinkPanel() {
        root.insertPanelVisible = false;
        root.editLinkStart = -1;
        root.editLinkEnd = -1;
        targetField.clear();
        labelField.clear();
    }

    function openBlockPanel(mode) {
        root.closeLinkPanel();
        root.blockPanelMode = mode;
        blockText.text = root.documentController.selected_text();
        if (mode === "code-block")
            languageChoice.currentIndex = 0;
        blockText.forceActiveFocus();
        blockText.selectAll();
    }

    function closeBlockPanel() {
        root.blockPanelMode = "";
        blockText.clear();
    }

    function editLink(details) {
        if (!details || Number(details.start) < 0)
            return;
        root.editLinkStart = Number(details.start);
        root.editLinkEnd = Number(details.end);
        targetField.text = String(details.target || "");
        labelField.text = String(details.label || "");
        root.insertPanelVisible = true;
        targetField.forceActiveFocus();
        targetField.selectAll();
    }

    implicitHeight: formatRow.implicitHeight + 12 + (insertPanelVisible ? insertPanel.implicitHeight + 7 : 0) + (blockPanelVisible ? blockInsertPanel.implicitHeight + 7 : 0)
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainer
    border.width: 1
    border.color: root.theme.outlineVariant

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 7

        Frame.FrameView {
            id: formatRow
            Layout.fillWidth: true
            implicitHeight: scene.height
            Layout.preferredHeight: implicitHeight
            theme: root.theme
            scene: UI.describe({
                mode: root.contentMode,
                checked: root.checkedActions(),
                blockStyle: Number(root.formatState.heading || 0) > 0 || root.formatState.quote || root.formatState.pullQuote || root.formatState.codeBlock || root.formatState.smallText,
                listStyle: root.formatState.listStyle
            }, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
            onEvent: (action, source) => {
                const popup = action.type === "textStyle" ? textStyleMenu : action.type === "lists" ? listStyleMenu : action.type === "overflow" ? overflowMenu : null;
                if (action.pressed) {
                    if (popup)
                        popup.sourceWasOpen = popup.opened;
                    return;
                }
                if (action.type === "mode")
                    root.contentModeRequested(action.value);
                else if (action.type === "textStyle")
                    textStyleMenu.toggleBelow(source);
                else if (action.type === "lists")
                    listStyleMenu.toggleBelow(source);
                else if (action.type === "overflow")
                    overflowMenu.toggleBelow(source);
                else
                    root.runAction(action.type);
            }
        }

        Rectangle {
            id: insertPanel
            Layout.fillWidth: true
            visible: root.insertPanelVisible
            implicitHeight: insertFields.implicitHeight + 14
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh

            ColumnLayout {
                id: insertFields
                anchors.fill: parent
                anchors.margins: 7
                spacing: 5
                Controls.TextField {
                    id: targetField
                    objectName: "knowledgeLinkTarget"
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("https://, ftp://, tactic-search:// or skey://")
                    readonly property bool supportedLink: /^(skey|tactic-search|https?|ftp):\/\//i.test(text.trim())
                }
                RowLayout {
                    Layout.fillWidth: true
                    Controls.TextField {
                        id: labelField
                        objectName: "knowledgeLinkLabel"
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Link text (optional)")
                    }
                    Controls.Button {
                        objectName: "knowledgeLinkApply"
                        theme: root.theme
                        text: root.editingLink ? qsTr("Save link") : qsTr("Link")
                        icon.name: root.editingLink ? "edit" : "link"
                        enabled: targetField.supportedLink
                        highlighted: true
                        onClicked: {
                            root.editorActionRequested();
                            if (root.editingLink) {
                                root.documentController.update_link(root.editLinkStart, root.editLinkEnd, targetField.text.trim(), labelField.text.trim());
                            } else {
                                root.documentController.insert_link(targetField.text.trim(), labelField.text.trim());
                            }
                            root.closeLinkPanel();
                        }
                    }
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Image URL")
                        icon.name: "image"
                        enabled: /^https?:\/\//i.test(targetField.text.trim())
                        onClicked: {
                            root.editorActionRequested();
                            root.documentController.insert_image(targetField.text.trim(), labelField.text.trim(), root.maximumImageWidth);
                            root.imageInserted();
                            targetField.clear();
                            labelField.clear();
                            root.insertPanelVisible = false;
                        }
                    }
                }
            }
        }

        Rectangle {
            id: blockInsertPanel
            objectName: "knowledgeBlockInsertPanel"
            Layout.fillWidth: true
            visible: root.blockPanelVisible
            implicitHeight: blockInsertFields.implicitHeight + 14
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh

            ColumnLayout {
                id: blockInsertFields
                anchors.fill: parent
                anchors.margins: 7
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    text: root.blockPanelMode === "code-block" ? qsTr("Insert code block") : root.blockPanelMode === "pullquote" ? qsTr("Insert pull quote") : qsTr("Insert quote")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }

                Flickable {
                    id: blockTextFlickable
                    Layout.fillWidth: true
                    Layout.preferredHeight: 112
                    clip: true
                    contentWidth: width - blockTextScrollBar.reservedExtent
                    contentHeight: Math.max(height, blockText.contentHeight + blockText.topPadding + blockText.bottomPadding)
                    boundsBehavior: Flickable.StopAtBounds

                    Controls.ScrollBar.vertical: Controls.ScrollBar {
                        id: blockTextScrollBar
                        theme: root.theme
                        flickableTarget: blockTextFlickable
                    }

                    Controls.TextArea {
                        id: blockText
                        objectName: "knowledgeBlockText"
                        width: blockTextFlickable.contentWidth
                        height: Math.max(blockTextFlickable.height, contentHeight + topPadding + bottomPadding)
                        theme: root.theme
                        placeholderText: root.blockPanelMode === "code-block" ? qsTr("Paste or type code") : qsTr("Quote text")
                        font.family: root.blockPanelMode === "code-block" ? "Consolas" : root.theme.fontFamily
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 7

                    Controls.ComboBox {
                        id: languageChoice
                        objectName: "knowledgeCodeLanguage"
                        visible: root.blockPanelMode === "code-block"
                        Layout.preferredWidth: 170
                        theme: root.theme
                        model: [
                            {
                                "label": "Python",
                                "value": "python"
                            },
                            {
                                "label": "JavaScript",
                                "value": "javascript"
                            },
                            {
                                "label": "JSON",
                                "value": "json"
                            },
                            {
                                "label": "Bash",
                                "value": "bash"
                            },
                            {
                                "label": "SQL",
                                "value": "sql"
                            },
                            {
                                "label": qsTr("Plain text"),
                                "value": "text"
                            }
                        ]
                        textRole: "label"
                        valueRole: "value"
                        translateDisplayText: false
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Controls.Button {
                        objectName: "knowledgeBlockCancel"
                        theme: root.theme
                        text: qsTr("Cancel")
                        icon.name: "close"
                        onClicked: root.closeBlockPanel()
                    }
                    Controls.Button {
                        objectName: "knowledgeBlockApply"
                        theme: root.theme
                        text: qsTr("Insert")
                        icon.name: root.blockPanelMode === "code-block" ? "code-block" : "format-quote"
                        highlighted: true
                        enabled: blockText.text.trim().length > 0
                        onClicked: {
                            root.editorActionRequested();
                            if (root.blockPanelMode === "code-block")
                                root.documentController.insert_code_block(blockText.text, String(languageChoice.currentValue || "python"));
                            else
                                root.documentController.insert_quote(blockText.text, root.blockPanelMode === "pullquote" ? "pull" : "quote");
                            root.closeBlockPanel();
                        }
                    }
                }
            }
        }
    }

    ActionMenu {
        id: textStyleMenu
        objectName: "knowledgeTextStyleMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 220
        actions: [
            {
                "title": qsTr("Normal text"),
                "command": "heading:0",
                "icon": "format-paragraph",
                "checked": root.actionChecked("heading:0")
            },
            {
                "separator": true
            },
            {
                "title": qsTr("H1 · Heading 1"),
                "translate": false,
                "command": "heading:1",
                "icon": "format-header-1",
                "checked": root.actionChecked("heading:1")
            },
            {
                "title": qsTr("H2 · Heading 2"),
                "translate": false,
                "command": "heading:2",
                "icon": "format-header-2",
                "checked": root.actionChecked("heading:2")
            },
            {
                "title": qsTr("H3 · Heading 3"),
                "translate": false,
                "command": "heading:3",
                "icon": "format-header-3",
                "checked": root.actionChecked("heading:3")
            },
            {
                "title": qsTr("H4 · Heading 4"),
                "translate": false,
                "command": "heading:4",
                "icon": "format-header-4",
                "checked": root.actionChecked("heading:4")
            },
            {
                "title": qsTr("H5 · Heading 5"),
                "translate": false,
                "command": "heading:5",
                "icon": "format-header-5",
                "checked": root.actionChecked("heading:5")
            },
            {
                "title": qsTr("H6 · Heading 6"),
                "translate": false,
                "command": "heading:6",
                "icon": "format-header-6",
                "checked": root.actionChecked("heading:6")
            },
            {
                "separator": true
            },
            {
                "title": qsTr("Quote"),
                "command": "quote",
                "icon": "format-quote",
                "checked": root.actionChecked("quote")
            },
            {
                "title": qsTr("Pull quote"),
                "command": "pullquote",
                "icon": "format-quote",
                "checked": root.actionChecked("pullquote")
            },
            {
                "title": qsTr("Code block"),
                "command": "code-block",
                "icon": "code-block",
                "checked": root.actionChecked("code-block")
            },
            {
                "title": qsTr("Small text"),
                "command": "small-text",
                "icon": "small-text",
                "checked": root.actionChecked("small-text")
            }
        ]
        onTriggered: command => root.runAction(command)
    }

    ActionMenu {
        id: listStyleMenu
        objectName: "knowledgeListStyleMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 220
        actions: [
            {
                "title": qsTr("Bulleted list"),
                "command": "bullet",
                "icon": "list-ul",
                "checked": root.actionChecked("bullet")
            },
            {
                "title": qsTr("Numbered list"),
                "command": "number",
                "icon": "list-ol",
                "checked": root.actionChecked("number")
            },
            {
                "title": qsTr("Checklist"),
                "command": "checklist",
                "icon": "checkbox-multiple-marked-outline",
                "checked": root.actionChecked("checklist")
            }
        ]
        onTriggered: command => root.runAction(command)
    }

    ActionMenu {
        id: overflowMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 220
        actions: [
            {
                "title": qsTr("Insert table"),
                "command": "table",
                "icon": "table-view",
                "visible": root.compactToolbar
            },
            {
                "title": qsTr("Italic · Ctrl+I"),
                "command": "italic",
                "icon": "italic",
                "visible": root.minimalToolbar,
                "checked": root.actionChecked("italic")
            },
            {
                "title": qsTr("Show attached files"),
                "command": "attach",
                "icon": "attachments-editor",
                "visible": root.minimalToolbar
            },
            {
                "title": qsTr("Underline"),
                "command": "underline",
                "icon": "underline",
                "visible": root.width < 650,
                "checked": root.actionChecked("underline")
            },
            {
                "title": qsTr("Strikethrough"),
                "command": "strike",
                "icon": "strikethrough",
                "visible": root.width < 690,
                "checked": root.actionChecked("strike")
            },
            {
                "separator": true
            },
            {
                "title": qsTr("Align left"),
                "command": "left",
                "icon": "align-left",
                "visible": !root.showAlignmentActions,
                "checked": root.actionChecked("left")
            },
            {
                "title": qsTr("Align center"),
                "command": "center",
                "icon": "align-center",
                "visible": !root.showAlignmentActions,
                "checked": root.actionChecked("center")
            },
            {
                "title": qsTr("Align right"),
                "command": "right",
                "icon": "align-right",
                "visible": !root.showAlignmentActions,
                "checked": root.actionChecked("right")
            },
            {
                "separator": true
            },
            {
                "title": qsTr("Clear formatting"),
                "command": "clear",
                "icon": "eraser"
            }
        ]
        onTriggered: command => root.runAction(command)
    }
}
