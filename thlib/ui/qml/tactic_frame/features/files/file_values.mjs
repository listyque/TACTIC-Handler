import { fileIcon } from '../objects/snapshot.ui.mjs';

export function fileName(path) {
    return String(path || '')
        .replace(/\\/g, '/')
        .split('/')
        .pop();
}

export function extension(path) {
    const name = fileName(path),
        index = name.lastIndexOf('.');
    return index > 0 ? name.slice(index + 1).toUpperCase() : 'FILE';
}

export function sourceIcon(path) {
    const type = /\.(apng|avif|png|jpe?g|webp|gif|tiff?|bmp|svg)$/i.test(path)
        ? 'image'
        : /\.(mov|mp4|avi|mkv|webm)$/i.test(path)
          ? 'movie'
          : '';
    return fileIcon('file', type, '', path);
}

export function prettySize(value) {
    for (const unit of ['B', 'KB', 'MB', 'GB', 'TB']) {
        if (value < 1024 || unit === 'TB')
            return value.toFixed(unit === 'B' ? 0 : 1) + ' ' + unit;
        value /= 1024;
    }
}
