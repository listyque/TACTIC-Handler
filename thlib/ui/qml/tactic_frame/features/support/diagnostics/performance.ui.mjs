import { spacing } from '../../../core/foundation.mjs';
import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const fields = [
    'sampleId',
    'action',
    'window',
    'handlerMs',
    'frameMs',
    'readyMs',
    'details',
    'slow',
    'status'
];

export function milliseconds(value, language) {
    return value >= 0
        ? Number(value).toFixed(1) + ' ' + translate('ms', language)
        : '—';
}

export function actionText(value, language) {
    return value.startsWith('Search tab: ')
        ? translate('Search tab', language) + ': ' + value.slice(12)
        : translate(value, language);
}

export function selection(rows, id, key, field = 'sampleId') {
    const index = rows.findIndex((row) => row[field] === id);
    const target =
        key === 'Home'
            ? 0
            : key === 'End'
              ? rows.length - 1
              : Math.max(
                    0,
                    Math.min(
                        rows.length - 1,
                        index + (key === 'ArrowUp' ? -1 : 1)
                    )
                );
    return rows[target] || null;
}

function columns(width) {
    const metric = width < 600 ? 56 : 96;
    return [Math.max(64, width - metric * 3 - 24), metric, metric, metric];
}

export function row(model, record, width, language) {
    const sizes = columns(width - 16);
    const children = [
        node('Box', 'sampleSlowOutline', rect(0, 0, width, 54), {
            background: 'transparent',
            border: record.slow ? 'red' : undefined,
            radius: 10
        }),
        label(
            'sampleAction',
            rect(8, 7, sizes[0] - 8, 22),
            actionText(record.action, language)
        ),
        label(
            'sampleWindow',
            rect(8, 29, sizes[0] - 8, 18),
            record.window || translate(record.status, language),
            muted
        )
    ];
    let x = sizes[0] + 8;
    for (const field of ['handlerMs', 'frameMs', 'readyMs']) {
        children.push(
            label(
                field,
                rect(x, 12, sizes[1] - 8, 30),
                milliseconds(record[field], language),
                {
                    color:
                        field === 'frameMs' && record[field] > 50
                            ? 'red'
                            : 'primaryText'
                }
            )
        );
        x += sizes[1];
    }
    const keys = {};
    for (const key of ['ArrowUp', 'ArrowDown', 'Home', 'End'])
        keys[key] = { type: 'sampleKey', id: record.sampleId, key };
    return {
        nodes: [
            node('Action', 'sample_' + record.sampleId, rect(0, 0, width, 54), {
                text: actionText(record.action, language),
                selected: model.selectedId === record.sampleId,
                normalColor: 'panel',
                selectedColor: 'contentSelection',
                border: record.slow ? 'red' : undefined,
                radius: 6,
                role: 'option',
                keys,
                action: { type: 'sample', record },
                children
            })
        ]
    };
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language);
    const compact = width < 600,
        margin = spacing.content;
    const inner = Math.max(0, width - margin * 2),
        contentHeight = Math.max(height, compact ? 610 : 490);
    const toolbarHeight = compact ? 80 : 40;
    const summary = model.summary || {
        count: 0,
        overBudget: 0,
        p95: 0,
        maximum: 0
    };
    const selected = model.selected || {};
    const nodes = [
        label(
            'performanceTitle',
            rect(margin, margin, compact ? inner : inner - 290, 30),
            text('UI responsiveness'),
            { fontRole: 'section' }
        ),
        button(
            'pauseUiMeasurements',
            rect(width - margin - 278, margin + (compact ? 38 : 0), 196, 36),
            text(
                model.recording ? 'Pause measurements' : 'Resume measurements'
            ),
            '',
            { type: 'record' },
            true
        ),
        button(
            'copyUiMeasurements',
            rect(width - margin - 76, margin + (compact ? 38 : 0), 36, 36),
            text('Copy measurements'),
            'content-copy',
            { type: 'copy' },
            true,
            { iconOnly: true }
        ),
        button(
            'clearUiMeasurements',
            rect(width - margin - 36, margin + (compact ? 38 : 0), 36, 36),
            text('Clear measurements'),
            'delete',
            { type: 'clear' },
            true,
            { iconOnly: true }
        )
    ];
    const noticeY = margin + toolbarHeight + 8;
    nodes.push(
        label(
            'performanceNotice',
            rect(margin, noticeY, inner, compact ? 94 : 54),
            text(
                'Target: a visible response within 50 ms. Input measures the next frame of the clicked window; controller rows measure work and its ready frame. A frame is not proof that asynchronous loading has finished.'
            ),
            Object.assign({}, muted, { wrap: true })
        )
    );
    let y = noticeY + (compact ? 100 : 60);
    if (model.browserFrames) {
        nodes.push(
            label(
                'browserFrameNotice',
                rect(margin, y, inner, compact ? 80 : 40),
                text(
                    'Browser frame timings bound a paint opportunity using animation callbacks. They do not confirm GPU presentation. Handler time for asynchronous operations includes waiting; details show the measured phases.'
                ),
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += compact ? 86 : 46;
    }
    nodes.push(
        label(
            'performanceSummary',
            rect(margin, y, inner, compact ? 42 : 24),
            text(
                'Samples: {count} · Frames over 50 ms: {overBudget} · p95: {p95} · Maximum: {maximum}'
            )
                .replace('{count}', summary.count)
                .replace('{overBudget}', summary.overBudget)
                .replace('{p95}', milliseconds(summary.p95, language))
                .replace('{maximum}', milliseconds(summary.maximum, language)),
            { wrap: true }
        )
    );
    y += compact ? 48 : 30;
    if (model.message) {
        nodes.push(
            label(
                'performanceMessage',
                rect(margin, y, inner, 30),
                text(model.message),
                {
                    color: model.failed ? 'red' : 'secondaryText',
                    wrap: true,
                    role: model.failed ? 'alert' : 'status'
                }
            )
        );
        y += 34;
    }
    const sizes = columns(inner - 32);
    let x = margin + 8;
    ['Action / window', 'Handler', 'First frame', 'Ready frame'].forEach(
        (name, index) => {
            nodes.push(
                label(
                    'performanceColumn' + index,
                    rect(x, y, sizes[index] - 8, 24),
                    text(name),
                    muted
                )
            );
            x += sizes[index];
        }
    );
    y += 28;
    const detailsY = contentHeight - margin - 95;
    nodes.push(
        node(
            'List',
            'uiPerformanceSamples',
            rect(margin, y, inner, Math.max(64, detailsY - y - 10)),
            {
                source: 'samples',
                role: 'listbox',
                keyField: 'sampleId',
                fields,
                rowHeight: 58,
                rowGap: 4,
                scrollbarId: 'uiPerformanceScrollBar',
                label: text('UI measurements')
            }
        )
    );
    if (!summary.count)
        nodes.push(
            label(
                'performanceEmpty',
                rect(margin + 8, y + 8, inner - 32, 60),
                text(
                    'No measurements yet. Resume measurements and interact with the application.'
                ),
                Object.assign({}, muted, { wrap: true })
            )
        );
    nodes.push(
        node(
            'Area',
            'uiMeasurementDetails',
            rect(margin, detailsY, inner, 95),
            {
                text: selected.action
                    ? actionText(selected.action, language) +
                      '\n' +
                      text(selected.status) +
                      '\n' +
                      selected.details
                    : text('Select a measurement for details'),
                label: text('Measurement details'),
                readOnly: true,
                enabled: true
            }
        )
    );
    return {
        nodes: [
            node('Scroll', 'performanceBody', rect(0, 0, width, height), {
                contentHeight,
                children: nodes
            })
        ]
    };
}
