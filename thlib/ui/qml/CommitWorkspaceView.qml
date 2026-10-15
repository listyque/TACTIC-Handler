import QtQuick

Loader {
    id: root
    required property var theme
    sourceComponent: fileWorkspaceController.enabled ? files : classic
    Component { id: files; FileWorkspaceView { theme: root.theme; controller: fileWorkspaceController } }
    Component { id: classic; CommitQueueView { theme: root.theme } }
}
