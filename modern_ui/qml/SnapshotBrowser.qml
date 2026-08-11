import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    signal notice(string message)

    readonly property bool showAllFiles:
        appController.snapshot_browser_show_all
    readonly property bool showMoreInfo:
        appController.snapshot_browser_show_more
    readonly property bool sideBySide:
        appController.snapshot_browser_orientation === "vertical"
    readonly property real splitterRatio:
        appController.snapshot_browser_splitter_ratio
    property string contextFileToken: ""
    property int selectedFileRow: -1
    property int displayedFileCount: 0
    readonly property bool showFileSize:
        root.showMoreInfo && filesPanel.width >= 340
    readonly property bool showFilePath:
        root.showMoreInfo && filesPanel.width >= 650
    readonly property bool showFileRepository:
        root.showMoreInfo && filesPanel.width >= 820
    readonly property bool showFileBaseType:
        root.showMoreInfo && filesPanel.width >= 940

    function fileExtension(name) {
        const value = String(name || "")
        const position = value.lastIndexOf(".")
        return position > 0 ? value.substring(position + 1).toLowerCase() : ""
    }

    function fileIcon(rowType, fileType, baseType, title) {
        if (rowType === "snapshot")
            return "snapshot"
        if (rowType === "type")
            return "folder"
        const kind = String(fileType || "").toLowerCase()
        const base = String(baseType || "").toLowerCase()
        const extension = fileExtension(title)
        if (["image", "icon", "web"].indexOf(kind) >= 0)
            return "image"
        if (["playblast", "movie", "video"].indexOf(kind) >= 0)
            return "movie"
        if (base.indexOf("sequence") >= 0)
            return "sequence"
        if (["zip", "rar", "7z", "tar", "gz"].indexOf(extension) >= 0)
            return "archive"
        return "insert_drive_file"
    }

    function updateDisplayedFileCount() {
        let count = 0
        const rows = snapshotFileModel.count()
        for (let row = 0; row < rows; ++row) {
            const record = snapshotFileModel.get(row)
            if (record.rowType === "file"
                    && (root.showAllFiles || !record.previewType))
                ++count
        }
        displayedFileCount = count
    }

    onShowAllFilesChanged: updateDisplayedFileCount()

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

    Rectangle {
        id: toolbar
        anchors.top: parent.top
        width: parent.width
        height: 46
        color: root.theme.panel

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 8
            spacing: 6

            CompactIconButton {
                id: settingsButton
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                theme: root.theme
                round: true
                backgroundColor: root.theme.surfaceContainerHigh
                iconName: "more_vert"
                iconSize: 16
                toolTip: qsTr("Snapshot Browser options")
                onPressed: settingsMenu.sourceWasOpen = settingsMenu.opened
                onClicked: {
                    settingsMenu.actions =
                        appController.snapshot_browser_actions()
                    settingsMenu.toggleBelow(settingsButton)
                }
            }
            Item { Layout.fillWidth: true }
            RefreshIconButton {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                theme: root.theme
                backgroundColor: root.theme.surfaceContainerHigh
                iconSize: 16
                toolTip: qsTr("Refresh snapshots")
                onClicked: appController.refresh_snapshot_browser()
            }
        }
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: root.theme.separator
        }
    }

    Item {
        id: browserArea
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 10

        Rectangle {
            id: previewArea
            property string currentUrl: ""
            property string currentTitle: "Preview"
            property string currentToken: ""
            property int currentIndex: 0
            property string outgoingUrl: ""
            property int transitionDirection: 1

            function showPreview(index, direction) {
                var count = snapshotPreviewModel.count()
                if (count < 1) {
                    currentIndex = 0
                    currentUrl = ""
                    currentTitle = "Preview"
                    currentToken = ""
                    return
                }
                var nextIndex = Math.max(0, Math.min(count - 1, index))
                var nextDirection = Number(direction || 0)
                if (nextDirection === 0)
                    nextDirection = nextIndex >= currentIndex ? 1 : -1
                outgoingUrl = currentUrl
                transitionDirection = nextDirection
                currentIndex = nextIndex
                var record = snapshotPreviewModel.get(nextIndex)
                currentUrl = record.url || ""
                currentTitle = record.title || "Preview"
                currentToken = record.token || ""
                if (outgoingUrl !== "" && outgoingUrl !== currentUrl) {
                    incomingLayer.x = transitionDirection
                        * Math.max(36, previewViewport.width * 0.18)
                    incomingLayer.opacity = 0
                    outgoingLayer.x = 0
                    outgoingLayer.opacity = 1
                    carouselTransition.restart()
                } else {
                    incomingLayer.x = 0
                    incomingLayer.opacity = 1
                    outgoingLayer.opacity = 0
                }
            }

            x: 0
            y: 0
            width: root.sideBySide
                ? Math.max(120, browserArea.width * root.splitterRatio - 4)
                : browserArea.width
            height: root.sideBySide
                ? browserArea.height
                : Math.max(90, browserArea.height * root.splitterRatio - 4)
            radius: 12
            color: root.theme.surfaceContainerLow
            border.color: root.theme.outline
            border.width: 1
            clip: true
            focus: true
            Keys.onLeftPressed: {
                const count = snapshotPreviewModel.count()
                if (count > 1)
                    showPreview(Math.max(0, currentIndex - 1), -1)
            }
            Keys.onRightPressed: {
                const count = snapshotPreviewModel.count()
                if (count > 1)
                    showPreview(Math.min(count - 1, currentIndex + 1), 1)
            }

            Item {
                id: previewViewport
                anchors.fill: parent
                anchors.margins: 6
                anchors.bottomMargin: snapshotPreviewModel.count() > 1 ? 22 : 6
                clip: true

                Item {
                    id: outgoingLayer
                    anchors.fill: parent
                    opacity: 0
                    ItemPreview {
                        anchors.fill: parent
                        theme: root.theme
                        source: previewArea.outgoingUrl
                        fallbackIcon: "movie"
                        accent: root.theme.surfaceContainerHigh
                        fillMode: Image.PreserveAspectFit
                        round: false
                        cornerRadius: root.theme.itemRadius
                    }
                }
                Item {
                    id: incomingLayer
                    anchors.fill: parent
                    ItemPreview {
                        anchors.fill: parent
                        theme: root.theme
                        source: previewArea.currentUrl
                        fallbackIcon: "movie"
                        accent: root.theme.surfaceContainerHigh
                        fillMode: Image.PreserveAspectFit
                        round: false
                        cornerRadius: root.theme.itemRadius
                    }
                }
            }

            Rectangle {
                z: 4
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: snapshotPreviewModel.count() > 1 ? 25 : 7
                width: Math.min(titleLabel.implicitWidth + 22, parent.width - 110)
                height: 28
                radius: 14
                color: root.theme.surfaceContainerHigh
                opacity: previewHover.hovered && previewArea.currentUrl !== ""
                    ? 0.92 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: root.theme.motionFast
                        easing.type: Easing.OutCubic
                    }
                }
                Label {
                    id: titleLabel
                    anchors.fill: parent
                    anchors.leftMargin: 11
                    anchors.rightMargin: 11
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: previewArea.currentTitle
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                    elide: Text.ElideMiddle
                }
            }

            ParallelAnimation {
                id: carouselTransition
                NumberAnimation {
                    target: incomingLayer
                    property: "x"
                    to: 0
                    duration: 300
                    easing.type: Easing.OutExpo
                }
                NumberAnimation {
                    target: incomingLayer
                    property: "opacity"
                    to: 1
                    duration: 200
                    easing.type: Easing.OutCubic
                }
                NumberAnimation {
                    target: outgoingLayer
                    property: "x"
                    to: -previewArea.transitionDirection
                        * Math.max(36, previewViewport.width * 0.18)
                    duration: 300
                    easing.type: Easing.OutExpo
                }
                NumberAnimation {
                    target: outgoingLayer
                    property: "opacity"
                    to: 0
                    duration: 200
                    easing.type: Easing.OutCubic
                }
            }

            CompactIconButton {
                id: previewOptionsButton
                z: 5
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: 10
                width: 34
                height: 34
                theme: root.theme
                round: true
                backgroundColor: root.theme.surfaceContainerHigh
                iconName: "more_vert"
                iconSize: 16
                toolTip: qsTr("Preview actions")
                opacity: previewHover.hovered
                    && previewArea.currentToken !== "" ? 1 : 0
                enabled: opacity > 0.5
                Behavior on opacity {
                    NumberAnimation {
                        duration: root.theme.motionFast
                        easing.type: Easing.OutCubic
                    }
                }
                onPressed: fileMenu.sourceWasOpen = fileMenu.opened
                onClicked: {
                    root.contextFileToken = previewArea.currentToken
                    fileMenu.actions = appController.snapshot_file_actions(false)
                    fileMenu.toggleBelow(previewOptionsButton)
                }
            }

            Rectangle {
                z: 5
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                width: previewCounter.implicitWidth + 16
                height: 26
                radius: 13
                visible: snapshotPreviewModel.count() > 0
                color: root.theme.surfaceContainerHigh
                opacity: 0.90
                Label {
                    id: previewCounter
                    anchors.centerIn: parent
                    text: (previewArea.currentIndex + 1) + " / "
                        + snapshotPreviewModel.count()
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }
            }

            PreviewNavigationButton {
                id: backButton
                z: 3
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 10
                width: 40
                height: 84
                theme: root.theme
                iconName: "chevron_left"
                toolTip: qsTr("Previous preview")
                opacity: previewHover.hovered && snapshotPreviewModel.count() > 1 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.InOutSine } }
                onClicked: previewArea.showPreview(
                    Math.max(0, previewArea.currentIndex - 1),
                    -1
                )
            }

            PreviewNavigationButton {
                id: forwardButton
                z: 3
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                width: 40
                height: 84
                theme: root.theme
                iconName: "chevron_right"
                toolTip: qsTr("Next preview")
                opacity: previewHover.hovered && snapshotPreviewModel.count() > 1 ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.InOutSine } }
                onClicked: previewArea.showPreview(
                    Math.min(
                        snapshotPreviewModel.count() - 1,
                        previewArea.currentIndex + 1
                    ),
                    1
                )
            }

            MouseArea {
                id: previewMouse
                z: 1
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: previewArea.currentToken !== ""
                    ? Qt.PointingHandCursor : Qt.ArrowCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onWheel: wheel => {
                    var count = snapshotPreviewModel.count()
                    if (count > 1)
                        previewArea.showPreview(
                            Math.max(
                                0,
                                Math.min(
                                    count - 1,
                                    previewArea.currentIndex
                                    + (wheel.angleDelta.y < 0 ? 1 : -1)
                                )
                            ),
                            wheel.angleDelta.y < 0 ? 1 : -1
                        )
                }
                onDoubleClicked: mouse => {
                    if (mouse.button === Qt.LeftButton && previewArea.currentToken !== "")
                        appController.invoke_snapshot_file_action("open", previewArea.currentToken)
                }
                onClicked: mouse => {
                    previewArea.forceActiveFocus()
                    if (mouse.button === Qt.RightButton && previewArea.currentToken !== "") {
                        root.contextFileToken = previewArea.currentToken
                        fileMenu.actions = appController.snapshot_file_actions(false)
                        fileMenu.openAt(previewArea, mouse.x, mouse.y)
                    }
                }
            }

            Md3Slider {
                theme: root.theme
                z: 3
                visible: snapshotPreviewModel.count() > 1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                anchors.bottomMargin: 3
                height: 18
                from: 0
                to: Math.max(0, snapshotPreviewModel.count() - 1)
                stepSize: 1
                snapMode: Slider.SnapAlways
                value: previewArea.currentIndex
                onMoved: previewArea.showPreview(Math.round(value))
            }

            HoverHandler { id: previewHover }

            Connections {
                target: snapshotPreviewModel
                function onModelReset() { previewArea.showPreview(0) }
                function onContentReplaced() {
                    Qt.callLater(function() { previewArea.showPreview(0) })
                }
                function onDataChanged() {
                    Qt.callLater(function() {
                        previewArea.showPreview(previewArea.currentIndex)
                    })
                }
            }
            Component.onCompleted: showPreview(0)
        }

        Rectangle {
            id: filesPanel
            x: root.sideBySide ? previewArea.width + 8 : 0
            y: root.sideBySide ? 0 : previewArea.height + 8
            width: root.sideBySide
                ? Math.max(0, browserArea.width - x) : browserArea.width
            height: root.sideBySide
                ? browserArea.height : Math.max(0, browserArea.height - y)
            radius: 12
            color: root.theme.surfaceContainerLow
            border.color: root.theme.outline
            border.width: 1
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    spacing: 8
                    Rectangle {
                        Layout.preferredWidth: 4
                        Layout.preferredHeight: 18
                        radius: 2
                        color: root.theme.action
                    }
                    Label {
                        text: root.showMoreInfo
                            ? qsTr("Files")
                            : (root.showAllFiles
                               ? qsTr("All snapshot files")
                               : qsTr("Published files"))
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                        Layout.minimumWidth: 40
                        elide: Text.ElideRight
                    }
                    Label {
                        visible: filesPanel.width >= 240
                        text: root.displayedFileCount
                            + (root.displayedFileCount === 1
                                ? qsTr(" file") : qsTr(" files"))
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                    }
                    Label {
                        visible: root.showFileSize
                        text: qsTr("Size")
                        color: root.theme.secondaryText
                        font.pixelSize: 9
                        horizontalAlignment: Text.AlignRight
                        Layout.preferredWidth: 54
                    }
                    Label {
                        visible: root.showFilePath
                        text: qsTr("Path")
                        color: root.theme.secondaryText
                        font.pixelSize: 9
                        Layout.preferredWidth: 170
                    }
                    Label {
                        visible: root.showFileRepository
                        text: qsTr("Repo")
                        color: root.theme.secondaryText
                        font.pixelSize: 9
                        Layout.preferredWidth: 64
                    }
                    Label {
                        visible: root.showFileBaseType
                        text: qsTr("Base Type")
                        color: root.theme.secondaryText
                        font.pixelSize: 9
                        Layout.preferredWidth: 70
                        rightPadding: 7
                    }
                }

                SmoothListView {
                    id: filesView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: snapshotFileModel
                    cacheBuffer: 360
                    spacing: 0

                    delegate: Item {
                        id: fileRow
                        required property string rowType
                        required property string token
                        required property string title
                        required property string fileType
                        required property string size
                        required property string path
                        required property string repository
                        required property string baseType
                        required property int depth
                        required property bool exists
                        required property bool previewType
                        required property bool checking
                        required property bool matchesRemote
                        required property int index

                        width: filesView.width
                        visible: root.showAllFiles || (rowType === "file" && !previewType)
                        height: visible ? (rowType === "snapshot" ? 32 : 30) : 0

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 2
                            radius: 8
                            color: root.selectedFileRow === fileRow.index
                                   && fileRow.rowType === "file"
                                   ? root.theme.secondaryContainer
                                   : fileMouse.containsMouse && fileRow.rowType === "file"
                                     ? root.theme.rowHover
                                   : fileRow.rowType === "snapshot"
                                     ? root.theme.surfaceContainerHigh
                                     : (fileRow.index % 2
                                        ? root.theme.row : "transparent")
                            Behavior on color { ColorAnimation { duration: 100 } }
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10 + (root.showAllFiles ? fileRow.depth * 14 : 0)
                            anchors.rightMargin: 10
                            spacing: 8
                            clip: true
                            MaterialIcon {
                                name: root.fileIcon(
                                    fileRow.rowType,
                                    fileRow.fileType,
                                    fileRow.baseType,
                                    fileRow.title
                                )
                                size: 15
                                color: !fileRow.exists ? root.theme.red
                                    : !fileRow.matchesRemote
                                        ? root.theme.yellow : root.theme.accent
                            }
                            Label {
                                text: fileRow.title || qsTr("Unnamed file")
                                color: fileRow.exists ? root.theme.primaryText : root.theme.secondaryText
                                font.bold: fileRow.rowType !== "file"
                                font.family: root.theme.fontFamily
                                font.pixelSize: 10
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                                Layout.minimumWidth: 40
                            }
                            Label {
                                visible: root.showFileSize
                                    && fileRow.rowType === "file"
                                text: fileRow.size
                                color: root.theme.secondaryText
                                font.pixelSize: 9
                                horizontalAlignment: Text.AlignRight
                                elide: Text.ElideRight
                                Layout.preferredWidth: 54
                            }
                            Label {
                                visible: root.showFilePath
                                    && fileRow.rowType === "file"
                                text: fileRow.path
                                color: root.theme.secondaryText
                                font.pixelSize: 9
                                elide: Text.ElideMiddle
                                Layout.preferredWidth: 170
                            }
                            Label {
                                visible: root.showFileRepository
                                    && fileRow.rowType === "file"
                                text: fileRow.repository
                                color: root.theme.secondaryText
                                font.pixelSize: 9
                                elide: Text.ElideRight
                                Layout.preferredWidth: 64
                            }
                            Label {
                                visible: root.showFileBaseType
                                    && fileRow.rowType === "file"
                                text: fileRow.baseType
                                color: root.theme.secondaryText
                                font.pixelSize: 9
                                elide: Text.ElideRight
                                Layout.preferredWidth: 70
                            }
                            Item {
                                id: fileState
                                visible: fileRow.rowType === "file"
                                    && (fileRow.checking || !fileRow.exists
                                        || !fileRow.matchesRemote)
                                Layout.preferredWidth: visible ? 20 : 0
                                Layout.preferredHeight: 20
                                BusyIndicator {
                                    anchors.fill: parent
                                    visible: fileRow.checking
                                    running: visible
                                }
                                MaterialIcon {
                                    anchors.centerIn: parent
                                    visible: !fileRow.checking
                                    name: !fileRow.exists
                                        ? "cloud_download" : "warning"
                                    size: 14
                                    color: !fileRow.exists
                                        ? root.theme.red : root.theme.yellow
                                }
                                HoverHandler { id: fileStateHover }
                                Md3ToolTip {
                                    theme: root.theme
                                    visible: fileStateHover.hovered
                                        && !root.theme.suppressToolTips
                                    text: fileRow.checking
                                        ? qsTr("Checking local file")
                                        : !fileRow.exists
                                            ? qsTr("Local file is not downloaded")
                                            : qsTr("Local file differs from the server")
                                }
                            }
                        }
                        MouseArea {
                            id: fileMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: fileRow.rowType === "file"
                                ? Qt.PointingHandCursor : Qt.ArrowCursor
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onDoubleClicked: mouse => {
                                if (fileRow.rowType === "file" && mouse.button === Qt.LeftButton)
                                    appController.invoke_snapshot_file_action("open", fileRow.token)
                            }
                            onClicked: mouse => {
                                if (fileRow.rowType !== "file")
                                    return
                                root.selectedFileRow = fileRow.index
                                if (mouse.button === Qt.RightButton) {
                                    root.contextFileToken = fileRow.token
                                    fileMenu.actions = appController.snapshot_file_actions(true)
                                    fileMenu.openAt(fileRow, mouse.x, mouse.y)
                                }
                            }
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                }
            }
        }

        Item {
            id: splitterHandle
            z: 20
            x: root.sideBySide ? previewArea.width : 0
            y: root.sideBySide ? 0 : previewArea.height
            width: root.sideBySide ? 8 : browserArea.width
            height: root.sideBySide ? browserArea.height : 8

            Rectangle {
                anchors.centerIn: parent
                width: root.sideBySide
                    ? (splitMouse.containsMouse || splitMouse.pressed ? 3 : 2)
                    : Math.max(36, Math.min(72, parent.width * 0.14))
                height: root.sideBySide
                    ? Math.max(36, Math.min(72, parent.height * 0.14))
                    : (splitMouse.containsMouse || splitMouse.pressed ? 3 : 2)
                radius: 2
                color: splitMouse.pressed
                    ? root.theme.action : root.theme.outlineVariant
                Behavior on width { NumberAnimation { duration: 100 } }
                Behavior on height { NumberAnimation { duration: 100 } }
                Behavior on color { ColorAnimation { duration: 110 } }
            }
            MouseArea {
                id: splitMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: root.sideBySide
                    ? Qt.SizeHorCursor : Qt.SizeVerCursor
                onPositionChanged: mouse => {
                    if (!pressed)
                        return
                    const point = splitterHandle.mapToItem(
                        browserArea, mouse.x, mouse.y
                    )
                    const ratio = root.sideBySide
                        ? point.x / Math.max(1, browserArea.width)
                        : point.y / Math.max(1, browserArea.height)
                    appController.set_snapshot_browser_splitter_ratio(ratio)
                }
            }
        }
    }

    ActionMenu {
        id: settingsMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: appController.snapshot_browser_actions()
        onTriggered: command => {
            if (command === "show_all")
                appController.toggle_snapshot_browser_option("all")
            else if (command === "show_more")
                appController.toggle_snapshot_browser_option("more")
            else if (command === "horizontal")
                appController.set_snapshot_browser_orientation("horizontal")
            else if (command === "vertical")
                appController.set_snapshot_browser_orientation("vertical")
        }
    }

    ActionMenu {
        id: fileMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: []
        onClosed: root.contextFileToken = ""
        onTriggered: command => {
            if (root.contextFileToken !== "")
                appController.invoke_snapshot_file_action(command, root.contextFileToken)
        }
    }

    Connections {
        target: snapshotFileModel

        function onContentReplaced() {
            root.updateDisplayedFileCount()
        }
        function onRowsInserted() {
            root.updateDisplayedFileCount()
        }
        function onRowsRemoved() {
            root.updateDisplayedFileCount()
        }
        function onModelReset() {
            root.updateDisplayedFileCount()
        }
    }

    Component.onCompleted: updateDisplayedFileCount()
}
