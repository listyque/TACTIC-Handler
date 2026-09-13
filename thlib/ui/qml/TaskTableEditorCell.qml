import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    objectName: "taskTableEditorCell"

    required property var theme
    required property var releaseCoordinator
    property Component editorComponent
    property bool editorActive: false
    property bool editingAllowed: true
    property bool scrolling: false
    property bool actionField: true
    property bool showIndicator: !actionField
    property bool showAccent: false
    property color accentColor: theme.action
    property bool showAvatar: false
    property var userModel: null
    property string avatarLogin: ""
    property string avatarSource: ""
    property string avatarInitials: ""
    property string displayText: ""
    property real textPointSize: Controls.Typography.body
    property bool editRequested: false
    property bool editorPopupOpen: false
    property bool editorResident: false
    property bool editorPressPending: false

    readonly property bool editorLoaded: editorLoader.active

    implicitWidth: 120
    implicitHeight: 29

    function cancelEditorRelease() {
        releaseCoordinator.cancel(root)
    }

    function scheduleEditorRelease() {
        releaseCoordinator.schedule(root)
    }

    function releaseEditorIfIdle() {
        const editor = editorLoader.item
        const popup = editor && editor.popup ? editor.popup : null
        if (!popup || (!popup.visible && !popup.opened)) {
            root.editRequested = false
            root.editorResident = false
        }
    }

    function handleEditorPressState(pressed) {
        if (pressed) {
            // Keep the lazy editor alive from pointer press until its native
            // popup owns the interaction. Otherwise a fast pointer move can
            // remove row hover before the deferred ComboBox open runs.
            cancelEditorRelease()
            editorPressPending = true
            editRequested = true
        } else if (editorPressPending) {
            editorPressPending = false
            if (!editorPopupOpen)
                scheduleEditorRelease()
        }
    }

    onEditorActiveChanged: {
        if (editorActive) {
            editorResident = true
            cancelEditorRelease()
        } else if (editorLoader.active && editingAllowed && !scrolling) {
            // First layout can move rows under a stationary pointer. Keep an
            // already-created hover editor resident briefly, but never turn
            // that geometry-only hover change into a popup-open request.
            scheduleEditorRelease()
        }
    }
    onScrollingChanged: {
        if (scrolling) {
            cancelEditorRelease()
            editRequested = false
            editorPopupOpen = false
            editorResident = false
            editorPressPending = false
        }
    }
    onEditingAllowedChanged: {
        if (!editingAllowed) {
            cancelEditorRelease()
            editRequested = false
            editorPopupOpen = false
            editorResident = false
            editorPressPending = false
        }
    }

    Component.onDestruction: cancelEditorRelease()

    Rectangle {
        anchors.fill: parent
        visible: !editorLoader.active
        radius: root.actionField
            ? Math.min(height / 2, root.theme.itemRadius)
            : root.theme.fieldRadius
        color: !root.editingAllowed
            ? root.theme.surfaceContainerLow
            : cellHover.hovered
                ? root.theme.surfaceContainerHigh
                : root.theme.surfaceContainerLow
        border.width: root.actionField ? 0 : 1
        border.color: root.theme.outlineVariant

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 11
            anchors.rightMargin: root.showIndicator ? 9 : 12
            spacing: 7

            Loader {
                active: root.showAvatar
                visible: active
                Layout.preferredWidth: active ? 22 : 0
                Layout.preferredHeight: active ? 22 : 0
                sourceComponent: UserAvatar {
                    theme: root.theme
                    userModel: root.userModel
                    login: root.avatarLogin
                    effectsEnabled: !root.scrolling
                    avatarUrl: root.avatarSource
                    initials: root.avatarInitials
                    previewSize: 22
                }
            }
            Loader {
                active: root.showAccent && String(root.accentColor).length > 0
                visible: active
                Layout.preferredWidth: active ? 9 : 0
                Layout.preferredHeight: active ? 9 : 0
                sourceComponent: Rectangle {
                    width: 9
                    height: 9
                    radius: 4.5
                    color: root.accentColor
                }
            }
            Label {
                objectName: "taskTableCellDisplayLabel"
                Layout.fillWidth: true
                text: root.displayText
                color: root.editingAllowed
                    ? root.theme.primaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.pointSize: root.textPointSize
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            Loader {
                active: root.showIndicator
                visible: active
                Layout.preferredWidth: active ? 17 : 0
                Layout.preferredHeight: active ? 17 : 0
                sourceComponent: Controls.MaterialIcon {
                    name: "expand_more"
                    size: 17
                    color: root.editingAllowed
                        ? root.theme.secondaryText : root.theme.disabledText
                }
            }
        }

        HoverHandler {
            id: cellHover
            cursorShape: root.editingAllowed
                ? Qt.PointingHandCursor : Qt.ArrowCursor
        }
        Controls.ActivationHandler {
            anchors.fill: parent
            enabled: root.editingAllowed && !root.scrolling
            cursorShape: Qt.PointingHandCursor
            onActivated: root.editRequested = true
        }
    }

    Loader {
        id: editorLoader
        anchors.fill: parent
        active: root.editingAllowed
            && !root.scrolling
            && (root.editorResident || root.editRequested
                || root.editorPopupOpen)
        sourceComponent: root.editorComponent
        onLoaded: {
            if (!root.editRequested || !item || !item.popup)
                return
            Qt.callLater(function() {
                if (editorLoader.item && editorLoader.item.popup)
                    editorLoader.item.popup.open()
            })
        }
    }

    Connections {
        target: editorLoader.item
        ignoreUnknownSignals: true

        function onDownChanged() {
            const editor = editorLoader.item
            if (!editor || editor.activationPressed !== undefined)
                return
            root.handleEditorPressState(editor.down)
        }

        function onActivationPressedChanged() {
            const editor = editorLoader.item
            if (!editor)
                return
            root.handleEditorPressState(editor.activationPressed)
        }
    }

    Connections {
        target: editorLoader.item && editorLoader.item.popup
            ? editorLoader.item.popup : null
        function onAboutToShow() {
            root.cancelEditorRelease()
            root.editorPopupOpen = true
        }
        function onOpened() {
            root.cancelEditorRelease()
            root.editorPopupOpen = true
        }
        function onClosed() {
            root.cancelEditorRelease()
            root.editorPopupOpen = false
            root.editRequested = false
            root.editorPressPending = false
            // A native popup can close while Qt transfers focus to its window.
            // Keep its editor alive for ComboBox's queued opening recovery.
            root.editorResident = root.editingAllowed && !root.scrolling
            if (root.editorResident && !root.editorActive)
                root.scheduleEditorRelease()
        }
    }
}
