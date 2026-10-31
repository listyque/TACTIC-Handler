// Only escaped text reaches either engine's rich suggestion label.
export function highlight(text, query, color = '') {
    const escape = (value) =>
        String(value).replace(
            /[&<>"']/g,
            (character) =>
                ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                })[character]
        );
    text = String(text || '');
    query = String(query || '').trim();
    if (!query) return escape(text);
    const index = text.toLocaleLowerCase().indexOf(query.toLocaleLowerCase());
    const accent = /^#[0-9a-f]{6,8}$/i.test(String(color)) ? String(color) : '';
    return index < 0
        ? escape(text)
        : escape(text.slice(0, index)) +
              (accent ? '<font color="' + accent + '">' : '') +
              '<u>' +
              escape(text.slice(index, index + query.length)) +
              '</u>' +
              (accent ? '</font>' : '') +
              escape(text.slice(index + query.length));
}
