import QtQuick

Item {
    id: root

    required property var theme
    readonly property bool presentationActive:
        parent ? parent.visible : visible

    Loader {
        id: surfaceLoader
        objectName: "taskDockSurfaceLoader"
        anchors.fill: parent
        asynchronous: true
        sourceComponent: tasksController.workspaceSurface === "browser"
            ? browserComponent : quickComponent
    }

    Component {
        id: quickComponent
        TaskProcessPanel {
            theme: root.theme
            presentationActive: root.presentationActive
        }
    }

    Component {
        id: browserComponent
        TasksWorkspaceView {
            objectName: "tasksWorkspaceView"
            theme: root.theme
            embedded: true
            presentationActive: root.presentationActive
        }
    }

}
