import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/search/header.ui.mjs" as Header
import "../../tactic_frame/core/foundation.mjs" as Foundation

Item {
    id: root
    required property var theme
    required property var controller
    required property var editorController
    required property real budget
    required property string language
    required property var groups
    readonly property var scene: {
        if (budget <= 0)
            return Header.quickStrip([], 0, language);
        const measured = groups.slice(0, 3).map(group => {
            const count = group.userPicker ? group.selectedUserCount + (group.myTasksSelected ? 1 : 0) : group.options.filter(option => option.selected).length;
            const item = Object.assign({}, group, {
                count: count,
                disabled: controller.search_state === "loading"
            });
            item.textWidth = metrics.advanceWidth(Header.quickLabel(item, language));
            return item;
        });
        return Header.quickStrip(measured, budget, language);
    }
    signal groupRequested(string key, var source)

    implicitWidth: scene.width
    // Cached settings emit groupsChanged; apply them after this binding settles.
    onGroupsChanged: if (groups.length > 0)
        Qt.callLater(editorController.ensure_current)
    Connections {
        target: root.controller
        enabled: root.groups.length > 0
        function onSearch_text_changed() {
            root.editorController.ensure_current();
        }
    }
    FontMetrics {
        id: metrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.Normal,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    Frame.FrameView {
        width: Math.max(0, root.scene.width - 38)
        height: 38
        theme: root.theme
        scene: root.scene
        onEvent: (action, source) => root.groupRequested(action.key, source)
    }
}
