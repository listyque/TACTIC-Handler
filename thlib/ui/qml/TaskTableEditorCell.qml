import QtQuick
import "controls" as Controls
import "features/tasks" as Tasks

Tasks.TaskCellDisplay {
    id: root
    objectName: "taskTableEditorCell"

    required property var releaseCoordinator
    property Component editorComponent
    property bool editorActive: false
    property bool editingAllowed: true
    actionField: true
    property bool cardField: false
    property bool showIndicator: !actionField
    property bool showAccent: false
    property color accentColor: theme.action
    property bool showAvatar: false
    property string avatarLogin: ""
    property string displayText: ""
    property real textPointSize: Controls.Typography.body
    property bool editRequested: false
    property bool editorPopupOpen: false
    property bool editorResident: false
    property bool editorPressPending: false
    property string editorIdentity: ""
    readonly property real avatarSize: Math.max(0, Math.min(22, height - 4))

    readonly property bool editorLoaded: editorLoader.active

    implicitWidth: 120
    implicitHeight: 29

    function cancelEditorRelease() {
        releaseCoordinator.cancel(root);
    }

    function scheduleEditorRelease() {
        releaseCoordinator.schedule(root);
    }

    function resetEditor() {
        if (!editorLoader.active && !editRequested && !editorPopupOpen && !editorResident && !editorPressPending)
            return;
        const editor = editorLoader.item;
        if (editor && editor.popup)
            editor.popup.close();
        cancelEditorRelease();
        editRequested = false;
        editorPopupOpen = false;
        editorResident = false;
        editorPressPending = false;
    }

    function releaseEditorIfIdle() {
        const editor = editorLoader.item;
        const popup = editor && editor.popup ? editor.popup : null;
        if (!popup || (!popup.visible && !popup.opened)) {
            root.editRequested = false;
            root.editorResident = false;
        }
    }

    function handleEditorPressState(pressed) {
        if (pressed) {
            // Keep the lazy editor alive from pointer press until its native
            // popup owns the interaction. Otherwise a fast pointer move can
            // remove row hover before the deferred ComboBox open runs.
            cancelEditorRelease();
            editorPressPending = true;
            editRequested = true;
        } else if (editorPressPending) {
            editorPressPending = false;
            if (!editorPopupOpen)
                scheduleEditorRelease();
        }
    }

    onEditorActiveChanged: {
        if (editorActive) {
            editorResident = true;
            cancelEditorRelease();
        } else if (editorLoader.active && editingAllowed && !scrolling) {
            // First layout can move rows under a stationary pointer. Keep an
            // already-created hover editor resident briefly, but never turn
            // that geometry-only hover change into a popup-open request.
            scheduleEditorRelease();
        }
    }
    onScrollingChanged: {
        if (scrolling)
            resetEditor();
    }
    onEditingAllowedChanged: {
        if (!editingAllowed)
            resetEditor();
    }
    onEditorIdentityChanged: resetEditor()

    Component.onDestruction: cancelEditorRelease()

    displayActive: !editorLoader.active
    model: ({
            text: root.showAvatar && !root.avatarLogin && ["Not assigned", "No supervisor"].includes(root.displayText) ? qsTr(root.displayText) : root.displayText,
            enabled: root.editingAllowed,
            hovered: root.editorActive || cellHover.hovered,
            actionField: root.actionField,
            cardField: root.cardField,
            indicator: root.showIndicator,
            showAccent: root.showAccent,
            accent: String(root.accentColor),
            avatar: root.showAvatar,
            fontRole: root.textPointSize <= Controls.Typography.caption ? "caption" : "body"
        })
    login: root.avatarLogin
    HoverHandler {
        id: cellHover
        enabled: root.displayActive
        cursorShape: root.editingAllowed ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    Controls.ActivationHandler {
        enabled: root.displayActive && root.editingAllowed && !root.scrolling
        cursorShape: Qt.PointingHandCursor
        onActivated: root.editRequested = true
    }

    Loader {
        id: editorLoader
        anchors.fill: parent
        active: root.editingAllowed && !root.scrolling && (root.editorResident || root.editRequested || root.editorPopupOpen)
        sourceComponent: root.editorComponent
        onLoaded: {
            if (!root.editRequested || !item || !item.popup)
                return;
            Qt.callLater(function () {
                if (editorLoader.item && editorLoader.item.popup)
                    editorLoader.item.popup.open();
            });
        }
    }

    Connections {
        enabled: editorLoader.active
        target: editorLoader.item
        ignoreUnknownSignals: true

        function onDownChanged() {
            const editor = editorLoader.item;
            if (!editor || editor.activationPressed !== undefined)
                return;
            root.handleEditorPressState(editor.down);
        }

        function onActivationPressedChanged() {
            const editor = editorLoader.item;
            if (!editor)
                return;
            root.handleEditorPressState(editor.activationPressed);
        }
    }

    Connections {
        enabled: editorLoader.active
        target: editorLoader.item && editorLoader.item.popup ? editorLoader.item.popup : null
        function onAboutToShow() {
            root.cancelEditorRelease();
            root.editorPopupOpen = true;
        }
        function onOpened() {
            root.cancelEditorRelease();
            root.editorPopupOpen = true;
        }
        function onClosed() {
            root.cancelEditorRelease();
            root.editorPopupOpen = false;
            root.editRequested = false;
            root.editorPressPending = false;
            // A native popup can close while Qt transfers focus to its window.
            // Keep its editor alive for ComboBox's queued opening recovery.
            root.editorResident = root.editingAllowed && !root.scrolling;
            if (root.editorResident && !root.editorActive)
                root.scheduleEditorRelease();
        }
    }
}
