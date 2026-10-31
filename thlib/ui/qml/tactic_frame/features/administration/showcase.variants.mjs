// Product and fixture hosts share the same real house-control examples.
import * as Variants from '../../controls/catalog/variants.mjs';
import { node, rect } from '../../core/frame.mjs';

export const examples = Variants.examples;
export const initial = Variants.initial;
export const transition = Variants.transition;

export function available(family) {
    return examples.filter((example) => example.family === family);
}

export function title(id, language) {
    const labels = {
        'preview-round': ['Round photo', 'Круглое фото'],
        'preview-square': ['Square initials', 'Квадратное с инициалами'],
        'preview-outline': ['Outlined preview', 'Превью с обводкой'],
        'preview-photo': ['Square photo · crop', 'Квадратное фото · обрезка'],
        'preview-contain': ['Fit whole image', 'Изображение целиком'],
        'preview-icon': ['Fallback icon', 'Иконка без изображения'],
        'preview-loading': ['Loading image', 'Загрузка изображения'],
        'preview-selected': ['Selected image', 'Выбранное изображение'],
        'preview-broken': ['Failed image', 'Ошибка изображения'],
        'preview-card': [
            'Image behind card content',
            'Изображение на фоне карточки'
        ],
        'attachment-image': ['Image attachment', 'Вложение с изображением'],
        'attachment-file': ['File attachment', 'Файловое вложение']
    };
    return labels[id]?.[language === 'ru' ? 1 : 0] || id.replace(/-/g, ' ');
}

export function describe(model, width, language, state) {
    const example = Variants.find(model.id);
    const scene = Variants.describe(
        model,
        width + 40,
        example.height + 116,
        language,
        state
    );
    scene.nodes = scene.nodes
        .filter((item) => !['exampleTitle', 'exampleEvents'].includes(item.id))
        .map((item) =>
            Object.assign({}, item, { x: item.x - 20, y: item.y - 64 })
        );
    return scene;
}

export function sample(model, width, language) {
    const example = Variants.find(model.variant);
    const height = example.height;
    const scene = describe(model.variantModel, width, language, model.state);
    return {
        height,
        nodes: [
            node('View', 'showcaseVariantPreview', rect(0, 0, width, height), {
                view: 'showcaseVariant',
                model: model.variantModel,
                state: model.state,
                language
            })
        ],
        code:
            "import * as Variants from './controls/catalog/variants.mjs';\n\n" +
            '// Native/Vue named port: ShowcaseControl; local events: Variants.transition.\n' +
            '// Port example: ' +
            JSON.stringify(example) +
            '\n' +
            '(' +
            JSON.stringify(scene, null, 2) +
            ')'
    };
}
