import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Composition from './layout.preview.mjs';
import * as Canvas from './canvas.mjs';

// Editor-only values: no record identity, external assets or server operations.
export function fallback(
    layout,
    records,
    searchType,
    selected,
    language,
    screenWidth = 1000
) {
    if (!layout?.elements?.length) return null;
    const tr = (text) => translate(text, language);
    const byName = new Map(layout.elements.map((item) => [item.name, item]));
    const chain = [];
    for (
        let item = byName.get(selected);
        item && chain.length < 8;
        item = byName.get(item.parent)
    )
        chain.push(item);
    const matches = (sample) =>
        chain.length
            ? chain.every((item) =>
                  Composition.visible(item, sample, layout, screenWidth)
              )
            : Composition.supports(layout, sample, screenWidth);
    if ((records || []).some(matches)) return null;
    const target =
        chain.find((item) => item.search_type)?.search_type || searchType;
    const conditions = chain.reduce(
        (all, item) => all.concat(item.when || []),
        []
    );
    const variant =
        chain.find((item) => item.variant && item.variant !== 'all')?.variant ||
        (conditions.includes('relation')
            ? 'relation'
            : conditions.includes('branch')
              ? 'process'
              : conditions.includes('snapshot')
                ? 'snapshot'
                : 'main');
    const sample = {
        kind: ['process', 'relation', 'versions'].includes(variant)
            ? 'branch'
            : ['snapshot', 'file'].includes(variant)
              ? variant
              : 'object',
        depth: variant === 'children' ? 1 : 0,
        search_type: target,
        title: tr('Example item'),
        subtitle: tr('Example description'),
        record: Object.assign(Object.create(null), {
            name: tr('Example item'),
            title: tr('Example item'),
            description: tr('Example description')
        }),
        preview: {},
        note_count: 3,
        task_count: 2,
        branch: {
            kind: variant,
            count: 3,
            relationship: 'instance',
            process: tr('Example process')
        },
        snapshot_display: {
            title: 'example.jpg',
            exists: false,
            version: 'v001',
            author: tr('Example author'),
            size: 1024
        },
        knowledge: [{ title: tr('Example item') }]
    };
    function bind(path, value) {
        const parts = String(path || '').split('.');
        if (
            !['record', 'node'].includes(parts[0]) ||
            parts.length < 2 ||
            parts.length > 6 ||
            parts.some((part) =>
                [
                    '__proto__',
                    'constructor',
                    'prototype',
                    '__search_key__',
                    'id'
                ].includes(part)
            )
        )
            return;
        let result = parts.shift() === 'record' ? sample.record : sample;
        for (const part of parts.slice(0, -1)) {
            if (!result[part] || typeof result[part] !== 'object')
                result[part] = Object.create(null);
            result = result[part];
        }
        const key = parts[parts.length - 1];
        if (result[key] === undefined) result[key] = value;
    }
    function values(current, depth) {
        if (!current || depth >= 8) return;
        for (const item of current.elements || []) {
            const options = item.options || {};
            let value = tr('Example value');
            if (
                options.format === 'progress' ||
                /(?:count|progress|percent)$/.test(options.bind || '')
            )
                value = 42;
            else if (['date', 'datetime'].includes(options.format))
                value = '2026-01-15T12:00:00Z';
            else if (options.format === 'badge') {
                let colors = {};
                try {
                    colors = JSON.parse(options.colors || '{}');
                } catch (error) {
                    /* Invalid XML keeps its normal validation error. */
                }
                value = Object.keys(colors)[0] || tr('Example status');
            }
            bind(options.bind, value);
            bind(options.badge, 3);
            if (item.widget_layout) values(item.widget_layout, depth + 1);
        }
    }
    values(layout, 0);
    return matches(sample) ? sample : null;
}

export function scene(
    layout,
    sample,
    width,
    height,
    selected,
    editing,
    language,
    screenWidth,
    assetBase
) {
    if (!layout || !sample || width <= 0 || height <= 0) return { nodes: [] };
    const composition = Composition.describe(
        layout,
        sample,
        Math.max(1, width - 16),
        selected,
        language,
        screenWidth,
        assetBase,
        'itemComposition',
        0,
        true
    );
    const content = editing
        ? Canvas.itemScene(composition, layout)
        : composition;
    return {
        canvasBoxes: content.canvasBoxes || [],
        nodes: [
            node('Scroll', 'layoutSampleScroll', rect(0, 0, width, height), {
                contentHeight: composition.height,
                scrollbarId: 'layoutSampleScrollBar',
                children: content.nodes
            })
        ]
    };
}
