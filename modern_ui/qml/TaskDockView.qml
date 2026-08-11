import QtQuick

Item {
    id: root

    required property var theme

    Loader {
        anchors.fill: parent
        sourceComponent: tasksController.workspaceSurface === "browser"
            ? browserComponent : quickComponent
    }

    Component {
        id: quickComponent
        TaskProcessPanel { theme: root.theme }
    }

    Component {
        id: browserComponent
        TasksWorkspaceView {
            theme: root.theme
            embedded: true
        }
    }

}
