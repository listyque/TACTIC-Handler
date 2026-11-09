import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { combineRegions } from './canvas.mjs';

export const zooms = [25, 50, 75, 100, 125, 150, 200];
export function dimensions(settings, width, height) {
    const pageWidth = settings.width || Math.max(320, Math.round(width - 32));
    return {
        width: pageWidth,
        height: Math.max(1, height - 32),
        scale:
            settings.zoom === 'fit'
                ? Math.min(1, Math.max(1, width - 32) / pageWidth)
                : Number(settings.zoom) / 100
    };
}
function step(settings, width, direction) {
    const percent = dimensions(settings, width, 1).scale * 100;
    return direction > 0
        ? zooms.find((value) => value > percent + 0.01) || 200
        : zooms
              .slice()
              .reverse()
              .find((value) => value < percent - 0.01) || 25;
}
export function describe(scene, settings, width, height) {
    const merged = combineRegions(scene);
    const size = dimensions(settings, width, height);
    const scroll = merged.nodes.find(
        (item) => item.id === 'customLayoutScroll'
    );
    const sourceChildren = scroll ? scroll.children : merged.nodes;
    const pageHeight = Math.max(size.height, (scroll?.contentHeight || 0) + 24);
    const children = sourceChildren.map((child) =>
        child.id === 'canvasOverlay'
            ? Object.assign({}, child, {
                  width: size.width - 24,
                  height: pageHeight - 24
              })
            : child
    );
    return Object.assign({}, merged, {
        nodes: [
            node('Scroll', 'pageViewportScroll', rect(0, 0, width, height), {
                contentWidth: Math.max(width, size.width * size.scale + 32),
                contentHeight: Math.max(height, pageHeight * size.scale + 32),
                scrollbarId: 'pageViewportBar',
                children: [
                    node(
                        'Box',
                        'pageViewportPaper',
                        rect(
                            Math.max(16, (width - size.width * size.scale) / 2),
                            16,
                            size.width,
                            pageHeight
                        ),
                        {
                            scale: size.scale,
                            // Resize handles and measurements extend beyond the paper.
                            clip: false,
                            background: 'workspace',
                            border: 'outlineVariant',
                            children: [
                                node(
                                    'Box',
                                    'pageViewportContent',
                                    rect(
                                        12,
                                        12,
                                        size.width - 24,
                                        pageHeight - 24
                                    ),
                                    { children, clip: false }
                                )
                            ]
                        }
                    )
                ]
            })
        ]
    });
}
export function controls(ui, width, language, enabled) {
    const tr = (text) => translate(text, language),
        settings = ui.canvas,
        nodes = [];
    let x = 0,
        y = 0;
    function place(kind, id, w, props) {
        w = Math.min(w, width);
        if (x && x + w > width) {
            x = 0;
            y += 38;
        }
        nodes.push(node(kind, id, rect(x, y, w, 32), props));
        x += w + 6;
    }
    place('Choice', 'pageCanvasSize', 132, {
        label: tr('Preview size'),
        value: String(settings.width || 'auto'),
        enabled,
        options: [
            ['auto', 'Auto'],
            ['360', 'Phone'],
            ['768', 'Tablet'],
            ['1280', 'Desktop'],
            ['1920', 'Wide']
        ]
            .map(([value, title]) => ({
                value,
                label: tr(title) + (value === 'auto' ? '' : ' · ' + value)
            }))
            .concat(
                settings.width &&
                    ![360, 768, 1280, 1920].includes(settings.width)
                    ? [
                          {
                              value: String(settings.width),
                              label: tr('Custom') + ' · ' + settings.width
                          }
                      ]
                    : []
            ),
        action: { type: 'canvasSize' }
    });
    const actual = dimensions(settings, width, 1).scale * 100;
    place('Button', 'pageCanvasZoomOut', 32, {
        text: tr('Zoom out'),
        icon: 'zoom-out',
        iconOnly: true,
        enabled: enabled && actual > 25,
        action: { type: 'canvasZoom', value: String(step(settings, width, -1)) }
    });
    place('Choice', 'pageCanvasZoom', 88, {
        label: tr('Canvas zoom'),
        value: String(settings.zoom),
        enabled,
        options: [{ value: 'fit', label: tr('Fit') }].concat(
            zooms.map((value) => ({ value: String(value), label: value + '%' }))
        ),
        action: { type: 'canvasZoom' }
    });
    place('Button', 'pageCanvasZoomIn', 32, {
        text: tr('Zoom in'),
        icon: 'zoom-in',
        iconOnly: true,
        enabled: enabled && actual < 200,
        action: { type: 'canvasZoom', value: String(step(settings, width, 1)) }
    });
    if (!ui.preview) {
        place('Button', 'pageMultiSelect', 32, {
            text: tr('Multiple selection'),
            icon: 'select-all',
            iconOnly: true,
            highlighted: ui.multiSelect,
            enabled,
            action: { type: 'multiSelect' }
        });
        place('Button', 'pageSnap', 32, {
            text: tr('Snap to guides'),
            icon: 'grid-view',
            iconOnly: true,
            highlighted: ui.snap,
            enabled,
            action: { type: 'snap' }
        });
        if (ui.selection.length > 1) {
            place('Label', 'pageSelectionCount', 64, {
                text: ui.selection.length + ' ' + tr('selected'),
                color: 'secondaryText'
            });
            place('Choice', 'pageAlign', 140, {
                label: tr('Align selected elements'),
                value: '',
                enabled,
                options: [
                    ['', 'Align'],
                    ['left', 'Left edges'],
                    ['centerX', 'Horizontal centers'],
                    ['right', 'Right edges'],
                    ['top', 'Top edges'],
                    ['centerY', 'Vertical centers'],
                    ['bottom', 'Bottom edges']
                ].map(([value, title]) => ({ value, label: tr(title) })),
                action: { type: 'align' }
            });
        }
    }
    if (ui.canvasSettings) {
        x = 0;
        y += 38;
        place('Label', 'pageCanvasWidthLabel', Math.min(190, width - 106), {
            text: tr('Preview width in pixels'),
            color: 'secondaryText'
        });
        place('Field', 'pageCanvasPixels', 76, {
            label: tr('Preview width in pixels'),
            placeholder: tr('Auto'),
            text: ui.canvasWidthText,
            enabled,
            inputMode: 'numeric',
            action: { type: 'canvasWidthBuffer' },
            commitAction: { type: 'canvasWidthCommit' }
        });
        place('Label', 'pageCanvasPixelsUnit', 22, {
            text: 'px',
            color: 'secondaryText'
        });
    }
    return { nodes, height: y + 32 };
}
