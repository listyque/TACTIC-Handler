import { button, rect } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { toolbar } from '../../controls/code/code.ui.mjs';
import { controls } from '../../core/foundation.mjs';

export function toolbarHeight(width) {
    return 30 + (width < 530 ? controls.scrollBar.extent : 0);
}

export function describe(model, width, language, revision) {
    const baseWidth = Math.max(440, width - 90);
    const scene = toolbar(
        Object.assign({}, model, { compactToolbar: false }),
        baseWidth,
        language,
        revision
    );
    const commands = [
        ['saved', 'Saved revisions', 'cloud-done', model.saved && !model.busy],
        [
            'selection',
            'Run selection',
            'play-selection',
            model.canCopy && !model.readOnly && !model.busy
        ],
        ['outline', 'Outline', 'format-list-bulleted', true]
    ];
    commands.forEach((row, index) =>
        scene.nodes.push(
            button(
                'scriptSource_' + row[0],
                rect(baseWidth + index * 30, 0, 28, 28),
                translate(row[1], language),
                row[2],
                { type: row[0] },
                row[3],
                { iconOnly: true, visible: row[0] !== 'saved' || !model.native }
            )
        )
    );
    scene.contentWidth = Math.max(530, width);
    return scene;
}
