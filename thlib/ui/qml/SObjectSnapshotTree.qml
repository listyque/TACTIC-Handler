import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/objects/snapshot_tree.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var metrics
    required property var snapshotProcessModel
    required property var controller
    property var expanded: ({})
    property var fileHeights: ({})
    property int revision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var groups: {
        const generation = revision;
        const rows = [];
        for (let index = 0; index < snapshotProcessModel.count(); ++index)
            rows.push(snapshotProcessModel.get(index));
        return rows;
    }
    readonly property var scene: UI.describe({
        metrics: metrics,
        groups: groups,
        expanded: expanded,
        fileHeights: fileHeights
    }, width, language)
    implicitHeight: scene.height
    Connections {
        target: root.snapshotProcessModel
        function onContentReplaced() {
            root.revision += 1;
        }
    }
    function measure(token, value) {
        if (!token || value <= 0 || fileHeights[token] === value)
            return;
        const next = Object.assign({}, fileHeights);
        next[token] = value;
        fileHeights = next;
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        views: ({
                attachment: {
                    component: attachment,
                    nodeProps: true
                }
            })
        onEvent: action => {
            if (action.type === "expand") {
                const next = Object.assign({}, root.expanded);
                next[action.value] = !next[action.value];
                root.expanded = next;
            } else if (action.type === "snapshot")
                root.controller.open_snapshot(action.index);
        }
    }
    Component {
        id: attachment
        Item {
            property var frameNode: null
            readonly property var record: frameNode ? frameNode.record : ({})
            AttachmentCard {
                width: parent.width
                height: implicitHeight
                theme: root.theme
                title: parent.record.title || ""
                extension: parent.record.extension || ""
                previewUrl: parent.record.previewUrl || ""
                sizeText: parent.record.sizeText || ""
                local: !!parent.record.exists
                animatePreview: false
                onImplicitHeightChanged: root.measure(parent.record.token, implicitHeight)
                Component.onCompleted: root.measure(parent.record.token, implicitHeight)
                onActivated: root.controller.activate_file(parent.record.token)
                onContextRequested: (x, y) => {
                    if (parent.record.exists)
                        root.controller.show_file_folder(parent.record.token);
                }
            }
        }
    }
}
