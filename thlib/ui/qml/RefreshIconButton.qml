import QtQuick
import "controls" as Controls

Controls.CompactIconButton {
    width: 38
    height: 38
    iconName: "refresh"
    iconSize: 17
    round: false
    opacity: enabled ? 1 : 0.38
}
