import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.." as TH
import "../../controls" as Controls
import "../../tactic_frame/controls/catalog/variants.mjs" as Variants

Item {
    id: root
    required property var theme
    required property var example
    property var userModel: typeof userListModel === 'undefined' ? null : userListModel
    property var emojiModel: typeof emojiCatalog === 'undefined' ? null : emojiCatalog
    property string language: "en"
    property var value
    property bool disabled: false
    property bool readOnly: false
    readonly property var settings: Object.assign({
        min: 0,
        max: 100,
        step: 1,
        decimals: 0
    }, example.properties)
    readonly property real numericValue: typeof value === "number" && isFinite(value) ? value : 0
    property var presets: [
        {
            value: "blue",
            label: "Blue",
            dark: "#78a6c4",
            light: "#3d7599",
            darkBase: "#292d30",
            lightBase: "#d4dce1"
        },
        {
            value: "green",
            label: "Green",
            dark: "#77b398",
            light: "#3d8062",
            darkBase: "#26342e",
            lightBase: "#d9e9df"
        }
    ]
    signal event(var action)
    enabled: !disabled
    function change(next) {
        if (!disabled && !readOnly)
            event({
                type: "change",
                value: next
            });
    }
    Loader {
        id: loader
        anchors.fill: parent
        sourceComponent: root.componentFor(root.example.kind)
        onLoaded: item.objectName = "exampleControl"
    }
    function componentFor(kind) {
        // Direct Frame bricks can be observed while an old View is being destroyed.
        if (Variants.directKinds.indexOf(kind) >= 0)
            return null;
        if (kind === "attachment")
            return attachmentBrick;
        if (kind === "segments")
            return segmentsBrick;
        if (kind === "spin")
            return spinBrick;
        if (kind === "slider")
            return sliderBrick;
        if (kind === "search")
            return searchBrick;
        if (kind === "status")
            return statusBrick;
        if (kind === "users")
            return usersBrick;
        if (kind === "identity")
            return identityBrick;
        if (kind === "emoji")
            return emojiBrick;
        if (kind === "image")
            return imageBrick;
        if (kind === "presets")
            return presetsBrick;
        if (kind === "chip")
            return chipBrick;
        if (kind === "tab")
            return tabBrick;
        if (kind === "menu")
            return menuBrick;
        if (kind === "progress")
            return progressBrick;
        if (kind === "busy")
            return busyBrick;
        if (kind === "empty")
            return emptyBrick;
        if (kind === "drop")
            return dropBrick;
        if (kind === "markdown")
            return markdownBrick;
        if (kind === "elide")
            return elideBrick;
        if (kind === "setting")
            return settingBrick;
        if (kind === "flow")
            return flowBrick;
        if (kind === "counter")
            return counterBrick;
        if (kind === "disclosure")
            return disclosureBrick;
        if (kind === "previewNavigation")
            return previewNavigationBrick;
        if (kind === "send")
            return sendBrick;
        if (kind === "filterChip")
            return filterChipBrick;
        if (kind === "loadingOverlay")
            return loadingOverlayBrick;
        if (kind === "packedChoices")
            return packedChoicesBrick;
        if (kind === "statusChip")
            return statusChipBrick;
        if (kind === "reaction")
            return reactionBrick;
        if (kind === "editorPanel")
            return editorPanelBrick;
        if (kind === "configurationSection")
            return configurationSectionBrick;
        if (kind === "sectionLabel")
            return sectionLabelBrick;
        if (kind === "infoValues")
            return infoValuesBrick;
        if (kind === "fieldFrame")
            return fieldFrameBrick;
        if (kind === "listItem")
            return listItemBrick;
        if (kind === "userGroup")
            return userGroupBrick;
        if (kind === "profileInfo")
            return profileInfoBrick;
        throw Error("Missing catalog brick: " + kind);
    }
    Component {
        id: attachmentBrick
        TH.AttachmentCard {
            theme: root.theme
            title: "Robot Arm"
            extension: root.settings.extension
            previewUrl: root.settings.source || ""
            sizeText: "128 KB"
            compact: !!root.settings.compact
            enabled: !root.disabled && !root.readOnly
            onActivated: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: segmentsBrick
        Controls.SegmentedButton {
            theme: root.theme
            model: Variants.options(root.example)
            currentValue: String(root.value)
            outlined: !!root.settings.outlined
            iconOnly: !!root.settings.iconOnly
            minimumSegmentWidth: 40
            onActivated: value => root.change(value)
        }
    }
    Component {
        id: spinBrick
        Controls.SpinBox {
            theme: root.theme
            language: root.language
            from: root.settings.min * Math.pow(10, decimals)
            to: root.settings.max * Math.pow(10, decimals)
            stepSize: root.settings.step * Math.pow(10, decimals)
            decimals: root.settings.decimals
            value: root.numericValue * Math.pow(10, decimals)
            readOnly: root.readOnly
            Accessible.name: qsTr("Size")
            onRealValueEdited: value => root.change(value)
        }
    }
    Component {
        id: sliderBrick
        Controls.Slider {
            theme: root.theme
            from: root.settings.min
            to: root.settings.max
            stepSize: root.settings.step
            value: root.numericValue
            enabled: !root.disabled && !root.readOnly
            Accessible.name: qsTr("Size")
            onMoved: root.change(value)
        }
    }
    Component {
        id: searchBrick
        Controls.SearchField {
            theme: root.theme
            text: String(root.value)
            placeholderText: qsTr("Search")
            readOnly: root.readOnly
            clearOnEscape: false
            suggestions: root.settings.suggestions ? [
                {
                    title: "Robot Arm",
                    description: "Example",
                    code: "arm"
                },
                {
                    title: "Robot Body",
                    description: "Example",
                    code: "body"
                }
            ] : null
            suggestionsUsePopupWindow: false
            openSuggestionsInNewTab: true
            onSuggestionAccepted: (index, record) => root.change(record.title)
            onSuggestionOpened: (index, record) => root.event({
                    type: "open",
                    value: record.title
                })
            onSearchRequested: root.event({
                type: "search"
            })
            onDismissed: root.event({
                type: "dismiss"
            })
            onSearchEdited: text => root.change(text)
        }
    }
    Component {
        id: statusBrick
        Controls.ComboBox {
            theme: root.theme
            model: Variants.options(root.example)
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            actionField: true
            currentIndex: model.findIndex(option => option.value === root.value)
            onActivated: root.change(currentValue)
        }
    }
    Component {
        id: usersBrick
        TH.UserPicker {
            userModel: root.userModel
            theme: root.theme
            selectedLogins: root.value
            includeCurrent: true
            onSelectionChanged: logins => root.change(logins)
        }
    }
    Component {
        id: identityBrick
        TH.UserIdentity {
            theme: root.theme
            login: "admin"
            displayName: "Administrator"
            initials: "A"
            avatarColor: "#557f75"
            avatarUrl: ""
            retired: !!root.settings.retired
            emphasized: !!root.settings.emphasized
            avatarSize: root.settings.avatarSize || 40
        }
    }
    Component {
        id: emojiBrick
        Item {
            Controls.CompactIconButton {
                id: emojiTrigger
                theme: root.theme
                iconName: "MDI_EMOTICON_OUTLINE"
                width: 36
                height: 36
                toolTip: qsTr("Choose emoji")
                onClicked: emojiPopup.toggleBelowItem(emojiTrigger, false, 4)
            }
            TH.EmojiPicker {
                id: emojiPopup
                theme: root.theme
                catalog: root.emojiModel
                usePopupWindow: false
                onEmojiSelected: emoji => root.change(emoji)
            }
        }
    }
    Component {
        id: imageBrick
        Controls.ImagePicker {
            theme: root.theme
            previewUrl: ""
            stagedPath: String(root.value)
            fallbackText: "RA"
            onSelectionRequested: image => root.change(String(image))
        }
    }
    Component {
        id: presetsBrick
        Controls.AccentPresetPicker {
            theme: root.theme
            model: root.presets
            currentValue: String(root.value)
            darkPreview: root.theme.dark
            onActivated: value => root.change(value)
        }
    }
    Component {
        id: chipBrick
        Controls.SummaryChip {
            theme: root.theme
            label: qsTr("Status")
            count: root.numericValue
            compact: !!root.settings.compact
            clickable: !!root.settings.clickable
            onClicked: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: tabBrick
        Controls.TabButton {
            theme: root.theme
            text: qsTr("Display")
            checked: !!root.value
            onClicked: root.change(!root.value)
        }
    }
    Component {
        id: menuBrick
        Item {
            Controls.CompactIconButton {
                id: menuTrigger
                theme: root.theme
                iconName: "more"
                width: 36
                height: 36
                toolTip: qsTr("Actions")
                onClicked: menuPopup.toggleBelowItem(menuTrigger, false, 4)
            }
            TH.ActionMenu {
                id: menuPopup
                theme: root.theme
                usePopupWindow: false
                preferredWidth: 244
                actions: [
                    {
                        title: qsTr("Refresh"),
                        icon: "refresh",
                        command: "refresh"
                    },
                    {
                        title: qsTr("Enabled"),
                        command: "enabled",
                        checkable: !!root.settings.checkable,
                        checked: !!root.value
                    },
                    {
                        title: qsTr("Delete"),
                        icon: "delete",
                        command: "delete",
                        enabled: false
                    }
                ]
                onTriggered: command => command === "enabled" ? root.change(!root.value) : root.event({
                        type: command
                    })
            }
        }
    }
    Component {
        id: progressBrick
        Controls.ProgressBar {
            theme: root.theme
            from: 0
            to: 1
            value: root.value === null ? 0 : root.numericValue
            indeterminate: root.value === null
            Accessible.name: qsTr("Progress")
        }
    }
    Component {
        id: busyBrick
        Controls.BusyIndicator {
            uiTheme: root.theme
            running: !!root.value && !root.disabled
        }
    }
    Component {
        id: emptyBrick
        Controls.EmptyState {
            theme: root.theme
            error: !!root.settings.error
            iconName: root.settings.error ? "warning" : "info"
            title: root.settings.error ? qsTr("Error") : qsTr("No records yet")
            message: qsTr("Description")
            actionText: root.settings.error ? qsTr("Retry") : ""
            actionIcon: "refresh"
            onActionRequested: root.event({
                type: "retry"
            })
        }
    }
    Component {
        id: dropBrick
        Controls.DropTargetOverlay {
            theme: root.theme
            accepted: !!root.settings.accepted
            promptText: root.settings.accepted ? qsTr("Drop files here") : qsTr("Unsupported file type")
            iconName: root.settings.accepted ? "move-to-inbox" : "cancel"
            border.color: root.settings.accepted ? root.theme.action : root.theme.error
        }
    }
    Component {
        id: markdownBrick
        Controls.DocumentPane {
            theme: root.theme
            documentKey: "example"
            text: String(root.value)
            onLinkActivated: link => root.event({
                    type: "link",
                    value: link
                })
        }
    }
    Component {
        id: elideBrick
        Text {
            text: String(root.value)
            elide: Text.ElideMiddle
            verticalAlignment: Text.AlignVCenter
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: 13
        }
    }
    Component {
        id: settingBrick
        Controls.SettingsRow {
            theme: root.theme
            title: qsTr("Enabled")
            description: qsTr("Description")
            Controls.Switch {
                theme: root.theme
                checked: !!root.value
                onToggled: root.change(checked)
            }
        }
    }
    Component {
        id: flowBrick
        Controls.ResponsiveFlow {
            id: exampleFlow
            minimumCellWidth: 120
            spacing: 8
            Repeater {
                model: Variants.options(root.example)
                Controls.Button {
                    required property var modelData
                    width: exampleFlow.cellWidth()
                    theme: root.theme
                    text: modelData.label
                    onClicked: root.change(modelData.value)
                }
            }
        }
    }
    Component {
        id: counterBrick
        Controls.ItemCountActionButton {
            theme: root.theme
            iconName: "comment"
            count: root.numericValue
            toolTip: qsTr("Notes")
            onClicked: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: disclosureBrick
        Controls.DisclosureButton {
            theme: root.theme
            identity: "sample"
            hasChildren: true
            expanded: !!root.value
            onActivated: root.change(!root.value)
        }
    }
    Component {
        id: previewNavigationBrick
        Controls.PreviewNavigationButton {
            theme: root.theme
            iconName: "chevron-right"
            toolTip: qsTr("Next")
            onClicked: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: sendBrick
        TH.MessageSendButton {
            theme: root.theme
            sending: !!root.value
            hasContent: true
            onClicked: root.change(true)
        }
    }

    Component {
        id: statusChipBrick
        Controls.StatusChip {
            theme: root.theme
            text: String(root.value)
            iconName: "check"
            accentColor: "#55a9ad"
            dense: !!root.settings.dense
            interactive: !!root.settings.interactive
            onClicked: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: reactionBrick
        TH.MessageReactionChip {
            theme: root.theme
            emoji: "👍"
            count: root.settings.count || 1
            checked: !!root.value
            onClicked: root.change(!root.value)
        }
    }
    Component {
        id: userGroupBrick
        TH.UserGroupSection {
            theme: root.theme
            title: String(root.value)
            compact: !!root.settings.compact
        }
    }
    Component {
        id: profileInfoBrick
        Controls.ProfileInfoRow {
            theme: root.theme
            iconName: "person"
            label: qsTr("Name")
            value: String(root.value)
        }
    }
    Component {
        id: sectionLabelBrick
        Controls.SectionLabel {
            theme: root.theme
            text: qsTr("Display")
        }
    }
    Component {
        id: infoValuesBrick
        Controls.InfoValueStrip {
            theme: root.theme
            items: root.settings.items || []
        }
    }
    Component {
        id: editorPanelBrick
        Controls.EditorPanel {
            theme: root.theme
            title: qsTr("Name")
            description: qsTr("Description")
            iconName: "settings"
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.theme.surfaceContainerHigh
                Label {
                    anchors.centerIn: parent
                    text: "Example"
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.hintingPreference: Font.PreferVerticalHinting
                    color: root.theme.primaryText
                }
            }
        }
    }
    Component {
        id: configurationSectionBrick
        TH.ConfigurationSection {
            theme: root.theme
            title: qsTr("Name")
            description: qsTr("Description")
            fillContentHeight: true
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.theme.surfaceContainerHigh
                Label {
                    anchors.centerIn: parent
                    text: "Example"
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.hintingPreference: Font.PreferVerticalHinting
                    color: root.theme.primaryText
                }
            }
        }
    }
    Component {
        id: listItemBrick
        Controls.EditorListItem {
            theme: root.theme
            text: String(root.value)
            description: qsTr("Description")
            iconName: "folder"
            selected: !!root.settings.selected
            wrapTitle: !!root.settings.wrapTitle
            badgeText: root.settings.badge ? "4" : ""
            onClicked: root.event({
                type: "activate"
            })
        }
    }
    Component {
        id: fieldFrameBrick
        TH.SObjectFieldFrame {
            theme: root.theme
            title: qsTr("Name")
            fieldName: "name"
            description: qsTr("Description")
            iconName: "edit"
            errorText: root.settings.error ? qsTr("Invalid value") : ""
            requiredField: !!root.settings.required
            readOnlyField: root.readOnly || !!root.settings.readOnly
            Controls.TextField {
                theme: root.theme
                width: parent.width
                text: String(root.value)
                readOnly: root.readOnly || !!root.settings.readOnly
                errorState: !!root.settings.error
                Accessible.name: qsTr("Name")
                onTextEdited: root.change(text)
            }
        }
    }

    Component {
        id: filterChipBrick
        TH.QuickFilterChip {
            theme: root.theme
            text: "Example"
            iconName: "filter"
            checked: !!root.value
            subtle: !!root.settings.subtle
            showAccentMarker: !!root.settings.marker
            emphasis: root.settings.emphasis || 0
            onClicked: root.change(!root.value)
        }
    }
    Component {
        id: loadingOverlayBrick
        TH.ContentLoadingOverlay {
            theme: root.theme
            message: qsTr("Loading…")
            cancellable: !!root.settings.cancellable
            onCancelRequested: root.event({
                type: "cancel"
            })
        }
    }

    Component {
        id: packedChoicesBrick
        Flickable {
            id: optionsViewport
            contentWidth: width
            contentHeight: packedChoices.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            TH.QuickFilterOptions {
                id: packedChoices
                width: optionsViewport.width - optionsScroll.reservedExtent
                theme: root.theme
                options: Variants.packedOptions(root.value).map(option => Object.assign({}, option, {
                        iconName: option.icon,
                        showAccentMarker: option.marker
                    }))
                viewport: optionsViewport
                contentTop: 0
                presentationActive: true
                viewportReady: true
                sizingChip: packedSizing
                onActivated: index => root.change(String(index))
            }
            TH.QuickFilterChip {
                id: packedSizing
                theme: root.theme
                visible: false
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: optionsScroll
                theme: root.theme
            }
        }
    }
}
