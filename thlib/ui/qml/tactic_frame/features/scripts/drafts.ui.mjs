import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

function ordered(value) {
    if (Array.isArray(value)) return value.map(ordered);
    if (!value || typeof value !== 'object') return value;
    const result = {};
    for (const key of Object.keys(value).sort())
        result[key] = ordered(value[key]);
    return result;
}

function pretty(value) {
    return JSON.stringify(ordered(value), null, 2);
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const current = model.draft || {},
        document = current.document || {};
    const inset = 8,
        gap = 8,
        inner = Math.max(0, width - 16);
    const narrow = inner < 760;
    const bodyTop = 152,
        bodyHeight = Math.max(160, height - bodyTop - 96);
    const sourceWidth = narrow ? inner : Math.floor((inner - gap) / 2);
    const sourceHeight = narrow
        ? Math.floor((bodyHeight - gap) / 2)
        : bodyHeight;
    const source = rect(inset, bodyTop, sourceWidth, sourceHeight);
    const report = narrow
        ? rect(inset, bodyTop + sourceHeight + gap, inner, sourceHeight)
        : rect(
              inset + sourceWidth + gap,
              bodyTop,
              inner - sourceWidth - gap,
              bodyHeight
          );
    const idle = !model.busy;
    const status = current.activated
        ? tr('Activated')
        : current.ready
          ? tr('Ready for source review')
          : current.draft_id
            ? tr('Fresh passing trials are required')
            : tr('Select an agent draft');
    const binding = Object.assign({}, document);
    delete binding.source;
    const reports =
        tr('External host reports do not replace source review.') +
        '\n\n' +
        (current.draft_id ? pretty(binding) + '\n\n' : '') +
        (current.trials || [])
            .map((row) =>
                [
                    `${row.case.expect}: ${row.status} · ${row.trial_id}`,
                    row.draft_revision !== current.revision
                        ? tr('Stale source')
                        : current.activated
                          ? tr('Historical report')
                          : row.dependency_revision ===
                              current.dependency_revision
                            ? tr('Current dependencies')
                            : tr('Stale dependencies'),
                    row.image,
                    row.error || '',
                    pretty(row.result || {})
                ].join('\n')
            )
            .join('\n\n');
    return {
        nodes: [
            label(
                'agentDraftHeading',
                rect(inset, 8, Math.max(0, inner - 160), 32),
                tr('Agent drafts'),
                { weight: 600 }
            ),
            button(
                'agentDraftBack',
                rect(width - 156, 8, 148, 32),
                tr('Back to editor'),
                'arrow-back',
                { type: 'back' },
                idle
            ),
            node(
                'Choice',
                'agentDraftChoice',
                rect(inset, 48, Math.max(0, inner - 48), 36),
                {
                    value: model.selected || '',
                    label: tr('Agent draft'),
                    enabled: idle,
                    options: (model.drafts || []).map((row) => ({
                        value: row.draft_id,
                        label: row.title
                    })),
                    action: { type: 'select' }
                }
            ),
            button(
                'agentDraftRefresh',
                rect(width - 48, 48, 40, 36),
                tr('Refresh agent drafts'),
                'refresh',
                { type: 'refresh' },
                idle,
                { iconOnly: true }
            ),
            label(
                'agentDraftStatus',
                rect(inset, 88, inner, 24),
                model.error || (model.busy ? tr('Loading…') : status)
            ),
            label(
                'agentDraftOwner',
                rect(inset, 116, inner, 28),
                tr('Runs on the Handler desktop after activation.'),
                muted
            ),
            node('Area', 'agentDraftSource', source, {
                text: document.source || '',
                label: tr('Draft source'),
                readOnly: true,
                enabled: true,
                wrap: false
            }),
            node('Area', 'agentDraftReports', report, {
                text: reports || tr('No isolated trial reports yet.'),
                label: tr('Isolated trial reports'),
                readOnly: true,
                enabled: true
            }),
            node(
                'CheckBox',
                'agentDraftReviewed',
                rect(inset, height - 80, inner, 32),
                {
                    text: tr(
                        'I reviewed the source, binding and execution owner'
                    ),
                    checked: !!model.reviewed,
                    enabled:
                        idle &&
                        !model.error &&
                        !!current.ready &&
                        !current.activated,
                    action: { type: 'reviewed' }
                }
            ),
            button(
                'agentDraftActivate',
                rect(inset, height - 40, Math.min(340, inner), 32),
                tr(
                    model.confirming
                        ? 'Confirm activation on the desktop'
                        : 'Activate reviewed draft'
                ),
                'check',
                { type: 'activate' },
                idle &&
                    !model.error &&
                    !!current.ready &&
                    !current.activated &&
                    !!model.reviewed
            )
        ]
    };
}
