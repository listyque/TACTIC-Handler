"""Package entry point; the VM dispatcher itself is preserved byte for byte."""
from . import dispatcher


def open_plugin(context):
    return dispatcher.show(parent=context.window, project_code=context.project, hide_handler=True)
