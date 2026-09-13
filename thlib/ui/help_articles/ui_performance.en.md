---
group: Reference
icon: ui-performance
order: 21
---
# UI responsiveness

> Open UI responsiveness from the application menu to measure interactions in every window. The target
> is visible feedback within 50 ms.

## Main controls

Measurements are paused by default. Select Resume measurements to start recording.

First frame measures input to a rendered frame in the same window. Ready frame measures a named
operation through its rendered result.

Controller phases explain time spent on synchronization, filtering and model updates; they do not
measure server readiness unless the operation includes it.

## Usage notes

- Measurements stay in memory, retain the last 250 entries, and can be paused, cleared or copied.
- Hidden diagnostics do not rebuild their list.
- Cached search tabs and recent chats retain their lists and scroll position; Refresh still requests
  current server data.

## Reading one measurement

Each row names the interaction, window, start and end phase, total duration and any controller phases
reported by that operation. A slow **First frame** points to input, binding, layout or rendering work.
A slow **Ready frame** with a quick first frame points to data preparation, a worker, server or model
publication after immediate feedback was already visible.

## Practical measurement

1. Clear existing entries and Resume measurements.
2. Perform one interaction at a time.
3. Repeat it once warm and once after an explicit Refresh.
4. Compare first-frame and ready-frame time, then inspect named phases.
5. Copy the result together with the matching Debug Log request when server work is involved.

Do not infer a server or GPU cause from total time alone. Measure the real boundary before changing
thread counts, cache settings or the graphics backend.

## Limits

This tool records application-instrumented interactions, not every operating-system, driver or DCC
event. A native Maya stall requires Maya profiling and DCC logs as well. Pausing measurement stops new
records and does not alter application behavior.
