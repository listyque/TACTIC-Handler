// Semantic paint states; hosts own pointer, focus, keyboard and composition.
export function buttonVisual(state = {}) {
    const enabled = state.enabled !== false && !state.loading;
    const active = state.hovered || state.focused;
    let background = 'surfaceContainerHigh';
    let content = 'primaryText';
    if (state.segmented) {
        background = !enabled
            ? 'transparent'
            : state.pressed
              ? 'surfaceContainerHighest'
              : state.checked
                ? 'selected'
                : active
                  ? 'rowHover'
                  : 'transparent';
        content = state.checked ? 'selectedText' : 'secondaryText';
    } else if (enabled) {
        if (state.pressed)
            background =
                state.destructive && state.highlighted ? 'error' : 'selected';
        else if (state.highlighted)
            background = state.destructive ? 'error' : 'action';
        else if (active) background = 'rowHover';
        else if (state.tonal) background = 'secondaryContainer';
        content = state.destructive
            ? state.highlighted
                ? 'onError'
                : 'error'
            : state.highlighted
              ? 'selectedText'
              : 'primaryText';
    }
    return {
        background,
        content: enabled ? content : 'disabledText',
        border: state.destructive ? 'error' : 'outlineVariant',
        borderWidth: state.segmented || state.highlighted || state.flat ? 0 : 1,
        pressedMix:
            enabled && state.pressed && state.destructive && state.highlighted
    };
}

export function fieldVisual(state = {}) {
    return {
        background:
            state.tableCell && !state.focused
                ? 'transparent'
                : 'surfaceContainerHigh',
        content: state.enabled === false ? 'disabledText' : 'primaryText',
        border: state.error ? 'error' : state.focused ? 'action' : 'outline',
        borderWidth: state.focused ? 2 : state.tableCell ? 0 : 1
    };
}

export function checkVisual(state = {}) {
    const selected = state.checked || state.mixed;
    const disabled = state.enabled === false;
    return {
        background: selected
            ? disabled
                ? 'surfaceContainerHigh'
                : 'action'
            : state.prominent
              ? 'surfaceContainerHighest'
              : 'transparent',
        content: disabled ? 'disabledText' : 'primaryText',
        mark: disabled ? 'disabledText' : 'selectedText',
        border: disabled
            ? 'disabledText'
            : selected || state.focused
              ? 'action'
              : state.prominent
                ? 'secondaryText'
                : 'outline',
        borderWidth: state.focused || state.prominent ? 2 : 1
    };
}

export function switchVisual(state = {}) {
    const disabled = state.enabled === false;
    return {
        background: disabled
            ? 'surfaceContainerHigh'
            : state.checked
              ? 'action'
              : 'surfaceContainerHighest',
        border: disabled
            ? 'disabledText'
            : state.checked || state.focused
              ? 'action'
              : 'outline',
        thumb: disabled
            ? 'disabledText'
            : state.checked
              ? 'selectedText'
              : 'secondaryText',
        borderWidth: state.focused ? 2 : 1
    };
}
