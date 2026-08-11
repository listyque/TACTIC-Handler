"""Regenerate the public thlib API baseline after an intentional API review."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    "thlib/tactic_classes.py",
    "thlib/tactic_query.py",
    "thlib/environment.py",
)


def _arguments(node):
    positional = [argument.arg for argument in node.args.posonlyargs]
    positional += [argument.arg for argument in node.args.args]
    required_count = len(positional) - len(node.args.defaults)
    return {
        "positional": positional,
        "required": positional[:required_count],
        "keywordOnly": [argument.arg for argument in node.args.kwonlyargs],
        "vararg": node.args.vararg.arg if node.args.vararg else "",
        "kwarg": node.args.kwarg.arg if node.args.kwarg else "",
    }


def build_manifest():
    manifest = {}
    function_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    for relative in SOURCES:
        source = (ROOT / relative).read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=relative)
        records = {}
        for node in tree.body:
            if node.name.startswith("_") if hasattr(node, "name") else True:
                continue
            if isinstance(node, function_types):
                records[node.name] = {"kind": "function", **_arguments(node)}
            elif isinstance(node, ast.ClassDef):
                methods = {}
                for child in node.body:
                    if isinstance(child, function_types) and not child.name.startswith("_"):
                        methods[child.name] = _arguments(child)
                records[node.name] = {"kind": "class", "methods": methods}
        manifest[relative] = records
    return manifest


def main():
    target = ROOT / "tests" / "contracts" / "thlib_public_api.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
