import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/toolbar.ui.mjs" as UI
import "../../../tactic_frame/controls/tabs/workspace.ui.mjs" as TabUI

Item {
    id: root
    required property var workspace
    readonly property var theme: workspace.theme
    readonly property bool canMaximize: typeof dockModel !== "undefined"
    readonly property bool maximized: canMaximize && dockModel.maximizedPanelId === "commit_queue"
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property bool hasOverflow: false
    property real scrollGutter: 0
    implicitHeight: theme.controlHeight + scrollGutter
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.views({
            style: root.theme.style,
            narrow: workspace.narrow,
            workspace: workspace.workspaceState.workspace,
            busy: workspace.busy,
            canCreate: true,
            canMaximize: root.canMaximize,
            maximized: root.maximized
        }, width, height, root.language)
        views: ({
                tabs: {
                    component: tabsPort
                }
            })
        onEvent: (action, source) => {
            if (action.type === "menu")
                workspace.menu(action.kind, source);
            else if (action.type === "tree")
                workspace.treeOpen = !workspace.treeOpen;
            else if (action.type === "create")
                workspace.act("create_change");
            else if (action.type === "maximize" && root.canMaximize)
                dockModel.maximize_panel("commit_queue");
        }
    }
    Component {
        id: tabsPort
        Flickable {
            id: viewTabs
            objectName: "workspaceViewTabs"
            anchors.fill: parent
            contentWidth: tabsRow.implicitWidth
            contentHeight: height
            clip: true
            ScrollBar.horizontal: Controls.ScrollBar {
                id: tabBar
                theme: workspace.theme
                flickableTarget: viewTabs
            }
            readonly property real gutter: tabBar.hasOverflow ? tabBar.reservedExtent : 0
            onGutterChanged: root.scrollGutter = gutter
            RowLayout {
                id: tabsRow
                spacing: 4
                width: implicitWidth
                Repeater {
                    model: workspace.workspaceState.tabs
                    delegate: Item {
                        id: tabItem
                        required property var modelData
                        implicitWidth: TabUI.viewTabWidth(tabVisual.labelImplicitWidth)
                        implicitHeight: workspace.theme.controlHeight
                        Layout.minimumWidth: implicitWidth
                        Layout.preferredWidth: implicitWidth
                        objectName: "workspaceViewTab:" + modelData.id
                        activeFocusOnTab: true
                        Accessible.role: Accessible.PageTab
                        Accessible.name: tabVisual.title
                        Keys.onReturnPressed: workspace.selectTab(modelData)
                        Keys.onSpacePressed: workspace.selectTab(modelData)
                        Controls.WorkspaceTabVisual {
                            id: tabVisual
                            anchors.fill: parent
                            theme: workspace.theme
                            title: tabItem.modelData.custom ? tabItem.modelData.title : qsTr(tabItem.modelData.title)
                            iconName: tabItem.modelData.icon
                            current: workspace.workspaceState.active_tab === tabItem.modelData.id
                            closable: true
                            hovered: tabHover.hovered
                            pressed: tabActivate.pressed
                            onCloseRequested: workspace.controller.close_tab(tabItem.modelData.id)
                        }
                        HoverHandler {
                            id: tabHover
                        }
                        Controls.ActivationHandler {
                            id: tabActivate
                            anchors.rightMargin: 36
                            enabled: true
                            onActivated: workspace.selectTab(tabItem.modelData)
                        }
                    }
                }
            }
        }
    }
}
