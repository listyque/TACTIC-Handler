"""Desktop-only Batch Render plugin entry point."""
from . import dispatcher


def open_plugin(context):
    return dispatcher.show(parent=context.window, project_code=context.project, hide_handler=True)
