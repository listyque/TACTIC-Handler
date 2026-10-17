// Handler WorkspaceResultsOrganization._task_group_value, before translated labels.
export function taskGroup(tasks, process, statuses, accent, compare) {
    const matching = tasks.filter((task) => task.process === process),
        values = [];
    for (const task of matching)
        if (task.status && !values.includes(task.status))
            values.push(task.status);
    if (!values.length)
        return {
            key: matching.length ? '__no_status__' : '__no_task__',
            label: matching.length ? 'No status' : 'No task',
            translate: true,
            rank: matching.length ? 9999 : 10000,
            accent
        };
    const catalog = Object.create(null);
    for (let index = 0; index < statuses.length; index++)
        catalog[statuses[index].key] = {
            rank: index,
            accent: statuses[index].accent || accent
        };
    values.sort(
        (left, right) =>
            (catalog[left]?.rank ?? 9000) - (catalog[right]?.rank ?? 9000) ||
            compare(left, right)
    );
    const key = values[0];
    return {
        key,
        label: key,
        rank: catalog[key]?.rank ?? 9000,
        accent: catalog[key]?.accent || accent
    };
}
