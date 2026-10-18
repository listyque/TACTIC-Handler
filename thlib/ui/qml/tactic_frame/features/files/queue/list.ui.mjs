import { captionedSwitch } from '../../../controls/forms/toggle.ui.mjs';
import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { toolbar } from './actions.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values);
    const w = width,
        h = height,
        children = [],
        actions = toolbar(model).filter((action) => action.visible),
        toolsWidth = (actions.length + 1) * 33,
        titleWidth = w >= 330 ? 85 : 0,
        countWidth = Math.max(32, 20 + String(model.count).length * 7);
    if (titleWidth) {
        children.push(
            node('Icon', 'commitQueueHeadingIcon', rect(11, 16, 16, 16), {
                icon: 'queue',
                color: 'action'
            })
        );
        children.push(
            label('commitQueueHeading', rect(33, 8, 50, 32), tr('QUEUE'), {
                fontRole: 'secondary',
                weight: 600,
                color: 'secondaryText'
            })
        );
    }
    children.push(
        node(
            'Box',
            'commitQueueCountPill',
            rect(10 + titleWidth, 13, countWidth, 22),
            {
                background: 'surfaceContainerHigh',
                radius: 11,
                children: [
                    label(
                        'commitQueueCount',
                        rect(0, 0, countWidth, 22),
                        String(model.count),
                        { fontRole: 'caption', weight: 600, align: 'center' }
                    )
                ]
            }
        )
    );
    children.push(
        button(
            'commitQueueHelpButton',
            rect(w - toolsWidth, 10, 28, 28),
            tr('Help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    actions.forEach((action, index) =>
        children.push(
            button(
                'commitQueueTool_' + action.command,
                rect(w - toolsWidth + (index + 1) * 33, 10, 28, 28),
                tr(action.title),
                action.icon,
                { type: action.command },
                action.enabled,
                { iconOnly: true, iconAction: true }
            )
        )
    );
    children.push(
        captionedSwitch(
            'commitQueueAutoCleanSwitch',
            rect(10, 47, w - 20, 32),
            {
                text: tr('Auto-clean'),
                checked: !!model.autoClean,
                enabled: !model.busy,
                action: { type: 'autoClean' }
            }
        )
    );
    let toolbarHeight = 86;
    if (model.serverQueueAvailable) {
        children.push(
            captionedSwitch(
                'commitQueueServerSwitch',
                rect(10, 82, w - 48, 32),
                {
                    text: tr('Server queue'),
                    checked: !!model.serverQueue,
                    enabled: !model.busy,
                    action: { type: 'serverQueue' }
                }
            )
        );
        children.push(
            node('Icon', 'commitQueueServerHelp', rect(w - 31, 89, 17, 17), {
                icon: 'info',
                color: 'secondaryText',
                toolTip: tr(
                    'Send files in chunks. The server checks in and reports results for the whole batch. Legacy mode is the default.'
                )
            })
        );
        toolbarHeight += 36;
    }
    const reselectHeight = model.record?.needsFiles ? 84 : 0,
        filesHeight = Math.min(
            Math.max(100, model.filesHeight || 142),
            Math.max(100, h - toolbarHeight - 110)
        ),
        filesTop = Math.max(
            toolbarHeight + 40,
            h - filesHeight - reselectHeight
        ),
        sourceStride = model.sourceTargets ? 45 : 34;
    children.push(
        node(
            'Box',
            'commitQueueListDivider',
            rect(0, toolbarHeight - 1, w, 1),
            { background: 'outlineVariant' }
        )
    );
    children.push(
        node(
            'List',
            'commitQueueRows',
            rect(
                6,
                toolbarHeight + 6,
                w - 12,
                Math.max(0, filesTop - toolbarHeight - 22)
            ),
            {
                source: 'operations',
                keyField: 'operationId',
                rowHeight: 72,
                rowGap: 4,
                label: tr('Commit Queue'),
                fields: [
                    'operationId',
                    'title',
                    'objectTitle',
                    'fileCount',
                    'context',
                    'status',
                    'selected',
                    'checked',
                    'progress',
                    'stage',
                    'error',
                    'canEdit',
                    'canCommit',
                    'previewUrl',
                    'canRetry'
                ]
            }
        )
    );
    if (!model.count)
        children.push(
            label(
                'commitQueueRowsEmpty',
                rect(12, toolbarHeight + 18, w - 24, 50),
                tr('No file check-ins yet.'),
                Object.assign({}, muted, { wrap: true, align: 'center' })
            )
        );
    children.push(
        node(
            'Splitter',
            'commitQueueFilesSplitter',
            rect(0, filesTop - 10, w, 10),
            {
                label: tr('Files pane height'),
                horizontal: true,
                reverse: true,
                value: filesHeight,
                min: 100,
                max: Math.max(100, Math.min(360, h - toolbarHeight - 110)),
                action: { type: 'filesHeightDraft' },
                commitAction: { type: 'filesHeight' },
                cancelAction: { type: 'filesHeightCancel' }
            }
        )
    );
    children.push(
        node('Box', 'commitQueueFileHeader', rect(0, filesTop, w, 36), {
            background: 'surfaceContainerLow',
            children: [
                node('Icon', 'commitQueueFilesIcon', rect(11, 10, 15, 15), {
                    icon: 'attachment',
                    color: 'action'
                }),
                label(
                    'commitQueueFilesHeading',
                    rect(32, 0, w - 76, 36),
                    tr('FILES'),
                    {
                        fontRole: 'secondary',
                        color: 'secondaryText',
                        weight: 600
                    }
                ),
                label(
                    'commitQueueFilesCount',
                    rect(w - 40, 0, 28, 36),
                    String(model.fileCount || 0),
                    {
                        fontRole: 'caption',
                        color: 'secondaryText',
                        align: 'right'
                    }
                )
            ]
        })
    );
    children.push(
        node(
            'List',
            'commitQueueSourceFiles',
            rect(6, filesTop + 40, w - 12, Math.max(0, filesHeight - 46)),
            {
                source: 'files',
                keyField: 'key',
                rowHeight: sourceStride,
                rowGap: 2,
                label: tr('FILES'),
                fields: [
                    'key',
                    'index',
                    'path',
                    'target',
                    'preview',
                    'canRemove'
                ]
            }
        )
    );
    if (!model.fileCount)
        children.push(
            label(
                'commitQueueSourceEmpty',
                rect(12, filesTop + 45, w - 24, 40),
                tr(
                    model.selected < 0
                        ? 'Select an operation to inspect its files.'
                        : 'No files'
                ),
                Object.assign({}, muted, { wrap: true, align: 'center' })
            )
        );
    if (reselectHeight) {
        children.push(
            label(
                'commitQueueReselectMessage',
                rect(10, h - 82, w - 20, 32),
                tr('Choose source files before check-in'),
                Object.assign({}, muted, { wrap: true })
            )
        );
        children.push(
            button(
                'commitQueueReselect',
                rect(10, h - 44, w - 118, 36),
                tr('Choose source files again'),
                'upload',
                { type: 'reselect' },
                !model.busy
            )
        );
        children.push(
            button(
                'commitQueueReselectDirectory',
                rect(w - 102, h - 44, 92, 36),
                tr('Directory'),
                'folder',
                { type: 'reselectDirectory' },
                !model.busy
            )
        );
    }
    return {
        nodes: [
            node('Box', 'commitQueueFilesDock', rect(0, 0, width, height), {
                background: 'panelDeep',
                border: 'outlineVariant',
                radius: 16,
                children
            })
        ]
    };
}
