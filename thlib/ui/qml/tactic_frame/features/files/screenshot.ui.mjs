import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';

const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

export function draw(origin, point, width, height) {
    const x1 = clamp(origin.x, 0, width),
        y1 = clamp(origin.y, 0, height),
        x2 = clamp(point.x, 0, width),
        y2 = clamp(point.y, 0, height);
    return rect(
        Math.min(x1, x2),
        Math.min(y1, y2),
        Math.abs(x2 - x1),
        Math.abs(y2 - y1)
    );
}

export function finish(region, origin, width, height) {
    if (region.width >= 32 && region.height >= 32) return region;
    const w = Math.min(128, width),
        h = Math.min(128, height);
    return rect(
        clamp(origin.x - w / 2, 0, width - w),
        clamp(origin.y - h / 2, 0, height - h),
        w,
        h
    );
}

export function move(region, delta, width, height) {
    return rect(
        clamp(region.x + delta.x, 0, Math.max(0, width - region.width)),
        clamp(region.y + delta.y, 0, Math.max(0, height - region.height)),
        Math.min(region.width, width),
        Math.min(region.height, height)
    );
}

export function resize(region, delta, width, height) {
    const availableWidth = Math.max(0, width - region.x),
        availableHeight = Math.max(0, height - region.y);
    return rect(
        region.x,
        region.y,
        clamp(
            region.width + delta.x,
            Math.min(32, availableWidth),
            availableWidth
        ),
        clamp(
            region.height + delta.y,
            Math.min(32, availableHeight),
            availableHeight
        )
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        region = model.region,
        instruction = tr(
            model.ready
                ? 'Move or resize the area, then capture'
                : 'Drag over the area to capture'
        ),
        pillWidth = Math.min(
            Math.max(0, width - 100),
            (model.instructionWidth || width - 128) + 28
        ),
        instructionHeight = Math.max(
            38,
            Math.ceil(
                (model.instructionWidth || width - 128) /
                    Math.max(1, pillWidth - 28)
            ) *
                18 +
                16
        ),
        nodes = [
            node('Box', 'screenshotTint', rect(0, 0, width, height), {
                background: 'blackMix',
                opacity: 0.08
            }),
            node(
                'Box',
                'screenshotInstructionPanel',
                rect((width - pillWidth) / 2, 18, pillWidth, instructionHeight),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 19,
                    children: [
                        label(
                            'screenshotInstruction',
                            rect(14, 0, pillWidth - 28, instructionHeight),
                            instruction,
                            { fontRole: 'bodyLarge', weight: 600, wrap: true }
                        )
                    ]
                }
            ),
            button(
                'screenshotCancel',
                rect(width - 46, 18, 28, 28),
                tr('Cancel screenshot'),
                'close',
                { type: 'cancel' },
                true,
                { iconOnly: true, iconAction: true }
            )
        ];
    if (region.width > 1 && region.height > 1)
        nodes.push(
            node(
                'Box',
                'screenshotRegionPaint',
                rect(region.x, region.y, region.width, region.height),
                {
                    background: 'action',
                    opacity: 0.08,
                    radius: 12
                }
            )
        );
    if (region.width > 1 && region.height > 1)
        nodes.push(
            node(
                'Box',
                'screenshotRegionBorder',
                rect(region.x, region.y, region.width, region.height),
                { border: 'action', borderWidth: 2, radius: 12 }
            )
        );
    if (model.ready) {
        const handle = rect(
                region.x + region.width - 24,
                region.y + region.height - 24,
                24,
                24
            ),
            gap = 6,
            redrawWidth = Math.max(
                112,
                buttonWidth(model.redrawWidth || 0, true)
            ),
            captureWidth = Math.max(
                112,
                buttonWidth(model.captureWidth || 0, true)
            ),
            toolbarWidth = Math.min(
                width - 16,
                redrawWidth + captureWidth + gap
            ),
            x = clamp(
                region.x + region.width - toolbarWidth - 32,
                8,
                Math.max(8, width - toolbarWidth - 8)
            ),
            preferredY = region.y + region.height + 8,
            y =
                preferredY + 38 <= height - 8
                    ? preferredY
                    : Math.max(8, region.y - 46),
            firstWidth = Math.min(
                redrawWidth,
                ((toolbarWidth - gap) * redrawWidth) /
                    (redrawWidth + captureWidth)
            );
        nodes.push(
            node('Box', 'screenshotResizePaint', handle, {
                background: 'action',
                radius: 8,
                children: [
                    node(
                        'Icon',
                        'screenshotResizeIcon',
                        rect(5.5, 5.5, 13, 13),
                        { icon: 'open-in-full', color: 'selectedText' }
                    )
                ]
            })
        );
        nodes.push(
            node('View', 'screenshotResizeHandle', handle, {
                view: 'resize',
                label: tr('Resize capture area')
            })
        );
        nodes.push(
            button(
                'screenshotDrawAgainButton',
                rect(x, y, firstWidth, 38),
                tr('Draw again'),
                'refresh',
                { type: 'redraw' },
                !model.busy
            )
        );
        nodes.push(
            button(
                'screenshotCaptureButton',
                rect(
                    x + firstWidth + gap,
                    y,
                    toolbarWidth - firstWidth - gap,
                    38
                ),
                tr(model.busy ? 'Capturing…' : 'Capture'),
                'camera',
                { type: 'capture' },
                !model.busy,
                { highlighted: true }
            )
        );
    }
    return { nodes };
}
