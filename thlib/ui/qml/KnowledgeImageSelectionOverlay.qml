import QtQuick

Rectangle {
    id: root
    objectName: "knowledgeSelectedImageFrame"

    required property var theme
    required property var editor
    required property var documentController
    required property real maximumWidth
    property bool active: true
    property bool moving: false
    property int dropPosition: -1
    signal contentChanged()
    signal moveStarted()
    signal moveUpdated(int position)
    signal moveFinished(int position)
    signal moveCanceled()

    readonly property rect selectedImageRect:
        root.documentController.imageSelected
        ? root.documentController.selectedImageRect
        : Qt.rect(0, 0, 0, 0)
    readonly property rect dropCursorRect:
        root.dropPosition >= 0
        ? root.editor.positionToRectangle(root.dropPosition)
        : Qt.rect(0, 0, 0, 0)

    visible: root.active && root.documentController.imageSelected
    x: root.editor.leftPadding + root.selectedImageRect.x
    y: root.editor.topPadding + root.selectedImageRect.y
    width: Math.max(1, root.selectedImageRect.width)
    height: Math.max(
        24,
        root.selectedImageRect.height)
    color: "transparent"
    border.width: 2
    border.color: root.theme.action
    radius: 2
    z: 4

    MouseArea {
        id: imageMovePointer
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        property point pressScenePoint: Qt.point(0, 0)
        property bool draggingImage: false

        onPressed: mouse => {
            pressScenePoint = mapToItem(null, mouse.x, mouse.y)
            draggingImage = false
        }
        onPositionChanged: mouse => {
            if (!pressed)
                return
            const scenePoint = mapToItem(null, mouse.x, mouse.y)
            if (!draggingImage
                    && Math.abs(scenePoint.x - pressScenePoint.x) < 6
                    && Math.abs(scenePoint.y - pressScenePoint.y) < 6) {
                return
            }
            if (!draggingImage) {
                draggingImage = true
                root.moveStarted()
            }
            const editorPoint = mapToItem(root.editor, mouse.x, mouse.y)
            root.moveUpdated(root.editor.positionAt(
                editorPoint.x, editorPoint.y))
        }
        onReleased: mouse => {
            if (draggingImage) {
                const editorPoint = mapToItem(root.editor, mouse.x, mouse.y)
                root.moveFinished(root.editor.positionAt(
                    editorPoint.x, editorPoint.y))
            }
            draggingImage = false
        }
        onCanceled: {
            if (draggingImage)
                root.moveCanceled()
            draggingImage = false
        }
    }

    Rectangle {
        objectName: "knowledgeImageDropIndicator"
        visible: root.moving && root.dropPosition >= 0
        x: root.dropCursorRect.x - root.x
        y: root.dropCursorRect.y - root.y
        width: 3
        height: Math.max(20, root.dropCursorRect.height)
        radius: 1
        color: root.theme.action
        z: 2
    }

    Rectangle {
        id: imageResizeHandle
        objectName: "knowledgeImageResizeHandle"
        visible: !root.documentController.selectedImageContentWidth
        width: 20
        height: 20
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: -8
        anchors.bottomMargin: -8
        radius: 8
        color: root.theme.action
        border.width: 2
        border.color: root.theme.workspace
        z: 3

        MouseArea {
            id: imageResizePointer
            anchors.centerIn: parent
            width: 32
            height: 32
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.SizeFDiagCursor
            property real startWidth: 0
            property real startHeight: 0
            property real startPointerSceneX: 0

            onPressed: mouse => {
                startWidth = root.width
                startHeight = root.height
                startPointerSceneX = mapToItem(
                    null, mouse.x, mouse.y).x
                root.documentController.begin_image_resize(
                    startWidth, startHeight)
            }
            onPositionChanged: mouse => {
                if (!pressed)
                    return
                const pointer = mapToItem(null, mouse.x, mouse.y)
                root.documentController.resize_selected_image(
                    startWidth + pointer.x - startPointerSceneX,
                    root.maximumWidth)
            }
            onReleased: root.contentChanged()
            onCanceled: root.contentChanged()
        }
    }
}
