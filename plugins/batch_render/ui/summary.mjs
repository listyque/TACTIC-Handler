// Summary geometry is independent of Qt; the host supplies Frame factories.
export function describe(frame, summary, width, language, tr) {
    const values = [
        [tr('PENDING'), String(summary.pending)],
        [tr('DONE / FAILED'), summary.completed + ' / ' + summary.failed],
        [tr('ELAPSED'), summary.elapsed],
        [tr('REMAINING'), summary.eta]
    ];
    const column = Math.max(0, width / values.length);
    const nodes = [frame.node('Box', 'summary-surface', frame.rect(0, 0, width, 62), {
        color: 'panel', radius: 0
    })];
    values.forEach((value, index) => {
        const x = index * column + 12;
        const cellWidth = Math.max(0, column - 24);
        nodes.push(frame.label('summary-label-' + index, frame.rect(x, 6, cellWidth, 16),
                               value[0], { fontRole: 'caption', color: 'secondaryText' }));
        nodes.push(frame.label('summary-value-' + index, frame.rect(x, 25, cellWidth, 24),
                               value[1], { fontRole: 'statistic', color: 'primaryText' }));
    });
    nodes.push(frame.node('Progress', 'summary-progress', frame.rect(0, 58, width, 4), {
        value: summary.progress, minimum: 0, maximum: 1
    }));
    return { nodes };
}
