import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property bool managed: true
    property bool loadingValues: true
    property var repositoryRecords: []
    property string sequenceNamingValue: ""

    component OptionCheck: Md3CheckBox {
        theme: root.theme
        Layout.fillWidth: true
        onToggled: root.updateValues()
    }

    function formValues() {
        return {
            "previewsThroughHttp": previewsHttp.checked,
            "doubleClickSave": doubleClickSave.checked,
            "doubleClickOpen": doubleClickOpen.checked,
            "showBuiltinProcesses": builtinProcesses.checked,
            "versionsSeparate": versionsSeparate.checked,
            "descriptionLimitEnabled": descriptionLimitEnabled.checked,
            "descriptionLimit": descriptionLimit.value,
            "displayLimit": displayLimit.value,
            "defaultViewMode": defaultViewMode.currentIndex,
            "versionsRight": versionsPosition.currentIndex === 0,
            "versionsBottom": versionsPosition.currentIndex === 1,
            "repositoryIndex": repository.currentIndex,
            "repositories": repositoryRecords,
            "checkinMethod": checkinMethod.currentIndex,
            "checkoutMethod": checkoutMethod.currentIndex,
            "updateVersionless": updateVersionless.checked,
            "generatePreviews": generatePreviews.checked,
            "createMayaDirs": createMayaDirs.checked,
            "createPlayblast": createPlayblast.checked,
            "confirmSaving": confirmSaving.checked,
            "confirmRevision": confirmRevision.checked,
            "sequencePaddingEnabled": sequencePaddingEnabled.checked,
            "sequencePadding": sequencePadding.value,
            "sequenceNaming": root.sequenceNamingValue,
            "syncDropPlate": syncDropPlate.checked,
            "uncheckDropPlate": uncheckDropPlate.checked,
            "clearDropPlate": clearDropPlate.checked,
            "groupCheckin": groupCheckin.checked,
            "keepFilename": keepFilename.checked,
            "includeSubfolders": includeSubfolders.checked,
            "allowSingleUdim": allowSingleUdim.checked,
            "allowSingleFrame": allowSingleFrame.checked,
            "minimumFramePadding": minimumFramePadding.value
        }
    }

    function loadValues(values) {
        loadingValues = true
        previewsHttp.checked = Boolean(values.previewsThroughHttp)
        doubleClickSave.checked = Boolean(values.doubleClickSave)
        doubleClickOpen.checked = Boolean(values.doubleClickOpen)
        builtinProcesses.checked = Boolean(values.showBuiltinProcesses)
        versionsSeparate.checked = Boolean(values.versionsSeparate)
        descriptionLimitEnabled.checked = Boolean(values.descriptionLimitEnabled)
        descriptionLimit.value = Number(values.descriptionLimit || 80)
        displayLimit.value = Number(values.displayLimit || 20)
        defaultViewMode.currentIndex = Number(values.defaultViewMode || 0)
        versionsPosition.currentIndex = values.versionsBottom ? 1 : 0
        repositoryRecords = values.repositories || []
        repository.currentIndex = values.repositoryIndex === undefined
            ? -1 : Number(values.repositoryIndex)
        checkinMethod.currentIndex = Number(values.checkinMethod || 0)
        checkoutMethod.currentIndex = Number(values.checkoutMethod || 0)
        updateVersionless.checked = Boolean(values.updateVersionless)
        generatePreviews.checked = Boolean(values.generatePreviews)
        createMayaDirs.checked = Boolean(values.createMayaDirs)
        createPlayblast.checked = Boolean(values.createPlayblast)
        confirmSaving.checked = Boolean(values.confirmSaving)
        confirmRevision.checked = Boolean(values.confirmRevision)
        sequencePaddingEnabled.checked = Boolean(values.sequencePaddingEnabled)
        sequencePadding.value = Number(values.sequencePadding || 3)
        sequenceNamingValue = values.sequenceNaming || ""
        syncDropPlate.checked = Boolean(values.syncDropPlate)
        uncheckDropPlate.checked = Boolean(values.uncheckDropPlate)
        clearDropPlate.checked = Boolean(values.clearDropPlate)
        groupCheckin.checked = Boolean(values.groupCheckin)
        keepFilename.checked = Boolean(values.keepFilename)
        includeSubfolders.checked = Boolean(values.includeSubfolders)
        allowSingleUdim.checked = Boolean(values.allowSingleUdim)
        allowSingleFrame.checked = Boolean(values.allowSingleFrame)
        minimumFramePadding.value = Number(values.minimumFramePadding || 3)
        loadingValues = false
    }

    function syncValues() {
        loadValues(configurationController.page_values("checkin_preferences"))
    }

    function updateValues() {
        if (managed && !loadingValues)
            configurationController.update_page(
                "checkin_preferences", formValues()
            )
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController
        function onSessionStarted() { root.syncValues() }
        function onPageReset(pageId) {
            if (pageId === "checkin_preferences")
                root.syncValues()
        }
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: optionsColumn.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: scroll
        }

        ColumnLayout {
            id: optionsColumn
            x: 22
            y: 20
            width: Math.max(0, scroll.availableWidth - 44)
            spacing: 14

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Search results")
                description: qsTr("Preview, double-click and result display behaviour.")
                iconName: "search"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 4

                    OptionCheck { id: previewsHttp; text: qsTr("Get previews through HTTP") }
                    OptionCheck { id: builtinProcesses; text: qsTr("Show builtin processes") }
                    OptionCheck { id: doubleClickSave; text: qsTr("Double-click to save") }
                    OptionCheck { id: doubleClickOpen; text: qsTr("Shift + double-click to open") }
                    OptionCheck { id: versionsSeparate; text: qsTr("Display versions separately") }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Versions position")
                            color: root.theme.secondaryText
                            font.pixelSize: 10
                        }
                        Md3ComboBox {
                            id: versionsPosition
                            Layout.fillWidth: true
                            theme: root.theme
                            model: ["Right", "Bottom"]
                            onActivated: root.updateValues()
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        OptionCheck {
                            id: descriptionLimitEnabled
                            text: qsTr("Description limit")
                            Layout.fillWidth: true
                        }
                        Md3SpinBox {
                            id: descriptionLimit
                            theme: root.theme
                            from: 20
                            to: 50000
                            stepSize: 5
                            enabled: descriptionLimitEnabled.checked
                            onValueChanged: root.updateValues()
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Search results limit")
                            color: root.theme.secondaryText
                            font.pixelSize: 10
                        }
                        Md3SpinBox {
                            id: displayLimit
                            theme: root.theme
                            from: 20
                            to: 5000
                            stepSize: 5
                            onValueChanged: root.updateValues()
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Default view")
                            color: root.theme.secondaryText
                            font.pixelSize: 10
                        }
                        Md3ComboBox {
                            id: defaultViewMode
                            Layout.preferredWidth: 150
                            theme: root.theme
                            model: ["Continuous", "Cards"]
                            onActivated: root.updateValues()
                        }
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Snapshots and files")
                description: qsTr("Repository, transfer method, naming and confirmation options.")
                iconName: "cloud-upload-alt"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 14
                    rowSpacing: 8

                    Label { text: qsTr("Current repository"); color: root.theme.secondaryText; font.pixelSize: 10 }
                    RowLayout {
                        Layout.fillWidth: true
                        Md3ComboBox {
                            id: repository
                            Layout.fillWidth: true
                            theme: root.theme
                            model: root.repositoryRecords
                            textRole: "title"
                            onActivated: root.updateValues()
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Repositories")
                            icon.name: "database"
                            onClicked: windowModel.show_window("repository_editor")
                        }
                    }
                    Label { text: qsTr("Check-in method"); color: root.theme.secondaryText; font.pixelSize: 10 }
                    Md3ComboBox {
                        id: checkinMethod
                        Layout.fillWidth: true
                        theme: root.theme
                        model: ["Preallocate", "In-Place", "Copy", "Move", "Upload"]
                        onActivated: root.updateValues()
                    }
                    Label { text: qsTr("Check-out method"); color: root.theme.secondaryText; font.pixelSize: 10 }
                    Md3ComboBox {
                        id: checkoutMethod
                        Layout.fillWidth: true
                        theme: root.theme
                        model: ["Local", "HTTP"]
                        onActivated: root.updateValues()
                    }
                    OptionCheck { id: updateVersionless; text: qsTr("Update versionless snapshot") }
                    OptionCheck { id: generatePreviews; text: qsTr("Generate previews") }
                    OptionCheck { id: createMayaDirs; text: qsTr("Create Maya directories") }
                    OptionCheck { id: createPlayblast; text: qsTr("Create screenshot (playblast)") }
                    OptionCheck { id: confirmSaving; text: qsTr("Confirm saving") }
                    OptionCheck { id: confirmRevision; text: qsTr("Confirm revision saving") }
                    RowLayout {
                        Layout.fillWidth: true
                        OptionCheck {
                            id: sequencePaddingEnabled
                            text: qsTr("Sequence padding")
                            Layout.fillWidth: true
                        }
                        Md3SpinBox {
                            id: sequencePadding
                            theme: root.theme
                            from: 1
                            to: 9
                            enabled: sequencePaddingEnabled.checked
                            onValueChanged: root.updateValues()
                        }
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Drop Plate")
                description: qsTr("Sequence detection and post-check-in behaviour.")
                iconName: "inbox"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 4

                    OptionCheck { id: syncDropPlate; text: qsTr("Sync Drop Plate to all tabs") }
                    OptionCheck { id: uncheckDropPlate; text: qsTr("Uncheck From Drop Plate after check-in") }
                    OptionCheck { id: clearDropPlate; text: qsTr("Clear Drop Plate after check-in") }
                    OptionCheck { id: groupCheckin; text: qsTr("Group selected files into one snapshot") }
                    OptionCheck { id: keepFilename; text: qsTr("Keep original filename") }
                    OptionCheck { id: includeSubfolders; text: qsTr("Include subfolders when adding directories") }
                    OptionCheck { id: allowSingleUdim; text: qsTr("Allow single UDIM/UV") }
                    OptionCheck { id: allowSingleFrame; text: qsTr("Allow single-frame sequence") }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Minimum frame padding")
                            color: root.theme.secondaryText
                            font.pixelSize: 10
                        }
                        Md3SpinBox {
                            id: minimumFramePadding
                            theme: root.theme
                            from: 1
                            to: 9
                            onValueChanged: root.updateValues()
                        }
                    }
                    Md3Button {
                        Layout.columnSpan: 2
                        theme: root.theme
                        text: qsTr("Matching Templates")
                        icon.name: "project-diagram"
                        onClicked: windowModel.show_window("matching_templates")
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Repository paths")
                description: repositoryEditorController.current_path.length
                    ? repositoryEditorController.current_path
                    : "No active repository path is configured."
                iconName: "folder-open"

                RowLayout {
                    Layout.fillWidth: true
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Open Repository Editor")
                        icon.name: "database"
                        onClicked: windowModel.show_window("repository_editor")
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Check paths")
                        flat: true
                        icon.name: "check-circle"
                        onClicked: repositoryEditorController.check_paths()
                    }
                    Item { Layout.fillWidth: true }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}
