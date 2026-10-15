import "../tactic_frame/core/icons.mjs" as Icons
import QtQuick

// Shared semantic icon renderer backed by the bundled icon-font catalog.
Item {
    id: root
    property string name: ""
    required property color color
    property real size: 24
    property real opticalScale: 0.78
    property bool forceSolid: false
    property bool nativeRendering: false
    readonly property string iconSet: typeof appController !== "undefined" ? String(appController.icon_set || "material-design") : "material-design"
    readonly property var solidGlyphs: typeof fontAwesomeSolidGlyphs !== "undefined" ? fontAwesomeSolidGlyphs : ({})
    readonly property var regularGlyphs: typeof fontAwesomeRegularGlyphs !== "undefined" ? fontAwesomeRegularGlyphs : ({})
    readonly property string solidFontFamily: typeof fontAwesomeSolidFontFamily !== "undefined" ? fontAwesomeSolidFontFamily : "Segoe UI"
    readonly property string regularFontFamily: typeof fontAwesomeRegularFontFamily !== "undefined" ? fontAwesomeRegularFontFamily : solidFontFamily
    readonly property var materialGlyphs: typeof materialDesignIconGlyphs !== "undefined" ? materialDesignIconGlyphs : ({})
    readonly property string materialFontFamily: typeof materialDesignIconFontFamily !== "undefined" ? materialDesignIconFontFamily : solidFontFamily
    implicitWidth: size
    implicitHeight: size

    readonly property var aliases: Icons.aliases

    readonly property var materialAliases: Icons.materialAliases

    readonly property var fluentAliases: Icons.fluentAliases

    readonly property var automaticOutlineGlyphs: Icons.automaticOutlineGlyphs

    function normalizedName(sourceName) {
        return Icons.semanticName(sourceName || "warning");
    }

    function fontAwesomeName(sourceName) {
        const normalized = normalizedName(sourceName);
        const candidate = Icons.ownValue(aliases, normalized) || normalized;
        return Icons.ownValue(solidGlyphs, candidate) !== undefined || Icons.ownValue(regularGlyphs, candidate) !== undefined ? candidate : "";
    }

    function materialName(sourceName) {
        const normalized = normalizedName(sourceName);
        const direct = Icons.ownValue(materialAliases, normalized) || normalized;
        if (glyphFor("material-design", direct).length > 0)
            return direct;
        const fontAwesome = Icons.ownValue(aliases, normalized) || normalized;
        const mapped = Icons.ownValue(materialAliases, fontAwesome) || fontAwesome;
        return glyphFor("material-design", mapped).length > 0 ? mapped : "";
    }

    function fluentName(sourceName) {
        const normalized = normalizedName(sourceName);
        return Icons.ownValue(fluentAliases, normalized) || normalized;
    }

    function qualifiedIcon(sourceName) {
        const normalized = normalizedName(sourceName);
        const separator = normalized.indexOf(":");
        if (separator <= 0)
            return ({});
        return {
            "set": normalized.slice(0, separator),
            "name": normalized.slice(separator + 1)
        };
    }

    function catalogIcon(setId, iconName) {
        if (typeof iconFontCatalog === "undefined")
            return ({});
        return iconFontCatalog.resolve(setId, iconName);
    }

    function iconSetOpticalScale(setId) {
        if (setId === "material-design")
            return 1.22;
        return String(setId).indexOf("fluent-") === 0 ? 1.08 : 1.0;
    }

    function glyphFor(setId, iconName) {
        if (setId === "material-design")
            return Icons.ownValue(materialGlyphs, iconName) || String(catalogIcon(setId, iconName).glyph || "");
        if (setId === "fontawesome-solid")
            return Icons.ownValue(solidGlyphs, iconName) || "";
        if (setId === "fontawesome-outline")
            return Icons.ownValue(regularGlyphs, iconName) || "";
        return String(catalogIcon(setId, iconName).glyph || "");
    }

    function glyphName(sourceName) {
        return fontAwesomeName(sourceName) || "exclamation-triangle";
    }

    Text {
        objectName: "materialIconGlyph"
        readonly property string fontAwesomeName: root.fontAwesomeName(root.name)
        readonly property string resolvedName: fontAwesomeName || "exclamation-triangle"
        readonly property string materialName: root.materialName(root.name)
        readonly property var selection: Icons.resolve(root.name, root.iconSet, root.glyphFor, root.forceSolid) || ({
                set: "fontawesome-solid",
                name: "exclamation-triangle"
            })
        readonly property string resolvedSet: selection.set
        readonly property bool useMaterial: resolvedSet === "material-design"
        readonly property bool useRegular: resolvedSet === "fontawesome-outline"
        readonly property bool useCatalog: resolvedSet.indexOf("fluent-") === 0
        readonly property string catalogGlyph: useCatalog ? root.glyphFor(resolvedSet, selection.name) : ""
        anchors.fill: parent
        text: root.glyphFor(resolvedSet, selection.name)
        color: root.color
        font.family: useCatalog ? String(root.catalogIcon(resolvedSet, selection.name).fontFamily || root.solidFontFamily) : useMaterial ? root.materialFontFamily : useRegular ? root.regularFontFamily : root.solidFontFamily
        font.pixelSize: Math.max(11, Math.round(root.size * root.opticalScale * root.iconSetOpticalScale(resolvedSet)))
        font.weight: useCatalog || useMaterial || useRegular ? Font.Normal : Font.Black
        font.hintingPreference: Font.PreferVerticalHinting
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        renderType: root.nativeRendering ? Text.NativeRendering : Text.QtRendering
        antialiasing: true
    }
}
