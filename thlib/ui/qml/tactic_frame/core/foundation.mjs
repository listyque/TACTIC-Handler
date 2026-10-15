import { fieldVisual, checkVisual, switchVisual } from './interaction.mjs';

// Point typography remains for feature labels that have not migrated yet.
export const typography = {
    micro: 8,
    caption: 8.25,
    label: 8.75,
    body: 9.25,
    bodyLarge: 10,
    title: 12
};

export const fontFamily = 'Segoe UI';

// Frame geometry and resolved text sizes use logical pixels in both engines.
// Legacy house controls keep the point-based API above until Frame supplies a font.
export const textStyles = Object.freeze({
    caption: 11,
    secondary: 12,
    body: 13,
    bodyLarge: 14,
    section: 15,
    title: 16,
    heading: 17,
    display: 18,
    hero: 24
});

// House-control geometry comes from Handler; hosts supply native input and paint.
export const controls = {
    document: {
        bodySize: 12,
        lineHeight: 17,
        headingSize: 18,
        headingLineHeight: 22.5,
        paragraphGap: 8,
        headingGap: 14,
        cellPadding: 4
    },
    field: { padding: 12, areaPadding: 10 },
    choice: { rowHeight: 34, visibleRows: 8, popupPadding: 4, popupGap: 4 },
    tooltip: {
        delay: 500,
        timeout: 5000,
        margin: 8,
        paddingX: 12,
        paddingY: 7,
        radius: 6
    },
    userPicker: {
        popupWidth: 294,
        popupHeight: 286,
        rowHeight: 48,
        avatarSize: 32
    },
    calendar: { popupWidth: 304, padding: 10, rowHeight: 30, daySize: 28 },
    colorPicker: { popupWidth: 380, planeHeight: 190, padding: 20 },
    iconPicker: { popupWidth: 560, popupHeight: 440 },
    button: {
        minimumWidth: 72,
        padding: 16,
        iconPadding: 12,
        spacing: 7,
        segmentedSpacing: 6,
        segmentedPaddingStart: 3,
        segmentedPaddingEnd: 7,
        iconSize: 16,
        compactIconSize: 18,
        segmentedIconSize: 15
    },
    iconButton: {
        extent: 28,
        iconSize: 17,
        surfaceInset: 2,
        hoveredOpacity: 0.08,
        pressedOpacity: 0.12
    },
    checkBox: {
        height: 36,
        compactHeight: 30,
        spacing: 9,
        compactSpacing: 6,
        indicator: 19,
        compactIndicator: 17,
        prominentIndicator: 22,
        iconSize: 15,
        compactIconSize: 13,
        prominentIconSize: 17,
        radius: 5
    },
    switch: { width: 42, height: 24, thumb: 18, inset: 3, spacing: 10 },
    splitter: {
        extent: 10,
        thickness: 3,
        length: 40,
        restingOpacity: 0.28,
        hoveredOpacity: 0.85,
        pressedOpacity: 1
    },
    scrollBar: {
        extent: 12,
        restingTrack: 6,
        expandedTrack: 11,
        restingThumb: 5,
        expandedThumb: 8,
        restingTrackOpacity: 0.055,
        expandedTrackOpacity: 0.15,
        restingThumbOpacity: 0.42,
        hoveredThumbOpacity: 0.72,
        pressedThumbOpacity: 0.9,
        disabledThumbOpacity: 0.18
    }
};

const styleMetrics = {
    md3: {
        controlHeight: 36,
        compactControlHeight: 32,
        fieldRadius: 10,
        buttonRadius: 18,
        itemRadius: 9,
        snapshotRadius: 5,
        surfaceRadius: 12,
        sectionRadius: 16,
        dialogRadius: 20,
        menuRadius: 16,
        iconButtonRadius: 4,
        communicationGroupedSpacing: 2,
        communicationGroupTailSize: 10,
        communicationBubbleRadius: 14,
        communicationGroupedBubbleRadius: 8,
        baseMotionInstant: 28,
        baseMotionFast: 48,
        baseMotionMedium: 56,
        baseMotionSlow: 72,
        baseMotionExtended: 104
    },
    material5: {
        controlHeight: 38,
        compactControlHeight: 34,
        fieldRadius: 15,
        buttonRadius: 16,
        itemRadius: 13,
        snapshotRadius: 10,
        surfaceRadius: 18,
        sectionRadius: 22,
        dialogRadius: 28,
        menuRadius: 20,
        iconButtonRadius: 9,
        communicationGroupedSpacing: 3,
        communicationGroupTailSize: 11,
        communicationBubbleRadius: 16,
        communicationGroupedBubbleRadius: 10,
        baseMotionInstant: 36,
        baseMotionFast: 60,
        baseMotionMedium: 76,
        baseMotionSlow: 96,
        baseMotionExtended: 128
    },
    fluent: {
        controlHeight: 34,
        compactControlHeight: 32,
        fieldRadius: 5,
        buttonRadius: 5,
        itemRadius: 5,
        snapshotRadius: 3,
        surfaceRadius: 7,
        sectionRadius: 8,
        dialogRadius: 8,
        menuRadius: 8,
        iconButtonRadius: 4,
        communicationGroupedSpacing: 2,
        communicationGroupTailSize: 10,
        communicationBubbleRadius: 7,
        communicationGroupedBubbleRadius: 4,
        baseMotionInstant: 24,
        baseMotionFast: 36,
        baseMotionMedium: 48,
        baseMotionSlow: 64,
        baseMotionExtended: 88
    }
};

export const layout = {
    appBarHeight: 44,
    sectionRailWidth: 48,
    dockTitleHeight: 38,
    dockWorkspaceHeaderHeight: 96,
    dockWorkspaceFooterHeight: 58,
    communicationListSpacing: 10,
    communicationBubblePadding: 10,
    communicationContentSpacing: 6,
    communicationAvatarSpacing: 8,
    scrollbarExtent: 12,
    splitterExtent: 10,
    windowMargin: 16,
    dragThreshold: 5
};

export function metrics(style) {
    return Object.assign({}, layout, styleMetrics[style] || styleMetrics.md3);
}

export function motion(style, preferences) {
    const values = metrics(style),
        flags = preferences || {},
        result = {};
    for (const duration of ['Instant', 'Fast', 'Medium', 'Slow', 'Extended']) {
        const value = values['baseMotion' + duration];
        result['motion' + duration] =
            flags.fade === false || flags.reduced ? 0 : value;
        result['clickMotion' + duration] =
            flags.click === false || flags.reduced ? 0 : value;
        result['hoverMotion' + duration] =
            flags.hover === false || flags.reduced ? 0 : value;
        result['popupMotion' + duration] =
            flags.popup === false || flags.reduced ? 0 : value;
    }
    result.scrollMotion = result.motionInstant;
    return result;
}

// Colors retain fractional sRGB channels so Qt and CSS do not round each blend.
export function blend(first, second, weight) {
    const amount = Math.max(0, Math.min(1, weight));
    return first.map(
        (channel, index) => channel * (1 - amount) + second[index] * amount
    );
}

export function readableText(color) {
    const luminance =
        (color[0] * 0.2126 + color[1] * 0.7152 + color[2] * 0.0722) / 255;
    return luminance > 0.56 ? [23, 32, 39] : [246, 248, 250];
}

function rgb(hex) {
    return [1, 3, 5].map((offset) =>
        parseInt(hex.slice(offset, offset + 2), 16)
    );
}

export function palette(style, dark, base, accent) {
    const black = [0, 0, 0],
        white = [255, 255, 255];
    const material = style === 'material5',
        fluent = style === 'fluent';
    const colors = {
        action: accent,
        blackMix: black,
        whiteMix: white
    };

    colors.paletteBase = material
        ? blend(base, accent, dark ? 0.07 : 0.05)
        : base;
    const surface = colors.paletteBase;
    colors.workspace = blend(
        surface,
        dark ? black : white,
        dark ? (fluent ? 0.23 : 0.34) : fluent ? 0.12 : 0.08
    );
    colors.topBar = blend(
        surface,
        dark ? white : black,
        dark ? (material ? 0.05 : 0.03) : 0.03
    );
    colors.toolBar = blend(
        surface,
        dark ? white : black,
        dark ? (material ? 0.11 : 0.08) : 0.07
    );
    colors.panel = blend(surface, dark ? black : white, dark ? 0.04 : 0.22);
    colors.panelRaised = blend(surface, white, dark ? 0.08 : 0.38);
    colors.panelDeep = blend(surface, black, dark ? 0.19 : 0.08);
    colors.row = blend(surface, white, dark ? 0.07 : 0.32);
    colors.rowHover = blend(colors.row, accent, dark ? 0.1 : 0.08);
    colors.selected = blend(accent, colors.panelRaised, dark ? 0.28 : 0.3);
    colors.contentSelection = blend(
        accent,
        colors.workspace,
        dark ? 0.68 : 0.72
    );
    colors.primaryText = readableText(colors.workspace);
    colors.contentAccent = blend(
        accent,
        colors.primaryText,
        dark ? 0.12 : 0.08
    );
    colors.selectedText = readableText(colors.selected);
    colors.contentSelectionText = readableText(colors.contentSelection);
    colors.secondaryText = blend(
        colors.primaryText,
        surface,
        dark ? 0.35 : 0.42
    );
    colors.disabledText = blend(colors.secondaryText, surface, 0.42);
    colors.separator = blend(surface, colors.primaryText, dark ? 0.11 : 0.18);
    colors.border = blend(surface, colors.primaryText, dark ? 0.24 : 0.3);

    const fixed = {
        green: '#52a86e',
        yellow: '#d5bd51',
        red: '#d65b67',
        missingFile: '#d45b5b',
        violet: '#a06bb4',
        cyan: '#56a7b3'
    };
    for (const name of Object.keys(fixed)) colors[name] = rgb(fixed[name]);
    const syntax = {
        Keyword: ['#d5bd51', '#808000'],
        String: ['#69b77d', '#008000'],
        Comment: ['#70a87a', '#008000'],
        Number: ['#66b8c4', '#000080'],
        Type: ['#bc84cf', '#800080'],
        Function: ['#66b8c4', '#00677c'],
        Definition: ['#d39562', '#7c4800'],
        Self: ['#88aac4', '#092e64'],
        Occurrence: ['#55545a', '#b4b4b4'],
        Search: ['#75651f', '#ffef0b']
    };
    for (const name of Object.keys(syntax))
        colors['syntax' + name] = rgb(syntax[name][dark ? 0 : 1]);
    colors.titleGreen = rgb(dark ? '#4c8700' : '#5f970d');
    colors.ripple = (dark ? white : black).concat((dark ? 0x34 : 0x22) / 255);
    colors.rippleStrong = (dark ? white : black).concat(
        (dark ? 0x38 : 0x24) / 255
    );
    colors.popupShadow = black.concat((dark ? 0x4a : 0x28) / 255);
    colors.dialogShadow = black.concat((dark ? 0x52 : 0x30) / 255);
    colors.scrim = black.concat((dark ? 0x99 : 0x73) / 255);
    const aliases = {
        tooltipSurface: 'panelRaised',
        tooltipText: 'primaryText',
        background: 'workspace',
        surface: 'panel',
        surfaceContainerLow: 'panel',
        surfaceContainer: 'toolBar',
        surfaceContainerHigh: 'panelRaised',
        surfaceContainerHighest: 'rowHover',
        surfaceVariant: 'toolBar',
        outline: 'border',
        outlineVariant: 'separator',
        primary: 'action',
        primaryContainer: 'selected',
        secondary: 'secondaryText',
        secondaryContainer: 'rowHover',
        tertiary: 'violet',
        tertiaryContainer: 'rowHover',
        error: 'red',
        errorContainer: 'rowHover',
        text: 'primaryText',
        muted: 'secondaryText',
        accent: 'action',
        accentContainer: 'selected'
    };
    for (const name of Object.keys(aliases))
        colors[name] = colors[aliases[name]];
    colors.onError = readableText(colors.error);
    colors.inverseSurface = rgb('#eeeeee');
    colors.inverseOnSurface = rgb('#202020');
    return colors;
}

export const cssRoles = {
    workspace: '--page',
    topBar: '--header',
    toolBar: '--surface-container',
    panel: '--surface',
    panelRaised: '--surface-high',
    panelDeep: '--surface-deep',
    row: '--row',
    rowHover: '--hover',
    selected: '--selected',
    selectedText: '--on-selected',
    contentSelection: '--content-selection',
    contentAccent: '--content-accent',
    primaryText: '--on-surface',
    secondaryText: '--muted',
    disabledText: '--disabled',
    border: '--outline',
    separator: '--outline-variant',
    action: '--primary',
    red: '--error',
    green: '--success',
    yellow: '--yellow',
    cyan: '--cyan',
    violet: '--violet',
    surfaceContainerLow: '--surface',
    surfaceContainer: '--surface-container',
    surfaceContainerHigh: '--surface-high',
    surfaceContainerHighest: '--surface-highest',
    secondaryContainer: '--secondary-container',
    outline: '--outline',
    outlineVariant: '--outline-variant',
    error: '--error',
    onError: '--on-error',
    ripple: '--ripple-color',
    popupShadow: '--shadow-color',
    scrim: '--scrim'
};

export function cssColor(channels) {
    return (
        'rgba(' +
        channels.slice(0, 3).join(',') +
        ',' +
        (channels.length === 4 ? channels[3] : 1) +
        ')'
    );
}

export function cssVariables(style, dark, base, accent, preferences) {
    const colors = palette(style, dark, base, accent),
        values = metrics(style),
        result = {};
    for (const role of Object.keys(cssRoles))
        result[cssRoles[role]] = cssColor(colors[role]);
    for (const name of Object.keys(values)) {
        const cssName =
            '--' +
            name.replace(/[A-Z]/g, (letter) => '-' + letter.toLowerCase());
        result[cssName] =
            values[name] + (name.indexOf('baseMotion') === 0 ? 'ms' : 'px');
    }
    for (const name of Object.keys(typography)) {
        const cssName =
            '--text-' +
            name.replace(/[A-Z]/g, (letter) => '-' + letter.toLowerCase());
        result[cssName] = typography[name] + 'pt';
    }
    result['--control-text-size'] = textStyles.body + 'px';
    result['--control-compact-text-size'] = textStyles.secondary + 'px';
    const states = {
        field: {
            idle: fieldVisual(),
            focus: fieldVisual({ focused: true }),
            error: fieldVisual({ error: true }),
            disabled: fieldVisual({ enabled: false })
        },
        check: {
            idle: checkVisual(),
            checked: checkVisual({ checked: true }),
            focus: checkVisual({ focused: true }),
            disabled: checkVisual({ enabled: false }),
            disabledChecked: checkVisual({ checked: true, enabled: false })
        },
        switch: {
            idle: switchVisual(),
            checked: switchVisual({ checked: true }),
            focus: switchVisual({ focused: true }),
            disabled: switchVisual({ enabled: false })
        }
    };
    for (const [kind, variants] of Object.entries(states)) {
        for (const [state, paint] of Object.entries(variants)) {
            for (const [part, value] of Object.entries(paint)) {
                const name = ('--' + kind + '-' + state + '-' + part).replace(
                    /[A-Z]/g,
                    (letter) => '-' + letter.toLowerCase()
                );
                result[name] =
                    typeof value === 'number'
                        ? value + 'px'
                        : value === 'transparent'
                          ? value
                          : cssColor(colors[value]);
            }
        }
    }
    for (const kind of Object.keys(controls)) {
        for (const name of Object.keys(controls[kind])) {
            const cssName =
                '--' +
                (kind + name[0].toUpperCase() + name.slice(1)).replace(
                    /[A-Z]/g,
                    (letter) => '-' + letter.toLowerCase()
                );
            result[cssName] =
                controls[kind][name] +
                (name.endsWith('Opacity') || name === 'visibleRows'
                    ? ''
                    : name === 'delay' || name === 'timeout'
                      ? 'ms'
                      : 'px');
        }
    }
    const timings = motion(style, preferences);
    for (const name of ['Instant', 'Fast', 'Medium', 'Slow', 'Extended'])
        result['--motion-' + name.toLowerCase()] =
            timings['motion' + name] + 'ms';
    const feedback = {
        '--motion-click': 'clickMotionFast',
        '--motion-click-expansion': 'clickMotionMedium',
        '--motion-click-slow': 'clickMotionSlow',
        '--motion-click-extended': 'clickMotionExtended',
        '--motion-hover': 'hoverMotionFast',
        '--motion-hover-medium': 'hoverMotionMedium',
        '--motion-fade': 'motionMedium',
        '--motion-fade-slow': 'motionSlow',
        '--motion-fade-extended': 'motionExtended',
        '--motion-popup': 'popupMotionMedium',
        '--motion-popup-fast': 'popupMotionFast',
        '--motion-popup-slow': 'popupMotionSlow'
    };
    for (const name of Object.keys(feedback))
        result[name] = timings[feedback[name]] + 'ms';
    for (const name of Object.keys(colors)) {
        if (name.indexOf('syntax') === 0)
            result['--syntax-' + name.slice(6).toLowerCase()] = cssColor(
                colors[name]
            );
    }
    result['--on-primary'] = cssColor(readableText(accent));
    result['--font-family'] = '"' + fontFamily + '", system-ui, sans-serif';
    result['--communication-bubble-radius'] =
        values.communicationBubbleRadius + 'px';
    result['--workspace-footer-height'] =
        values.dockWorkspaceFooterHeight + 'px';
    result['--preview-radius'] = values.snapshotRadius + 'px';
    return result;
}
