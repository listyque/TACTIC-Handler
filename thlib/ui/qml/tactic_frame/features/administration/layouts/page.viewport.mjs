import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

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
    const size = dimensions(settings, width, height);
    const scroll = scene.nodes.find((item) => item.id === 'customLayoutScroll');
    const sourceChildren = scroll ? scroll.children : scene.nodes;
    const pageHeight = Math.max(size.height, (scroll?.contentHeight || 0) + 24);
    const children = sourceChildren.map((child) =>
        child.id === 'canvasOverlay'
            ? Object.assign({}, child, {
                  width: size.width - 24,
                  height: pageHeight - 24
              })
            : child
    );
    return Object.assign({}, scene, {
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
                                    { children }
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
    const tr = (text) => translate(text, language);
    const settings = ui.canvas;
    const narrow = width < 520;
    const nodes = [
        node('Choice', 'pageCanvasSize', rect(0, 0, Math.min(182, width), 32), {
            label: tr('Preview size'),
            value: String(settings.width || 'auto'),
            enabled,
            options: [
                { value: 'auto', label: tr('Auto') },
                { value: '360', label: tr('Phone') + ' · 360' },
                { value: '768', label: tr('Tablet') + ' · 768' },
                { value: '1280', label: tr('Desktop') + ' · 1280' },
                { value: '1920', label: tr('Wide') + ' · 1920' }
            ].concat(
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
        }),
        node('Field', 'pageCanvasPixels', rect(190, 0, 76, 32), {
            label: tr('Preview width in pixels'),
            placeholder: tr('Auto'),
            text: ui.canvasWidthText,
            enabled,
            inputMode: 'numeric',
            action: { type: 'canvasWidthBuffer' },
            commitAction: { type: 'canvasWidthCommit' }
        }),
        label('pageCanvasPixelsUnit', rect(272, 0, 22, 32), 'px', muted)
    ];
    const left = narrow ? 0 : 304,
        top = narrow ? 40 : 0;
    const actual = dimensions(settings, width, 1).scale * 100;
    nodes.push(
        button(
            'pageCanvasZoomOut',
            rect(left, top, 32, 32),
            tr('Zoom out'),
            'zoom-out',
            { type: 'canvasZoom', value: String(step(settings, width, -1)) },
            enabled && actual > 25,
            { iconOnly: true }
        ),
        node('Choice', 'pageCanvasZoom', rect(left + 38, top, 122, 32), {
            label: tr('Canvas zoom'),
            value: String(settings.zoom),
            enabled,
            toolTip: settings.zoom === 'fit' ? tr('Fit width') : '',
            options: [{ value: 'fit', label: tr('Fit') }].concat(
                zooms.map((value) => ({
                    value: String(value),
                    label: value + '%'
                }))
            ),
            action: { type: 'canvasZoom' }
        }),
        button(
            'pageCanvasZoomIn',
            rect(left + 166, top, 32, 32),
            tr('Zoom in'),
            'zoom-in',
            { type: 'canvasZoom', value: String(step(settings, width, 1)) },
            enabled && actual < 200,
            { iconOnly: true }
        )
    );
    let height = narrow ? 72 : 32;
    if (!ui.preview) {
        const y = height + 8;
        nodes.push(
            button(
                'pageMultiSelect',
                rect(0, y, 32, 32),
                tr('Multiple selection'),
                'select-all',
                { type: 'multiSelect' },
                enabled,
                { iconOnly: true, highlighted: ui.multiSelect }
            ),
            label(
                'pageSelectionCount',
                rect(40, y, 72, 32),
                String((ui.selection || []).length) + ' ' + tr('selected'),
                muted
            ),
            node(
                'Choice',
                'pageAlign',
                rect(120, y, Math.min(178, Math.max(1, width - 166)), 32),
                {
                    label: tr('Align selected elements'),
                    value: '',
                    enabled: enabled && (ui.selection || []).length > 1,
                    options: [
                        { value: '', label: tr('Align') },
                        { value: 'left', label: tr('Left edges') },
                        { value: 'centerX', label: tr('Horizontal centers') },
                        { value: 'right', label: tr('Right edges') },
                        { value: 'top', label: tr('Top edges') },
                        { value: 'centerY', label: tr('Vertical centers') },
                        { value: 'bottom', label: tr('Bottom edges') }
                    ],
                    action: { type: 'align' }
                }
            ),
            button(
                'pageSnap',
                rect(Math.min(306, width - 32), y, 32, 32),
                tr('Snap to guides'),
                'grid-view',
                { type: 'snap' },
                enabled,
                { iconOnly: true, highlighted: ui.snap }
            )
        );
        height += 40;
    }
    return { nodes, height };
}
