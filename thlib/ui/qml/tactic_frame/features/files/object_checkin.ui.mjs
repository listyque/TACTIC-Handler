import { spacing } from '../../core/foundation.mjs';
import { captionedSwitch } from '../../controls/forms/toggle.ui.mjs';
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { sourceIcon, prettySize } from './file_values.mjs';
import * as Confirmation from '../../controls/feedback/confirmation.ui.mjs';

export function modeChoice(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        compact = width < 360,
        headingHeight = model.inline ? 26 : 64,
        columns = compact || model.inline ? 2 : 3,
        gap = 8,
        cell = (width - gap * (columns - 1)) / columns,
        children = [
            label(
                'multiFileCheckinQuestion',
                rect(0, 0, width, headingHeight),
                model.inline
                    ? tr('Check in multiple files?')
                    : tr(
                          '{count} files selected. Check in one group or separately in sequence?',
                          { count: model.count }
                      ),
                { wrap: true }
            )
        ],
        choices = [
            ['group', 'One group', 'multiFileCheckinGroupButton'],
            ['individual', 'Separately', 'multiFileCheckinSeparateButton']
        ];
    if (!model.inline)
        choices.push(['cancel', 'Cancel', 'multiFileCheckinCancelButton']);
    choices.forEach(([value, title, id], index) =>
        children.push(
            button(
                id,
                rect(
                    index < columns ? index * (cell + gap) : 0,
                    headingHeight + 10 + Math.floor(index / columns) * 46,
                    index >= columns ? width : cell,
                    38
                ),
                tr(title),
                '',
                { type: 'mode', value },
                !model.busy,
                { highlighted: value === (model.mode || 'group') }
            )
        )
    );
    return {
        height: headingHeight + 10 + Math.ceil(choices.length / columns) * 46,
        nodes: children
    };
}

export function revision(model, width, height, language) {
    return Confirmation.describe(
        {
            message: translate(
                'The file stored in this revision will be replaced. Use Save snapshot when you need a new version.',
                language
            ),
            accept: 'Replace revision',
            destructive: true,
            busy: !!model.busy,
            acceptId: 'revisionCheckinAccept',
            rejectId: 'revisionCheckinCancel'
        },
        width,
        height,
        language
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        margin = spacing.content,
        inner = Math.max(0, width - margin * 2 - 16),
        nodes = [],
        body = [],
        footerHeight = width < 370 ? 96 : 52;
    const canChoose =
        !model.busy &&
        (!model.append || !!model.ready) &&
        !model.appendUncertain;
    let y = 0;
    if (model.append)
        nodes.push(
            node('Box', 'snapshotAppendSurface', rect(0, 0, width, height), {
                background: 'surfaceContainerHigh',
                radius: 0
            })
        );
    function notice(id, text, error) {
        if (!text) return;
        const h = Math.max(40, captionHeight(text, inner - 20) * 1.2 + 16);
        body.push(
            node('Box', id, rect(0, y, inner, h), {
                background: error ? 'errorContainer' : 'surfaceContainerLow',
                radius: 12,
                children: [
                    label(id + 'Text', rect(10, 8, inner - 20, h - 16), text, {
                        wrap: true,
                        color: error ? 'error' : 'secondaryText',
                        role: error ? 'alert' : 'status'
                    })
                ]
            })
        );
        y += h + 8;
    }
    if (model.busy) notice('objectCheckinBusy', tr('Loading data…'), false);
    notice('objectCheckinError', model.error, true);
    if (model.appendUncertain)
        notice(
            'objectCheckinUnknown',
            tr(
                'The attachment result is unknown. Close this window and refresh the snapshot before retrying.'
            ),
            true
        );
    if (model.revision)
        notice(
            'objectCheckinRevisionNotice',
            tr(
                'The file stored in this revision will be replaced. Use Save snapshot when you need a new version.'
            ),
            false
        );
    const fields = [];
    if (!model.revision && !model.append)
        fields.push({
            field: 'repositoryAlias',
            title: 'Repository',
            kind: 'Choice',
            value: model.repositoryAlias,
            options: model.repositories
        });
    if (!model.preview)
        fields.push(
            {
                field: 'process',
                title: 'Process',
                kind: 'Choice',
                value: model.process,
                options: model.processes,
                readOnly: model.revision || model.append
            },
            {
                field: 'context',
                title: 'Context',
                kind: 'Field',
                text: model.context,
                readOnly: model.revision || model.append
            }
        );
    if (model.append)
        fields.push({
            field: 'fileType',
            title: 'File type',
            kind: 'Field',
            text: model.fileType ?? 'attachment'
        });
    const columns = inner >= 650 ? 2 : 1,
        cellWidth = (inner - (columns - 1) * 12) / columns;
    fields.forEach((field, index) => {
        const x = (index % columns) * (cellWidth + 12),
            top = y + Math.floor(index / columns) * 72;
        body.push(
            label(
                'objectCheckinLabel_' + field.field,
                rect(x, top, cellWidth, 22),
                tr(field.title),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
        body.push(
            node(
                field.kind,
                'objectCheckinField_' + field.field,
                rect(x, top + 26, cellWidth, 36),
                {
                    label: tr(field.title),
                    text: field.text,
                    value: field.value,
                    options: field.options,
                    enabled: !model.busy && !field.readOnly,
                    maxLength:
                        field.field === 'context'
                            ? 256
                            : field.field === 'fileType'
                              ? 128
                              : undefined,
                    action: { type: 'field', field: field.field }
                }
            )
        );
    });
    y += Math.ceil(fields.length / columns) * 72;
    if (!model.append) {
        body.push(
            label(
                'objectCheckinDescriptionLabel',
                rect(0, y, inner, 22),
                tr('Description'),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
        body.push(
            node(
                'Area',
                'objectCheckinDescription',
                rect(0, y + 26, inner, 72),
                {
                    label: tr('Description'),
                    text: model.description || '',
                    enabled: !model.busy,
                    action: { type: 'field', field: 'description' }
                }
            )
        );
        y += 108;
    }
    const compact = inner < 420,
        chooseWidth = compact ? inner - 44 : Math.min(260, inner - 150);
    body.push(
        button(
            'objectCheckinChooseFiles',
            rect(0, y, chooseWidth, 38),
            tr('Choose files for check-in'),
            'upload',
            { type: 'choose' },
            canChoose
        )
    );
    body.push(
        button(
            'objectCheckinClipboard',
            rect(
                chooseWidth + 8,
                y,
                compact ? 36 : Math.max(0, inner - chooseWidth - 8),
                38
            ),
            tr('Save from Clipboard'),
            'clipboard',
            { type: 'clipboard' },
            canChoose,
            { iconOnly: compact }
        )
    );
    y += 48;
    const listHeight = model.count ? Math.min(220, model.count * 44) : 54;
    body.push(
        node('List', 'objectCheckinFiles', rect(0, y, inner, listHeight), {
            source: 'files',
            keyField: 'key',
            rowHeight: 44,
            rowGap: 2,
            label: tr('Source files'),
            fields: ['key', 'index', 'path', 'title', 'size', 'canRemove']
        })
    );
    if (!model.count)
        body.push(
            label(
                'objectCheckinFilesEmpty',
                rect(8, y + 2, inner - 24, 46),
                tr(
                    'Drop files here, paste an image, or choose files for check-in.'
                ),
                { wrap: true, color: 'secondaryText', fontRole: 'secondary' }
            )
        );
    y += listHeight + 12;
    if (model.count > 1 && !model.append) {
        const choices = modeChoice(
            { inline: true, mode: model.mode, busy: model.busy },
            inner,
            language
        );
        body.push(
            node(
                'Box',
                'objectCheckinModeChoice',
                rect(0, y, inner, choices.height),
                { children: choices.nodes }
            )
        );
        y += choices.height + 8;
    }
    body.push(
        captionedSwitch('objectCheckinKeepName', rect(0, y, inner, 36), {
            text: tr('Keep original file names'),
            checked: !!model.keepFileName,
            enabled: !model.busy,
            action: { type: 'field', field: 'keepFileName' }
        })
    );
    y += 46;
    if (model.discard) {
        notice(
            'objectCheckinDiscardNotice',
            tr('Discard unsaved changes?'),
            false
        );
        const w = (inner - 8) / 2;
        body.push(
            button(
                'objectCheckinContinue',
                rect(0, y, w, 38),
                tr('Continue editing'),
                '',
                { type: 'continue' },
                !model.busy
            )
        );
        body.push(
            button(
                'objectCheckinDiscard',
                rect(w + 8, y, w, 38),
                tr('Discard'),
                '',
                { type: 'discard' },
                !model.busy,
                { destructive: true }
            )
        );
        y += 48;
    }
    nodes.push(
        node(
            'Scroll',
            'objectCheckinBody',
            rect(
                margin,
                margin,
                width - margin * 2,
                Math.max(0, height - footerHeight - margin - 8)
            ),
            {
                contentHeight: y,
                scrollbarId: 'objectCheckinBodyScrollBar',
                children: body
            }
        )
    );
    const stacked = width < 370,
        buttonWidth = stacked ? width - margin * 2 : 96,
        buttonY = height - footerHeight + 6;
    nodes.push(
        button(
            'objectCheckinCancel',
            rect(margin, buttonY, buttonWidth, 38),
            tr('Cancel'),
            '',
            { type: 'close' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'objectCheckinSubmit',
            rect(
                stacked ? margin : margin + buttonWidth + 8,
                buttonY + (stacked ? 46 : 0),
                stacked ? buttonWidth : width - margin * 2 - buttonWidth - 8,
                38
            ),
            tr(model.append ? 'Attach files' : 'Add to Commit Queue'),
            'save',
            { type: 'submit' },
            !!model.ready &&
                !model.busy &&
                !model.appendUncertain &&
                model.count > 0 &&
                !!(String(model.context || '').trim() || model.process) &&
                (!model.revision || !!model.confirmed) &&
                (model.append || !!model.hasQueue),
            { highlighted: true }
        )
    );
    return { nodes };
}

export function fileRow(record, width, language) {
    return {
        nodes: [
            node(
                'Box',
                'objectCheckinFile_' + record.key,
                rect(0, 0, width, 42),
                {
                    background: 'surfaceContainerLow',
                    radius: 10,
                    children: [
                        node(
                            'Icon',
                            'objectCheckinFileIcon_' + record.key,
                            rect(8, 12, 18, 18),
                            { icon: sourceIcon(record.path), color: 'action' }
                        ),
                        label(
                            'objectCheckinFileName_' + record.key,
                            rect(34, 3, Math.max(0, width - 72), 20),
                            record.title,
                            { toolTip: record.path, elideMiddle: true }
                        ),
                        label(
                            'objectCheckinFileSize_' + record.key,
                            rect(34, 24, Math.max(0, width - 72), 15),
                            prettySize(record.size),
                            { fontRole: 'caption', color: 'secondaryText' }
                        ),
                        button(
                            'objectCheckinFileRemove_' + record.key,
                            rect(width - 34, 7, 28, 28),
                            translate('Remove file', language),
                            'close',
                            {
                                type: 'removeFile',
                                index: record.index,
                                path: record.path
                            },
                            !!record.canRemove,
                            { iconOnly: true, iconAction: true }
                        )
                    ]
                }
            )
        ]
    };
}
