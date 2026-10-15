"""Native TACTIC command for bundled TACTIC-Handler procedures."""

import traceback

from pyasm.command import Command
from pyasm.common import Environment
from tactic_client_lib import TacticServerStub

from . import invoke


class QueryCommand(Command):
    def get_title(self):
        return "TACTIC-Handler: {}".format(self.kwargs.get("procedure", ""))

    def execute(self):
        name = self.kwargs.get("procedure")
        try:
            server = TacticServerStub.get(protocol="local")
            server.login = Environment.get_user_name()
            result = invoke(
                name,
                self.kwargs.get("arguments"),
                server,
                self.kwargs.get("source_sha256"),
            )
        except Exception as error:
            raise RuntimeError(
                "TACTIC-Handler procedure {} failed:\n{}".format(
                    name, traceback.format_exc()
                )
            ) from error
        self.add_description(self.get_title())
        return result
