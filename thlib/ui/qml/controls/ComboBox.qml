import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import QtQuick.Layouts
import QtQuick.Window
import "." as Controls

QtControls.ComboBox {
    id: control

    required property var theme
    property string colorRole: ""
    property bool actionField: false
    property bool showIndicator: !actionField
    property bool translateDisplayText: true
    property string leadingIcon: ""
    property string iconRole: ""
    property color leadingIconColor: theme.secondaryText
    property real maximumPopupWidth: 560
    property real popupHorizontalPadding: 34
    property bool activationPressed: false
    property bool _popupWasVisibleOnPress: false
    property bool _keyboardOpenRequested: false
    property bool _keyboardSessionActive: false
    property bool _restoreFocusAfterClose: false
    property double _openingTransactionUntil: 0
    property double _lastTouchActivationAt: -1000
    readonly property real popupDecorationWidth:
        popupHorizontalPadding
        + (iconRole.length > 0 || colorRole.length > 0 ? 24 : 0)
        + 2 * optionsPopup.effectiveShadowMargin
    readonly property real widestOptionTextWidth: {
        const optionCount = control.count
        let widest = 0
        for (let index = 0; index < optionCount; ++index) {
            const value = control.textAt(index)
            const label = control.translateDisplayText
                ? qsTr(value) : value
            widest = Math.max(
                widest, optionFontMetrics.advanceWidth(String(label || "")))
        }
        return widest
    }
    readonly property real preferredPopupWidth: Math.max(
        control.width,
        Math.ceil(widestOptionTextWidth + popupDecorationWidth)
    )

    FontMetrics {
        id: optionFontMetrics
        font: control.font
    }

    function optionValue(index, roleName) {
        if (!roleName || index < 0 || !control.model)
            return ""
        if (control.model.get)
            return control.model.get(index)[roleName] || ""
        const value = control.model[index]
        return value && value[roleName] !== undefined
            ? value[roleName] : ""
    }

    function beginOpeningTransaction(duration) {
        _openingTransactionUntil = Date.now() + duration
    }

    function recoverInterruptedOpening() {
        if (Date.now() >= _openingTransactionUntil)
            return false
        _openingTransactionUntil = 0
        Qt.callLater(function() {
            Qt.callLater(function() {
                if (control.visible && control.enabled
                        && !control.popup.opened)
                    control.popup.open()
            })
        })
        return true
    }

    function cancelOpeningTransaction() {
        _openingTransactionUntil = 0
    }

    function togglePopupFromPointer(touchInput, sourceWasOpen) {
        const now = Date.now()
        const touchDuplicateWindow =
            theme.baseMotionExtended + theme.baseMotionFast
        if (!touchInput
                && now - _lastTouchActivationAt < touchDuplicateWindow) {
            // Popup.Window receives a delayed synthetic mouse press as an
            // outside click before the owner MouseArea can reject it. Restore
            // the touch-opened popup after that event has fully unwound.
            if (!popup.opened && !popup.visible) {
                beginOpeningTransaction(touchDuplicateWindow)
                popup.openingInputGuardDuration = touchDuplicateWindow
                popup.protectNextOpenFromDuplicateInput = true
                Qt.callLater(function() {
                    Qt.callLater(function() {
                        if (control.visible && control.enabled
                                && !control.popup.opened)
                            control.popup.open()
                    })
                })
            }
            return
        }
        if (touchInput)
            _lastTouchActivationAt = now
        if (sourceWasOpen || popup.opened || popup.visible) {
            cancelOpeningTransaction()
            if (popup.opened || popup.visible)
                popup.close()
            return
        }
        if (Controls.PopupCoordinator.wasJustClosed(
                popup, theme.baseMotionFast)) {
            cancelOpeningTransaction()
            return
        }
        const duration = touchInput
            ? theme.baseMotionExtended + theme.baseMotionFast
            : theme.baseMotionFast
        popup.openingInputGuardDuration = duration
        if (!touchInput) {
            // Let Qt finish the ComboBox click before creating its native
            // popup window. One queued turn is enough; the former second turn
            // made the first click look like focus-only on Windows.
            beginOpeningTransaction(duration)
            popup.protectNextOpenFromDuplicateInput = true
            Qt.callLater(function() {
                if (control.visible && control.enabled
                        && !control.popup.opened)
                    control.popup.open()
            })
            return
        }

        beginOpeningTransaction(duration)
        popup.protectNextOpenFromDuplicateInput = true
        // Touchscreens can send a delayed synthetic mouse event after the
        // authentic touch. Let that dispatch unwind before creating the
        // native popup window; the duplicate-input branch above restores it
        // if the platform still closes it.
        Qt.callLater(function() {
            Qt.callLater(function() {
                if (control.visible && control.enabled
                        && !control.popup.opened)
                    control.popup.open()
            })
        })
    }

    function movePopupHighlight(step) {
        if (control.count <= 0)
            return
        const current = optionsList.currentIndex >= 0
            ? optionsList.currentIndex
            : Math.max(0, control.currentIndex)
        optionsList.currentIndex = (
            current + step + control.count
        ) % control.count
        optionsList.positionViewAtIndex(
            optionsList.currentIndex, ListView.Contain)
    }

    function activatePopupHighlight() {
        const index = optionsList.currentIndex
        if (index < 0 || index >= control.count)
            return
        control.cancelOpeningTransaction()
        control.currentIndex = index
        control.activated(index)
        control._restoreFocusAfterClose = true
        control.popup.close()
    }

    function restoreKeyboardFocusAfterClose() {
        if (!control._restoreFocusAfterClose)
            return
        control._restoreFocusAfterClose = false
        Qt.callLater(function() {
            if (control.visible && control.enabled) {
                const ownerWindow = control.Window.window
                if (ownerWindow)
                    ownerWindow.requestActivate()
                control.forceActiveFocus(Qt.PopupFocusReason)
            }
        })
    }

    function handlePopupClosed() {
        const recovering = control.recoverInterruptedOpening()
        if (control._keyboardSessionActive && !recovering) {
            control._keyboardSessionActive = false
            control._restoreFocusAfterClose = true
        }
        control.restoreKeyboardFocusAfterClose()
    }

    function openPopupFromKeyboard() {
        if (control.count <= 0 || control.popup.visible)
            return
        control.beginOpeningTransaction(
            control.theme.baseMotionExtended
                + control.theme.baseMotionFast)
        control.popup.protectNextOpenFromDuplicateInput = false
        control._keyboardSessionActive = true
        control.popup.open()
    }

    implicitWidth: 140
    implicitHeight: theme.compactControlHeight
    leftPadding: 11
    rightPadding: showIndicator ? 32 : 12
    topPadding: 0
    bottomPadding: 0
    font.family: theme.fontFamily
    font.pointSize: Typography.body

    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (!control.popup.visible) {
            if (event.key === Qt.Key_Down || event.key === Qt.Key_Up) {
                if (!control.editable && control.count > 0) {
                    const step = event.key === Qt.Key_Down ? 1 : -1
                    const nextIndex = (
                        Math.max(0, control.currentIndex)
                        + step + control.count
                    ) % control.count
                    control.currentIndex = nextIndex
                    control.activated(nextIndex)
                    event.accepted = true
                }
                return
            }
            if (!control.editable
                    && (event.key === Qt.Key_Return
                        || event.key === Qt.Key_Enter
                        || event.key === Qt.Key_Space)) {
                // Open only after this key's release has left Qt's ComboBox
                // delivery path; opening during press makes the same physical
                // key immediately activate the highlighted popup row.
                control._keyboardOpenRequested = true
                event.accepted = true
            }
            return
        }
        if (event.key === Qt.Key_Escape && control.popup.visible) {
            control.cancelOpeningTransaction()
            control.popup.close()
            event.accepted = true
            return
        }
        if (event.key === Qt.Key_Down || event.key === Qt.Key_Up) {
            control.movePopupHighlight(
                event.key === Qt.Key_Down ? 1 : -1)
            event.accepted = true
            return
        }
        if (event.key !== Qt.Key_Return
                && event.key !== Qt.Key_Enter
                && event.key !== Qt.Key_Space)
            return
        control.activatePopupHighlight()
        event.accepted = true
    }
    Keys.onReleased: event => {
        if (!control.popup.visible && control._keyboardOpenRequested
                && (event.key === Qt.Key_Return
                    || event.key === Qt.Key_Enter
                    || event.key === Qt.Key_Space)) {
            control._keyboardOpenRequested = false
            control.openPopupFromKeyboard()
            event.accepted = true
            return
        }
        if (control.popup.visible && (
                event.key === Qt.Key_Escape
                || event.key === Qt.Key_Down
                || event.key === Qt.Key_Up
                || event.key === Qt.Key_Return
                || event.key === Qt.Key_Enter
                || event.key === Qt.Key_Space))
            event.accepted = true
    }

    contentItem: RowLayout {
        spacing: 7
        Controls.MaterialIcon {
            visible: control.leadingIcon.length > 0
                || (!!control.iconRole
                    && !!control.optionValue(control.currentIndex, control.iconRole))
            name: control.leadingIcon.length > 0
                ? control.leadingIcon
                : control.optionValue(control.currentIndex, control.iconRole)
            size: control.actionField ? 17 : 15
            color: control.enabled
                ? control.leadingIconColor : control.theme.disabledText
        }
        Rectangle {
            visible: !!control.colorRole
                && control.leadingIcon.length === 0
                && (!control.iconRole
                    || !control.optionValue(control.currentIndex, control.iconRole))
                && !!control.optionValue(control.currentIndex, control.colorRole)
            Layout.preferredWidth: 9
            Layout.preferredHeight: 9
            radius: 4.5
            color: control.optionValue(control.currentIndex, control.colorRole)
        }
        Label {
            objectName: "comboBoxDisplayLabel"
            Layout.fillWidth: true
            text: control.translateDisplayText
                ? qsTr(control.displayText) : control.displayText
            color: control.enabled
                ? control.theme.primaryText : control.theme.disabledText
            font: control.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    indicator: Controls.MaterialIcon {
        visible: control.showIndicator
        x: control.width - width - 9
        y: (control.height - height) / 2
        name: control.popup.opened ? "expand_less" : "expand_more"
        size: 17
        color: control.enabled
            ? control.theme.secondaryText : control.theme.disabledText
    }

    background: Rectangle {
        radius: control.actionField
            ? Math.min(height / 2, control.theme.itemRadius)
            : control.theme.fieldRadius
        color: control.actionField
            ? !control.enabled
                ? control.theme.surfaceContainerLow
                : control.down || control.activationPressed
                    ? control.theme.surfaceContainer
                    : control.hovered
                        ? control.theme.surfaceContainerHigh
                        : control.theme.surfaceContainerLow
            : !control.enabled
                ? control.theme.surfaceContainerLow
            : control.theme.surfaceContainerLow
        border.width: control.actionField
            ? 0 : control.activeFocus ? 2 : 1
        border.color: control.activeFocus
            ? control.theme.action : control.theme.outlineVariant

        Behavior on color {
            ColorAnimation {
                duration: control.down || control.activationPressed
                    ? control.theme.clickMotionFast
                    : control.theme.hoverMotionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    HoverHandler {
        objectName: "comboBoxCursorHandler"
        cursorShape: control.enabled && control.editable
            ? Qt.IBeamCursor : Qt.PointingHandCursor
    }

    MouseArea {
        id: pointerActivation
        x: control.editable ? control.width - width : 0
        y: 0
        width: control.editable
            ? (control.showIndicator ? 40 : 0) : control.width
        height: control.height
        z: 10
        enabled: control.enabled
            && (!control.editable || control.showIndicator)
        acceptedButtons: Qt.LeftButton
        cursorShape: Qt.PointingHandCursor
        onPressed: {
            control.activationPressed = true
            control._popupWasVisibleOnPress =
                control.popup.opened || control.popup.visible
            control.forceActiveFocus(Qt.MouseFocusReason)
        }
        onCanceled: {
            control.activationPressed = false
            control._popupWasVisibleOnPress = false
        }
        onReleased: {
            control.activationPressed = false
        }
        onClicked: function(mouse) {
            control.togglePopupFromPointer(
                mouse.source !== Qt.MouseEventNotSynthesized,
                control._popupWasVisibleOnPress)
            control._popupWasVisibleOnPress = false
        }
    }

    delegate: ItemDelegate {
        id: option

        required property int index

        width: Math.max(0, optionsList.width - optionsScrollBar.reservedExtent - 4)
        height: 34
        leftPadding: 12
        rightPadding: 10
        highlighted: optionsList.currentIndex === index
        hoverEnabled: true
        onHoveredChanged: {
            if (hovered)
                optionsList.currentIndex = index
        }
        onClicked: control.cancelOpeningTransaction()

        contentItem: RowLayout {
            spacing: 8
            Controls.MaterialIcon {
                visible: !!control.iconRole
                    && !!control.optionValue(option.index, control.iconRole)
                name: control.optionValue(option.index, control.iconRole)
                size: 16
                color: option.highlighted
                    ? control.theme.action : control.theme.secondaryText
            }
            Rectangle {
                visible: !!control.colorRole
                    && (!control.iconRole
                        || !control.optionValue(option.index, control.iconRole))
                    && !!control.optionValue(option.index, control.colorRole)
                Layout.preferredWidth: 9
                Layout.preferredHeight: 9
                radius: 4.5
                color: control.optionValue(option.index, control.colorRole)
            }
            Label {
                Layout.fillWidth: true
                text: control.translateDisplayText
                    ? qsTr(control.textAt(option.index))
                    : control.textAt(option.index)
                color: control.theme.primaryText
                font: control.font
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }
        background: Rectangle {
            radius: control.theme.itemRadius
            color: option.highlighted
                ? control.theme.secondaryContainer : "transparent"
        }
    }

    popup: Controls.Popup {
        id: optionsPopup
        objectName: "comboBoxPopup"

        theme: control.theme
        usePopupWindow: true
        coordinateGlobally: true
        coordinateOpenPopups: true
        openingAnchorItem: control
        restoreOwnerActivationOnClose: false
        function cancelOpeningRecovery() {
            control.cancelOpeningTransaction()
        }
        settledClosePolicy: QtControls.Popup.CloseOnEscape
            | QtControls.Popup.CloseOnPressOutside
        y: control.height + 4
        width: Math.min(
            control.preferredPopupWidth,
            control.maximumPopupWidth,
            optionsPopup.maximumAvailableWidth
        )
        padding: 4
        implicitHeight: Math.min(
            control.count * 34
                + optionsPopup.topPadding + optionsPopup.bottomPadding,
            8 * 34 + optionsPopup.topPadding + optionsPopup.bottomPadding,
            optionsPopup.maximumAvailableHeight
        )
        height: implicitHeight
        onAboutToShow: {
            optionsPopup.preparePositionAtItem(
                control, 0, control.height + 4)
        }
        onOpened: {
            optionsList.currentIndex = control.currentIndex >= 0
                ? control.currentIndex : (control.count > 0 ? 0 : -1)
        }
        onClosed: {
            control.handlePopupClosed()
        }
        Shortcut {
            sequence: "Down"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: control.movePopupHighlight(1)
        }
        Shortcut {
            sequence: "Up"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: control.movePopupHighlight(-1)
        }
        Shortcut {
            sequence: "Space"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Return"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Enter"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: control.activatePopupHighlight()
        }
        Shortcut {
            sequence: "Esc"
            context: Qt.WindowShortcut
            enabled: optionsPopup.visible
            onActivated: {
                control.cancelOpeningTransaction()
                control._restoreFocusAfterClose = true
                optionsPopup.close()
            }
        }
        contentItem: ListView {
            id: optionsList
            objectName: "comboBoxPopupList"
            implicitHeight: contentHeight
            clip: true
            currentIndex: control.highlightedIndex
            model: control.delegateModel
            keyNavigationWraps: true
            boundsBehavior: Flickable.StopAtBounds
            Keys.priority: Keys.BeforeItem
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Escape) {
                    control.cancelOpeningTransaction()
                    control._restoreFocusAfterClose = true
                    optionsPopup.close()
                    event.accepted = true
                    return
                }
                if (event.key === Qt.Key_Down || event.key === Qt.Key_Up) {
                    control.movePopupHighlight(
                        event.key === Qt.Key_Down ? 1 : -1)
                    event.accepted = true
                    return
                }
                if (event.key === Qt.Key_Return
                        || event.key === Qt.Key_Enter
                        || event.key === Qt.Key_Space) {
                    control.activatePopupHighlight()
                    event.accepted = true
                }
            }
            Controls.ScrollBar.vertical: Controls.ScrollBar {
                id: optionsScrollBar
                theme: control.theme
                flickableTarget: parent
            }
        }

    }
}
