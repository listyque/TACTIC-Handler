import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = Object.freeze({
    inset: 8,
    gap: 7,
    header: 32,
    narrow: 720,
    navigation: 310
});

export function toggleNavigation(model, hasDocument) {
    return {
        navigationExpanded: !model.navigationExpanded,
        navigationPage: !hasDocument
    };
}

export function layout(model, width, height) {
    const inner = Math.max(0, width - 16);
    const single = width < metrics.narrow || model.navigationExpanded === false;
    const top = 8 + metrics.header + metrics.gap + (model.error ? 45 : 0);
    const body = Math.max(0, height - top - 8);
    const navigation = single
        ? inner
        : Math.min(metrics.navigation, inner * 0.34);
    const pageX = single ? 8 : 8 + navigation + 17;
    return {
        single,
        header: rect(8, 8, inner, metrics.header),
        error: rect(8, 47, inner, 38),
        navigation: rect(8, top, navigation, body),
        divider: rect(8 + navigation + 8, top, 1, body),
        page: rect(pageX, top, Math.max(0, width - pageX - 8), body),
        body: rect(8, top, inner, body),
        navigationVisible:
            !!model.initialized && (!single || model.navigationPage !== false),
        pageVisible:
            !!model.initialized && (!single || model.navigationPage === false)
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const bounds = layout(model, width, height);
    const nodes = [
        node('Icon', 'knowledgeIcon', rect(8, 14, 20, 20), {
            icon: 'book-open',
            color: 'action'
        })
    ];
    let right = width - 8;
    function action(id, text, icon, type, visible, enabled) {
        if (visible) right -= 30;
        nodes.push(
            button(
                id,
                rect(Math.max(8, right), 9, 30, 30),
                tr(text),
                icon,
                { type },
                enabled,
                { iconOnly: true, visible: !!visible }
            )
        );
        if (visible) right -= 7;
    }
    const writable = !model.busy && !model.organizationDirty;
    action(
        'knowledgeReload',
        'Reload articles',
        'refresh',
        'reload',
        true,
        writable
    );
    action(
        'knowledgeCreateSection',
        'Create section',
        'folder-plus',
        'createSection',
        model.initialized && model.canEdit,
        !model.saving && !model.organizationDirty
    );
    action(
        'knowledgeCreateArticle',
        'Create article',
        'create-article',
        'createArticle',
        model.initialized && model.canEdit,
        !model.saving && !model.organizationDirty
    );
    action(
        'knowledgeDiscardOrganization',
        'Discard order changes',
        'undo',
        'discardOrder',
        model.organizationDirty,
        !model.busy
    );
    action(
        'knowledgeSaveOrganization',
        'Save order',
        'save',
        'saveOrder',
        model.organizationDirty,
        !model.busy
    );
    action(
        'knowledgeToggleNavigation',
        model.navigationExpanded === false
            ? 'Show article navigation'
            : 'Hide article navigation',
        model.navigationExpanded === false ? 'chevron-right' : 'chevron-left',
        'navigation',
        model.initialized && width >= metrics.narrow,
        true
    );
    nodes.push(
        label(
            'knowledgeTitle',
            rect(35, 8, Math.max(0, right - 35), 32),
            tr('Knowledge Base'),
            { fontRole: 'title', weight: 600 }
        )
    );
    if (model.error) {
        nodes.push(
            node('Box', 'knowledgeErrorSurface', bounds.error, {
                background: 'surfaceContainerLow',
                radius: 8,
                border: 'error'
            })
        );
        nodes.push(
            label(
                'knowledgeErrorText',
                rect(40, 50, Math.max(0, width - 96), 32),
                model.error,
                {
                    color: 'primaryText',
                    toolTip: model.error,
                    maxLines: 2,
                    fontRole: 'caption'
                }
            )
        );
        nodes.push(
            node('Icon', 'knowledgeErrorIcon', rect(16, 58, 16, 16), {
                icon: 'exclamation-circle',
                color: 'error'
            })
        );
        nodes.push(
            button(
                'knowledgeErrorDismiss',
                rect(Math.max(8, width - 46), 51, 30, 30),
                tr('Dismiss error'),
                'close',
                { type: 'dismissError' },
                true,
                { iconOnly: true }
            )
        );
    }
    if (model.initialized) {
        nodes.push(
            node('View', 'knowledgeNavigation', bounds.navigation, {
                view: 'navigation',
                visible: bounds.navigationVisible
            })
        );
        if (!bounds.single)
            nodes.push(
                node('Box', 'knowledgeDivider', bounds.divider, {
                    background: 'outlineVariant'
                })
            );
        nodes.push(
            node('View', 'knowledgePage', bounds.page, {
                view: 'page',
                visible: bounds.pageVisible
            })
        );
    } else
        nodes.push(
            node('View', 'knowledgeInitialization', bounds.body, {
                view: 'initialization'
            })
        );
    return { nodes, bounds };
}
