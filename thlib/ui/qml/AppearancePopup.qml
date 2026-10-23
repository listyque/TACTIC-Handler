import QtQuick
import QtQuick.Controls
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    preferredSurfaceWidth: 320
    minimumSurfaceWidth: 280
    maximumSurfaceHeight: 520
    contentSpacing: 10
    parent: Overlay.overlay

    readonly property real rowWidth: Math.max(0, viewport.width - verticalScrollBar.reservedExtent)

    function toggleBelow(sourceItem) {
        toggleBelowItem(sourceItem, true, 6);
    }

    readonly property string currentThemeDescription: {
        const options = typeof appController !== "undefined" ? appController.theme_options || [] : [];
        const current = typeof appController !== "undefined" ? appController.theme_style : "";
        for (let i = 0; i < options.length; ++i) {
            if (options[i].value === current)
                return options[i].description || "";
        }
        return "";
    }

    readonly property string currentIconSetDescription: {
        const options = typeof appController !== "undefined" ? appController.icon_set_options || [] : [];
        const current = typeof appController !== "undefined" ? appController.icon_set : "";
        for (let i = 0; i < options.length; ++i) {
            if (options[i].value === current)
                return options[i].description || "";
        }
        return "";
    }

    Column {
        width: root.rowWidth
        spacing: 4

        Label {
            text: qsTr("Interface language")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }

        Label {
            width: parent.width
            text: qsTr("Changes application labels and help text while project-defined names remain unchanged.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            wrapMode: Text.WordWrap
        }

        Item {
            width: parent.width
            height: 2
        }

        Controls.ComboBox {
            id: languageCombo
            objectName: "appearanceLanguageCombo"
            theme: root.theme
            width: parent.width
            height: root.theme.controlHeight
            model: typeof localizationController !== "undefined" ? localizationController.language_options : []
            textRole: "label"
            currentIndex: {
                const current = typeof localizationController !== "undefined" ? localizationController.current_language : "en";
                for (let i = 0; i < count; ++i) {
                    if (optionValue(i, "value") === current)
                        return i;
                }
                return 0;
            }
            onActivated: index => {
                if (typeof localizationController !== "undefined")
                    localizationController.set_language(optionValue(index, "value"));
            }
        }
    }

    Rectangle {
        width: root.rowWidth
        height: 1
        color: root.theme.outlineVariant
    }

    Column {
        width: root.rowWidth
        spacing: 4

        Label {
            text: qsTr("Interface style")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }

        Label {
            width: parent.width
            text: root.currentThemeDescription ? qsTr(root.currentThemeDescription) : ""
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            wrapMode: Text.WordWrap
        }

        Item {
            width: parent.width
            height: 2
        }

        Controls.ComboBox {
            id: themeStyleCombo
            objectName: "appearanceThemeStyleCombo"
            theme: root.theme
            width: parent.width
            height: root.theme.controlHeight
            model: typeof appController !== "undefined" ? appController.theme_options : []
            textRole: "label"
            currentIndex: {
                const current = typeof appController !== "undefined" ? appController.theme_style : "";
                for (let i = 0; i < count; ++i) {
                    if (optionValue(i, "value") === current)
                        return i;
                }
                return 0;
            }
            onActivated: index => {
                if (typeof appController !== "undefined")
                    appController.set_theme_style(optionValue(index, "value"));
            }
        }
    }

    Rectangle {
        width: root.rowWidth
        height: 1
        color: root.theme.outlineVariant
    }

    Column {
        width: root.rowWidth
        spacing: 4

        Label {
            text: qsTr("Color mode")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }

        Label {
            width: parent.width
            text: qsTr("Choose light or dark surfaces, or follow the system preference.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            wrapMode: Text.WordWrap
        }

        Item {
            width: parent.width
            height: 2
        }

        Controls.ComboBox {
            id: colorModeCombo
            objectName: "appearanceColorModeCombo"
            theme: root.theme
            width: parent.width
            height: root.theme.controlHeight
            model: [
                { value: "dark", label: qsTr("Dark") },
                { value: "light", label: qsTr("Light") }
            ]
            textRole: "label"
            currentIndex: typeof appController !== "undefined" && appController.dark_theme ? 0 : 1
            onActivated: index => {
                if (typeof appController !== "undefined")
                    appController.set_dark_theme(optionValue(index, "value") === "dark");
            }
        }
    }

    Rectangle {
        width: root.rowWidth
        height: 1
        color: root.theme.outlineVariant
    }

    Column {
        width: root.rowWidth
        spacing: 4

        Label {
            text: qsTr("Icon set")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }

        Label {
            width: parent.width
            text: root.currentIconSetDescription ? qsTr(root.currentIconSetDescription) : ""
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            wrapMode: Text.WordWrap
        }

        Item {
            width: parent.width
            height: 2
        }

        Controls.ComboBox {
            id: iconSetCombo
            objectName: "appearanceIconSetCombo"
            theme: root.theme
            width: parent.width
            height: root.theme.controlHeight
            model: typeof appController !== "undefined" ? appController.icon_set_options : []
            textRole: "label"
            currentIndex: {
                const current = typeof appController !== "undefined" ? appController.icon_set : "";
                for (let i = 0; i < count; ++i) {
                    if (optionValue(i, "value") === current)
                        return i;
                }
                return 0;
            }
            onActivated: index => {
                if (typeof appController !== "undefined")
                    appController.set_icon_set(optionValue(index, "value"));
            }
        }
    }
}
