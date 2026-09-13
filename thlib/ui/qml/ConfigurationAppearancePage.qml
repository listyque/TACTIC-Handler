import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool managed: false
    property bool loadingValues: true
    property var themeAccentValues: ({})
    readonly property var renderBackendOptions: [
        {
            "value": "automatic",
            "label": qsTr("Automatic (recommended)"),
            "description": qsTr("Uses the stable OpenGL backend on Windows and the native Qt default on other systems.")
        },
        {
            "value": "opengl",
            "label": qsTr("OpenGL"),
            "description": qsTr("GPU rendering without the Windows DXGI/MPO presentation path that can cause full-display flicker.")
        },
        {
            "value": "d3d11",
            "label": qsTr("Direct3D 11"),
            "description": qsTr("Native Windows backend. On some MPO or HDR configurations it can make the whole display flicker during UI updates.")
        },
        {
            "value": "d3d12",
            "label": qsTr("Direct3D 12"),
            "description": qsTr("Modern native Windows backend. Requires compatible graphics drivers.")
        },
        {
            "value": "vulkan",
            "label": qsTr("Vulkan"),
            "description": qsTr("Cross-platform GPU backend. Requires a working Vulkan driver.")
        },
        {
            "value": "software",
            "label": qsTr("Software"),
            "description": qsTr("CPU rendering for troubleshooting. It avoids graphics-driver issues but is noticeably slower.")
        }
    ]

    function formValues() {
        return {
            "darkTheme": darkTheme.checked,
            "themeStyle": themeStyle.currentValue || "md3",
            "themeAccents": themeAccentValues,
            "iconSet": iconSet.currentValue || "material-design",
            "clickAnimations": clickAnimations.checked,
            "hoverAnimations": hoverAnimations.checked,
            "fadeAnimations": fadeAnimations.checked,
            "popupAnimations": popupAnimations.checked,
            "renderBackend": renderBackend.currentValue || "automatic",
            "language": interfaceLanguage.currentValue || "en"
        }
    }

    function syncValues() {
        const values = configurationController.page_values(
            "appearance"
        )
        loadingValues = true
        darkTheme.checked = Boolean(values.darkTheme)
        const selectedTheme = values.themeStyle || "md3"
        for (let row = 0; row < themeStyle.count; ++row) {
            if (themeStyle.model[row].value === selectedTheme) {
                themeStyle.currentIndex = row
                break
            }
        }
        themeAccentValues = values.themeAccents
            || appController.theme_accents
        syncAccentPickers()
        const selectedIconSet = values.iconSet || "material-design"
        for (let row = 0; row < iconSet.count; ++row) {
            if (iconSet.model[row].value === selectedIconSet) {
                iconSet.currentIndex = row
                break
            }
        }
        clickAnimations.checked = values.clickAnimations === undefined
            ? true : Boolean(values.clickAnimations)
        hoverAnimations.checked = values.hoverAnimations === undefined
            ? true : Boolean(values.hoverAnimations)
        fadeAnimations.checked = values.fadeAnimations === undefined
            ? true : Boolean(values.fadeAnimations)
        popupAnimations.checked = values.popupAnimations === undefined
            ? fadeAnimations.checked : Boolean(values.popupAnimations)
        const selectedRenderBackend = values.renderBackend || "automatic"
        for (let row = 0; row < renderBackend.count; ++row) {
            if (renderBackend.model[row].value
                    === selectedRenderBackend) {
                renderBackend.currentIndex = row
                break
            }
        }
        const selectedLanguage = values.language || "en"
        for (let row = 0; row < interfaceLanguage.count; ++row) {
            if (interfaceLanguage.model[row].value
                    === selectedLanguage) {
                interfaceLanguage.currentIndex = row
                break
            }
        }
        loadingValues = false
    }

    function currentStyleId() {
        return themeStyle.currentValue || "md3"
    }

    function accentFor(mode) {
        const styleValues = themeAccentValues[currentStyleId()]
            || ({})
        return String(styleValues[mode] || "steel")
    }

    function syncAccentPickers() {
        lightAccent.currentValue = accentFor("light")
        darkAccent.currentValue = accentFor("dark")
    }

    function setAccent(mode, value) {
        const values = Object.assign({}, themeAccentValues)
        const style = currentStyleId()
        const styleValues = Object.assign({}, values[style] || ({}))
        styleValues[mode] = String(value || "steel")
        values[style] = styleValues
        themeAccentValues = values
        syncAccentPickers()
        updateValues()
    }

    function updateValues() {
        if (!root.managed || loadingValues)
            return
        configurationController.update_page(
            "appearance", formValues()
        )
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController

        function onSessionStarted() {
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === "appearance")
                root.syncValues()
        }
    }

    ScrollView {
        id: appearanceScroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: appearanceContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: appearanceScroll
        }

        ColumnLayout {
            id: appearanceContent
            x: 22
            y: 20
            width: Math.max(0, appearanceScroll.availableWidth - 44)
            spacing: 14

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Appearance")
                description: qsTr("Choose the interface style, color mode, palettes, and semantic icon set.")
                iconName: "palette"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Dark color mode")
                    description: qsTr("Use dark surfaces and the dark palette assigned to the selected interface style.")
                    Controls.Switch {
                        theme: root.theme
                        id: darkTheme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Interface style")
                    description: themeStyle.currentIndex >= 0
                        ? qsTr(themeStyle.model[themeStyle.currentIndex].description)
                        : qsTr("Select the component style used throughout the application.")
                    Controls.ComboBox {
                        id: themeStyle
                        theme: root.theme
                        Layout.preferredWidth: 240
                        model: appController.theme_options
                        textRole: "label"
                        valueRole: "value"
                        onActivated: {
                            root.syncAccentPickers()
                            root.updateValues()
                        }
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Light mode palette")
                    description: qsTr("Base surface and accent used when the application is in light mode.")
                    Controls.AccentPresetPicker {
                        id: lightAccent
                        Layout.preferredWidth: Math.min(380, appearanceContent.width * 0.48)
                        theme: root.theme
                        model: appController.accent_presets
                        darkPreview: false
                        onActivated: function(value) {
                            root.setAccent("light", value)
                        }
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Dark mode palette")
                    description: qsTr("Base surface and accent used when the application is in dark mode.")
                    Controls.AccentPresetPicker {
                        id: darkAccent
                        Layout.preferredWidth: Math.min(380, appearanceContent.width * 0.48)
                        theme: root.theme
                        model: appController.accent_presets
                        darkPreview: true
                        onActivated: function(value) {
                            root.setAccent("dark", value)
                        }
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Icon set")
                    description: iconSet.currentIndex >= 0
                        ? qsTr(iconSet.model[iconSet.currentIndex].description)
                        : qsTr("Select the bundled icon vocabulary used by application actions.")
                    Controls.ComboBox {
                        id: iconSet
                        theme: root.theme
                        Layout.preferredWidth: 240
                        model: appController.icon_set_options
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Click animations")
                    description: qsTr("Animate press feedback, ripples, switches, and disclosure controls.")
                    Controls.Switch {
                        id: clickAnimations
                        objectName: "clickAnimationsSwitch"
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Hover animations")
                    description: qsTr("Animate pointer hover feedback while keeping the same hover states available instantly when disabled.")
                    Controls.Switch {
                        id: hoverAnimations
                        objectName: "hoverAnimationsSwitch"
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Fades and transitions")
                    description: qsTr("Animate appearing content, view transitions, expansion, and other interface fades.")
                    Controls.Switch {
                        id: fadeAnimations
                        objectName: "fadeAnimationsSwitch"
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Menu and popup animations")
                    description: qsTr("Animate opening and closing menus, dropdowns, popups, and tooltips. Disable for instant appearance and dismissal.")
                    showDivider: false
                    Controls.Switch {
                        id: popupAnimations
                        objectName: "popupAnimationsSwitch"
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Language")
                description: qsTr("Choose the language used by the application interface.")
                iconName: "language"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Interface language")
                    description: qsTr("Changes application labels and help text while project-defined names remain unchanged.")
                    showDivider: false
                    Controls.ComboBox {
                        id: interfaceLanguage
                        theme: root.theme
                        Layout.preferredWidth: 240
                        model: localizationController.language_options
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Rendering")
                description: qsTr("Choose how Qt Quick draws and presents the interface. Changes take effect after restarting TACTIC Handler.")
                iconName: "memory"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Graphics backend")
                    description: renderBackend.currentIndex >= 0
                        ? renderBackend.model[
                            renderBackend.currentIndex
                        ].description
                        : qsTr("Select the graphics API used to render the interface.")
                    showDivider: false
                    Controls.ComboBox {
                        id: renderBackend
                        objectName: "renderBackendCombo"
                        theme: root.theme
                        Layout.preferredWidth: 260
                        model: root.renderBackendOptions
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
            }

            Item {
                Layout.preferredHeight: 8
            }
        }
    }
}
