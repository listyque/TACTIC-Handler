export function fraction(value, minimum = 0, maximum = 1) {
    if (typeof value !== 'number' || !isFinite(value)) return null;
    if (maximum <= minimum) return 0;
    return Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)));
}
