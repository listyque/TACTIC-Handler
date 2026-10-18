import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/mappings.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string value: ""
    property string primaryStream: ""
    property bool enabledEditing: true
    property string written: ""
    property string parseError: ""
    property bool technical: false
    property int nextId: 0
    property var rows: []
    signal edited(string value)
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property var presentation: UI.describe({
        rows: rows,
        value: value,
        error: parseError,
        technical: technical,
        enabled: enabledEditing
    }, width, language)
    implicitHeight: presentation.height
    function load() {
        if (value === written)
            return;
        try {
            const data = value ? JSON.parse(value) : [];
            if (!Array.isArray(data))
                throw new Error(qsTr("Mappings must be an array"));
            const next = data.map(row => ({
                        id: String(++nextId),
                        stream: row.stream || "",
                        source: row.source || "",
                        target: row.target || "...",
                        exclude: Boolean(row.exclude),
                        writable: Boolean(row.writable)
                    }));
            rows = next;
            parseError = "";
        } catch (error) {
            parseError = String(error.message);
        }
    }
    function publish() {
        const values = rows.map(row => {
            const value = {
                stream: row.stream,
                source: row.source,
                exclude: row.exclude,
                writable: row.writable
            };
            if (!row.exclude)
                value.target = row.target;
            return value;
        });
        written = JSON.stringify(values);
        edited(written);
    }
    function changed(row, key, value) {
        const next = Object.assign({}, row);
        next[key] = value;
        return next;
    }
    function dispatch(action) {
        if (action.type === "technical") {
            technical = !technical;
            return;
        }
        if (!enabledEditing)
            return;
        if (action.type === "json") {
            edited(action.value);
            return;
        }
        if (action.type === "add" && rows.length < 256) {
            rows = rows.concat([
                {
                    id: String(++nextId),
                    stream: primaryStream,
                    source: "...",
                    target: "...",
                    exclude: false,
                    writable: true
                }
            ]);
            publish();
            return;
        }
        const row = rows.find(row => row.id === action.key);
        if (!row)
            return;
        if (action.type === "remove")
            rows = rows.filter(item => item.id !== action.key);
        else if (action.type === "field" && ["stream", "source", "target", "exclude", "writable"].includes(action.field))
            rows = rows.map(item => item.id === action.key ? changed(item, action.field, action.value) : item);
        else
            return;
        publish();
    }
    onValueChanged: load()
    Component.onCompleted: load()
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: ({
                nodes: root.presentation.nodes
            })
        onEvent: action => root.dispatch(action)
    }
}
