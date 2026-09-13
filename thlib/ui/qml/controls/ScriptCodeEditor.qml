import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Item {
    id: root

    required property var theme
    required property var controller
    property alias text: editor.text
    readonly property alias selectedText: editor.selectedText
    property alias cursorPosition: editor.cursorPosition
    property bool searchVisible: false
    property bool replaceVisible: false
    property var completionItems: []
    property int completionIndex: 0
    property var symbols: []
    property int matchIndex: -1
    property int matchCount: 0
    property bool applyingCommand: false
    property string bufferKey: ""
    property real fontPointSize: Typography.body
    property int historyLimit: 120
    property var histories: ({})
    property int historyRevision: 0
    readonly property int lineNumberCount: Math.max(1, editor.lineCount)
    readonly property bool canUndo: historyRevision >= 0 && historyCanUndo()
    readonly property bool canRedo: historyRevision >= 0 && historyCanRedo()
    readonly property bool canCopy: editor.selectedText.length > 0
    readonly property bool canCut: canCopy
    readonly property bool canPaste: editor.canPaste
    readonly property bool editorActiveFocus: editor.activeFocus
    signal textEdited()
    signal runRequested()
    signal outlineRequested()

    function lineNumbers(count) {
        let values = []
        for (let number = 1; number <= count; ++number)
            values.push(String(number))
        return values.join("\n")
    }

    function syntaxColors() {
        return {
            "keyword": String(theme.syntaxKeyword),
            "string": String(theme.syntaxString),
            "comment": String(theme.syntaxComment),
            "number": String(theme.syntaxNumber),
            "type": String(theme.syntaxType),
            "function": String(theme.syntaxFunction),
            "definition": String(theme.syntaxDefinition),
            "decorator": String(theme.syntaxDefinition),
            "self": String(theme.syntaxSelf),
            "module": String(theme.syntaxSelf),
            "occurrence": String(theme.syntaxOccurrence),
            "search": String(theme.syntaxSearch)
        }
    }

    function searchOptions() {
        return {
            "caseSensitive": matchCase.checked,
            "wholeWord": wholeWord.checked,
            "regex": regularExpression.checked
        }
    }

    function refreshHighlights() {
        controller.update_editor_highlights(
            editor.selectedText, findField.text, searchOptions())
    }

    function updateMatches(selectNext) {
        const matches = controller.search_matches(
            editor.text, findField.text, searchOptions())
        matchCount = matches.length
        if (!matches.length) {
            matchIndex = -1
            return
        }
        if (matchIndex >= matches.length)
            matchIndex = matches.length - 1
        if (selectNext)
            findNext(false)
    }

    function showFind(replaceMode) {
        if (searchVisible && replaceVisible === replaceMode) {
            closeFind()
            return
        }
        searchVisible = true
        replaceVisible = replaceMode
        findField.forceActiveFocus()
        findField.selectAll()
        updateMatches(false)
    }

    function closeFind() {
        searchVisible = false
        replaceVisible = false
        findField.text = ""
        refreshHighlights()
        editor.forceActiveFocus()
    }

    function findNext(backwards) {
        const matches = controller.search_matches(
            editor.text, findField.text, searchOptions())
        matchCount = matches.length
        if (!matches.length) {
            matchIndex = -1
            return
        }
        let index = -1
        if (backwards) {
            for (let i = matches.length - 1; i >= 0; --i) {
                if (matches[i].end < editor.selectionStart) {
                    index = i
                    break
                }
            }
            if (index < 0)
                index = matches.length - 1
        } else {
            for (let i = 0; i < matches.length; ++i) {
                if (matches[i].start > editor.selectionStart) {
                    index = i
                    break
                }
            }
            if (index < 0)
                index = 0
        }
        matchIndex = index
        editor.select(matches[index].start, matches[index].end)
        editor.forceActiveFocus()
    }

    function replaceCurrent() {
        if (!replaceVisible || !findField.text.length)
            return
        const matches = controller.search_matches(
            editor.text, findField.text, searchOptions())
        let target = null
        for (let i = 0; i < matches.length; ++i) {
            if (matches[i].start === editor.selectionStart
                    && matches[i].end === editor.selectionEnd) {
                target = matches[i]
                break
            }
        }
        if (!target) {
            findNext(false)
            return
        }
        editor.remove(target.start, target.end)
        editor.insert(target.start, replaceField.text)
        editor.cursorPosition = target.start + replaceField.text.length
        updateMatches(false)
        findNext(false)
    }

    function replaceAll() {
        const matches = controller.search_matches(
            editor.text, findField.text, searchOptions())
        if (!matches.length)
            return
        let value = editor.text
        for (let i = matches.length - 1; i >= 0; --i)
            value = value.slice(0, matches[i].start)
                + replaceField.text + value.slice(matches[i].end)
        applyingCommand = true
        editor.text = value
        applyingCommand = false
        recordHistory()
        root.textEdited()
        matchIndex = -1
        updateMatches(false)
        editor.forceActiveFocus()
    }

    function applyCommand(command) {
        const result = controller.apply_editor_command(
            command, editor.text, editor.selectionStart, editor.selectionEnd)
        applyingCommand = true
        editor.text = result.text
        applyingCommand = false
        editor.select(result.start, result.end)
        recordHistory()
        root.textEdited()
        editor.forceActiveFocus()
    }

    function replaceText(value) {
        applyingCommand = true
        editor.text = String(value || "")
        editor.cursorPosition = 0
        applyingCommand = false
        recordHistory()
        root.textEdited()
        editor.forceActiveFocus()
    }

    function currentHistory() {
        return histories[bufferKey || "__default__"] || null
    }

    function ensureHistory(value) {
        const key = bufferKey || "__default__"
        let state = histories[key]
        if (!state) {
            state = {
                "entries": [],
                "index": 0,
                "lastText": String(value || ""),
                "cursor": 0,
                "start": 0,
                "end": 0
            }
            histories[key] = state
            historyRevision++
        }
        return state
    }

    function loadBuffer(key, value) {
        bufferKey = String(key || "__default__")
        const state = ensureHistory(value)
        const requested = String(value || "")
        if (state.lastText !== requested) {
            state.entries = []
            state.index = 0
            state.lastText = requested
            state.cursor = 0
            state.start = 0
            state.end = 0
        }
        applyingCommand = true
        editor.text = state.lastText
        editor.select(
            Math.min(state.start, editor.length),
            Math.min(state.end, editor.length))
        editor.cursorPosition = Math.min(state.cursor, editor.length)
        applyingCommand = false
        historyRevision++
        Qt.callLater(root.revealCursor)
    }

    function revealCursor() {
        const flickable = editorScroll.contentItem
        if (!flickable)
            return
        flickable.contentX = Math.min(
            Math.max(0, flickable.contentWidth - flickable.width),
            Math.max(0, editor.cursorRectangle.x - editor.leftPadding)
        )
        flickable.contentY = Math.min(
            Math.max(0, flickable.contentHeight - flickable.height),
            Math.max(0, editor.cursorRectangle.y - editor.topPadding)
        )
    }

    function recordHistory() {
        const state = ensureHistory(editor.text)
        const before = String(state.lastText || "")
        const after = editor.text
        if (before === after) {
            state.cursor = editor.cursorPosition
            state.start = editor.selectionStart
            state.end = editor.selectionEnd
            historyRevision++
            return
        }
        let prefix = 0
        const shared = Math.min(before.length, after.length)
        while (prefix < shared && before[prefix] === after[prefix])
            prefix++
        let suffix = 0
        while (suffix < shared - prefix
                && before[before.length - 1 - suffix]
                    === after[after.length - 1 - suffix])
            suffix++
        state.entries = state.entries.slice(0, state.index)
        state.entries.push({
            "start": prefix,
            "removed": before.slice(prefix, before.length - suffix),
            "inserted": after.slice(prefix, after.length - suffix),
            "beforeCursor": state.cursor,
            "beforeStart": state.start,
            "beforeEnd": state.end,
            "afterCursor": editor.cursorPosition,
            "afterStart": editor.selectionStart,
            "afterEnd": editor.selectionEnd
        })
        if (state.entries.length > historyLimit)
            state.entries.splice(0, state.entries.length - historyLimit)
        state.index = state.entries.length
        state.lastText = after
        state.cursor = editor.cursorPosition
        state.start = editor.selectionStart
        state.end = editor.selectionEnd
        historyRevision++
    }

    function historyCanUndo() {
        const state = currentHistory()
        return !!state && state.index > 0
    }

    function historyCanRedo() {
        const state = currentHistory()
        return !!state && state.index < state.entries.length
    }

    function applyHistoryIndex(index) {
        const state = currentHistory()
        if (!state || index < 0 || index > state.entries.length)
            return
        let value = state.lastText
        while (state.index > index) {
            const entry = state.entries[state.index - 1]
            value = value.slice(0, entry.start) + entry.removed
                + value.slice(entry.start + entry.inserted.length)
            state.index--
            state.cursor = entry.beforeCursor
            state.start = entry.beforeStart
            state.end = entry.beforeEnd
        }
        while (state.index < index) {
            const entry = state.entries[state.index]
            value = value.slice(0, entry.start) + entry.inserted
                + value.slice(entry.start + entry.removed.length)
            state.index++
            state.cursor = entry.afterCursor
            state.start = entry.afterStart
            state.end = entry.afterEnd
        }
        state.lastText = value
        applyingCommand = true
        editor.text = value
        editor.select(
            Math.min(state.start, editor.length),
            Math.min(state.end, editor.length))
        editor.cursorPosition = Math.min(state.cursor, editor.length)
        applyingCommand = false
        historyRevision++
        root.textEdited()
        editor.forceActiveFocus()
    }

    function undoEdit() {
        const state = currentHistory()
        if (state && state.index > 0)
            applyHistoryIndex(state.index - 1)
    }

    function redoEdit() {
        const state = currentHistory()
        if (state && state.index < state.entries.length)
            applyHistoryIndex(state.index + 1)
    }

    function historyActions() {
        const state = currentHistory()
        if (!state)
            return []
        const actions = []
        for (let index = state.entries.length; index >= 0; --index) {
            const distance = state.index - index
            let title = qsTr("Current state")
            if (distance > 0)
                title = qsTr("%1 edits back").arg(distance)
            else if (distance < 0)
                title = qsTr("%1 edits forward").arg(-distance)
            actions.push({
                "title": title,
                "translate": false,
                "command": "history:" + String(index),
                "checked": index === state.index,
                "icon": index === state.index ? "check" : "history"
            })
        }
        return actions
    }

    function goToHistory(command) {
        const prefix = "history:"
        if (String(command).indexOf(prefix) === 0)
            applyHistoryIndex(Number(String(command).slice(prefix.length)))
    }

    function copySelection() {
        editor.copy()
        editor.forceActiveFocus()
    }

    function cutSelection() {
        editor.cut()
        editor.forceActiveFocus()
    }

    function pasteClipboard() {
        editor.paste()
        editor.forceActiveFocus()
    }

    function requestCompletions(manual) {
        completionItems = controller.code_completions(
            editor.text, editor.cursorPosition, manual)
        completionIndex = 0
        if (completionItems.length > 0) {
            if (!completionPopup.visible) {
                completionPopup.preparePositionAtItem(
                    editor,
                    editor.cursorRectangle.x + 4,
                    editor.cursorRectangle.y
                        + editor.cursorRectangle.height + 4)
                completionPopup.open()
            }
        } else {
            completionPopup.close()
        }
    }

    function acceptCompletion(suffix) {
        if (!completionPopup.visible || completionItems.length === 0)
            return false
        const item = completionItems[completionIndex]
        applyingCommand = true
        editor.remove(item.start, item.end)
        editor.insert(item.start, item.insertText)
        editor.cursorPosition = item.start + item.insertText.length
            + Number(item.cursorOffset || 0)
        suffix = String(suffix || "")
        if (suffix.length) {
            const suffixPosition = editor.cursorPosition
            editor.insert(suffixPosition, suffix)
            editor.cursorPosition = suffixPosition + suffix.length
        }
        applyingCommand = false
        recordHistory()
        root.textEdited()
        completionPopup.close()
        editor.forceActiveFocus()
        return true
    }

    function insertIndentSpaces() {
        const lineStart = editor.text.lastIndexOf(
            "\n", Math.max(0, editor.cursorPosition - 1)) + 1
        const column = editor.cursorPosition - lineStart
        const count = 4 - column % 4
        const position = editor.cursorPosition
        editor.insert(position, "    ".slice(0, count))
        editor.cursorPosition = position + count
    }

    function currentLine() {
        return editor.text.slice(0, editor.cursorPosition).split("\n").length
    }

    function goToLine(line) {
        const target = Math.max(1, Number(line || 1))
        let position = 0
        for (let current = 1; current < target; ++current) {
            position = editor.text.indexOf("\n", position)
            if (position < 0)
                return false
            position++
        }
        editor.select(position, position)
        editor.cursorPosition = position
        editor.forceActiveFocus()
        Qt.callLater(root.revealCursor)
        return true
    }

    function navigateSymbol(delta) {
        if (!symbols || symbols.length === 0)
            return false
        const line = currentLine()
        let target = null
        if (delta > 0) {
            for (let index = 0; index < symbols.length; ++index) {
                if (Number(symbols[index].line) > line) {
                    target = symbols[index]
                    break
                }
            }
            target = target || symbols[0]
        } else {
            for (let index = symbols.length - 1; index >= 0; --index) {
                if (Number(symbols[index].line) < line) {
                    target = symbols[index]
                    break
                }
            }
            target = target || symbols[symbols.length - 1]
        }
        return goToLine(target.line)
    }

    function goToDefinition() {
        let start = editor.cursorPosition
        let end = editor.cursorPosition
        const isName = function(character) {
            return /[A-Za-z0-9_]/.test(character)
        }
        while (start > 0 && isName(editor.text[start - 1]))
            start--
        while (end < editor.text.length && isName(editor.text[end]))
            end++
        const name = editor.text.slice(start, end)
        for (let index = 0; index < symbols.length; ++index) {
            if (String(symbols[index].name) === name)
                return goToLine(symbols[index].line)
        }
        return false
    }

    function forceActiveFocus() {
        editor.forceActiveFocus()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        ColumnLayout {
            id: searchColumn
            objectName: "scriptEditorSearchPanel"
            Layout.fillWidth: true
            visible: root.searchVisible
            spacing: 3

            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Controls.TextField {
                    id: findField
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Find")
                    Keys.onReturnPressed: event => {
                        root.findNext((event.modifiers & Qt.ShiftModifier) !== 0)
                        event.accepted = true
                    }
                    onTextChanged: {
                        root.matchIndex = -1
                        root.updateMatches(false)
                        root.refreshHighlights()
                    }
                }
                Label {
                    text: root.matchCount > 0
                        ? String(root.matchIndex + 1) + " / " + String(root.matchCount)
                        : qsTr("No matches")
                    color: root.matchCount > 0
                        ? root.theme.secondaryText : root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.caption
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "expand_less"
                    toolTip: qsTr("Previous match (Shift+F3)")
                    onClicked: root.findNext(true)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "expand_more"
                    toolTip: qsTr("Next match (F3)")
                    onClicked: root.findNext(false)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Close search")
                    onClicked: root.closeFind()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                visible: root.replaceVisible
                spacing: 4
                Controls.TextField {
                    id: replaceField
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Replace with")
                    Keys.onReturnPressed: event => {
                        root.replaceCurrent()
                        event.accepted = true
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Replace")
                    flat: true
                    onClicked: root.replaceCurrent()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Replace all")
                    flat: true
                    onClicked: root.replaceAll()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Controls.CheckBox {
                    id: matchCase
                    theme: root.theme
                    text: qsTr("Match case")
                    onToggled: {
                        root.updateMatches(false)
                        root.refreshHighlights()
                    }
                }
                Controls.CheckBox {
                    id: wholeWord
                    theme: root.theme
                    text: qsTr("Whole word")
                    onToggled: {
                        root.updateMatches(false)
                        root.refreshHighlights()
                    }
                }
                Controls.CheckBox {
                    id: regularExpression
                    theme: root.theme
                    text: qsTr("Regular expression")
                    onToggled: {
                        root.updateMatches(false)
                        root.refreshHighlights()
                    }
                }
                Item { Layout.fillWidth: true }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                id: lineNumberGutter
                objectName: "scriptEditorLineNumberGutter"
                Layout.preferredWidth: Math.max(
                    36,
                    fontMetrics.advanceWidth("0")
                        * String(root.lineNumberCount).length + 16
                )
                Layout.fillHeight: true
                color: root.theme.surfaceContainerLow
                clip: true

                Text {
                    objectName: "scriptEditorLineNumberText"
                    y: editor.topPadding - (editorScroll.contentItem
                        ? Number(editorScroll.contentItem.contentY || 0) : 0)
                    width: parent.width - 7
                    text: root.lineNumbers(root.lineNumberCount)
                    color: root.theme.secondaryText
                    font.family: editor.font.family
                    font.pointSize: editor.font.pointSize
                    lineHeight: editor.cursorRectangle.height
                    lineHeightMode: Text.FixedHeight
                    horizontalAlignment: Text.AlignRight
                }

            }

            ScrollView {
                id: editorScroll
                objectName: "scriptEditorSourceScrollView"
                readonly property real stableContentWidth:
                    Math.max(0, width - leftPadding - rightPadding)
                readonly property real stableContentHeight:
                    Math.max(0, height - topPadding - bottomPadding)
                Layout.fillWidth: true
                Layout.fillHeight: true
                rightPadding: 16
                bottomPadding: 16
                clip: true
                background: Rectangle {
                    color: root.theme.surfaceContainerHigh
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    objectName: "scriptEditorSourceVerticalScrollBar"
                    theme: root.theme
                    flickableTarget: editorScroll.contentItem
                }
                ScrollBar.horizontal: Controls.ScrollBar {
                    objectName: "scriptEditorSourceHorizontalScrollBar"
                    theme: root.theme
                    flickableTarget: editorScroll.contentItem
                }

                Controls.TextArea {
                    id: editor
                    objectName: "scriptEditorSourceText"
                    theme: root.theme
                    font.family: "Consolas"
                    font.pointSize: root.fontPointSize
                    wrapMode: TextEdit.NoWrap
                    tabStopDistance: fontMetrics.advanceWidth(" ") * 4
                    persistentSelection: true
                    width: Math.max(
                        editorScroll.stableContentWidth, implicitWidth)
                    height: Math.max(
                        editorScroll.stableContentHeight, implicitHeight)
                    background: Item {}
                    onTextChanged: {
                        if (!root.applyingCommand) {
                            root.recordHistory()
                            root.textEdited()
                        }
                        root.refreshHighlights()
                        completionDelay.restart()
                    }
                    onCursorPositionChanged: {
                        const state = root.currentHistory()
                        if (state && state.lastText === editor.text) {
                            state.cursor = editor.cursorPosition
                            state.start = editor.selectionStart
                            state.end = editor.selectionEnd
                        }
                    }
                    onSelectedTextChanged: {
                        const state = root.currentHistory()
                        if (state && state.lastText === editor.text) {
                            state.cursor = editor.cursorPosition
                            state.start = editor.selectionStart
                            state.end = editor.selectionEnd
                        }
                        root.refreshHighlights()
                    }
                    Keys.onPressed: event => {
                        const ctrl = (event.modifiers & Qt.ControlModifier) !== 0
                        const shift = (event.modifiers & Qt.ShiftModifier) !== 0
                        const alt = (event.modifiers & Qt.AltModifier) !== 0
                        const enter = event.key === Qt.Key_Return
                            || event.key === Qt.Key_Enter
                        if (ctrl && enter) {
                            completionPopup.close()
                            root.runRequested()
                            event.accepted = true
                            return
                        }
                        if (completionPopup.visible) {
                            if (event.key === Qt.Key_Down
                                    || event.key === Qt.Key_Up) {
                                const delta = event.key === Qt.Key_Down ? 1 : -1
                                root.completionIndex = (
                                    root.completionIndex + delta
                                    + root.completionItems.length
                                ) % root.completionItems.length
                                completionList.positionViewAtIndex(
                                    root.completionIndex, ListView.Contain)
                                event.accepted = true
                                return
                            }
                            if (!ctrl && enter) {
                                completionPopup.close()
                                event.accepted = false
                                return
                            }
                            if (event.key === Qt.Key_Tab) {
                                event.accepted = root.acceptCompletion("")
                                return
                            }
                            if (!ctrl && event.key === Qt.Key_Space) {
                                event.accepted = root.acceptCompletion(" ")
                                return
                            }
                            if (event.key === Qt.Key_Escape) {
                                completionPopup.close()
                                event.accepted = true
                                return
                            }
                        }
                        if (ctrl && shift && event.key === Qt.Key_O) {
                            root.outlineRequested()
                            event.accepted = true
                            return
                        } else if (alt && event.key === Qt.Key_Up) {
                            event.accepted = root.navigateSymbol(-1)
                        } else if (alt && event.key === Qt.Key_Down) {
                            event.accepted = root.navigateSymbol(1)
                        } else if (event.key === Qt.Key_F12) {
                            event.accepted = root.goToDefinition()
                        } else if (ctrl && shift && event.key === Qt.Key_K) {
                            root.applyCommand("delete_line")
                            event.accepted = true
                        } else if (ctrl && !shift && event.key === Qt.Key_Z) {
                            root.undoEdit()
                            event.accepted = true
                        } else if ((ctrl && event.key === Qt.Key_Y)
                                || (ctrl && shift && event.key === Qt.Key_Z)) {
                            root.redoEdit()
                            event.accepted = true
                        } else if (ctrl && event.key === Qt.Key_Space) {
                            root.requestCompletions(true)
                            event.accepted = true
                        } else if (ctrl && event.key === Qt.Key_F) {
                            root.showFind(false)
                            event.accepted = true
                        } else if (ctrl && event.key === Qt.Key_H) {
                            root.showFind(true)
                            event.accepted = true
                        } else if (event.key === Qt.Key_F3) {
                            root.findNext(shift)
                            event.accepted = true
                        } else if (ctrl && event.key === Qt.Key_Slash) {
                            root.applyCommand("toggle_comment")
                            event.accepted = true
                        } else if (ctrl && event.key === Qt.Key_D) {
                            root.applyCommand("duplicate")
                            event.accepted = true
                        } else if (event.key === Qt.Key_Backtab) {
                            root.applyCommand("unindent")
                            event.accepted = true
                        } else if (event.key === Qt.Key_Tab) {
                            if (editor.selectionStart !== editor.selectionEnd)
                                root.applyCommand("indent")
                            else
                                root.insertIndentSpaces()
                            event.accepted = true
                        }
                    }
                }
            }
        }
    }

    FontMetrics {
        id: fontMetrics
        font: editor.font
    }

    Timer {
        id: completionDelay
        interval: 140
        repeat: false
        onTriggered: {
            if (editor.activeFocus)
                root.requestCompletions(false)
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.searchVisible && !completionPopup.visible
        onActivated: root.closeFind()
    }

    Controls.Popup {
        id: completionPopup
        objectName: "scriptEditorCompletionPopup"
        theme: root.theme
        usePopupWindow: false
        width: Math.min(560, Math.max(340, root.width * 0.62))
        height: Math.min(270, Math.max(100, completionList.contentHeight + 12))
        padding: 5
        settledClosePolicy: Controls.Popup.CloseOnEscape
            | Controls.Popup.CloseOnPressOutside

        contentItem: ListView {
            id: completionList
            model: root.completionItems
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            currentIndex: root.completionIndex
            delegate: Controls.PopupAction {
                id: completionAction
                required property int index
                required property var modelData
                width: completionList.width
                height: modelData.detail ? 46 : 34
                hoverEnabled: true
                leftPadding: 10
                rightPadding: 10
                Accessible.name: String(modelData.label || "")
                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: index === root.completionIndex
                        ? root.theme.secondaryContainer
                        : completionAction.down
                            ? root.theme.surfaceContainerHighest
                            : completionAction.hovered
                                ? root.theme.rowHover : "transparent"
                }
                contentItem: RowLayout {
                    spacing: 8
                    Controls.MaterialIcon {
                        name: modelData.kind === "function"
                                || modelData.kind === "method" ? "code"
                            : modelData.kind === "class" ? "type"
                            : modelData.kind === "module" ? "api" : "description"
                        size: 14
                        color: root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: modelData.label
                            color: root.theme.primaryText
                            font.family: "Consolas"
                            font.pointSize: Typography.body
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: text.length > 0
                            text: modelData.detail || ""
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                    Rectangle {
                        Layout.preferredWidth: 62
                        Layout.preferredHeight: 20
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerHighest
                        Label {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            anchors.rightMargin: 4
                            text: String(modelData.kind || "value").toUpperCase()
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.caption
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }
                onHoveredChanged: {
                    if (hovered)
                        root.completionIndex = index
                }
                onClicked: {
                    root.completionIndex = index
                    root.acceptCompletion()
                }
            }
            Controls.ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: completionList
            }
        }
    }

    Component.onCompleted: {
        controller.attach_editor_document(editor.textDocument, syntaxColors())
        refreshHighlights()
    }
}
