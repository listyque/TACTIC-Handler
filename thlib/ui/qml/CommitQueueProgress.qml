import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root
    required property var theme
    required property var progress
    objectName: "commitQueueProgress"
    visible: Object.keys(progress).length > 0
    spacing: 4
    readonly property string phase: progress.phase || ""
    function size(bytes) { return qsTr("%1 MB").arg((Number(bytes || 0) / 1048576).toFixed(1)) }
    Label {
        objectName: "commitQueueProgressStage"
        Layout.fillWidth: true
        text: root.progress.uploadInterrupted
            ? qsTr("Upload interrupted. Use Retry to resume the existing batch.")
            : root.progress.error
            ? qsTr("Progress unavailable. Check-in results are not confirmed; retrying status requests.")
            : root.phase === "hooks" ? qsTr("Running before check-in hooks")
            : root.phase === "preparing" ? qsTr("Preparing files and checksums")
            : root.phase === "uploading" ? qsTr("Uploading files")
            : root.phase === "committing" ? qsTr("Checking in on server")
            : qsTr("Finished")
        color: root.progress.error ? root.theme.error : root.theme.primaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    Label {
        objectName: "commitQueueProgressFile"
        Layout.fillWidth: true
        visible: root.progress.filename ? true : false
        text: root.progress.filename || ""
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WrapAnywhere
    }
    ProgressBar {
        objectName: "commitQueueUploadProgress"
        Layout.fillWidth: true
        visible: root.phase !== "hooks"
        from: 0
        to: 1
        indeterminate: Boolean(root.progress.busy) && !root.progress.totalsKnown
        value: root.progress.totalBytes > 0 ? root.progress.bytesDone / root.progress.totalBytes
            : root.progress.totalFiles > 0 ? root.progress.filesDone / root.progress.totalFiles : 0
        Accessible.name: qsTr("Upload progress")
    }
    Label {
        objectName: "commitQueueUploadSummary"
        Layout.fillWidth: true
        visible: root.progress.totalFiles > 0
        text: root.progress.totalsKnown
            ? qsTr("Uploaded %1 / %2 files · %3 / %4")
                .arg(root.progress.filesDone).arg(root.progress.totalFiles)
                .arg(root.size(root.progress.bytesDone)).arg(root.size(root.progress.totalBytes))
            : qsTr("Uploaded %1 files · %2").arg(root.progress.filesDone).arg(root.size(root.progress.bytesDone))
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
    }
    ProgressBar {
        objectName: "commitQueueServerProgress"
        Layout.fillWidth: true
        from: 0
        to: Math.max(1, root.progress.totalOperations || 0)
        value: (root.progress.completed || 0) + (root.progress.failed || 0) + (root.progress.cancelled || 0)
        Accessible.name: qsTr("Server check-in progress")
    }
    Label {
        objectName: "commitQueueServerSummary"
        Layout.fillWidth: true
        text: qsTr("Check-ins: %1 / %2 completed · %3 failed · %4 cancelled · %5 running")
            .arg(root.progress.completed || 0).arg(root.progress.totalOperations || 0)
            .arg(root.progress.failed || 0).arg(root.progress.cancelled || 0).arg(root.progress.running || 0)
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
    }
    Label {
        objectName: "commitQueueProgressElapsed"
        Layout.fillWidth: true
        text: qsTr("Elapsed: %1 s").arg(root.progress.elapsed || 0)
            + (root.progress.busy && root.progress.idleSeconds >= 15
                ? " · " + qsTr("No new progress for %1 s").arg(root.progress.idleSeconds) : "")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.caption
        wrapMode: Text.WordWrap
    }
}
