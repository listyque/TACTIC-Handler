// Executable compositions of house controls; every draft belongs to this local scene.
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import {
    examples,
    initial as variantInitial
} from '../../controls/catalog/variants.mjs';
import { surfaces } from '../tasks/workspace.ui.mjs';
import { title as variantTitle } from './showcase.variants.mjs';

export const families = [
    'search',
    'identity',
    'menus',
    'popups',
    'feedback',
    'tables',
    'scroll-layout',
    'previews',
    'drag-files',
    'editors',
    'graphs',
    'input-runtime',
    'domain-fragments'
];
const photo =
    examples.find(
        (row) =>
            row.kind === 'Preview' &&
            String(row.properties.source).startsWith('data:')
    )?.properties.source || '';
const tableRows = Array.from({ length: 100 }, (_, i) => ({
    selected: false,
    name: 'Object ' + (i + 1),
    value: String(i * 10)
}));

export function models(model) {
    return {
        sampleCells:
            model.family !== 'tables' || model.state === 'empty'
                ? []
                : tableRows
    };
}

export function cell(grid, record, row, column, model, language = 'en') {
    const key = row + ':' + column;
    return {
        nodes: [
            node(
                column === 0 ? 'CheckBox' : 'Field',
                'sampleCell_' + key,
                rect(0, 0, grid.cellWidth, grid.rowHeight),
                {
                    text:
                        column === 0
                            ? ''
                            : model.cells[key] === undefined
                              ? column === 1
                                  ? 'Object ' + (row + 1)
                                  : String(row * 10)
                              : String(model.cells[key]),
                    checked:
                        model.cells[key] === undefined
                            ? model.state === 'selected' && row === 0
                            : !!model.cells[key],
                    label: translate(
                        column === 0 ? 'Selected' : 'Value',
                        language
                    ),
                    tableCell: true,
                    enabled: grid.enabled && !grid.readOnly,
                    readOnly: grid.readOnly,
                    action: { type: 'sampleCell', row, column }
                }
            )
        ]
    };
}

export function describe(model, family, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        enabled = !['disabled', 'readonly', 'loading'].includes(model.state),
        flags = {
            enabled: !['disabled', 'loading'].includes(model.state),
            readOnly: model.state === 'readonly',
            error: model.state === 'error'
        },
        h = model.state === 'long' ? 64 : 36;
    let y = 0;
    function add(kind, id, height, props, w = width) {
        nodes.push(node(kind, id, rect(0, y, w, height), props));
        y += height + 16;
    }
    function title(text) {
        add('Label', 'sampleTitle_' + y, 28, {
            text: tr(text),
            fontRole: 'section',
            weight: 600
        });
    }
    function action(id, text, type, value) {
        nodes.push(
            button(
                id,
                rect(0, y, Math.min(width, 240), 36),
                tr(text),
                '',
                { type, value },
                enabled
            )
        );
        y += 52;
    }
    if (model.state === 'loading' && !['search', 'feedback'].includes(family))
        add('Progress', 'sampleLoading', 4, {
            text: tr('Loading'),
            indeterminate: true
        });
    if (model.state === 'error' && family !== 'feedback')
        add('Label', 'sampleError', 40, {
            text: tr('Something went wrong'),
            color: 'error',
            role: 'alert',
            wrap: true
        });
    if (family === 'search') {
        title('Search suggestions');
        const rows =
            model.state === 'empty' || model.state === 'loading'
                ? []
                : ['Robot Arm', 'Robot Body', 'Workshop']
                      .filter((text) =>
                          text
                              .toLowerCase()
                              .includes(model.search.toLowerCase())
                      )
                      .map((text, i) => ({
                          title: text,
                          description: tr('Example'),
                          code: String(i)
                      }));
        add(
            'Search',
            'sampleSearch',
            44,
            Object.assign({}, flags, {
                text: model.search,
                placeholder: tr('Search objects'),
                label: tr('Search objects'),
                suggestions: rows,
                errorText: model.state === 'error' ? tr('Search failed') : '',
                action: { type: 'search' },
                acceptAction: { type: 'searchAccept' },
                commitAction: { type: 'searchSubmit' }
            })
        );
        if (model.state === 'loading')
            add('Progress', 'sampleSearchPending', 4, {
                text: tr('Loading'),
                indeterminate: true
            });
        add('Label', 'sampleSearchCount', 28, {
            text: String(rows.length) + ' · ' + tr('Search suggestions'),
            color: 'secondaryText'
        });
    } else if (family === 'identity') {
        for (const [login, name, initials, retired, emphasized] of [
            ['admin', 'Administrator', 'A', false, true],
            [
                'vfx_anna',
                model.state === 'long' ? model.text.repeat(4) : 'Anna',
                'VA',
                false,
                false
            ],
            ['archived', 'Retired', 'AR', true, false]
        ]) {
            add('Identity', 'sampleIdentity_' + login, 52, {
                text: tr(name),
                login,
                initials,
                accent: 'action',
                retired,
                emphasized,
                opacity: model.state === 'disabled' ? 0.5 : 1
            });
        }
        add('UserChoice', 'sampleIdentityChoice', 36, {
            value: model.user,
            options: [
                { value: 'admin', label: 'Administrator', login: 'admin' },
                { value: 'vfx_anna', label: 'Anna', login: 'vfx_anna' }
            ],
            enabled,
            action: { type: 'user' },
            label: tr('User')
        });
    } else if (family === 'menus') {
        title('Context menu');
        add(
            'View',
            'sampleMenu',
            36,
            {
                view: 'showcaseMenu',
                text: tr('Open menu'),
                enabled,
                checked: model.menuChecked,
                language,
                action: { type: 'sampleMenu' },
                actions: [
                    { title: tr('Actions'), header: true, translate: false },
                    {
                        title: tr('Edit'),
                        command: 'edit',
                        icon: 'edit',
                        translate: false
                    },
                    {
                        title: tr('Selected'),
                        command: 'toggle',
                        checked: model.menuChecked,
                        translate: false
                    },
                    { separator: true },
                    {
                        title: tr('More'),
                        children: [
                            {
                                title: tr('Refresh'),
                                command: 'refresh',
                                icon: 'refresh',
                                translate: false
                            }
                        ],
                        translate: false
                    },
                    {
                        title: tr('Delete'),
                        command: 'delete',
                        icon: 'delete',
                        enabled: false,
                        translate: false
                    }
                ]
                    .filter((row) => model.state !== 'empty')
                    .concat(
                        model.state === 'empty'
                            ? [
                                  {
                                      title: tr('No results'),
                                      enabled: false,
                                      translate: false
                                  }
                              ]
                            : []
                    )
            },
            Math.min(width, 240)
        );
        add('Label', 'sampleMenuResult', 40, {
            text: model.last || tr('Choose an action'),
            wrap: true
        });
    } else if (family === 'popups') {
        title('Confirmation');
        action('sampleOpenDialog', 'Open dialog', 'sampleDialogOpen');
        add('View', 'sampleDialog', 0, {
            view: 'showcaseDialog',
            text: tr('Confirmation'),
            message:
                model.state === 'empty'
                    ? ''
                    : model.state === 'long'
                      ? model.text.repeat(8)
                      : tr('Changes stay in this example.'),
            open: model.dialogOpen,
            popupWidth: 440,
            cancelText: tr('Cancel'),
            acceptText: tr('Apply'),
            enabled,
            language,
            error: flags.error,
            action: { type: 'sampleDialog' }
        });
        add('Label', 'sampleDialogResult', 36, {
            text: model.last || tr('No changes'),
            wrap: true
        });
    } else if (family === 'feedback') {
        title('Progress');
        add('Progress', 'sampleProgress', 4, {
            text: tr('Progress'),
            value: model.progress / 100,
            indeterminate: model.state === 'loading'
        });
        add('Label', 'sampleProgressValue', 28, {
            text: String(model.progress) + '%'
        });
        action('sampleAdvance', 'Continue', 'sampleAdvance');
        add('Empty', 'sampleEmpty', 220, {
            text: tr(
                model.state === 'error' ? 'Something went wrong' : 'No results'
            ),
            message: tr('Changes stay in this example.'),
            error: flags.error,
            icon: flags.error ? 'alert' : 'search',
            actionText: tr('Retry'),
            actionIcon: 'refresh',
            action: { type: 'sampleRetry' },
            enabled
        });
    } else if (family === 'tables') {
        title('Table');
        add('Grid', 'sampleGrid', 330, {
            text: tr('Table'),
            source: 'sampleCells',
            cellWidth: 160,
            rowHeight: 38,
            labelWidth: 40,
            headerHeight: 32,
            rowHeaders: models(model).sampleCells.map((_, i) => ({
                label: String(i + 1)
            })),
            columnHeaders: [tr('Selected'), tr('Name'), tr('Value')],
            revision: model.revision,
            enabled,
            readOnly: flags.readOnly
        });
        if (model.state === 'empty')
            add('Empty', 'sampleGridEmpty', 180, {
                text: tr('No results'),
                icon: 'table'
            });
    } else if (family === 'scroll-layout') {
        title('Resizable panels');
        const split = Math.max(0, Math.min(width - 60, model.split * width));
        const pane = (id, x, w) =>
            node('Scroll', id, rect(x, y, w, 240), {
                contentWidth: 420,
                contentHeight: 700,
                children: Array.from({ length: 14 }, (_, i) =>
                    label(
                        id + '_' + i,
                        rect(12, i * 48, 380, 36),
                        tr('Row') + ' ' + (i + 1)
                    )
                )
            });
        nodes.push(
            pane('sampleLeftPane', 0, split),
            pane(
                'sampleRightPane',
                split + 12,
                Math.max(0, width - split - 12)
            ),
            node('Splitter', 'sampleSplitter', rect(split, y, 12, 240), {
                min: 0,
                max: Math.max(48, width - 60),
                value: split,
                enabled,
                text: tr('Resize panels'),
                action: { type: 'sampleSplit', width },
                commitAction: { type: 'sampleSplit', width }
            })
        );
        y += 256;
        action(
            'sampleCollapsePane',
            model.split < 0.2 ? 'Expand' : 'Collapse',
            'sampleCollapse'
        );
    } else if (family === 'previews') {
        const thumbnails = [
            'preview-round',
            'preview-square',
            'preview-outline',
            'preview-photo',
            'preview-contain',
            'preview-icon',
            'preview-loading',
            'preview-selected'
        ];
        const columns = width >= 560 ? 4 : width >= 280 ? 2 : 1;
        const cellWidth = (width - (columns - 1) * 16) / columns;
        for (let index = 0; index < thumbnails.length; index++) {
            const id = thumbnails[index],
                example = examples.find((row) => row.id === id);
            const x = (index % columns) * (cellWidth + 16),
                top = y + Math.floor(index / columns) * 144;
            nodes.push(
                node(
                    'Preview',
                    'sample_' + id,
                    rect(x, top, 96, 96),
                    Object.assign({}, example.properties, {
                        round: example.properties.round === true,
                        source:
                            model.state === 'empty' || model.state === 'error'
                                ? ''
                                : example.properties.source,
                        loading:
                            model.state === 'loading' ||
                            example.properties.loading,
                        selected:
                            model.state === 'selected' ||
                            example.properties.selected,
                        fit: id === 'preview-contain' ? 'contain' : 'cover'
                    })
                )
            );
            nodes.push(
                label(
                    'caption_' + id,
                    rect(x, top + 104, cellWidth, 32),
                    variantTitle(id, language),
                    {
                        fontRole: 'caption',
                        wrap: true
                    }
                )
            );
        }
        y += Math.ceil(thumbnails.length / columns) * 144;
        for (const id of [
            'preview-card',
            'attachment-image',
            'attachment-file'
        ]) {
            const example = examples.find((row) => row.id === id);
            title(variantTitle(id, language));
            add('View', 'sample_' + id, example.height, {
                view: 'showcaseVariant',
                model: variantInitial(id),
                state: model.state,
                language,
                gallery: id
            });
        }
    } else if (family === 'drag-files') {
        title('Files');
        add(
            'FileField',
            'sampleFile',
            44,
            Object.assign({}, flags, {
                text: model.files.map((file) => file.name).join(', '),
                label: tr('Choose file'),
                action: { type: 'sampleFiles' }
            })
        );
        add('Box', 'sampleDrop', 144, {
            enabled,
            background: 'surfaceContainerLow',
            border: flags.error ? 'error' : 'outlineVariant',
            radius: 8,
            dropAction: { type: 'sampleFiles', name: 'file-ingest' },
            children: [
                label(
                    'sampleDropText',
                    rect(16, 16, Math.max(0, width - 32), 110),
                    tr('Drop files here or choose a file above.'),
                    { wrap: true, align: 'center' }
                )
            ]
        });
        for (const file of model.files)
            add('Label', 'sampleFile_' + y, 36, {
                text: file.name,
                elideMiddle: true
            });
        action('sampleFilesClear', 'Clear', 'sampleFilesClear');
    } else if (family === 'editors') {
        title('Source code');
        add(
            'Code',
            'sampleEditor',
            320,
            Object.assign({}, flags, {
                text: model.state === 'empty' ? '' : model.editorText,
                service: 'sourceEditor',
                bufferKey: 'showcaseEditable',
                language,
                syntax: 'python',
                action: { type: 'sampleEditor' }
            })
        );
    } else if (family === 'graphs') {
        title('Graph');
        const records =
            model.state === 'empty'
                ? []
                : [
                      {
                          identity: 'a',
                          label: 'Model',
                          nodeX: 24,
                          nodeY: 24,
                          color: 'action'
                      },
                      {
                          identity: 'b',
                          label: 'Review',
                          nodeX: Math.min(width - 180, 300),
                          nodeY: 160,
                          color: 'action'
                      }
                  ];
        add(
            'Graph',
            'sampleGraph',
            360,
            Object.assign({}, flags, {
                enabled,
                nodes: records.map((row) =>
                    Object.assign(
                        {},
                        row,
                        model.graphPositions.find(
                            (p) => p.identity === row.identity
                        ) || {}
                    )
                ),
                edges: records.length ? [{ from: 'a', to: 'b' }] : [],
                selectedNodes:
                    model.state === 'selected' ? ['a'] : model.graphSelected,
                resetKey: 'showcaseGraph_' + model.resetRevision,
                action: { type: 'sampleGraph' },
                selectAction: { type: 'sampleGraphSelect' },
                moveAction: { type: 'sampleGraphMove' }
            })
        );
        action('sampleGraphReset', 'Reset', 'sampleGraphReset');
    } else if (family === 'input-runtime') {
        title('Mouse, keyboard and touch');
        add('Button', 'sampleActivation', h, {
            text:
                model.state === 'long' ? model.text.repeat(3) : tr('Activate'),
            enabled,
            action: { type: 'sampleActivate' },
            pressAction: { type: 'samplePress' },
            cancelAction: { type: 'sampleCancel' },
            toolTip: tr('Mouse, keyboard and touch')
        });
        add(
            'Field',
            'sampleIME',
            36,
            Object.assign({}, flags, {
                text: model.ime,
                label: tr('Text'),
                placeholder: 'IME · Кириллица · 日本語',
                action: { type: 'sampleIME' }
            })
        );
        add('Label', 'sampleInputCounts', 44, {
            text:
                tr('Activated') +
                ': ' +
                model.activations +
                ' · ' +
                tr('Pressed') +
                ': ' +
                model.presses +
                ' · ' +
                tr('Cancelled') +
                ': ' +
                model.cancels,
            wrap: true
        });
    } else if (family === 'domain-fragments') {
        title('Task workspace surface');
        const part = surfaces(
            { value: model.surface, disabled: !enabled, controlHeight: 36 },
            width,
            language
        );
        add('Box', 'sampleTaskSurfaces', part.height, {
            background: 'transparent',
            children: part.nodes
        });
        add('Identity', 'sampleTaskAssignee', 48, {
            text: 'Anna',
            login: 'vfx_anna',
            initials: 'VA',
            accent: 'action'
        });
        add('StatusChip', 'sampleTaskStatus', 32, {
            text: tr('In progress'),
            accent: 'action'
        });
        add(
            'Area',
            'sampleTaskDraft',
            100,
            Object.assign({}, flags, {
                text: model.taskDraft,
                label: tr('Description'),
                action: { type: 'sampleTaskDraft' }
            })
        );
        action('sampleTaskSave', 'Save', 'sampleTaskSave');
        if (model.last === 'sampleTaskSave')
            add('Label', 'sampleTaskSaved', 28, {
                text: tr('Saved'),
                color: 'green',
                role: 'status'
            });
    }
    const scene = { nodes, models: models(model) };
    // All geometry and control properties are copyable; ports/cell callbacks have named public owners.
    const code =
        "import * as Showcase from './features/administration/showcase.ui.mjs';\n\n" +
        '// FrameView: models = example.models; local model = Showcase.initial();\n' +
        '// describeCell = (grid, record, row, column) => Showcase.cell(grid, record, row, column, model);\n' +
        '// Menu/dialog ports: ComponentShowcase hosts. Events: Showcase.transition.\n' +
        '(' +
        JSON.stringify(scene, null, 2) +
        ')';
    return { nodes, height: y, code };
}
