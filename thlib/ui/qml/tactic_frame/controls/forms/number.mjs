// Numeric controls exchange real values; native SpinBox keeps its scaled integers.
export function clamp(value, minimum, maximum, decimals = 0) {
    if (typeof value !== 'number' || !isFinite(value)) return null;
    const scale = Math.pow(10, Math.floor(Math.max(0, Math.min(8, decimals))));
    const bounded = Math.max(minimum, Math.min(maximum, value));
    const rounded = Math.round(bounded * scale) / scale;
    return isFinite(rounded) ? rounded : bounded;
}

export function step(
    value,
    direction,
    minimum,
    maximum,
    increment = 1,
    decimals = 0
) {
    return clamp(value + direction * increment, minimum, maximum, decimals);
}

function separator(language) {
    return String(language).split(/[-_]/)[0] === 'ru' ? ',' : '.';
}

export function pattern(decimals = 0, language = 'en') {
    const digits = Math.floor(Math.max(0, Math.min(8, decimals)));
    const point = separator(language) === ',' ? ',' : '\\.';
    // Qt's PCRE2 bridge needs literal grouping spaces instead of JS regex escapes.
    const group = separator(language) === ',' ? '[\u00a0\u202f ]' : ',';
    const integer = '(?:\\d+|\\d{1,3}(?:' + group + '\\d{3})+)';
    return digits
        ? '^[+-]?(?:' +
              integer +
              '(?:' +
              point +
              '\\d{0,' +
              digits +
              '})?|' +
              point +
              '\\d{1,' +
              digits +
              '})$'
        : '^[+-]?' + integer + '$';
}

export function parse(text, decimals = 0, language = 'en') {
    const source = String(text);
    if (!new RegExp(pattern(decimals, language)).test(source)) return null;
    const ungrouped =
        separator(language) === ','
            ? source.replace(/[\u00a0\u202f ]/g, '')
            : source.replace(/,/g, '');
    const value = Number(ungrouped.replace(separator(language), '.'));
    return isFinite(value) ? value : null;
}

export function format(value, decimals = 0, language = 'en') {
    const rounded = clamp(value, -Number.MAX_VALUE, Number.MAX_VALUE, decimals);
    if (rounded === null) return '';
    const digits = Math.floor(Math.max(0, Math.min(8, decimals)));
    const parts = rounded.toFixed(digits).split('.');
    if (parts[1]) parts[1] = parts[1].replace(/0+$/, '');
    if (parts.length > 1 && !parts[1]) parts.pop();
    parts[0] = parts[0].replace(
        /\B(?=(\d{3})+(?!\d))/g,
        separator(language) === ',' ? '\u00a0' : ','
    );
    return parts.join(separator(language));
}
