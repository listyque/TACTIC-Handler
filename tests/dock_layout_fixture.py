"""A populated split workspace for exercising dock geometry independently of defaults."""

import json
from dataclasses import asdict

from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.workspace_models.docks_tree import (
    DockSplit,
    DockStack,
    serialize_layout,
    stack,
)


def three_column_layout():
    work = DockSplit("horizontal", 0.34, stack("results"), stack("tasks"))
    details = DockStack(
        (
            "notes", "task_calendar", "timesheet", "work_reports",
            "cost_reports", "snapshot", "description",
        ),
        "notes",
    )
    return DockSplit("horizontal", 0.66, work, details)


def three_column_settings():
    visible = {"results", "tasks", "notes", "task_calendar", "snapshot"}
    panels = [
        {**asdict(panel), "visible": panel.panel_id in visible}
        for panel in DockPanelModel._defaults()
    ]
    return {
        "workspace/dockLayout": json.dumps({
            "panels": panels,
            "layout": serialize_layout(three_column_layout()),
        }),
    }
