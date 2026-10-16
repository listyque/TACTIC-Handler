import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/support/diagnostics/performance.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var selectedSample: ({})
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            recording: uiPerformance.recording,
            summary: uiPerformance.summary,
            selectedId: selectedSample.sampleId || 0,
            selected: selectedSample,
            browserFrames: false
        })
    function row(list, record) {
        return UI.row(frameModel, record, list.width - 16, language);
    }
    function dispatch(action) {
        if (action.type === "record")
            uiPerformance.set_recording(!uiPerformance.recording);
        else if (action.type === "copy")
            uiPerformance.copy_results();
        else if (action.type === "clear") {
            selectedSample = ({});
            uiPerformance.clear();
        } else if (action.type === "sample")
            selectedSample = action.record;
        else if (action.type === "sampleKey") {
            const rows = [];
            for (let index = 0; index < uiPerformance.summary.count; index++)
                rows.push(uiPerformanceModel.get(index));
            const target = UI.selection(rows, action.id, action.key);
            if (target) {
                selectedSample = target;
                frame.focusListRow("uiPerformanceSamples", rows.findIndex(record => record.sampleId === target.sampleId), "sample_" + target.sampleId);
            }
        }
    }
    Connections {
        target: uiPerformance
        function onChanged() {
            if (!root.selectedSample.sampleId)
                return;
            for (let index = 0; index < uiPerformance.summary.count; index++) {
                const record = uiPerformanceModel.get(index);
                if (record.sampleId === root.selectedSample.sampleId) {
                    root.selectedSample = record;
                    return;
                }
            }
            root.selectedSample = ({});
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Frame.FrameView {
        id: frame
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        models: ({
                samples: uiPerformanceModel
            })
        describeRow: root.row
        onEvent: action => root.dispatch(action)
    }
}
