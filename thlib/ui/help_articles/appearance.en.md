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

Enabled interface animations use short durations across all styles: about 2.5 times faster than the previous motion timing. The switches above still disable their respective animations completely.

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
If OpenGL stutters while resizing and Vulkan works on this computer, select Vulkan explicitly;
Automatic currently selects OpenGL on Windows.
Software rendering shows preview images without rounded clipping because Qt's graphical effects are unavailable there.


## Legacy template icons

Known icons from legacy templates are mapped to modern symbols in the shared icon catalogue. For example, PICTURE_EDIT uses an image, DETAILS a document, PHOTOS an image collection, FILM/MOVIE_VIEW a film and PLUGIN a puzzle piece. Old built-in PNG filenames and exact /context/icons/... references use the same mappings. The selected icon set still applies; an explicitly qualified font icon keeps its family. Project XML is preserved. This catalogue covers the shipped template references, not every historical IconWdg icon or custom plugin image. Unknown custom names, paths and remote images are not guessed from their labels. Restart Handler after installing the updated UI; reload the browser after updating Stream.
