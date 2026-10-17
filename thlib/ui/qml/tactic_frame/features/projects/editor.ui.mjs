import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Settings from '../configuration/settings.ui.mjs';
import { controls } from '../../core/foundation.mjs';

export function fields(model) {
    const fields = [
        {
            kind: 'Heading',
            id: 'projectEditorImageTitle',
            title: 'Project image',
            description:
                'Choose a large image; the repository web representation is used automatically when available.'
        },
        {
            kind: 'View',
            id: 'projectEditorImage',
            fullWidth: true,
            height: 210,
            props: { view: 'image' }
        },
        {
            kind: 'Heading',
            id: 'projectEditorDetails',
            title: 'Project details',
            description:
                'Category and type describe how the project is organized; the project code is permanent.'
        },
        {
            kind: 'Field',
            field: 'code',
            title: 'Project code',
            description:
                'Permanent TACTIC identifier. It cannot be changed here.',
            readOnly: true
        },
        {
            kind: 'Field',
            field: 'title',
            title: 'Name',
            description:
                'Human-readable project title shown throughout the application.',
            props: { maxLength: 100 }
        },
        {
            kind: 'Field',
            field: 'category',
            title: 'Category',
            description: 'Groups related projects in the chooser.'
        },
        {
            kind: model.typeOptions?.length ? 'Choice' : 'Field',
            field: 'type',
            title: 'Type',
            description: 'Project classification stored by TACTIC.',
            options: model.typeOptions
        },
        {
            kind: 'Area',
            field: 'description',
            title: 'Description',
            description:
                'Explain the purpose of the project for people browsing the workspace.',
            height: 96
        },
        {
            kind: 'Heading',
            id: 'projectEditorLifecycle',
            title: 'Lifecycle',
            description:
                'Archived projects stay on the server but are hidden by default. Templates are available for creating new projects.'
        },
        {
            kind: 'Switch',
            field: 'archived',
            title: 'Archive project',
            description:
                'Hide this project from the default active-project list without deleting it.'
        },
        {
            kind: 'Switch',
            field: 'isTemplate',
            title: 'Use as template',
            description:
                'Mark this project as a source template for future projects.'
        }
    ];
    if (model.extraFields?.length)
        fields.push(
            {
                kind: 'Heading',
                id: 'projectEditorAdditional',
                title: 'Additional settings'
            },
            ...model.extraFields
        );
    return fields;
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        footer = model.discard ? 116 : 62;
    const formFields = fields(model);
    const imageWidth = Math.max(1, Settings.contentWidth(width) - 32);
    if (imageWidth < 160 + controls.imagePicker.minimumActionsWidth) {
        const description = text(
            'Choose a large image; the repository web representation is used automatically when available.'
        );
        const lines = Math.max(
            1,
            Math.ceil((description.length * 7) / imageWidth)
        );
        formFields.find((field) => field.id === 'projectEditorImage').height =
            160 + 12 + 18 + lines * 16 + 10 + 36 + (model.stagedImage ? 41 : 0);
    }
    const nodes = [
        node('Box', 'projectEditorSurface', rect(0, 0, width, height), {
            background: 'panelDeep'
        }),
        label(
            'projectEditorTitle',
            rect(24, 12, width - 200, 28),
            text('Edit project'),
            { fontRole: 'title', weight: 600, role: 'heading' }
        ),
        button(
            'projectEditorHelp',
            rect(width - 86, 12, 32, 32),
            text('Project help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true }
        ),
        button(
            'projectEditorClose',
            rect(width - 48, 12, 32, 32),
            text('Close'),
            'close',
            { type: 'close' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    const body = Settings.describe(
        {
            fields: formFields,
            values: model.values || {},
            busy:
                model.busy || model.loading || model.uncertain || model.blocked,
            error: model.error,
            notice: model.loading ? text('Loading data…') : text(model.notice),
            style: model.style
        },
        width,
        Math.max(0, height - 52 - footer),
        language
    );
    for (const child of body.nodes)
        nodes.push(Object.assign({}, child, { y: child.y + 52 }));
    nodes.push(
        node(
            'Box',
            'projectEditorFooter',
            rect(0, height - footer, width, footer),
            { background: 'surfaceContainerLow', radius: 0 }
        )
    );
    if (model.discard) {
        nodes.push(
            label(
                'projectEditorDiscardText',
                rect(20, height - footer + 10, width - 40, 38),
                text('Discard changes?'),
                { wrap: true }
            )
        );
        nodes.push(
            button(
                'projectEditorKeep',
                rect(20, height - 48, 142, 36),
                text('Keep editing'),
                '',
                { type: 'keep' },
                !model.busy
            )
        );
        nodes.push(
            button(
                'projectEditorDiscard',
                rect(width - 176, height - 48, 156, 36),
                text('Discard changes'),
                '',
                { type: 'discard' },
                !model.busy,
                { destructive: true }
            )
        );
    } else {
        nodes.push(
            button(
                'projectEditorCancel',
                rect(20, height - 48, 110, 36),
                text('Cancel'),
                '',
                { type: 'close' },
                !model.busy
            )
        );
        nodes.push(
            button(
                'projectEditorSave',
                rect(width - 150, height - 48, 130, 36),
                text('Save'),
                'save',
                { type: 'save' },
                model.dirty &&
                    !model.busy &&
                    !model.uncertain &&
                    !model.blocked &&
                    !model.loading,
                { highlighted: true }
            )
        );
    }
    const header = nodes.splice(1, 3);
    nodes.splice(
        1,
        0,
        node('Box', 'projectEditorHeader', rect(0, 0, width, 48), {
            titlebar: true,
            chromeRight: 86,
            background: 'surfaceContainerLow',
            radius: 0,
            children: header
        })
    );
    return { nodes };
}
