from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import keyword
import re
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


_STDLIB_MODULES = frozenset({
    "collections", "datetime", "functools", "itertools", "json", "math",
    "os", "pathlib", "re", "sys", "typing",
})
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_KNOWN_EXPRESSION_TARGETS = {
    "th": ("class", "tactic_handler_api.api", "HandlerAPI"),
    "th.files": ("class", "tactic_handler_api.files", "FilesAPI"),
    "th.repositories": ("class", "tactic_handler_api.files", "RepositoriesAPI"),
    "th.ui": ("class", "tactic_handler_api.ui", "UIAPI"),
    "th.commit_queue()": ("class", "tactic_handler_api.checkin", "CommitQueue"),
    "tactic_handler_api.get_api()": ("class", "tactic_handler_api.api", "HandlerAPI"),
}


def _format(foreground=None, background=None, *, bold=False, italic=False):
    value = QTextCharFormat()
    if foreground:
        value.setForeground(QColor(foreground))
    if background:
        value.setBackground(QColor(background))
    if bold:
        value.setFontWeight(QFont.DemiBold)
    if italic:
        value.setFontItalic(True)
    return value


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Theme-aware Python highlighter with search and occurrence overlays."""

    def __init__(self, document, colors=None):
        super().__init__(document)
        self._colors = dict(colors or {})
        self._selected_word = ""
        self._search = ""
        self._search_options = {}
        self._module_names = ()
        self._build_rules()

    def _color(self, name, fallback):
        value = self._colors.get(name, fallback)
        return value.name() if isinstance(value, QColor) else str(value)

    def _build_rules(self):
        keyword_words = keyword.kwlist + ["True", "False", "None"]
        builtin_words = [
            name for name in dir(builtins)
            if not name.startswith("_")
        ]
        self._rules = [
            (
                QRegularExpression(r"\b(?:" + "|".join(keyword_words) + r")\b"),
                _format(self._color("keyword", "#d5bd51"), bold=True),
            ),
            (
                QRegularExpression(r"\b(?:" + "|".join(builtin_words) + r")\b"),
                _format(self._color("type", "#a06bb4")),
            ),
            (
                QRegularExpression(
                    r"\b(?:0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+|"
                    r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?j?)\b"
                ),
                _format(self._color("number", "#56a7b3")),
            ),
            (
                QRegularExpression(r"@[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"),
                _format(self._color("decorator", "#ce8750")),
            ),
            (
                QRegularExpression(r"\b[A-Za-z_]\w*(?=\s*\()"),
                _format(self._color("function", "#56a7b3")),
            ),
            (
                QRegularExpression(r"\b(?:def|class)\s+\K[A-Za-z_]\w*"),
                _format(self._color("definition", "#ce8750"), bold=True),
            ),
            (
                QRegularExpression(r"\b(?:self|cls)\b"),
                _format(self._color("self", "#78a6c4"), italic=True),
            ),
            (
                QRegularExpression(r"(?<!\w)(?:[furbFURB]{0,2})'(?:\\.|[^'\\])*'"),
                _format(self._color("string", "#52a86e")),
            ),
            (
                QRegularExpression(r'(?<!\w)(?:[furbFURB]{0,2})"(?:\\.|[^"\\])*"'),
                _format(self._color("string", "#52a86e")),
            ),
            (
                QRegularExpression(r"#[^\n]*"),
                _format(self._color("comment", "#52a86e"), italic=True),
            ),
        ]
        self._triple_single = QRegularExpression("'''")
        self._triple_double = QRegularExpression('"""')
        self._string_format = _format(self._color("string", "#52a86e"))
        self._module_format = _format(
            self._color("module", "#78a6c4"), bold=True
        )
        self._occurrence_format = _format(
            background=self._color("occurrence", "#55545a")
        )
        self._search_format = _format(
            background=self._color("search", "#8b7527"), bold=True
        )

    def set_colors(self, colors):
        colors = dict(colors or {})
        if colors == self._colors:
            return
        self._colors = colors
        self._build_rules()
        self.rehighlight()

    def set_overlays(self, selected_word, search, options=None):
        selected_word = str(selected_word or "")
        if not re.fullmatch(r"[A-Za-z_]\w*", selected_word):
            selected_word = ""
        search = str(search or "")
        options = dict(options or {})
        if (
            selected_word == self._selected_word
            and search == self._search
            and options == self._search_options
        ):
            return
        self._selected_word = selected_word
        self._search = search
        self._search_options = options
        self.rehighlight()

    @staticmethod
    def _matches(pattern, text):
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            if match.capturedLength() > 0:
                yield match.capturedStart(), match.capturedLength()

    def _highlight_multiline(self, text, delimiter, state):
        start = 0
        if self.previousBlockState() != state:
            start_match = delimiter.match(text)
            start = start_match.capturedStart() if start_match.hasMatch() else -1
        while start >= 0:
            end_match = delimiter.match(text, start + 3)
            if not end_match.hasMatch():
                self.setCurrentBlockState(state)
                self.setFormat(start, len(text) - start, self._string_format)
                return
            length = end_match.capturedStart() - start + 3
            self.setFormat(start, length, self._string_format)
            next_match = delimiter.match(text, start + length)
            start = next_match.capturedStart() if next_match.hasMatch() else -1

    def highlightBlock(self, text):  # noqa: N802 - Qt virtual method
        if self.currentBlock().blockNumber() == 0:
            self._module_names = _imported_display_names(
                self.document().toPlainText()
            )
        if self._module_names:
            modules = QRegularExpression(
                r"\b(?:" + "|".join(
                    re.escape(name) for name in self._module_names
                ) + r")\b"
            )
            for start, length in self._matches(modules, text):
                self.setFormat(start, length, self._module_format)
        for pattern, text_format in self._rules:
            for start, length in self._matches(pattern, text):
                self.setFormat(start, length, text_format)
        self.setCurrentBlockState(0)
        self._highlight_multiline(text, self._triple_single, 1)
        self._highlight_multiline(text, self._triple_double, 2)

        if self._selected_word:
            occurrence = QRegularExpression(
                r"\b" + QRegularExpression.escape(self._selected_word) + r"\b"
            )
            for start, length in self._matches(occurrence, text):
                self.setFormat(start, length, self._occurrence_format)

        search = self._search
        if search:
            options = self._search_options
            expression = search if options.get("regex") else QRegularExpression.escape(search)
            if options.get("wholeWord"):
                expression = r"\b(?:" + expression + r")\b"
            pattern = QRegularExpression(expression)
            if not options.get("caseSensitive"):
                pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            if pattern.isValid():
                for start, length in self._matches(pattern, text):
                    self.setFormat(start, length, self._search_format)


def _node_signature(node):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ""
    if isinstance(node, ast.ClassDef):
        return "class"
    arguments = []
    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
    for argument, default in zip(positional, defaults):
        label = argument.arg
        if default is not None:
            try:
                label += "=" + ast.unparse(default)
            except (AttributeError, ValueError):
                label += "=…"
        arguments.append(label)
    if node.args.vararg:
        arguments.append("*" + node.args.vararg.arg)
    arguments.extend(argument.arg for argument in node.args.kwonlyargs)
    if node.args.kwarg:
        arguments.append("**" + node.args.kwarg.arg)
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}({', '.join(arguments)})"


@lru_cache(maxsize=8)
def _safe_tree(source):
    """Share read-only trees across outline, completion and highlighting.

    Recover the valid prefix at the error, not by reparsing every trailing
    line. The bounded cache retains only a few recent document revisions.
    """
    candidate = source
    while candidate:
        try:
            return ast.parse(candidate)
        except SyntaxError as error:
            lines = candidate.splitlines()
            end = min(len(lines) - 1, max(0, (error.lineno or 1) - 1))
            candidate = "\n".join(lines[:end])
    return None


def _module_source_path(module_name):
    module_name = str(module_name or "")
    if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module_name):
        return None
    relative = Path(*module_name.split("."))
    roots = [_REPOSITORY_ROOT]
    roots.extend(Path(value) for value in sys.path if value)
    checked = set()
    for root in roots:
        try:
            root = root.resolve()
        except OSError:
            continue
        if root in checked:
            continue
        checked.add(root)
        for candidate in (
            root / relative.with_suffix(".py"),
            root / relative / "__init__.py",
        ):
            if candidate.is_file():
                return candidate
    return None


@lru_cache(maxsize=64)
def _module_tree_cached(path, modified_ns):
    del modified_ns
    try:
        return ast.parse(Path(path).read_text(
            encoding="utf-8", errors="replace"
        ))
    except (OSError, SyntaxError):
        return None


def _module_tree(module_name):
    path = _module_source_path(module_name)
    if path is None:
        return None
    try:
        modified_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _module_tree_cached(str(path), modified_ns)


def _symbols_from_nodes(nodes):
    result = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            doc = (ast.get_docstring(node) or "").strip().splitlines()
            result.append((
                node.name, kind, _node_signature(node), doc[0] if doc else "",
            ))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    result.append((target.id, "value", "", ""))
    return tuple(result)


def _source_symbols(module_name):
    tree = _module_tree(module_name)
    return _symbols_from_nodes(tree.body) if tree else ()


def _class_member_symbols(class_node):
    result = list(_symbols_from_nodes(class_node.body))
    names = {item[0] for item in result}
    for node in ast.walk(class_node):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id in {"self", "cls"}
                and not target.attr.startswith("_")
                and target.attr not in names
            ):
                result.append((target.attr, "value", "", "Instance attribute"))
                names.add(target.attr)
    return tuple(result)


def _class_symbols(module_name, class_name):
    tree = _module_tree(module_name)
    if not tree:
        return ()
    target = next((
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ), None)
    return _class_member_symbols(target) if target else ()


def _imported_display_names(source):
    tree = _safe_tree(source)
    if not tree:
        return ()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(
                imported.asname or imported.name.split(".", 1)[0]
                for imported in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            names.update(
                imported.asname or imported.name
                for imported in node.names if imported.name != "*"
            )
    return tuple(sorted(name for name in names if name.isidentifier()))


@lru_cache(maxsize=16)
def _stdlib_symbols(module_name):
    if module_name not in _STDLIB_MODULES:
        return ()
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return ()
    result = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        value = getattr(module, name)
        kind = (
            "class" if isinstance(value, type)
            else "function" if callable(value) else "value"
        )
        detail = ""
        if callable(value):
            try:
                detail = str(inspect.signature(value))
            except (TypeError, ValueError):
                pass
        result.append((name, kind, detail, "Python standard library"))
    return tuple(result)


def _module_aliases(tree):
    aliases = {}
    if not tree:
        return aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                aliases[
                    imported.asname or imported.name.split(".", 1)[0]
                ] = imported.name if imported.asname else imported.name.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            for imported in node.names:
                if imported.name == "*":
                    continue
                dotted = f"{module}.{imported.name}".strip(".")
                if _module_source_path(dotted):
                    aliases[imported.asname or imported.name] = dotted
    return aliases


def _module_symbols(module_name):
    if module_name in _STDLIB_MODULES:
        return _stdlib_symbols(module_name)
    return _source_symbols(module_name)


def _target_symbols(target):
    kind, module_name, class_name = target
    if kind == "class":
        return _class_symbols(module_name, class_name)
    return _module_symbols(module_name)


def _class_node(tree, name):
    if not tree:
        return None
    return next((
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == name
    ), None)


def _enclosing_class(tree, line):
    candidates = [
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        and node.lineno <= line <= (getattr(node, "end_lineno", None) or line)
    ] if tree else []
    return min(candidates, key=lambda node: (
        (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno
    ), default=None)


def _local_expression_symbols(expression, tree, line):
    name = expression[:-2] if expression.endswith("()") else expression
    if name in {"self", "cls"}:
        owner = _enclosing_class(tree, line)
        return _class_member_symbols(owner) if owner else ()
    owner = _class_node(tree, name)
    if owner:
        return _class_member_symbols(owner)
    if not tree or "." in name:
        return ()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            owner = _class_node(tree, value.func.id)
            if owner:
                return _class_member_symbols(owner)
    return ()


def _expression_symbols(expression, aliases, tree, line):
    first = expression.split(".", 1)[0]
    first_name = first[:-2] if first.endswith("()") else first
    module_name = aliases.get(first_name)
    normalized = expression
    if module_name:
        normalized = module_name + expression[len(first_name):]

    target = _KNOWN_EXPRESSION_TARGETS.get(normalized)
    if target:
        return _target_symbols(target)
    if module_name:
        tail = expression[len(first_name):].lstrip(".")
        if not tail:
            return _module_symbols(module_name)
        target_name = tail[:-2] if tail.endswith("()") else tail
        if "." not in target_name:
            members = _class_symbols(module_name, target_name)
            if members:
                return members
        nested_module = f"{module_name}.{target_name}"
        if _module_source_path(nested_module):
            return _module_symbols(nested_module)
    return _local_expression_symbols(expression, tree, line)


def _completion_record(name, kind, signature, doc, start, end):
    detail = signature
    if doc:
        detail = (detail + " — " if detail else "") + doc
    callable_item = kind in {"builtin", "class", "function"}
    return {
        "label": name,
        "insertText": name + "()" if callable_item else name,
        "cursorOffset": -1 if callable_item else 0,
        "kind": kind,
        "detail": detail,
        "start": start,
        "end": end,
    }


def document_symbols(source):
    tree = _safe_tree(str(source or ""))
    if not tree:
        return []
    result = []

    def append_nodes(nodes, owner="", depth=0):
        for node in nodes:
            if not isinstance(node, (
                ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
            )):
                continue
            name = node.name
            qualified = f"{owner}.{name}" if owner else name
            kind = (
                "class" if isinstance(node, ast.ClassDef)
                else "method" if owner else "function"
            )
            result.append({
                "name": name,
                "qualifiedName": qualified,
                "kind": kind,
                "detail": _node_signature(node),
                "line": int(node.lineno),
                "endLine": int(getattr(node, "end_lineno", node.lineno)),
                "depth": depth,
            })
            append_nodes(node.body, qualified, depth + 1)

    append_nodes(tree.body)
    return result


def completion_items(source, cursor_position, manual=False):
    source = str(source or "")
    cursor_position = max(0, min(int(cursor_position), len(source)))
    before = source[:cursor_position]
    match = re.search(
        r"(?P<base>[A-Za-z_]\w*(?:\([^()\n]*\))?"
        r"(?:\.[A-Za-z_]\w*(?:\([^()\n]*\))?)*)\."
        r"(?P<prefix>[A-Za-z_]\w*)?$",
        before,
    )
    if match:
        base = match.group("base") or ""
        prefix = match.group("prefix") or ""
    else:
        match = re.search(r"(?P<prefix>[A-Za-z_]\w*)?$", before)
        base = ""
    if not match:
        return []
    prefix = match.group("prefix") or ""
    if not manual and not base and len(prefix) < 2:
        return []

    tree = _safe_tree(source)
    aliases = _module_aliases(tree)

    start = match.start("prefix")
    values = []
    if base:
        symbols = _expression_symbols(
            base, aliases, tree, before.count("\n") + 1
        )
        for name, kind, signature, doc in symbols:
            if prefix and not name.casefold().startswith(prefix.casefold()):
                continue
            values.append(_completion_record(
                name, kind, signature, doc, start, cursor_position
            ))
    else:
        candidates = {}
        for name in keyword.kwlist:
            candidates[name] = ("keyword", "Python keyword")
        for name in dir(builtins):
            if not name.startswith("_"):
                value = getattr(builtins, name)
                candidates[name] = (
                    "class" if isinstance(value, type) else "builtin",
                    "Python built-in",
                )
        for alias, module_name in aliases.items():
            candidates[alias] = (
                "module",
                "Python standard library" if module_name in _STDLIB_MODULES
                else module_name,
            )
        if tree:
            for node in ast.walk(tree):
                name = getattr(node, "name", "")
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and name:
                    candidates[name] = (
                        "class" if isinstance(node, ast.ClassDef) else "function",
                        _node_signature(node),
                    )
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    candidates[node.id] = ("variable", "Local name")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    for imported in node.names:
                        candidates[imported.asname or imported.name.split(".")[0]] = (
                            "module", "Imported name"
                        )
        for name, (kind, detail) in candidates.items():
            if prefix and not name.casefold().startswith(prefix.casefold()):
                continue
            values.append(_completion_record(
                name, kind, detail, "", start, cursor_position
            ))
    values.sort(key=lambda item: (
        not item["label"].casefold().startswith(prefix.casefold()),
        item["label"].casefold(),
    ))
    return values[:200]


def find_matches(text, query, options=None):
    text, query = str(text or ""), str(query or "")
    options = dict(options or {})
    if not query:
        return []
    expression = query if options.get("regex") else re.escape(query)
    if options.get("wholeWord"):
        expression = r"\b(?:" + expression + r")\b"
    flags = 0 if options.get("caseSensitive") else re.IGNORECASE
    try:
        pattern = re.compile(expression, flags)
    except re.error:
        return []
    return [
        {"start": match.start(), "end": match.end()}
        for match in pattern.finditer(text) if match.end() > match.start()
    ]


def edit_command(action, text, start, end):
    text = str(text or "")
    start, end = sorted((max(0, int(start)), max(0, int(end))))
    start, end = min(start, len(text)), min(end, len(text))
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    block = text[line_start:line_end]
    lines = block.split("\n")

    if action == "toggle_comment":
        nonempty = [line for line in lines if line.strip()]
        remove = bool(nonempty) and all(
            line.lstrip().startswith("#") for line in nonempty
        )
        changed = []
        for line in lines:
            indent = len(line) - len(line.lstrip(" \t"))
            if not line.strip():
                changed.append(line)
            elif remove:
                offset = indent + (1 if line[indent:].startswith("#") else 0)
                if offset < len(line) and line[offset] == " ":
                    offset += 1
                changed.append(line[:indent] + line[offset:])
            else:
                changed.append(line[:indent] + "# " + line[indent:])
        replacement = "\n".join(changed)
    elif action in {"indent", "unindent"}:
        if action == "indent":
            replacement = "\n".join("    " + line for line in lines)
        else:
            replacement = "\n".join(
                line[4:] if line.startswith("    ")
                else line[1:] if line.startswith("\t")
                else line.lstrip(" ") if len(line) - len(line.lstrip(" ")) < 4
                else line for line in lines
            )
    elif action == "duplicate":
        if start != end:
            selected = text[start:end]
            return {
                "text": text[:end] + selected + text[end:],
                "start": end, "end": end + len(selected),
            }
        insertion = "\n" + block
        return {
            "text": text[:line_end] + insertion + text[line_end:],
            "start": line_end + 1,
            "end": line_end + len(insertion),
        }
    elif action == "delete_line":
        delete_start = line_start
        delete_end = line_end
        if delete_end < len(text):
            delete_end += 1
        elif delete_start > 0:
            delete_start -= 1
        return {
            "text": text[:delete_start] + text[delete_end:],
            "start": delete_start,
            "end": delete_start,
        }
    else:
        return {"text": text, "start": start, "end": end}

    updated = text[:line_start] + replacement + text[line_end:]
    return {
        "text": updated,
        "start": line_start,
        "end": line_start + len(replacement),
    }
