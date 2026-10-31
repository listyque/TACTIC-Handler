pragma ComponentBehavior: Bound
import QtQuick
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/administration.ui.mjs" as UI
import "../../tactic_frame/features/administration/administration.state.mjs" as State

Item {
    id: root
    objectName: "administrationFrameShell"
    required property var theme
    readonly property var controller: administrationController
    readonly property bool framePage: ["groups", "users", "rules", "raw", "sidebar", "columns", "types", "schema", "workflow", "layouts", "dashboards", "plugins", "showcase"].includes(controller.section)
    readonly property bool columnsVisible: controller.section === "columns"
    property var ui: State.initial()
    property bool columnsDirty: false
    readonly property string language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
    readonly property var frameModel: ({
            section: controller.section,
            streamApi: controller.streamAvailable,
            layoutParent: controller.section === "layouts" && root.contentHost?.layouts?.navigationParent || controller.layoutParent,
            project: controller.project,
            projects: projectModel.allProjects.map(row => ({
                        value: row.projectCode,
                        label: row.title,
                        preview: row.preview || "",
                        category: row.category || "",
                        kind: row.isBuiltin ? "Built-in" : row.isTemplate ? "Templates" : row.isRetired ? "Retired" : ""
                    })),
            locked: controller.projectLocked || columnsDirty,
            busy: controller.busy,
            drafts: UI.sections.filter(row => root.sectionDirty(row.id)).map(row => row.id)
        })
    function sectionDirty(section) {
        if (section === "groups")
            return controller.dirty || controller.groupUncertain;
        if (section === "types" && controller.namingEditor && (controller.namingEditor.dirty || controller.namingEditor.writeUncertain))
            return true;
        if (section === "workflow" && (controller.workflowEditor.rulesEditor.dirty || controller.workflowEditor.rulesEditor.writeUncertain))
            return true;
        if (section === "columns")
            return columnsDirty;
        if (section === "sidebar")
            return sidebarEditorController.dirty;
        const editor = {
            types: controller.typesEditor,
            schema: controller.schemaEditor,
            workflow: controller.workflowEditor,
            rules: controller.securityEditor,
            users: controller.usersEditor,
            raw: controller.rawEditor,
            plugins: controller.pluginsEditor,
            dashboards: controller.dashboardEditor,
            layouts: controller.layoutEditor
        }[section];
        return !!editor && (editor.dirty || editor.writeUncertain);
    }
    function dispatch(event) {
        const result = State.transition(ui, frameModel, event);
        ui = result.ui;
        for (const command of result.commands) {
            switch (command.type) {
            case "return-layout":
                if (controller.section === "layouts" && root.contentHost?.layouts?.navigationParent)
                    root.contentHost.layouts.dispatch({
                        type: "backLayout"
                    });
                else
                    controller.return_to_page_layout();
                break;
            case "section":
                controller.select_section(command.value);
                break;
            case "project":
                controller.select_project(command.value);
                break;
            case "help":
                windowModel.open_help(command.topic);
                break;
            case "close":
                windowModel.close_window("administration");
                break;
            }
        }
    }
    property var contentHost: null
    Connections {
        target: root.controller
        function onPageColumnsRequested(searchType, view) {
            const columns = root.contentHost ? root.contentHost.columns : null;
            const same = columns && columns.selectedCatalog.searchType === searchType && columns.selectedCatalog.view === view && !columnsEditorController.busy;
            if (!same && (columnsEditorController.busy || columnsEditorController.catalogUncertain || (columns && columns.catalogDirty))) {
                root.controller.dashboardEditor.fail(qsTr("Save or discard changes before continuing"));
                return;
            }
            root.controller.remember_page_layout("columns", "");
            if (!same)
                columnsEditorController.open_scoped_definition(searchType, view, root.controller.project);
            root.controller.select_section("columns");
        }
    }
    readonly property var groupsView: contentHost ? contentHost.groups : null
    readonly property var savePage: {
        switch (controller.section) {
        case "raw":
            return contentHost ? contentHost.raw : null;
        case "plugins":
            return contentHost ? contentHost.plugins : null;
        case "types":
            return contentHost ? contentHost.types : null;
        case "schema":
            return contentHost ? contentHost.schema : null;
        case "workflow":
            return contentHost ? contentHost.workflow : null;
        case "rules":
            return contentHost ? contentHost.rules : null;
        case "users":
            return contentHost ? contentHost.users : null;
        case "groups":
            return groupsView;
        case "columns":
            return contentHost ? contentHost.columns : null;
        case "sidebar":
            return contentHost ? contentHost.sidebar : null;
        case "dashboards":
            return contentHost ? contentHost.dashboards : null;
        case "layouts":
            return contentHost ? contentHost.layouts : null;
        default:
            return null;
        }
    }
    readonly property bool documentPage: ["raw", "types", "schema", "workflow", "rules", "users", "layouts", "dashboards"].includes(controller.section)
    readonly property bool headerCreateVisible: controller.section === "groups" || (documentPage && !!savePage && !!savePage.allowCreate)
    readonly property bool headerCreateEnabled: controller.section === "groups" ? Boolean(groupsView && groupsView.canCreateGroup) : Boolean(savePage && savePage.canCreateDocument)
    readonly property bool headerReloadVisible: controller.section === "groups" || controller.section === "columns" || (documentPage && !!savePage && !!savePage.allowReload)
    readonly property bool headerReloadEnabled: controller.section === "groups" ? Boolean(groupsView && groupsView.canReloadGroup) : controller.section === "columns" ? Boolean(savePage && savePage.canReloadCatalog) : Boolean(savePage && savePage.canReloadDocument)
    readonly property bool namingActive: controller.section === "types" && !!savePage && savePage.namingPage
    readonly property var saveController: {
        if (namingActive)
            return controller.namingEditor;
        if (controller.section === "groups")
            return controller;
        if (controller.section === "columns")
            return columnsEditorController;
        if (controller.section === "sidebar")
            return sidebarEditorController;
        return savePage ? savePage.controller : null;
    }
    readonly property bool saveDirty: controller.section === "columns" ? Boolean(savePage && savePage.catalogDirty) : Boolean(saveController && saveController.dirty)
    readonly property bool saveBusy: Boolean(saveController && saveController.busy)
    readonly property bool saveCanWrite: {
        if (!controller.canManage || !savePage || !saveController)
            return false;
        if (namingActive)
            return !!savePage.namingView && !!saveController.currentObject.searchType;
        if (controller.section === "groups")
            return Boolean(controller.canManage);
        if (controller.section === "columns")
            return !!savePage.selectedCatalog.identity;
        if (controller.section === "sidebar")
            return Boolean(saveController.canEdit);
        return Boolean(saveController.canWrite);
    }
    readonly property string saveButtonName: namingActive ? "namingSave" : controller.section === "groups" ? "saveSecurityGroup" : controller.section === "columns" ? "saveDefinitionCatalogXml" : controller.section === "sidebar" ? "sidebarSaveButton" : "adminSaveDocument"

    function saveCurrent() {
        if (!controller.canManage || !savePage || !saveCanWrite || !saveDirty || saveBusy)
            return;
        if (namingActive)
            savePage.namingView.requestSave();
        else if (controller.section === "groups")
            groupsView.requestSave();
        else
            savePage.requestSave();
    }

    function discardCurrent() {
        if (!controller.canManage || !savePage || !saveDirty || saveBusy)
            return;
        if (namingActive)
            savePage.namingView.discardChanges();
        else
            savePage.discardChanges();
    }

    function createCurrent() {
        if (!headerCreateEnabled)
            return;
        if (controller.section === "groups")
            groupsView.createGroup();
        else
            savePage.createDocument();
    }

    function reloadCurrent() {
        if (!headerReloadEnabled)
            return;
        if (controller.section === "groups")
            groupsView.reloadGroup();
        else if (controller.section === "columns")
            savePage.reloadCatalog();
        else
            savePage.reloadDocument();
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: ({
                sections: UI.availableSections(root.frameModel)
            })
        describeRow: (list, record) => UI.row(list, record, root.frameModel, root.ui, root.language)
        views: ({
                projectPicker: projectPickerPort,
                toolbar: toolbarPort,
                content: contentPort
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: projectPickerPort
        AdminProjectPicker {
            theme: root.theme
            model: root.frameModel
            language: root.language
            onSelected: code => root.dispatch({
                    type: "project",
                    value: code
                })
        }
    }
    Component {
        id: toolbarPort
        Frame.FrameView {
            objectName: "administrationHeaderSaveBar"
            theme: root.theme
            scene: root.savePage && typeof root.savePage.toolbarScene === "function" ? root.savePage.toolbarScene(width) : ({
                    nodes: []
                })
            onEvent: action => root.savePage.dispatch(action)
        }
    }
    Component {
        id: contentPort
        Item {
            Component.onCompleted: root.contentHost = this
            Component.onDestruction: root.contentHost = null
            readonly property var groups: groupsView
            readonly property var raw: rawLoader.item
            readonly property var plugins: pluginsLoader.item
            readonly property var types: typesLoader.item
            readonly property var schema: schemaLoader.item
            readonly property var workflow: workflowLoader.item
            readonly property var rules: rulesLoader.item
            readonly property var users: usersLoader.item
            readonly property var columns: columnsLoader.item
            readonly property var dashboards: dashboardsLoader.item
            readonly property var layouts: layoutsLoader.item
            readonly property var sidebar: sidebarLoader.item
            SecurityGroupsView {
                id: groupsView
                anchors.fill: parent
                visible: root.controller.section === "groups"
                theme: root.theme
                controller: root.controller
                groupsModel: administrationGroupModel
                membersModel: administrationMemberModel
                language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
                saveActionsInHeader: true
            }
            Loader {
                id: showcaseLoader
                anchors.fill: parent
                active: root.controller.section === "showcase"
                visible: active
                sourceComponent: ComponentShowcaseView {
                    theme: root.theme
                    sourceEditor: root.controller.componentSourceEditor
                    sampleServices: root.controller.componentSamples
                    language: root.language
                }
            }
            Loader {
                id: pluginsLoader
                anchors.fill: parent
                visible: root.controller.section === "plugins"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminPluginsView {
                    theme: root.theme
                    controller: root.controller.pluginsEditor
                    language: root.language
                    onHelpRequested: windowModel.open_help("plugins")
                }
            }
            Loader {
                id: rawLoader
                anchors.fill: parent
                visible: root.controller.section === "raw"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminRawDatabaseView {
                    language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
                    theme: root.theme
                    controller: root.controller.rawEditor
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: typesLoader
                anchors.fill: parent
                visible: root.controller.section === "types"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminSearchTypesView {
                    theme: root.theme
                    controller: root.controller.typesEditor
                    namingController: root.controller.namingEditor
                    projectCode: root.controller.project
                    saveActionsInHeader: true
                    onOpenWorkflowRequested: identity => root.controller.open_type_workflow(identity)
                    onCreateWorkflowRequested: root.controller.create_type_workflow(root.controller.typesEditor)
                }
            }
            Loader {
                id: schemaLoader
                anchors.fill: parent
                visible: root.controller.section === "schema"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminGraphView {
                    id: schemaView
                    theme: root.theme
                    controller: root.controller.schemaEditor
                    saveActionsInHeader: true
                    onCreateSearchTypeRequested: (x, y) => root.controller.schemaTypeEditor.open(x, y)
                    onNodeWorkflowsRequested: root.controller.open_schema_node_workflows()
                    onDeleteSearchTypeRequested: identity => {
                        if (root.controller.prepare_schema_node_deletion(identity))
                            schemaView.showDeleteConfirmation();
                    }
                }
            }
            Loader {
                id: workflowLoader
                anchors.fill: parent
                visible: root.controller.section === "workflow"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminGraphView {
                    theme: root.theme
                    controller: root.controller.workflowEditor
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: rulesLoader
                anchors.fill: parent
                visible: root.controller.section === "rules"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminSecurityView {
                    language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
                    theme: root.theme
                    controller: root.controller.securityEditor
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: usersLoader
                anchors.fill: parent
                visible: root.controller.section === "users"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: AdminUsersView {
                    theme: root.theme
                    controller: root.controller.usersEditor
                    language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: columnsLoader
                anchors.fill: parent
                visible: root.columnsVisible
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: ColumnsEditorView {
                    objectName: "administrationColumnsEditor"
                    theme: root.theme
                    projectCode: root.controller.project
                    canWrite: root.controller.canManage
                    saveActionsInHeader: true
                    onCatalogDirtyChanged: root.columnsDirty = catalogDirty
                }
            }
            Loader {
                id: dashboardsLoader
                anchors.fill: parent
                visible: root.controller.section === "dashboards"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: PageLayoutEditorView {
                    theme: root.theme
                    controller: root.controller.dashboardEditor
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: layoutsLoader
                anchors.fill: parent
                visible: root.controller.section === "layouts"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: LayoutEditorView {
                    objectName: "administrationLayoutEditor"
                    theme: root.theme
                    controller: root.controller.layoutEditor
                    language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
                    saveActionsInHeader: true
                }
            }
            Loader {
                id: sidebarLoader
                anchors.fill: parent
                visible: root.controller.section === "sidebar"
                active: false
                onVisibleChanged: if (visible)
                    active = true
                Component.onCompleted: if (visible)
                    active = true
                sourceComponent: SidebarEditorView {
                    objectName: "administrationSidebarEditor"
                    theme: root.theme
                    saveActionsInHeader: true
                }
            }
        }
    }
}
