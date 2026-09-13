import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool managed: true
    property bool loadingValues: true
    property string sequenceNamingValue: ""

    component OptionSwitch: Controls.Switch {
        theme: root.theme
        text: ""
        onToggled: root.updateValues()
    }

    function formValues() {
        return {
            "previewsThroughHttp": previewsHttp.checked,
            "verifyRepositoryMd5": verifyRepositoryMd5.checked,
            "autoCleanRepositorySync": autoCleanRepositorySync.checked,
            "repositorySyncScopeMode": repositorySyncScopeMode.currentIndex,
            "repositorySyncPartialChunkSize": repositorySyncPartialChunkSize.value,
            "doubleClickSave": doubleClickSave.checked,
            "doubleClickOpen": doubleClickOpen.checked,
            "showBuiltinProcesses": builtinProcesses.checked,
            "versionsSeparate": versionsSeparate.checked,
            "descriptionLimitEnabled": descriptionLimitEnabled.checked,
            "descriptionLimit": descriptionLimit.value,
            "displayLimit": displayLimit.value,
            "defaultViewMode": defaultViewMode.currentIndex,
            "loadingMode": loadingMode.currentIndex === 1
                ? "infinite" : "pages",
            "snapshotShowAll": snapshotShowAll.checked,
            "snapshotShowMore": snapshotShowMore.checked,
            "snapshotContentMode": ["both", "preview", "files"][
                snapshotContentMode.currentIndex
            ],
            "snapshotOrientation": snapshotOrientation.currentIndex === 1
                ? "vertical" : "horizontal",
            "commitQueueAutoClean": commitQueueAutoClean.checked,
            "versionsRight": versionsPosition.currentIndex === 0,
            "versionsBottom": versionsPosition.currentIndex === 1,
            "checkinMethod": checkinMethod.currentIndex,
            "checkoutMethod": checkoutMethod.currentIndex,
            "updateVersionless": updateVersionless.checked,
            "generatePreviews": generatePreviews.checked,
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
        verifyRepositoryMd5.checked = Boolean(values.verifyRepositoryMd5)
        autoCleanRepositorySync.checked = Boolean(values.autoCleanRepositorySync)
        repositorySyncScopeMode.currentIndex = Math.max(0,
            Math.min(1, Number(values.repositorySyncScopeMode || 0)))
        repositorySyncPartialChunkSize.value = Math.max(1,
            Number(values.repositorySyncPartialChunkSize || 10))
        doubleClickSave.checked = Boolean(values.doubleClickSave)
        doubleClickOpen.checked = Boolean(values.doubleClickOpen)
        builtinProcesses.checked = Boolean(values.showBuiltinProcesses)
        versionsSeparate.checked = Boolean(values.versionsSeparate)
        descriptionLimitEnabled.checked = Boolean(values.descriptionLimitEnabled)
        descriptionLimit.value = Number(values.descriptionLimit || 80)
        displayLimit.value = Number(values.displayLimit || 20)
        defaultViewMode.currentIndex = Number(values.defaultViewMode || 0)
        loadingMode.currentIndex = values.loadingMode === "infinite" ? 1 : 0
        snapshotShowAll.checked = Boolean(values.snapshotShowAll)
        snapshotShowMore.checked = Boolean(values.snapshotShowMore)
        snapshotContentMode.currentIndex = values.snapshotContentMode
                === "preview" ? 1
            : values.snapshotContentMode === "files" ? 2 : 0
        snapshotOrientation.currentIndex = values.snapshotOrientation
                === "vertical" ? 1 : 0
        commitQueueAutoClean.checked = Boolean(values.commitQueueAutoClean)
        versionsPosition.currentIndex = values.versionsBottom ? 1 : 0
        checkinMethod.currentIndex = Number(values.checkinMethod || 0)
        checkoutMethod.currentIndex = Number(values.checkoutMethod || 0)
        updateVersionless.checked = Boolean(values.updateVersionless)
        generatePreviews.checked = Boolean(values.generatePreviews)
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
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: scroll
        }

        ColumnLayout {
            id: optionsColumn
            x: 22
            y: 20
            width: Math.max(0, scroll.availableWidth - 44)
            spacing: 22

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Search results")
                description: qsTr("Choose how result items are loaded and initially presented.")
                iconName: "search"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Preview delivery")
                    description: qsTr("Load preview files through the TACTIC HTTP endpoint instead of relying only on repository access.")
                    OptionSwitch { id: previewsHttp }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Built-in processes")
                    description: qsTr("Include TACTIC built-in processes together with project-defined processes in result items.")
                    OptionSwitch { id: builtinProcesses }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Result limit")
                    description: qsTr("Maximum number of sObjects requested for one search result page.")
                    Controls.SpinBox {
                        id: displayLimit
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 20
                        to: 5000
                        stepSize: 5
                        onValueChanged: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Loading mode")
                    description: qsTr("Use explicit result pages or load the next page when scrolling reaches the end.")
                    Controls.ComboBox {
                        id: loadingMode
                        Layout.preferredWidth: 170
                        theme: root.theme
                        model: [qsTr("Pages"), qsTr("Continuous")]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Default result view")
                    description: qsTr("Initial presentation used when a search tab has no saved view state.")
                    showDivider: false
                    Controls.ComboBox {
                        id: defaultViewMode
                        Layout.preferredWidth: 170
                        theme: root.theme
                        model: [qsTr("Continuous"), qsTr("Cards")]
                        onActivated: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Item interactions")
                description: qsTr("Define the actions performed by double-click gestures on result items.")
                iconName: "mouse"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Double-click to save")
                    description: qsTr("A regular double-click downloads or saves the selected snapshot using the configured checkout behaviour.")
                    OptionSwitch { id: doubleClickSave }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Shift + double-click to open")
                    description: qsTr("Holding Shift while double-clicking opens the selected file in its associated application.")
                    showDivider: false
                    OptionSwitch { id: doubleClickOpen }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Versions and descriptions")
                description: qsTr("Control version placement and the amount of descriptive text shown on result items.")
                iconName: "history"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Separate versions")
                    description: qsTr("Display snapshot versions in a dedicated area instead of mixing them with the main item content.")
                    OptionSwitch { id: versionsSeparate }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Versions position")
                    description: qsTr("Choose where the separate version area appears relative to the result item.")
                    Controls.ComboBox {
                        id: versionsPosition
                        Layout.preferredWidth: 150
                        theme: root.theme
                        model: [qsTr("Right"), qsTr("Bottom")]
                        enabled: versionsSeparate.checked
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Description length")
                    description: qsTr("Limit long sObject descriptions in results. Disable the switch to show the complete text.")
                    showDivider: false
                    OptionSwitch { id: descriptionLimitEnabled }
                    Controls.SpinBox {
                        id: descriptionLimit
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 20
                        to: 50000
                        stepSize: 5
                        enabled: descriptionLimitEnabled.checked
                        onValueChanged: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Snapshot Browser defaults")
                description: qsTr("Choose the initial content and layout used by Snapshot Browser.")
                iconName: "photo_library"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Show every snapshot")
                    description: qsTr("Include snapshots from every process instead of only the selected process.")
                    OptionSwitch { id: snapshotShowAll }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Show more metadata")
                    description: qsTr("Expand the additional snapshot metadata by default.")
                    OptionSwitch { id: snapshotShowMore }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial content")
                    description: qsTr("Show preview and files together, preview only, or files only.")
                    Controls.ComboBox {
                        id: snapshotContentMode
                        Layout.preferredWidth: 190
                        theme: root.theme
                        model: [
                            qsTr("Preview and files"),
                            qsTr("Preview only"),
                            qsTr("Files only")
                        ]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial orientation")
                    description: qsTr("Arrange preview and file content side by side or from top to bottom.")
                    showDivider: false
                    Controls.ComboBox {
                        id: snapshotOrientation
                        Layout.preferredWidth: 170
                        theme: root.theme
                        model: [qsTr("Horizontal"), qsTr("Vertical")]
                        onActivated: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("File transfer")
                description: qsTr("Choose how files move between TACTIC and the workstation.")
                iconName: "database"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Check-in method")
                    description: qsTr("Choose whether new files are preallocated, kept in place, copied, moved, or uploaded.")
                    Controls.ComboBox {
                        id: checkinMethod
                        Layout.preferredWidth: 190
                        theme: root.theme
                        model: [qsTr("Preallocate"), qsTr("In-Place"), qsTr("Copy"), qsTr("Move"), qsTr("Upload")]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Check-out method")
                    description: qsTr("Use direct local repository access or download files through the TACTIC HTTP endpoint.")
                    showDivider: false
                    Controls.ComboBox {
                        id: checkoutMethod
                        Layout.preferredWidth: 190
                        theme: root.theme
                        model: [qsTr("Local"), qsTr("HTTP")]
                        onActivated: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Snapshot creation")
                description: qsTr("Defaults applied while preparing new snapshots and DCC output files.")
                iconName: "cloud-upload-alt"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Update versionless snapshot")
                    description: qsTr("Refresh the versionless snapshot whenever a new numbered version is checked in.")
                    OptionSwitch { id: updateVersionless }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Generate previews")
                    description: qsTr("Create supported thumbnail and preview files as part of the check-in preparation.")
                    OptionSwitch { id: generatePreviews }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Clean completed Commit Queue items")
                    description: qsTr("Remove successful operations from Commit Queue automatically.")
                    OptionSwitch { id: commitQueueAutoClean }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Confirm saving")
                    description: qsTr("Ask for confirmation before saving a prepared check-in operation.")
                    OptionSwitch { id: confirmSaving }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Confirm revision saving")
                    description: qsTr("Ask separately before saving a revision instead of a new version.")
                    OptionSwitch { id: confirmRevision }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Sequence padding")
                    description: qsTr("Enable a fixed number of digits when sequence frame numbers are generated.")
                    showDivider: false
                    OptionSwitch { id: sequencePaddingEnabled }
                    Controls.SpinBox {
                        id: sequencePadding
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 1
                        to: 9
                        enabled: sequencePaddingEnabled.checked
                        onValueChanged: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Repository synchronization")
                description: qsTr("Control repository discovery, validation, and completed transfer cleanup.")
                iconName: "repository-sync"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Verify files with MD5")
                    description: qsTr("Compare checksums to detect changed local files. Enable only when stronger validation is worth the additional CPU work.")
                    OptionSwitch { id: verifyRepositoryMd5 }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Clean completed downloads")
                    description: qsTr("Remove completed Repository Sync rows automatically after each successful download batch.")
                    OptionSwitch { id: autoCleanRepositorySync }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Discovery mode")
                    description: qsTr("Full scope discovers every file before downloading; partial scope overlaps discovery and transfer in chunks.")
                    Controls.ComboBox {
                        id: repositorySyncScopeMode
                        Layout.preferredWidth: 170
                        theme: root.theme
                        model: [qsTr("Full scope"), qsTr("Partial scope")]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Partial scope chunk size")
                    description: qsTr("Number of repository records discovered per chunk while partial scope mode is active.")
                    showDivider: false
                    enabled: repositorySyncScopeMode.currentIndex === 1
                    Controls.SpinBox {
                        id: repositorySyncPartialChunkSize
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 1
                        to: 250
                        stepSize: 1
                        onValueChanged: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Drop Plate completion")
                description: qsTr("Choose what happens to Drop Plate state after a successful check-in.")
                iconName: "inbox"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Share Drop Plate across tabs")
                    description: qsTr("Use one Drop Plate selection for every compatible search tab.")
                    OptionSwitch { id: syncDropPlate }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Uncheck submitted files")
                    description: qsTr("Keep submitted files in Drop Plate but clear their checked state after check-in.")
                    OptionSwitch { id: uncheckDropPlate }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Clear submitted files")
                    description: qsTr("Remove successfully submitted files from Drop Plate after check-in.")
                    showDivider: false
                    OptionSwitch { id: clearDropPlate }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("File matching and naming")
                description: qsTr("Define how dropped directories, sequences, UDIM sets, and snapshot filenames are recognized.")
                iconName: "rule"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Group selected files")
                    description: qsTr("Combine the selected files into one snapshot instead of preparing a snapshot for each file.")
                    OptionSwitch { id: groupCheckin }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Keep original filename")
                    description: qsTr("Preserve source filenames instead of applying the active naming template.")
                    OptionSwitch { id: keepFilename }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Include subfolders")
                    description: qsTr("Scan nested folders when a directory is added to Drop Plate.")
                    OptionSwitch { id: includeSubfolders }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Allow a single UDIM or UV tile")
                    description: qsTr("Recognize one matching tile as a valid UDIM or UV set instead of requiring multiple tiles.")
                    OptionSwitch { id: allowSingleUdim }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Allow a single-frame sequence")
                    description: qsTr("Recognize one numbered file as a sequence when its padding matches the configured rules.")
                    OptionSwitch { id: allowSingleFrame }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Minimum frame padding")
                    description: qsTr("Smallest number of frame digits accepted by automatic sequence detection.")
                    Controls.SpinBox {
                        id: minimumFramePadding
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 1
                        to: 9
                        onValueChanged: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Matching templates")
                    description: qsTr("Edit the templates used to associate dropped files with check-in contexts.")
                    showDivider: false
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Open")
                        icon.name: "project-diagram"
                        onClicked: windowModel.show_window("matching_templates")
                    }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}
