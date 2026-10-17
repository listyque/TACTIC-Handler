import QtQuick
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/configuration/settings.ui.mjs" as UI
import "../../tactic_frame/features/configuration/configuration.ui.mjs" as Configuration

Item {
    id: root
    required property var theme
    required property string pageId
    property bool managed: false
    property var values: ({})
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property string canonicalPage: {
        const page = Configuration.pages.find(entry => (entry.nativeId || entry.id) === root.pageId);
        return page ? page.id : root.pageId;
    }
    property int presetsRevision: 0
    readonly property var formModel: {
        const revision = presetsRevision;
        const projected = Object.assign({}, values);
        const levels = values.debugLogLevels || [];
        for (const level of ["LOG", "INFO", "WARNING", "MISSING", "EXCEPTION", "ERROR", "CRITICAL", "API"])
            projected["debug_" + level] = levels.includes(level);
        projected.activityNotifications = typeof activityFeedController !== "undefined" ? activityFeedController.notificationsEnabled : true;
        projected.messageNotifications = typeof messagesController !== "undefined" ? messagesController.notificationsEnabled : true;
        projected.versionsPosition = values.versionsBottom ? 1 : 0;
        projected.lightAccent = (values.themeAccents || {})[values.themeStyle]?.light || "steel";
        projected.darkAccent = (values.themeAccents || {})[values.themeStyle]?.dark || "steel";
        const presets = [];
        if (root.canonicalPage === "server")
            for (let index = 0; index < serverPresetModel.count(); index++) {
                const preset = serverPresetModel.get(index);
                presets.push({
                    value: preset.label,
                    label: preset.label,
                    dataLabel: true
                });
            }
        return {
            native: true,
            values: projected,
            style: theme.style,
            columns: root.canonicalPage === "tasks" ? values.columns || [] : [],
            cacheBusy: root.canonicalPage === "cache" && typeof serverCacheController !== "undefined" && serverCacheController.busy,
            serverTestBusy: root.canonicalPage === "server" && configurationController.server_test_busy,
            signedIn: root.canonicalPage === "server" && appController.has_ticket && !appController.authentication_required,
            notice: root.canonicalPage === "server" ? configurationController.server_test_message : root.canonicalPage === "cache" && typeof serverCacheController !== "undefined" ? serverCacheController.message : "",
            options: root.canonicalPage === "appearance" ? {
                themeStyle: appController.theme_options,
                iconSet: appController.icon_set_options,
                language: localizationController.language_options
            } : {
                presetName: presets
            }
        };
    }
    readonly property var fields: Configuration.pages.some(entry => entry.id === canonicalPage) ? UI.fieldsFor(canonicalPage, formModel) : UI.dccFields(configurationController.page_schema(pageId))
    function syncValues() {
        values = configurationController.page_values(pageId);
    }
    function formValues() {
        return values;
    }
    function loadValues(next) {
        values = next;
    }
    function publish(next) {
        values = next;
        if (managed)
            configurationController.update_page(pageId, values);
    }
    function dispatch(action) {
        if (action.type === "field" || action.type === "step") {
            if (action.field === "activityNotifications") {
                if (typeof activityFeedController !== "undefined")
                    activityFeedController.set_notifications_enabled(action.value);
            } else if (action.field === "messageNotifications") {
                if (typeof messagesController !== "undefined")
                    messagesController.set_notifications_enabled(action.value);
            } else if (action.field.startsWith("debug_")) {
                const levels = values.debugLogLevels || [];
                const level = action.field.slice(6);
                publish(Object.assign({}, values, {
                    debugLogLevels: action.value ? levels.concat(level) : levels.filter(value => value !== level)
                }));
            } else if (["lightAccent", "darkAccent"].includes(action.field)) {
                const accents = Object.assign({}, values.themeAccents || {});
                accents[values.themeStyle] = Object.assign({}, accents[values.themeStyle] || {});
                accents[values.themeStyle][action.field === "lightAccent" ? "light" : "dark"] = action.value;
                publish(Object.assign({}, values, {
                    themeAccents: accents
                }));
            } else if (action.field === "presetName") {
                publish(configurationController.server_preset_values(action.value));
            } else if (action.field === "versionsPosition") {
                publish(Object.assign({}, values, {
                    versionsRight: action.value === 0,
                    versionsBottom: action.value === 1
                }));
            } else
                publish(UI.change(values, action, fields));
        } else if (action.type.startsWith("column"))
            publish(Object.assign({}, values, {
                columns: UI.editColumn(values.columns || [], action)
            }));
        else if (action.type === "clearTabs")
            configurationController.flush_search_cache();
        else if (action.type === "clearData")
            clearConfirmation.open();
        else if (action.type === "matchingTemplates")
            windowModel.show_window("matching_templates");
        else if (action.type === "presets")
            windowModel.show_window("server_presets");
        else if (action.type === "test")
            configurationController.test_server(values);
        else if (action.type === "signIn" && configurationController.apply_current())
            appController.request_authentication();
    }
    Component.onCompleted: syncValues()
    Connections {
        target: typeof serverPresetModel === "undefined" ? null : serverPresetModel
        function onModelReset() {
            root.presetsRevision++;
        }
        function onRowsInserted() {
            root.presetsRevision++;
        }
        function onRowsRemoved() {
            root.presetsRevision++;
        }
        function onDataChanged() {
            root.presetsRevision++;
        }
    }
    Connections {
        target: configurationController
        function onSessionStarted() {
            root.syncValues();
        }
        function onPageReset(pageId) {
            if (pageId === root.pageId)
                root.syncValues();
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(Object.assign({}, root.formModel, {
            fields: root.fields
        }), width, height, root.language)
        views: ({
                lightAccent: lightPalette,
                darkAccent: darkPalette
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: lightPalette
        Controls.AccentPresetPicker {
            theme: root.theme
            model: appController.accent_presets
            currentValue: root.formModel.values.lightAccent
            onActivated: value => root.dispatch({
                    type: "field",
                    field: "lightAccent",
                    value
                })
        }
    }
    Component {
        id: darkPalette
        Controls.AccentPresetPicker {
            theme: root.theme
            model: appController.accent_presets
            darkPreview: true
            currentValue: root.formModel.values.darkAccent
            onActivated: value => root.dispatch({
                    type: "field",
                    field: "darkAccent",
                    value
                })
        }
    }
    Controls.Dialog {
        id: clearConfirmation
        objectName: "configurationCacheClearConfirmation"
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(430, root.width - 32)
        modal: true
        title: qsTr("Clear cached server data?")
        padding: 0
        headerPadding: 20
        contentItem: Frame.FrameView {
            implicitHeight: 220
            theme: root.theme
            scene: Configuration.confirmation({
                kind: "clear"
            }, width, height, root.language)
            onEvent: action => {
                clearConfirmation.close();
                if (action.type === "accept")
                    configurationController.clear_data_cache();
            }
        }
    }
}
