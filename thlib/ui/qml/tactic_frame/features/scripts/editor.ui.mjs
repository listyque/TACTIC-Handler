import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = Object.freeze({
    inset: 8,
    gap: 4,
    toolbar: 32,
    tabs: 38,
    outputHeader: 40,
    footer: 38,
    minimumMain: 360,
    minimumTree: 160
});

export function layout(model, width, height) {
    const { inset, gap, toolbar, tabs, outputHeader, footer } = metrics;
    const inner = Math.max(0, width - inset * 2);
    const treeWidth = model.treeHidden
        ? 0
        : Math.min(
              Math.max(metrics.minimumTree, model.treeWidth || 200),
              Math.max(0, inner - metrics.minimumMain - gap)
          );
    const mainWidth = inner - (treeWidth ? treeWidth + gap : 0);
    const bodyHeight = Math.max(0, height - inset * 2);
    const noticeHeight = model.notice ? 38 : 0;
    const outputHeight = Math.min(
        model.outputHidden
            ? outputHeader
            : Math.max(80, model.outputHeight || 120),
        Math.max(
            outputHeader,
            bodyHeight - toolbar - tabs - footer - noticeHeight - 128
        )
    );
    const outputTop = toolbar + gap + tabs + gap;
    const sourceTop = outputTop + outputHeight + gap;
    const footerTop = Math.max(
        sourceTop,
        bodyHeight - footer - noticeHeight - gap
    );
    return {
        main: rect(inset, inset, mainWidth, bodyHeight),
        toolbar: rect(0, 0, mainWidth, toolbar),
        tabs: rect(0, toolbar + gap, mainWidth, tabs),
        output: rect(0, outputTop, mainWidth, outputHeight),
        outputSplitter: rect(0, outputTop + outputHeight, mainWidth, gap),
        source: rect(0, sourceTop, mainWidth, footerTop - sourceTop - gap),
        footer: rect(0, footerTop, mainWidth, footer),
        notice: rect(0, footerTop + footer + gap, mainWidth, noticeHeight),
        treeSplitter: rect(inset + mainWidth, inset, gap, bodyHeight),
        tree: rect(inset + mainWidth + gap, inset, treeWidth, bodyHeight),
        treeVisible: treeWidth > 0
    };
}

export function commands(model) {
    const idle = !model.busy && !model.running;
    return {
        create: idle && model.canEdit,
        save: idle && model.editable && !model.uncertain,
        run: idle && model.editable && !!model.source?.trim(),
        refresh: idle,
        triggers: idle && model.canEdit && model.native,
        drafts: idle && model.canEdit,
        closeAll: idle && model.tabCount > 0
    };
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language),
        allowed = commands(model);
    const contentWidth = Math.max(480, width),
        nodes = [];
    nodes.push(
        button(
            'scriptNew',
            rect(0, 1, 30, 30),
            tr('New script'),
            'add',
            { type: 'create' },
            allowed.create,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'scriptSave',
            rect(34, 1, 30, 30),
            tr('Save current script to server'),
            'save',
            { type: 'save' },
            allowed.save,
            { iconOnly: true }
        )
    );
    const fieldWidth = (contentWidth - 340) / 2;
    nodes.push(
        node('Field', 'scriptFolder', rect(72, 1, fieldWidth, 30), {
            text: model.folder || '',
            label: tr('Script folder'),
            placeholder: tr('Folder'),
            enabled: !model.busy && !model.running,
            readOnly: !model.editable,
            action: { type: 'folder' }
        })
    );
    nodes.push(
        label(
            'scriptPathSeparator',
            rect(74 + fieldWidth, 1, 12, 30),
            '/',
            muted
        )
    );
    nodes.push(
        node('Field', 'scriptTitle', rect(88 + fieldWidth, 1, fieldWidth, 30), {
            text: model.title || '',
            label: tr('Script title'),
            placeholder: tr('Title'),
            enabled: !model.busy && !model.running,
            readOnly: !model.editable,
            action: { type: 'title' }
        })
    );
    const languageX = 94 + fieldWidth * 2;
    nodes.push(
        node('Choice', 'scriptLanguage', rect(languageX, 1, 132, 30), {
            value: model.language,
            label: tr('Script language'),
            enabled: !model.busy && !model.running && model.canEdit,
            options: (model.languages || []).map((row) =>
                Object.assign({}, row, {
                    label: tr(row.label)
                })
            ),
            action: { type: 'language' }
        })
    );
    [
        ['triggers', 'Script triggers', 'bolt'],
        ['drafts', 'Agent drafts', 'code'],
        ['refresh', 'Refresh scripts from server', 'refresh'],
        [
            'tree',
            model.treeHidden
                ? 'Show scripts and outline'
                : 'Hide scripts and outline',
            model.treeHidden ? 'chevron-left' : 'chevron-right'
        ]
    ]
        .filter(
            (row) =>
                row[0] !== 'drafts' ||
                !model.native ||
                model.streamApi !== false
        )
        .forEach((row, index) =>
            nodes.push(
                button(
                    'script_' + row[0],
                    rect(languageX + 136 + index * 28, 3, 26, 26),
                    tr(row[1]),
                    row[2],
                    { type: row[0] },
                    row[0] === 'tree' || allowed[row[0]],
                    {
                        iconOnly: true,
                        highlighted: row[0] === 'tree' && !model.treeHidden
                    }
                )
            )
        );
    return { nodes, contentWidth };
}

export function outputToolbar(model, width, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            node('Icon', 'scriptOutputIcon', rect(8, 10, 16, 16), {
                icon: 'terminal',
                color: 'action'
            }),
            label(
                'scriptOutputTitle',
                rect(30, 4, Math.max(0, width - 126), 28),
                tr('Output'),
                { weight: 600 }
            ),
            ...[
                ['wrap', 'Wrap output', 'wrap-lines'],
                ['clear', 'Clear output', 'delete-sweep'],
                [
                    'output',
                    model.outputHidden ? 'Expand output' : 'Collapse output',
                    model.outputHidden ? 'expand-more' : 'expand-less'
                ]
            ].map((row, index) =>
                button(
                    'scriptOutput_' + row[0],
                    rect(width - 90 + index * 28, 5, 26, 26),
                    tr(row[1]),
                    row[2],
                    { type: row[0] },
                    row[0] !== 'clear' || !!model.output,
                    {
                        iconOnly: true,
                        highlighted: row[0] === 'wrap' && model.outputWrap
                    }
                )
            )
        ]
    };
}

export function footer(model, width, language) {
    const tr = (text) => translate(text, language),
        targetWidth = Math.min(220, Math.max(100, width - 230));
    return {
        nodes: [
            button(
                'scriptRun',
                rect(0, 0, 124, 38),
                tr('Run Script'),
                'play-arrow',
                { type: 'run' },
                commands(model).run,
                { highlighted: true }
            ),
            label(
                'scriptRunIn',
                rect(width - targetWidth - 74, 0, 68, 38),
                tr(model.running ? 'Running…' : 'Run in'),
                muted
            ),
            node(
                'Choice',
                'scriptTarget',
                rect(width - targetWidth, 0, targetWidth, 38),
                {
                    label: tr('Execution target'),
                    value: model.target,
                    options: (model.targets || []).map((row) =>
                        Object.assign({}, row, {
                            label:
                                row.translate === false
                                    ? row.label
                                    : tr(row.label)
                        })
                    ),
                    enabled:
                        model.canEdit &&
                        !model.busy &&
                        !model.running &&
                        (model.targets || []).length > 1,
                    action: { type: 'target' }
                }
            )
        ]
    };
}

export function sideTabs(model, width, language) {
    return {
        nodes: [
            node(
                'Segmented',
                'scriptSideMode',
                rect(4, 4, Math.max(0, width - 8), 28),
                {
                    label: translate('Scripts panel', language),
                    value: model.side,
                    options: ['scripts', 'outline'].map((value) => ({
                        value,
                        label: translate(
                            value === 'scripts' ? 'Scripts' : 'Outline',
                            language
                        )
                    })),
                    action: { type: 'side' }
                }
            )
        ]
    };
}

export function splitter(model, width, height, horizontal, language) {
    return {
        nodes: [
            node(
                'Splitter',
                horizontal ? 'scriptOutputSplitter' : 'scriptTreeSplitter',
                rect(0, 0, width, height),
                {
                    text: translate(
                        horizontal ? 'Output height' : 'Scripts panel width',
                        language
                    ),
                    horizontal,
                    reverse: !horizontal,
                    value: horizontal ? model.outputHeight : model.treeWidth,
                    min: horizontal ? 80 : 160,
                    max: 500,
                    action: { type: horizontal ? 'outputHeight' : 'treeWidth' }
                }
            )
        ]
    };
}
