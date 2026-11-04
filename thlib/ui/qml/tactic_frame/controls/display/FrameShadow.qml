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
        if (!w || !h || !shadow)
            return;
        function roundedRect(rx, ry, rw, rh, rr) {
            const rad = Math.max(0, Math.min(rr, rw / 2, rh / 2));
            c.beginPath();
            c.moveTo(rx + rad, ry);
            c.arcTo(rx + rw, ry, rx + rw, ry + rh, rad);
            c.arcTo(rx + rw, ry + rh, rx, ry + rh, rad);
            c.arcTo(rx, ry + rh, rx, ry, rad);
            c.arcTo(rx, ry, rx + rw, ry, rad);
            c.closePath();
        }
        const blur = Math.max(1, Number(shadow && shadow.blur) || 12);
        const offsetY = Number(shadow && shadow.y) || 0;
        const baseAlpha = (Number(shadow && shadow.opacity) || 1) * 0.22;
        const steps = 4;
        c.strokeStyle = theme.popupShadow;
        for (let i = steps; i >= 1; i--) {
            const spread = (blur * i) / steps;
            const lw = spread * 0.65;
            c.lineWidth = lw;
            c.globalAlpha = baseAlpha * ((steps - i + 1) / (steps * 1.5));
            roundedRect(x - spread * 0.35, y + offsetY * (i / steps) - spread * 0.15, w + spread * 0.7, h + spread * 0.5, r + spread * 0.35);
            c.stroke();
        }
        c.globalAlpha = 1;
        c.fillStyle = "black";
        c.globalCompositeOperation = "destination-out";
        roundedRect(x, y, w, h, r);
        c.fill();
        c.globalCompositeOperation = "source-over";
    }
}
