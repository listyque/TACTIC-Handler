"""Small Python 3 Maya entry point installed by Handler Configuration."""

import json
import os
import subprocess
import sys
from pathlib import Path

_launch_process = None

def _root():
    receipt = Path(__file__).resolve().parents[1] / "integration.json"
    root = Path(json.loads(receipt.read_text(encoding="utf-8"))["handler_root"]).resolve()
    if not (root / "launch.pyw").is_file():
        raise FileNotFoundError("Handler moved. Reinstall the Maya integration from Configuration.")
    return root


def _maya(root):
    for name, module in list(sys.modules.items()):
        if name.split(".")[0] not in {
            "handler_server", "tactic_handler_dcc", "tactic_handler_api", "thlib", "custom_scripts"
        }:
            continue
        origin = getattr(module, "__file__", None)
        locations = [origin] if origin else list(getattr(module, "__path__", []))
        if any(not Path(location).resolve().is_relative_to(root) for location in locations):
            raise RuntimeError("Another Handler integration is loaded. Save work and restart Maya to switch.")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tactic_handler_dcc import maya
    return maya


def _shelf():
    from maya import cmds, mel

    name = "TACTIC_Stream"
    command = "import tactic_stream_maya; tactic_stream_maya.connect(show=True)"
    if cmds.shelfLayout(name, exists=True):
        return
    parent = mel.eval("$tsShelfTop = $gShelfTopLevel")
    shelf = cmds.shelfLayout(name, parent=parent)
    cmds.shelfButton(
        parent=shelf, label="TACTIC Handler", annotation="Open TACTIC Handler",
        image1="pythonFamily.png", imageOverlayLabel="TH", sourceType="python",
        command=command, docTag="tactic_stream/integration",
    )


def connect(show=False):
    global _launch_process
    from maya import cmds

    try:
        root = _root()
        maya = _maya(root)
        runtime = maya.runtime()
        if runtime is not None and runtime.state not in {"stopped", "failed"}:
            client_root = getattr(runtime.client, "handler_root", "")
            if not client_root or Path(client_root).resolve() != root:
                raise RuntimeError("Another Handler connection is active. Save work and restart Maya to switch.")
        if runtime is None or runtime.state in {"stopped", "failed"}:
            runtime = maya.startup(root, autostart_handler=False,
                                   show_on_connect=False, pin_handler=True)
        if show:
            if runtime.connected:
                runtime.show_handler()
            else:
                if _launch_process is not None and _launch_process.poll() is None:
                    return runtime
                launcher = root.parent / "TACTIC Handler.exe"
                if not launcher.is_file():
                    raise FileNotFoundError("Start Handler manually; this installation has no TACTIC Handler.exe")
                if os.name != "nt":
                    raise OSError("The portable Handler launcher requires Windows")
                _launch_process = subprocess.Popen(
                    [str(launcher)], cwd=str(root.parent),
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
        return runtime
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        cmds.warning("TACTIC Stream integration: " + str(error))
        return None


def autostart():
    from maya import cmds

    try:
        _shelf()
        return connect()
    except (OSError, RuntimeError) as error:
        cmds.warning("TACTIC Stream integration: " + str(error))
        return None
