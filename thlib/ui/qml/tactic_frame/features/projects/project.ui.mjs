import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Configuration from '../configuration/configuration.ui.mjs';
import * as Settings from '../configuration/settings.ui.mjs';
import { controls, metrics } from '../../core/foundation.mjs';

export const steps = [
    {
        id: '0',
        title: 'Details',
        icon: 'edit',
        description: 'Choose a name and a unique code for the project.'
    },
    {
        id: '1',
        title: 'Preview Image',
        icon: 'image',
        description:
            'Optional image used to identify the project. TACTIC uploads it and creates its preview during project creation.'
    },
    {
        id: '2',
        title: 'Template',
        icon: 'layers',
        description:
            'Copy the template configuration, or create an empty project. Templates and themes are loaded from your TACTIC server.'
    },
    {
        id: '3',
        title: 'Review',
        icon: 'check-circle',
        description: 'Check the details before creating your project.'
    }
];

const details = [
    {
        kind: 'Field',
        field: 'title',
        title: 'Project title',
        description:
            'The title can contain spaces and special characters, up to 100 characters.',
        props: { maxLength: 100 }
    },
    {
        kind: 'Field',
        field: 'code',
        title: 'Project code',
        description:
            'Use letters, numbers and underscores, up to 30 characters. The code cannot start with a number and must be unique, including retired projects.',
        props: { maxLength: 30 }
    },
    { kind: 'Field', field: 'category', title: 'Category' },
    {
        kind: 'Area',
        field: 'description',
        title: 'Project description',
        height: 96
    }
];

export function wizardDirty(draft, image) {
    return !!(
        draft.title ||
        draft.code ||
        draft.category ||
        draft.description ||
        draft.namespace ||
        draft.theme ||
        (draft.source && draft.source !== '_empty') ||
        draft.isTemplate ||
        image
    );
}

export function wizardFields(model, language) {
    const empty = model.draft.source === '_empty';
    const heading = (id, title, description) => ({
        kind: 'Heading',
        id,
        title,
        description
    });
    let fields;
    if (model.step === 0)
        fields = [
            heading('projectDetails', 'Project details'),
            ...details,
            {
                kind: 'Field',
                field: 'namespace',
                title: 'Namespace',
                description:
                    'Prefix for new Search Types: studio gives studio/shot, for example. Leave empty to use the project code. Does not rename the project. The sthpw and prod namespaces are reserved.',
                enabled: empty,
                props: { maxLength: 30 }
            },
            {
                kind: 'Switch',
                field: 'isTemplate',
                title: 'Use this project as a template',
                enabled: empty
            },
            {
                kind: 'Switch',
                field: 'isMainProject',
                title: 'Main project',
                description:
                    'An empty project can become the default project at the TACTIC root URL. TACTIC may need a restart for this to take effect.',
                enabled: empty
            }
        ];
    else if (model.step === 1)
        fields = [
            heading('projectImage', 'Project image', steps[1].description),
            {
                kind: 'View',
                id: 'projectImagePicker',
                field: 'image',
                fullWidth: true,
                height: 210,
                props: { view: 'image' }
            }
        ];
    else if (model.step === 2) {
        fields = [
            heading(
                'projectSource',
                'Copy from template',
                steps[2].description
            ),
            {
                kind: 'Choice',
                field: 'source',
                title: 'Template',
                description: empty
                    ? ''
                    : 'A template supplies its own namespace and configuration. Main-project, namespace, theme and template flags apply only to an empty project.',
                options: model.templates
            },
            {
                kind: 'Button',
                field: 'manageTemplates',
                title: 'Manage templates',
                props: { icon: 'settings' },
                action: { type: 'templates' }
            },
            {
                kind: 'Button',
                field: 'refreshTemplates',
                title: 'Refresh templates',
                props: { icon: 'refresh' },
                action: { type: 'refresh' }
            }
        ];
        if (empty)
            fields.push(
                heading('emptyProjectSettings', 'Empty project settings'),
                {
                    kind: 'Choice',
                    field: 'theme',
                    title: 'Theme',
                    description:
                        'A project theme installs server widget configuration. It does not change your personal interface appearance.',
                    options: model.themes
                }
            );
        const theme = model.themes?.find(
            (theme) => theme.value === model.draft.theme
        );
        if (empty && theme?.preview)
            fields.push({
                kind: 'Preview',
                id: 'projectThemePreview',
                fullWidth: true,
                height: 160,
                props: { source: theme.preview, fallbackText: theme.label }
            });
        if (empty && theme?.description)
            fields.push({
                kind: 'Area',
                field: 'themeDescription',
                title: 'Description',
                height: 80,
                readOnly: true
            });
    } else {
        fields = [
            heading('projectReview', 'Project summary'),
            ...details.map((field) =>
                Object.assign({}, field, { readOnly: true })
            )
        ];
        fields.push({
            kind: 'Field',
            field: 'templateLabel',
            title: 'Template',
            readOnly: true
        });
        if (empty)
            fields.push(
                ...[
                    ['namespace', 'Namespace'],
                    ['themeLabel', 'Theme'],
                    ['mainLabel', 'Main project'],
                    ['templateFlagLabel', 'Use this project as a template']
                ].map(([field, title]) => ({
                    kind: 'Field',
                    field,
                    title,
                    readOnly: true
                }))
            );
        if (model.image)
            fields.push({
                kind: 'View',
                id: 'projectReviewImage',
                field: 'image',
                fullWidth: true,
                height: 210,
                props: { view: 'image' }
            });
    }
    return fields.map((field) =>
        Object.assign({}, field, {
            enabled:
                !model.busy && !model.createdCode && field.enabled !== false
        })
    );
}

export function wizard(model, width, height, language) {
    const text = (key) => translate(key, language),
        footer = model.discard ? 118 : 62;
    const scene = Configuration.describe(
        {
            title: 'Create project',
            product: model.product,
            page: String(model.step),
            pages: steps.map((step, index) =>
                Object.assign({}, step, {
                    enabled:
                        !model.busy && !model.createdCode && index <= model.step
                })
            ),
            busy: false,
            actions: [
                ['Project creation help', 'help', 'help', true],
                ['Close', 'close', 'close', !model.busy]
            ]
        },
        width,
        Math.max(0, height - footer),
        language
    );
    const bounds = scene.pageBounds;
    const draft = Object.assign({}, model.draft, {
        namespace:
            model.draft.namespace || (model.step === 3 ? model.draft.code : ''),
        themeDescription:
            model.themes?.find((row) => row.value === model.draft.theme)
                ?.description || '',
        templateLabel:
            model.templates?.find((row) => row.value === model.draft.source)
                ?.label || '',
        themeLabel:
            model.themes?.find((row) => row.value === model.draft.theme)
                ?.label || text('No theme'),
        mainLabel: text(model.draft.isMainProject ? 'Yes' : 'No'),
        templateFlagLabel: text(model.draft.isTemplate ? 'Yes' : 'No')
    });
    const fields =
        model.ready && !model.uncertain
            ? wizardFields(model, language)
            : [
                  {
                      kind: 'Button',
                      id: 'projectReload',
                      title: 'Refresh templates',
                      props: { icon: 'refresh' },
                      action: { type: 'refresh' }
                  }
              ];
    const imageWidth = Settings.contentWidth(bounds.width) - 32;
    if (imageWidth < 160 + controls.imagePicker.minimumActionsWidth) {
        const buttonHeight = metrics(model.style).controlHeight;
        for (const field of fields)
            if (field.props?.view === 'image')
                field.height = Math.max(
                    210,
                    160 +
                        controls.imagePicker.rowSpacing +
                        buttonHeight +
                        (model.image ? buttonHeight + 5 : 0)
                );
    }
    const body = Settings.describe(
        {
            fields,
            values: draft,
            busy: model.busy,
            style: model.style,
            error: model.error,
            notice: model.uncertain
                ? text(
                      'The creation result is unknown. Refresh the catalog before trying again.'
                  )
                : !model.ready
                  ? text('Loading project templates…')
                  : model.busy
                    ? text('Working…')
                    : ''
        },
        bounds.width,
        bounds.height,
        language
    );
    for (const item of body.nodes)
        scene.nodes.push(
            Object.assign({}, item, {
                x: item.x + bounds.x,
                y: item.y + bounds.y
            })
        );
    scene.nodes.push(
        node(
            'Box',
            'projectWizardFooter',
            rect(0, height - footer, width, footer),
            { background: 'surfaceContainerLow', radius: 0 }
        )
    );
    const y = height - 48;
    if (model.discard) {
        scene.nodes.push(
            label(
                'projectDiscardQuestion',
                rect(16, height - footer + 12, width - 32, 36),
                text('Discard this project draft?'),
                { wrap: true }
            )
        );
        scene.nodes.push(
            button(
                'projectKeepEditing',
                rect(16, y, 142, 36),
                text('Keep editing'),
                '',
                { type: 'keep' },
                !model.busy
            )
        );
        scene.nodes.push(
            button(
                'projectDiscard',
                rect(Math.max(164, width - 172), y, 156, 36),
                text('Discard changes'),
                '',
                { type: 'discard' },
                !model.busy,
                { destructive: true }
            )
        );
    } else {
        const compact = width < 560;
        const primaryWidth = model.createdCode
            ? Math.min(240, width - 100)
            : model.step === 3
              ? 174
              : 120;
        scene.nodes.push(
            button(
                'projectCancel',
                rect(16, y, compact ? 36 : 88, 36),
                text('Cancel'),
                compact ? 'close' : '',
                { type: 'close' },
                !model.busy,
                { iconOnly: compact }
            )
        );
        if (model.step > 0 && !model.createdCode)
            scene.nodes.push(
                button(
                    'projectBack',
                    rect(
                        width - primaryWidth - (compact ? 60 : 112),
                        y,
                        compact ? 36 : 88,
                        36
                    ),
                    text('Back'),
                    'previous',
                    { type: 'back' },
                    !model.busy,
                    { iconOnly: compact }
                )
            );
        const last = model.step === 3;
        scene.nodes.push(
            button(
                'projectNext',
                rect(width - primaryWidth - 16, y, primaryWidth, 36),
                text(
                    last
                        ? model.createdCode
                            ? 'Retry opening project'
                            : 'Create project'
                        : 'Next'
                ),
                last ? 'add' : 'next',
                { type: last ? 'submit' : 'next' },
                model.ready &&
                    !model.busy &&
                    !model.uncertain &&
                    !model.imageValidating,
                { highlighted: true }
            )
        );
    }
    return scene;
}
