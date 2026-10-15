"""Readable diagnostic views of Python requests; never execute their contents."""

import ast


def request_code_blocks(command: str) -> list[dict[str, str]]:
    """Separate multiline arguments from the call without changing the log."""
    if not command:
        return []
    try:
        tree = ast.parse(command)
    except (SyntaxError, ValueError):
        return [{"name": "", "text": command}]
    if not (len(tree.body) == 2 and isinstance(tree.body[0], ast.Import)
            and isinstance(tree.body[1], ast.Expr)
            and isinstance(tree.body[1].value, ast.Call)):
        return [{"name": "", "text": command}]

    arguments = []

    class MultilineArguments(ast.NodeTransformer):
        def visit_Constant(self, node):  # noqa: N802 - ast visitor
            if isinstance(node.value, str) and "\n" in node.value:
                name = f"request_text_{len(arguments) + 1}"
                arguments.append({"name": name, "text": node.value})
                return ast.copy_location(ast.Name(id=name, ctx=ast.Load()), node)
            return node

    tree = MultilineArguments().visit(tree)
    call = tree.body[1].value
    values = [ast.unparse(arg) for arg in call.args]
    values.extend(ast.unparse(keyword) for keyword in call.keywords)
    request = (ast.unparse(tree.body[0]) + "\n" + ast.unparse(call.func) + "(\n"
               + "\n".join(f"    {value}," for value in values) + "\n)")
    return [{"name": "", "text": request}, *arguments]
