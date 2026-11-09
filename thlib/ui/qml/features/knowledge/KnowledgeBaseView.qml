import QtQuick
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/workspace.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property bool narrow: width < 720
    property bool navigationPage: true
    property bool navigationExpanded: true
    readonly property bool singlePane: root.narrow || !root.navigationExpanded
    property bool dockResizeActive: false

    function consumeOpenArticleRequest() {
        if (!knowledgeController.openArticlePending)
            return;
        root.navigationPage = false;
        knowledgeController.acknowledge_article_open();
    }

    Component.onCompleted: root.consumeOpenArticleRequest()

    Controls.DockWorkspaceFooter {
        objectName: "knowledgeDockSurface"
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    Connections {
        target: knowledgeController
        function onStateChanged() {
            root.consumeOpenArticleRequest();
            if (root.singlePane && (knowledgeController.identity.length > 0 || knowledgeController.creating))
                root.navigationPage = false;
        }
    }

    readonly property var presentation: ({
            initialized: knowledgeController.initialized,
            canEdit: knowledgeController.canEdit,
            busy: knowledgeController.busy,
            error: knowledgeController.error,
            organizationDirty: knowledgeController.organizationDirty,
            navigationExpanded: root.navigationExpanded,
            navigationPage: root.navigationPage
        })
    readonly property var scene: UI.describe(root.presentation, width, height, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
    function dispatch(action) {
        if (action.type === "reload")
            knowledgeController.reload();
        else if (action.type === "dismissError")
            knowledgeController.dismiss_error();
        else if (action.type === "navigation") {
            const next = UI.toggleNavigation(root.presentation, knowledgeController.identity.length > 0 || knowledgeController.creating);
            root.navigationExpanded = next.navigationExpanded;
            root.navigationPage = next.navigationPage;
        } else if (action.type === "saveOrder")
            knowledgeController.save_organization();
        else if (action.type === "discardOrder")
            knowledgeController.discard_organization();
        else if (action.type === "createArticle" || action.type === "createSection")
            knowledgeController.create(action.type === "createArticle" ? "article" : "section", knowledgeController.document.kind === "section" ? knowledgeController.identity : String(knowledgeController.document.parentCode || ""));
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        views: ({
                navigation: navigationComponent,
                page: pageComponent,
                initialization: initializationComponent
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: navigationComponent
        KnowledgeNavigation {
            objectName: "knowledgeNavigation"
            theme: root.theme
            controller: knowledgeController
            onArticleRequested: root.navigationPage = false
        }
    }
    Component {
        id: pageComponent
        Item {
            Loader {
                id: articleLoader
                objectName: "knowledgeArticleLoader"
                anchors.fill: parent
                active: knowledgeController.identity.length > 0 || knowledgeController.creating
                sourceComponent: knowledgeController.editing ? editorComponent : viewerComponent
            }
            Controls.EmptyState {
                anchors.fill: parent
                visible: !articleLoader.active && !knowledgeController.busy
                theme: root.theme
                iconName: "file"
                title: qsTr("Choose an article")
                message: qsTr("Sections, full-text search, files, and object links stay together here.")
            }
        }
    }
    Component {
        id: initializationComponent
        CollaborationInitializationState {
            theme: root.theme
            canInitialize: knowledgeController.canInitialize
            busy: knowledgeController.busy
            error: ""
            featureIcon: "file"
            featureTitle: qsTr("Knowledge Base is not initialized")
            featureMessage: qsTr("Initialize the collaboration schema before writing project documentation.")
            projectCode: knowledgeController.projectCode
            onInitializeRequested: knowledgeController.initialize()
        }
    }

    Component {
        id: viewerComponent
        KnowledgeArticleViewer {
            theme: root.theme
            controller: knowledgeController
            resizeActive: root.dockResizeActive
            backNavigationAvailable: root.scene.bounds.single
            onBackRequested: root.navigationPage = true
        }
    }
    Component {
        id: editorComponent
        KnowledgeArticleEditor {
            theme: root.theme
            controller: knowledgeController
            resizeActive: root.dockResizeActive
            backNavigationAvailable: root.scene.bounds.single
            onBackRequested: root.navigationPage = true
        }
    }
}
