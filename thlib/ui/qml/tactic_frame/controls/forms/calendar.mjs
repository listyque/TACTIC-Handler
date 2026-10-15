// Local wall-clock dates. Never introduce a UTC conversion at this UI boundary.
export function localDate(
    year,
    month,
    day = 1,
    hour = 0,
    minute = 0,
    second = 0
) {
    const result = new Date(0);
    result.setFullYear(year, month, day);
    result.setHours(hour, minute, second, 0);
    return result;
}

export function parse(value, includeTime = true) {
    const match = String(value || '').match(
        /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.\d{1,6})?)?(Z|[+-]\d{2}:\d{2})?)?$/
    );
    if (!match || (!includeTime && match[4])) return null;
    const [year, month, day, hour, minute, second] = match
        .slice(1, 7)
        .map((part) => Number(part || 0));
    if (year < 1) return null;
    const offset = match[7];
    if (
        offset &&
        offset !== 'Z' &&
        (Number(offset.slice(1, 3)) > 23 || Number(offset.slice(4)) > 59)
    )
        return null;
    const date = localDate(year, month - 1, day, hour, minute, second);
    return date.getFullYear() === year &&
        date.getMonth() === month - 1 &&
        date.getDate() === day &&
        date.getHours() === hour &&
        date.getMinutes() === minute &&
        date.getSeconds() === second
        ? date
        : null;
}

export function monthDays(year, month) {
    const first = localDate(year, month, 1);
    const last = new Date(first);
    last.setMonth(first.getMonth() + 1, 0);
    const offset = (first.getDay() + 6) % 7;
    return Array.from({ length: 42 }, (_, index) => {
        const day = index - offset + 1;
        return day > 0 && day <= last.getDate() ? day : 0;
    });
}
