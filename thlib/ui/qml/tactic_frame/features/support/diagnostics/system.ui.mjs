import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function initial() {
    return {
        busy: false,
        pending: '',
        error: '',
        sections: [],
        cpuCount: 1,
        sender: '',
        recipients: '',
        scriptPath: '',
        includeInternal: false,
        mailConfigured: false,
        directories: {},
        links: [],
        internalLinks: [],
        results: {}
    };
}
export function valueText(value, language) {
    return value === null
        ? translate('None configured', language)
        : typeof value === 'boolean'
          ? translate(value ? 'Yes' : 'No', language)
          : typeof value === 'object'
            ? JSON.stringify(value)
            : String(value || '—');
}
export function report(model, language) {
    return (model.sections || [])
        .map(
            (section) =>
                translate(section.title, language) +
                '\n' +
                section.fields
                    .map(
                        ([name, value]) =>
                            translate(name, language) +
                            ': ' +
                            valueText(value, language)
                    )
                    .join('\n')
        )
        .join('\n\n');
}
export function testPlan(model) {
    return {
        iterations: Math.max(1, Math.min(256, Number(model.cpuCount) || 1)),
        parallel: 8
    };
}
export function balancePlan() {
    return { iterations: 50, parallel: 8 };
}
export function resultText(result, language) {
    const tr = (text) => translate(text, language);
    if (!result) return '';
    if (result.error) return tr(result.error);
    if (result.opened !== undefined)
        return (
            tr('Opened pages') +
            ': ' +
            result.opened +
            ' / ' +
            result.total +
            (result.blocked ? '\n' + tr('Allow pop-ups to open all pages') : '')
        );
    if (result.sequentialMs !== undefined)
        return (
            tr('Sequential') +
            ': ' +
            result.sequentialMs.toFixed(1) +
            ' ms · ' +
            result.count +
            ' ' +
            tr('requests') +
            '\n' +
            tr('Parallel') +
            ': ' +
            result.parallelMs.toFixed(1) +
            ' ms · ' +
            result.count +
            ' ' +
            tr('requests') +
            ' · ' +
            result.parallel +
            ' ' +
            tr('parallel requests')
        );
    if (result.samples) {
        const workers = [],
            ports = [];
        for (const sample of result.samples) {
            const identity = sample.node + ':' + sample.pid;
            if (workers.indexOf(identity) < 0) workers.push(identity);
            if (sample.port && ports.indexOf(String(sample.port)) < 0)
                ports.push(String(sample.port));
        }
        return (
            tr('Observed workers') +
            ': ' +
            workers.length +
            ' · ' +
            tr('Ports') +
            ': ' +
            (ports.join(', ') || '—') +
            '\n' +
            tr('Samples') +
            ': ' +
            result.samples.length +
            '\n' +
            tr('This sample does not show the configured worker count.')
        );
    }
    if (result.paths)
        return result.paths
            .map(
                (row) =>
                    row.path +
                    ': ' +
                    tr(row.available ? 'Accessible' : 'Not accessible')
            )
            .join('\n');
    return tr(result.message || '');
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        pad = 12,
        bodyWidth = Math.max(0, width - pad * 2),
        inner = Math.max(0, bodyWidth - 16),
        compact = inner < 580,
        content = [],
        enabled = !model.busy;
    let y = 0,
        serial = 0;
    function heading(title) {
        content.push(
            node(
                'Box',
                'systemHeadingBackground_' + serial,
                rect(0, y, inner, 32),
                { background: 'panel', radius: 0 }
            )
        );
        content.push(
            label(
                'systemHeading_' + serial++,
                rect(10, y + 5, inner - 20, 22),
                tr(title),
                { weight: 600, role: 'heading' }
            )
        );
        y += 44;
    }
    function paragraph(id, text, error) {
        const lines = String(text)
            .split('\n')
            .reduce(
                (sum, line) =>
                    sum +
                    Math.max(
                        1,
                        Math.ceil(
                            line.length /
                                Math.max(12, Math.floor((inner - 16) / 7))
                        )
                    ),
                0
            );
        const h = Math.max(24, lines * 22);
        content.push(
            label(id, rect(8, y, inner - 16, h), text, {
                wrap: true,
                color: error ? 'red' : 'secondaryText',
                role: error ? 'alert' : undefined
            })
        );
        y += h + 8;
    }
    function row(name, value) {
        const labelWidth = compact ? inner - 16 : 185,
            valueWidth = compact ? inner - 16 : inner - 209;
        const text = valueText(value, language),
            title = tr(name),
            labelHeight = Math.max(
                26,
                Math.ceil(
                    title.length / Math.max(10, Math.floor(labelWidth / 7))
                ) * 22
            ),
            h = Math.max(
                26,
                text
                    .split('\n')
                    .reduce(
                        (sum, line) =>
                            sum +
                            Math.max(
                                1,
                                Math.ceil(
                                    line.length /
                                        Math.max(10, Math.floor(valueWidth / 7))
                                )
                            ),
                        0
                    ) * 22
            );
        content.push(
            label(
                'systemName_' + serial,
                rect(8, y, labelWidth, labelHeight),
                title,
                Object.assign({}, muted, { wrap: true })
            )
        );
        content.push(
            label(
                'systemValue_' + serial++,
                rect(
                    compact ? 8 : 201,
                    y + (compact ? labelHeight : 0),
                    valueWidth,
                    h
                ),
                text,
                { wrap: true, tooltip: text }
            )
        );
        y += (compact ? h + labelHeight : Math.max(h, labelHeight)) + 8;
    }
    function field(id, title, value, key) {
        content.push(
            label(id + 'Label', rect(8, y, inner - 16, 22), tr(title), muted)
        );
        y += 26;
        content.push(
            node('Field', id, rect(8, y, inner - 16, 38), {
                label: tr(title),
                text: value || '',
                enabled,
                action: { type: 'field', field: key }
            })
        );
        y += 50;
    }
    function test(id, title, kind, extra) {
        const icons = {
            balance: 'hub',
            performance: 'ui-performance',
            email: 'send',
            handoff: 'folder',
            links: 'open-in-new',
            script: 'code'
        };
        content.push(
            button(
                id,
                rect(8, y, Math.min(inner - 16, 260), 36),
                tr(title),
                icons[kind],
                Object.assign(
                    { type: 'test', name: kind, plan: testPlan(model) },
                    extra || {}
                ),
                enabled
            )
        );
        y += 48;
        const result = model.results && model.results[kind];
        if (model.pending === kind)
            paragraph(id + 'Pending', tr('Running test…'));
        if (result)
            paragraph(
                id + 'Result',
                resultText(result, language),
                !!result.error
            );
    }
    for (const title of [
        'Server',
        'Python',
        'Client',
        'TACTIC Handler',
        'Browser'
    ]) {
        const section = (model.sections || []).find(
            (item) => item.title === title
        );
        if (section) {
            heading(title);
            for (const field of section.fields) row(field[0], field[1]);
            y += 8;
        }
    }
    heading('Load Balancing');
    paragraph(
        'systemBalanceExplanation',
        tr('Sample server requests to identify responding workers and ports.')
    );
    test('systemBalanceTest', 'Test load balancing', 'balance');
    heading('Performance Test');
    paragraph(
        'systemPerformanceExplanation',
        tr(
            'Build the Users table definition and read its rows through sequential and parallel requests.'
        ) +
            ' ' +
            testPlan(model).iterations +
            ' ' +
            tr('requests')
    );
    test('systemPerformanceTest', 'Test performance', 'performance');
    heading('Mail Server');
    const mail = (model.sections || []).find(
        (item) => item.title === 'Mail Server'
    );
    if (mail) for (const field of mail.fields) row(field[0], field[1]);
    field('systemMailFrom', 'From', model.sender, 'sender');
    field('systemMailTo', 'To', model.recipients, 'recipients');
    if (!model.mailConfigured)
        paragraph('systemMailMissing', tr('No mail server is configured'));
    test('systemEmailTest', 'Email Send Test', 'email');
    heading('Asset Folders');
    const folders = (model.sections || []).find(
        (item) => item.title === 'Asset Folders'
    );
    if (folders) for (const field of folders.fields) row(field[0], field[1]);
    test('systemHandoffTest', 'Test client handoff', 'handoff');
    heading('Link Test');
    paragraph(
        'systemLinksExplanation',
        tr(
            'Open the project pages in browser windows. This can take a few minutes.'
        )
    );
    content.push(
        node('CheckBox', 'systemIncludeInternal', rect(8, y, inner - 16, 36), {
            text: tr('Include built-in pages'),
            label: tr('Include built-in pages'),
            checked: !!model.includeInternal,
            enabled,
            action: { type: 'field', field: 'includeInternal' }
        })
    );
    y += 44;
    const links =
        (model.includeInternal ? model.internalLinks : model.links) || [];
    test('systemLinkTest', 'Run link test', 'links');
    if (!links.length)
        paragraph('systemNoLinks', tr('No project pages configured'));
    for (let index = 0; index < links.length; index++) {
        const link = links[index];
        content.push(
            button(
                'systemOpenLink_' + index,
                rect(8, y, inner - 16, 34),
                link.title || link.name,
                'open-in-new',
                { type: 'openLink', url: link.url },
                enabled
            )
        );
        y += 42;
    }
    heading('Python Script Test');
    field('systemScriptPath', 'Script Path', model.scriptPath, 'scriptPath');
    test('systemScriptTest', 'Run script', 'script');
    const nodes = [
        button(
            'systemRefresh',
            rect(pad, pad, 132, 36),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            enabled
        ),
        button(
            'systemCopy',
            rect(pad + 140, pad, 140, 36),
            tr('Copy'),
            'content_copy',
            { type: 'copy' },
            enabled && !!model.sections?.length
        )
    ];
    if (model.error)
        nodes.push(
            label('systemStatus', rect(pad, 56, inner, 44), tr(model.error), {
                wrap: true,
                color: 'red',
                role: 'alert'
            })
        );
    const top = model.error ? 108 : 60;
    nodes.push(
        node(
            'Scroll',
            'systemBody',
            rect(pad, top, bodyWidth, Math.max(0, height - top - pad)),
            { contentHeight: y, children: content }
        )
    );
    return { nodes };
}
