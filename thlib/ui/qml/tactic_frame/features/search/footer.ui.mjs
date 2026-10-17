import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const pageSizes = [20, 25, 50, 100, 200, 500];

export function countText(model, width, language) {
    if (width < 520)
        return String(model.total == null ? model.count : model.total);
    if (model.mode === 'infinite')
        return translate('{count} results', language, {
            count: model.total == null ? model.count : model.total
        });
    return model.total == null
        ? model.range
        : translate('{range} of {total}', language, {
              range: model.count === 0 ? '0' : model.range,
              total: model.total
          });
}

export function menu(kind, model) {
    if (kind === 'size')
        return [{ title: 'Items per page', header: true }].concat(
            pageSizes.map((size) => ({
                title: size + ' items',
                icon: 'list',
                command: String(size),
                checked: size === model.pageSize,
                enabled: !model.busy
            }))
        );
    return [{ title: 'Result loading', header: true }].concat(
        ['pages', 'infinite'].map((mode) => ({
            title: mode === 'pages' ? 'Pages' : 'Continuous',
            icon: mode === 'pages' ? 'view_kanban' : 'layers',
            command: mode,
            checked: mode === model.mode,
            enabled: !model.busy
        }))
    );
}

export function describe(model, width, height, language) {
    const text = (key, values) => translate(key, language, values),
        compact = width < 1200,
        narrow = width < 520,
        y = (height - 36) / 2,
        nodes = [],
        pages = model.mode !== 'infinite';
    let right = width - 8;
    const add = (id, title, icon, type, size, enabled, extra) => {
        right -= size;
        nodes.push(
            button(
                id,
                rect(right, y, size, 36),
                title,
                icon,
                { type },
                enabled,
                Object.assign({ iconOnly: size === 36 }, extra || {})
            )
        );
        right -= 8;
    };
    if (model.canCreate)
        add(
            'searchCreateItemButton',
            text('New item'),
            'add',
            'create',
            compact ? 36 : 124,
            !model.busy,
            { highlighted: true, label: text('Create record') }
        );
    if (model.localSync)
        add(
            'searchRepositorySync',
            text('Sync current Search Type'),
            'repository-sync',
            'sync',
            36,
            !model.busy
        );
    if (model.queue)
        add(
            'searchCommitQueue',
            text(model.fileProject ? 'Changelists' : 'Commit Queue'),
            'queue',
            'queue',
            36,
            true
        );
    add(
        'searchLoadingMode',
        text(model.mode === 'infinite' ? 'Continuous' : 'Pages'),
        model.mode === 'infinite' ? 'layers' : 'view_kanban',
        'mode',
        compact ? 36 : 164,
        !model.busy,
        {
            tonal: true,
            label: text('Result loading'),
            pressAction: { type: 'press', menu: 'mode' }
        }
    );
    if (pages && !compact)
        add(
            'searchPageSize',
            text('{count} / page', { count: model.pageSize }),
            'list',
            'size',
            142,
            !model.busy,
            {
                tonal: true,
                label: text('Items per page'),
                pressAction: { type: 'press', menu: 'size' }
            }
        );
    if (pages) {
        add(
            'searchNextPage',
            text('Next page'),
            'chevron_right',
            'next',
            36,
            !model.busy && model.hasNext
        );
        if (compact)
            add(
                'searchPagePicker',
                String(model.page) +
                    ' / ' +
                    (model.pageCount == null ? '…' : model.pageCount),
                '',
                'pagePicker',
                narrow ? 60 : 92,
                !model.busy,
                { pressAction: { type: 'press', menu: 'pagePicker' } }
            );
        else
            for (const number of (model.pageNumbers || []).slice().reverse()) {
                right -= 34;
                nodes.push(
                    button(
                        'searchPage_' + number,
                        rect(right, y, 34, 36),
                        String(number),
                        '',
                        { type: 'page', value: number },
                        !model.busy,
                        { radio: true, selected: number === model.page }
                    )
                );
                right -= 2;
            }
        add(
            'searchPreviousPage',
            text('Previous page'),
            'chevron_left',
            'previous',
            36,
            !model.busy && model.page > 1
        );
    }
    let left = 12;
    if (!compact) {
        nodes.push(
            label('searchShowing', rect(left, y, 74, 36), text('Showing'), {
                weight: 600,
                fontRole: 'bodyLarge'
            })
        );
        left += 82;
    }
    if (right - left > 36) {
        const count = countText(model, width, language),
            pillWidth = Math.min(
                right - left,
                Math.ceil(model.countWidth || count.length * 7) + 16
            );
        nodes.push(
            node('Box', 'searchResultRange', rect(left, y + 6, pillWidth, 24), {
                background: 'rowHover',
                radius: 12,
                children: [
                    label(
                        'searchResultCount',
                        rect(8, 0, pillWidth - 16, 24),
                        count,
                        { color: 'secondaryText', fontRole: 'bodyLarge' }
                    )
                ]
            })
        );
    }
    return { nodes };
}

export function pagePicker(value, width, language) {
    const text = (key) => translate(key, language);
    return {
        nodes: [
            node('Field', 'searchPageNumber', rect(0, 0, width, 36), {
                text: String(value || ''),
                label: text('Page number'),
                inputType: 'number',
                inputMode: 'numeric',
                action: { type: 'pageDraft' },
                keys: { Enter: { type: 'go' } }
            }),
            button(
                'searchGoToPage',
                rect(0, 44, width, 36),
                text('Go to page'),
                'next',
                { type: 'go' },
                true
            )
        ]
    };
}
