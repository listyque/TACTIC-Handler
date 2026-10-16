import QtQuick

Item {
    id: root

    required property var theme
    required property string identity
    property bool expanded: false
    property bool hasChildren: false
    property bool loading: false
    property real iconSize: 15
    property real indicatorSize: 22
    property bool loadingRequested: false
    readonly property bool showLoading: loading && loadingRequested
    signal activated(int modifiers)
    property int pendingActivationKey: 0
    activeFocusOnTab: enabled && hasChildren && !loading
    Accessible.role: Accessible.Button
    Accessible.name: expanded ? qsTr("Collapse item") : qsTr("Expand item")
    Accessible.onPressAction: activate(Qt.NoModifier)
    onActiveFocusChanged: if (!activeFocus)
        pendingActivationKey = 0
    onEnabledChanged: if (!enabled)
        pendingActivationKey = 0
    function activate(modifiers) {
        if (!enabled || !hasChildren || loading)
            return;
        loadingRequested = true;
        activated(modifiers);
        Qt.callLater(function () {
            if (!root.loading)
                root.loadingRequested = false;
        });
    }
    Keys.onPressed: event => {
        if (![Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter].includes(event.key))
            return;
        event.accepted = true;
        if (!event.isAutoRepeat)
            pendingActivationKey = event.key;
    }
    Keys.onReleased: event => {
        if (event.key !== pendingActivationKey)
            return;
        event.accepted = true;
        if (event.isAutoRepeat)
            return;
        pendingActivationKey = 0;
        activate(event.modifiers);
    }

    onIdentityChanged: loadingRequested = false
    onLoadingChanged: {
        if (!loading)
            loadingRequested = false;
    }

    MaterialIcon {
        objectName: "workspaceDisclosureIcon"
        anchors.centerIn: parent
        name: "chevron_right"
        size: root.iconSize
        color: root.theme.secondaryText
        visible: root.hasChildren && !root.showLoading
        opacity: root.showLoading ? 0 : 1
        rotation: root.expanded ? 90 : 0

        Behavior on opacity {
            NumberAnimation {
                duration: root.theme.motionFast
            }
        }
        Behavior on rotation {
            NumberAnimation {
                duration: root.theme.clickMotionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    Loader {
        anchors.centerIn: parent
        width: root.indicatorSize
        height: width
        active: root.showLoading
        sourceComponent: Item {
            objectName: "workspaceDisclosureSpinner"
            anchors.fill: parent
            BusyIndicator {
                uiTheme: root.theme
                anchors.fill: parent
                running: true
            }
        }
    }

    MouseArea {
        id: pointer
        anchors.fill: parent
        enabled: root.hasChildren
        hoverEnabled: true
        cursorShape: root.showLoading ? Qt.BusyCursor : Qt.PointingHandCursor
        onClicked: mouse => {
            root.forceActiveFocus(Qt.MouseFocusReason);
            root.activate(mouse.modifiers);
        }
    }
    ToolTip {
        theme: root.theme
        visible: pointer.containsMouse && !root.theme.suppressToolTips
        text: root.Accessible.name
    }
}
