import QtQuick
import "../../tactic_frame/shell/window.sizing.mjs" as Sizing

QtObject {
    function windowMinimumWidth(kind) {
        return Sizing.windowMinimumWidth(kind);
    }
    function windowMinimumHeight(kind) {
        return Sizing.windowMinimumHeight(kind);
    }
    function dockMinimumWidth(kind) {
        return Sizing.dockMinimumWidth(kind);
    }
    function dockMinimumHeight(kind) {
        return Sizing.dockMinimumHeight(kind);
    }
}
