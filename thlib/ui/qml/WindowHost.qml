import QtQuick
import QtQuick.Window
import QtQml.Models

Item {
    id: root
    required property var theme
    property var ownerWindow: Window.window
    property bool workspaceEnabled: true
    property int windowGeneration: 0

    function ownerFor(parentId) {
        const generation = root.windowGeneration
        if (parentId) {
            for (let i = 0; i < windows.count; ++i) {
                const candidate = windows.objectAt(i)
                if (candidate && candidate.windowId === parentId && candidate.visible)
                    return candidate
            }
        }
        return root.ownerWindow
    }

    // The proxy retains the four primary workspaces after first use. Other
    // closed tools release their native windows and content.
    Instantiator {
        id: windows
        model: visibleWindowModel
        onObjectAdded: root.windowGeneration += 1
        onObjectRemoved: root.windowGeneration += 1
        delegate: FloatingWindow {
            required property string parentWindowId
            ownerWindow: root.ownerFor(parentWindowId)
            theme: root.theme
            workspaceEnabled: root.workspaceEnabled
        }
    }
}
