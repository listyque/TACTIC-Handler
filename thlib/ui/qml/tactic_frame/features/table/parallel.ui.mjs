import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(cell, width, height, language, expanded = {}) {
    const children = [],
        inner = Math.max(1, width - 24),
        barHeight = (cell.barHeight || 1) + 1,
        steps = cell.steps || 6,
        labelHeight = 20,
        rowHeight = Math.max(28, steps * barHeight + labelHeight + 4);
    let index = 0,
        left = 0;
    function append(groups, parent) {
        for (const group of groups) {
            const identity = parent + '/' + group.process,
                extent = Math.max(74, (group.bars || []).length * 12 + 8),
                top = 0;
            const bars = group.bars || [];
            bars.forEach((bar, taskIndex) => {
                const x = left + 4 + taskIndex * 12;
                for (let step = 0; step < steps; step++) {
                    const level = 100 - ((step + 1) * 100) / steps,
                        filled = level < bar.percent || level === 0;
                    children.push(
                        node(
                            'Box',
                            'parallelBar_' +
                                index +
                                '_' +
                                taskIndex +
                                '_' +
                                step,
                            rect(
                                x,
                                top + step * barHeight,
                                10,
                                cell.barHeight || 1
                            ),
                            {
                                background: filled
                                    ? bar.color
                                    : 'outlineVariant',
                                radius: 0
                            }
                        )
                    );
                }
                children.push(
                    node(
                        'Action',
                        'parallelTask_' + index + '_' + taskIndex,
                        rect(x, top, 10, steps * barHeight),
                        {
                            text: '',
                            tooltip: [
                                bar.assigned,
                                bar.status,
                                bar.description,
                                bar.bidStart,
                                bar.bidEnd
                            ]
                                .filter(Boolean)
                                .join(' · '),
                            action: {
                                type: 'service',
                                name: 'task-details',
                                taskKey: bar.search_key,
                                taskCode: bar.taskCode,
                                process: bar.process || group.process
                            }
                        }
                    )
                );
            });
            if (labelHeight) {
                if (group.children?.length) {
                    children.push(
                        button(
                            'parallelExpand_' + index,
                            rect(
                                left,
                                top + steps * barHeight,
                                extent,
                                labelHeight
                            ),
                            group.label,
                            expanded[identity] ? 'expand-less' : 'expand-more',
                            { type: 'parallel-toggle', identity },
                            true,
                            {
                                compact: true,
                                translateLabel: false,
                                iconAction: true
                            }
                        )
                    );
                } else
                    children.push(
                        label(
                            'parallelLabel_' + index,
                            rect(
                                left + 4,
                                top + steps * barHeight,
                                extent - 8,
                                labelHeight
                            ),
                            group.label,
                            {
                                fontRole:
                                    cell.labelFormat === 'small'
                                        ? 'secondary'
                                        : 'body',
                                tooltip: group.process
                            }
                        )
                    );
            }
            if (!group.children?.length)
                children.push(
                    node(
                        'Action',
                        'parallelProcess_' + index,
                        rect(left, top + steps * barHeight + 1, extent, 28),
                        {
                            text: '',
                            tooltip:
                                translate('Open tasks', language) +
                                ' · ' +
                                group.label,
                            action: {
                                type: 'service',
                                name: 'task-details',
                                process:
                                    (group.bars || [])[0]?.process ||
                                    group.process
                            },
                            background: 'transparent',
                            radius: 0
                        }
                    )
                );
            index++;
            left += extent;
            if (expanded[identity]) append(group.children || [], identity);
        }
    }
    append(cell.groups || [], '');
    if (!index)
        children.push(
            label(
                'parallelEmpty',
                rect(4, 0, inner, 28),
                translate(cell.diagnostic || 'No tasks', language),
                { color: 'secondaryText' }
            )
        );
    return {
        nodes: [
            node('Scroll', 'parallelScroll', rect(0, 0, width, height), {
                contentWidth: Math.max(width, left + 24),
                contentHeight: rowHeight + 16,
                scrollbarId: 'parallelScrollBar',
                children
            })
        ]
    };
}
