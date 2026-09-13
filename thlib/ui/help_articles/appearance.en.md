---
group: Configuration
icon: palette
order: 35
---
# Appearance configuration

> Appearance controls the visual theme, semantic icon font, motion, interface language, and Qt
> graphics backend. Most changes apply immediately; the graphics backend requires a restart.

## Appearance

| Setting | What it controls |
| --- | --- |
| **Dark color mode** | Uses dark surfaces and the dark palette assigned to the selected interface style. Turning it off uses the light palette. |
| **Interface style** | Selects the component styling rules. Each style remembers its own light and dark palettes. |
| **Light mode palette** | Base surface and accent used while dark mode is off. |
| **Dark mode palette** | Base surface and accent used while dark mode is on. |
| **Icon set** | Chooses the bundled semantic icon font. Material Design Icons is the default. Automatic follows the application's preferred set; the other options force a family. Material Design and Fluent glyphs are optically scaled to match Font Awesome without changing control geometry. Unknown dynamic icons still fall back to another bundled family instead of disappearing. |
| **Click animations** | Animates press feedback, ripples, switches, and disclosure controls. Disabled controls still change state, but without motion. |
| **Hover animations** | Animates pointer hover transitions. Hover states still appear immediately when disabled. |
| **Fades and transitions** | Animates appearing content, view changes, expansion, and other interface fades. |
| **Menu and popup animations** | Animates menus, combo boxes, popups, and tooltips. Disable it for instant opening and dismissal. |

## Language

**Interface language** changes application labels and selects the matching help articles. Project
names, Search Types, processes, statuses, and other server-defined data are never translated.

## Graphics backend

| Backend | Use it when |
| --- | --- |
| **Automatic (recommended)** | You want stable OpenGL on Windows and Qt's native default elsewhere. |
| **OpenGL** | You need GPU rendering without the Windows DXGI/MPO presentation path that may flicker. |
| **Direct3D 11** | You prefer the native Windows backend and the current MPO/HDR setup is stable. |
| **Direct3D 12** | The workstation has a compatible modern Windows graphics driver. |
| **Vulkan** | A working Vulkan driver is installed and this backend is specifically needed. |
| **Software** | You are diagnosing graphics-driver problems. It uses the CPU and is noticeably slower. |

Restart TACTIC Handler after changing the backend. On supported Windows versions, switching between
light and dark mode also updates native window title bars.
