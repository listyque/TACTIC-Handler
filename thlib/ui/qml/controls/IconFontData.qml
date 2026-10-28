pragma Singleton

import QtQml

QtObject {
    id: root

    // Convert context QVariantMaps once per engine, not for every icon delegate.
    readonly property var solidGlyphs: typeof fontAwesomeSolidGlyphs !== "undefined" ? Object.assign({}, fontAwesomeSolidGlyphs) : ({})
    readonly property var regularGlyphs: typeof fontAwesomeRegularGlyphs !== "undefined" ? Object.assign({}, fontAwesomeRegularGlyphs) : ({})
    readonly property var materialGlyphs: typeof materialDesignIconGlyphs !== "undefined" ? Object.assign({}, materialDesignIconGlyphs) : ({})
    readonly property string solidFontFamily: typeof fontAwesomeSolidFontFamily !== "undefined" ? fontAwesomeSolidFontFamily : "Segoe UI"
    readonly property string regularFontFamily: typeof fontAwesomeRegularFontFamily !== "undefined" ? fontAwesomeRegularFontFamily : root.solidFontFamily
    readonly property string materialFontFamily: typeof materialDesignIconFontFamily !== "undefined" ? materialDesignIconFontFamily : root.solidFontFamily
}
