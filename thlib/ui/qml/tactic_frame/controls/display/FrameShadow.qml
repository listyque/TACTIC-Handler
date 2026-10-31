pragma ComponentBehavior: Bound
import QtQuick

// Paint the empty surface only; updates inside the card never invalidate its shadow.
Canvas {
    id: root
    required property var theme
    required property var shadow
    property real surfaceRadius: 8
    readonly property var shadowPalette: theme.framePalette
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onShadowChanged: requestPaint()
    onShadowPaletteChanged: requestPaint()
    onSurfaceRadiusChanged: requestPaint()
    onPaint: {
        const c = getContext("2d"), inset = 16;
        const w = Math.max(0, width - inset * 2), h = Math.max(0, height - inset * 2);
        const r = Math.min(surfaceRadius, w / 2, h / 2), x = inset, y = inset;
        c.clearRect(0, 0, width, height);
        if (!w || !h)
            return;
        c.beginPath();
        c.moveTo(x + r, y);
        c.arcTo(x + w, y, x + w, y + h, r);
        c.arcTo(x + w, y + h, x, y + h, r);
        c.arcTo(x, y + h, x, y, r);
        c.arcTo(x, y, x + w, y, r);
        c.closePath();
        c.shadowColor = theme.popupShadow;
        c.shadowBlur = shadow.blur;
        c.shadowOffsetY = shadow.y;
        c.globalAlpha = shadow.opacity;
        c.fillStyle = "black";
        c.fill();
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        c.globalAlpha = 1;
        c.globalCompositeOperation = "destination-out";
        c.fill();
        c.globalCompositeOperation = "source-over";
    }
}
