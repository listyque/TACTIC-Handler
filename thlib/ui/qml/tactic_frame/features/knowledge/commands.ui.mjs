import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// These bars own presentation only; drafts, revisions and writes stay with the host.
export function editorHeight(width) {
    return width < 640 ? 70 : 32;
}
export function viewerHeight(width) {
    return width < 640 ? 99 : 62;
}

export function editor(model, width, language) {
    const tr = (text) => translate(text, language);
    const article = model.kind === 'article';
    const actions = [];
    actions.push([
        'knowledgeMetadataToggle',
        model.creating
            ? 'Back to title and summary'
            : model.metadataExpanded
              ? 'Hide title and summary'
              : 'Show title and summary',
        model.creating
            ? 'arrow-left'
            : model.metadataExpanded
              ? 'chevron-up'
              : 'chevron-down',
        'metadata',
        article && (!model.creating || model.step === 1)
    ]);
    actions.push([
        'knowledgeLinkSelectedObjects',
        'Link selected objects to article',
        'link',
        'link',
        article && !!model.selectionCount
    ]);
    actions.push(['knowledgeCancelAction', 'Cancel', 'close', 'discard']);
    actions.push([
        'knowledgeArchiveAction',
        article ? 'Delete article' : 'Delete section',
        'delete',
        'delete',
        !model.creating
    ]);
    actions.push([
        'knowledgeSaveDraft',
        'Save as draft',
        'save',
        'saveDraft',
        article && !!(model.creating || model.draft)
    ]);
    actions.push([
        'knowledgeSave',
        model.creating || model.draft ? 'Publish' : 'Save',
        model.creating || model.draft ? 'send' : 'save',
        'save',
        !article || !model.creating || model.step === 1
    ]);
    const nodes = [];
    let left = model.back ? 37 : 0;
    nodes.push(
        button(
            'knowledgeEditorBack',
            rect(0, 1, 30, 30),
            tr('Back to articles'),
            'arrow-left',
            { type: 'back' },
            !model.busy,
            { iconOnly: true, visible: !!model.back }
        )
    );
    nodes.push(
        node('Icon', 'knowledgeEditorKindIcon', rect(left, 6, 20, 20), {
            icon: article ? 'file' : 'folder',
            color: 'action'
        })
    );
    left += 27;
    let right = width;
    const compact = width < 1180;
    for (let index = actions.length - 1; index >= 0; index--) {
        const [id, text, icon, type, shown] = actions[index];
        const visible = shown !== false;
        const size = compact
            ? 30
            : type === 'saveDraft'
              ? 140
              : type === 'metadata'
                ? 220
                : type === 'link'
                  ? 210
                  : 120;
        if (visible) right -= size;
        const save = type === 'save' || type === 'saveDraft';
        nodes.push(
            button(
                id,
                rect(Math.max(0, right), width < 640 ? 39 : 1, size, 30),
                tr(text),
                icon,
                { type },
                !model.busy &&
                    (!save ||
                        !!(model.dirty || model.localDraft || model.draft)),
                {
                    visible,
                    iconOnly: compact,
                    highlighted: type === 'save',
                    destructive: type === 'delete',
                    tonal: type === 'saveDraft'
                }
            )
        );
        if (visible) right -= 7;
    }
    const title = tr(article ? 'Edit article' : 'Edit section');
    const available = Math.max(0, (width < 640 ? width : right) - left);
    const stepWidth = article && model.creating ? 96 : 0;
    nodes.push(
        label(
            'knowledgeEditorTitle',
            rect(
                left,
                0,
                Math.max(0, available - (width < 640 ? 0 : stepWidth)),
                32
            ),
            title,
            { fontRole: 'title', weight: 600, role: 'heading', level: 3 }
        )
    );
    nodes.push(
        label(
            'knowledgeCreationStep',
            rect(
                width < 640 ? 0 : left + available - stepWidth,
                width < 640 ? 44 : 6,
                stepWidth,
                20
            ),
            tr('Step {step} of 2').replace('{step}', (model.step || 0) + 1),
            {
                fontRole: 'caption',
                color: 'secondaryText',
                visible: !!stepWidth
            }
        )
    );
    return { nodes };
}

export function viewer(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let left = 10,
        right = width - 10;
    nodes.push(
        node(
            'Box',
            'knowledgeViewerSurface',
            rect(0, 0, width, viewerHeight(width)),
            { background: 'surfaceContainerLow', radius: 12 }
        )
    );
    nodes.push(
        button(
            'knowledgeViewerBack',
            rect(left, 16, 30, 30),
            tr('Back to articles'),
            'arrow-left',
            { type: 'back' },
            true,
            { iconOnly: true, visible: !!model.back }
        )
    );
    if (model.back) {
        left += 39;
    }
    nodes.push(
        node('Box', 'knowledgeViewerKindSurface', rect(left, 11, 40, 40), {
            background: 'surfaceContainerHigh',
            radius: 8
        })
    );
    nodes.push(
        node('Icon', 'knowledgeViewerKindIcon', rect(left + 10, 21, 20, 20), {
            icon: model.kind === 'section' ? 'folder-open' : 'file',
            color: model.kind === 'section' ? 'tertiary' : 'action'
        })
    );
    left += 49;
    const actions = [];
    actions.push(['knowledgeCopySearchKey', 'Copy search key', 'copy', 'copy']);
    if (model.kind === 'article' && !model.localDraft)
        actions.push([
            'knowledgeChangeHistory',
            'Change history',
            'history',
            'history'
        ]);
    if (model.kind === 'article' && model.tocCount)
        actions.push([
            'knowledgeToggleTableOfContents',
            model.tocVisible
                ? 'Hide table of contents'
                : 'Show table of contents',
            'list-ul',
            'toc'
        ]);
    if (model.kind === 'article' && model.resourceCount && !model.history)
        actions.push([
            'knowledgeToggleResources',
            model.resourcesVisible
                ? 'Hide linked objects and attached files'
                : 'Show linked objects and attached files',
            'attachments-editor',
            'resources'
        ]);
    if (model.canEdit && !model.history) {
        actions.push([
            'knowledgeViewerDelete',
            model.kind === 'article' ? 'Delete article' : 'Delete section',
            'delete',
            'delete'
        ]);
        actions.push(['knowledgeEdit', 'Edit', 'edit', 'edit']);
    }
    for (let index = actions.length - 1; index >= 0; index--) {
        const [id, text, icon, type] = actions[index];
        right -= 30;
        nodes.push(
            button(
                id,
                rect(right, width < 640 ? 62 : 16, 30, 30),
                tr(text),
                icon,
                { type },
                !model.busy ||
                    type === 'toc' ||
                    type === 'resources' ||
                    type === 'back',
                {
                    iconOnly: true,
                    destructive: type === 'delete',
                    tonal:
                        type === 'edit' ||
                        (type === 'toc' && model.tocVisible) ||
                        (type === 'resources' && model.resourcesVisible)
                }
            )
        );
        right -= 7;
    }
    const titleWidth = Math.max(0, (width < 640 ? width - 10 : right) - left);
    nodes.push(
        label(
            'knowledgeViewerTitle',
            rect(left, 9, titleWidth, 24),
            model.title || '',
            { fontRole: 'title', weight: 600, role: 'heading', level: 3 }
        )
    );
    const readingWidth =
        model.kind === 'article' && model.minutes
            ? Math.min(106, titleWidth)
            : 0;
    nodes.push(
        label(
            'knowledgeViewerDescription',
            rect(left, 34, Math.max(0, titleWidth - readingWidth), 18),
            model.description || '',
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    if (readingWidth)
        nodes.push(
            label(
                'knowledgeReadingTime',
                rect(left + titleWidth - readingWidth, 34, readingWidth, 18),
                tr('{minutes} min read').replace('{minutes}', model.minutes),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    return { nodes };
}
