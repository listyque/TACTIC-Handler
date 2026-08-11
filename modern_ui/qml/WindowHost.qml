import QtQuick
import QtQuick.Window
import QtQml.Models

Item {
    id: root
    required property var theme
    property var ownerWindow: Window.window
    property bool workspaceEnabled: true

    // Window is a QQuickWindow rather than a QQuickItem, so Instantiator is
    // used instead of Repeater. Python still owns lifecycle and persistence.
    Instantiator {
        model: windowModel
        delegate: FloatingWindow {
            ownerWindow: root.ownerWindow
            theme: root.theme
            workspaceEnabled: root.workspaceEnabled
        }
    }
}
