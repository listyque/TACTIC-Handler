"""Build the optional TACTIC-side query package from the current client API."""

import ast
from functools import lru_cache
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent / "tactic_handler_queries"
SOURCE = ROOT / "thlib" / "tactic_query.py"
OUTPUT = ROOT / "dist" / "tactic_handler_queries.zip"
MODULE_NAME = "tactic_handler_queries"
CLIENT_ONLY = {
    "_parse_procedure_module", "_function_source_lines", "prepare_serverside_script",
    "traceback_handle", "get_traceback",
}


@lru_cache(maxsize=1)
def server_source():
    source_path = SOURCE if SOURCE.is_file() else SOURCE.with_suffix(".source")
    source = source_path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    procedures = (
        "".join(lines[node.lineno - 1:node.end_lineno]).rstrip()
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name not in CLIENT_ONLY
    )
    return ("\n\n\n".join(procedures) + "\n").encode("utf-8")


def build(output=OUTPUT):
    source = server_source()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in ("__init__.py", "command.py"):
            path = PACKAGE / name
            archive.write(
                path if path.is_file() else path.with_suffix(".source"),
                f"{MODULE_NAME}/{name}",
            )
        archive.writestr(f"{MODULE_NAME}/api.py", source)
        archive.write(PACKAGE / "manifest.xml", f"{MODULE_NAME}/manifest.xml")
    return output


if __name__ == "__main__":
    print(build())
