---
group: Guide
icon: code
order: 93
---
# Internal structure: expression-valued Search filters

> How native Search computes filter values, how the API checks nested access, and how writing expressions join a Command. The original filter rules are retained; this is not full Search/API parity.

## From a filter to a query

`Search.add_op_filters()` consumes the filter document used by `query`, `get_all_children`, `query_snapshots` and the lookup part of `get_unique_sobject`. Enabled `fast_query` delegates to the same query path. The implementation lives in `pyasm/search/search.py`, with no separate query model.

An expression computes a value before Search binds it to a column comparison. It is not substituted as raw SQL and is not evaluated separately for every result row.

```python
from pyasm.search import Search

search = Search('cg/assets')
search.add_op_filters([
    ['code', "@GET(cg/assets['code','DEMO_ARM'].code)"],
])
objects = search.get_sobjects()

# Same filter through the original XML-RPC client
objects = server.query('cg/assets', filters=[
    ['code', "@GET(cg/assets['code','DEMO_ARM'].code)"],
])
```

Project resolution follows the active project and the full search type. Qualified types can address another registered project, but its permissions are checked independently. Expression values, including quotes and non-ASCII text, remain bound query parameters.

## Original value rules

| Filter | Behavior |
| --- | --- |
| `[column, value]` | A string beginning with `@`, a variable such as `$LOGIN`, `{@…}` or `{$…}` is evaluated with `Search.eval(single=True)`, then used as an equality value. Other strings stay literal. |
| `[column, operator, value]` | The same expression detection applies. A remaining string enclosed in `{…}` is also evaluated. This includes a brace string returned by the first expression. |
| `single=True` evaluation | A list result supplies its first value, not a membership query. |
| `[column, 'in', value]` / `'not in'` | The computed pipe string or list supplies the membership values; the original empty-value removal still applies. |
| An empty `@GET` result | Evaluates to `None`; an equality filter becomes `IS NULL`. |
| Initial `None` or `''` in a three-part filter | The filter is skipped before evaluation, as in the source. |
| `[column, 'between', start, end]` | This four-part range branch does not expand expressions in its endpoints. |

For example, `[column, '{0}']` keeps a literal string, while `[column, '=', '{0}']` evaluates the brace template. `@VAR` remains the original no-op; it does not assign a filter variable or execute nested arguments. Built-in variables such as `$LOGIN` use the active request identity. `add_op_filters` has no additional `vars` parameter.

```python
filters = [
    ['code', 'in', "@JOIN(@GET(cg/assets['code','in','DEMO_ARM|DEMO_CAT_PROP'].code),'|')"],
]
objects = server.query('cg/assets', filters=filters)
```

Ordering, paging, grouping markers and JSON filter documents keep their existing behavior. Raw SQL in a single-argument API filter remains rejected. Direct core `add_filter()` binds a literal value; it does not invoke this expression expansion.

## Permissions, cache and writes

The API uses the same scoped expression access policy for `eval()` and filter expansion. It checks nested types and writing methods and restores the preceding callbacks after success or failure. A value cached by trusted server Python does not let a reader bypass the API's protected-type checks. Access to the outer query type does not grant access to a nested login, ticket or another project's objects.

Administrator calls to `query`, enabled `fast_query`, `get_all_children` and `query_snapshots` run in the existing `ApiClientCmd`, as does `eval`; `get_unique_sobject` already uses Command. This permits authorized writing expressions to participate in the original transaction and journal. If a later filter fails, preceding writes roll back. Successful writing expressions commit their changes, so an expression-valued query is not inherently read-only.

Ordinary readers can evaluate permitted read expressions. `@UPDATE` and `@PYTHON` still require persisted administrator privileges and an active Command. Sudo or an in-memory identity does not grant script execution. Direct core use inherits the caller's context; write-capable server scripts must run through Command.

## Verification and remaining limits

Thirty source-runtime cases cover two/three-part filters, templates, variables, nulls, single/list behavior, pipe membership, groups, JSON, qualified columns and quoted values. Thirty targeted Windows tests also check the unchanged XML-RPC SDK, server Python, nested policies and their restoration, an authenticated reader, successful writes and rollback, plus existing DDL, joins and Workflow contracts. PostgreSQL checks query, children, snapshots, unique lookup and write rollback in an isolated database. Tests are in `tests/test_search_expression_filters.py` and `tests/test_expression_paths.py`.

Database-clock timestamp filters are now supported within their validated syntax; quoting, vendors and limits are documented in [timestamp filter help](timestamp_filters.en.md). Remaining Search restrictions include complex automatic SQL expressions, unsupported joins/relationships and old UI palette methods. This block adds no API methods or signatures and does not make every expression or administrative operation available.

[Core model](core_model.en.md) · [Connections](connections.en.md) · [Site](site_context.en.md) · [Script Editor](script_editor.en.md)

The supported mixed Search/Select query contract and its limits are described in [Search/Select help](search_select.en.md).

## Advanced Search and Quick Filter ownership

Quick Filters appear as managed cards in Advanced Search. **Edit as custom filter** keeps the executable condition and detaches it from its Quick Filter chips. Process, assignee and status facets refer to the same related task. Removing a managed card removes that part of the quick selection when applied. Expressions entered in this search editor are read-only; the general Script Editor/API permission contract above is unchanged.

**Filter Processes** changes which process, built-in and child branches are visible. Cancel keeps the previous visibility. Save applies the draft, and Save and close also hides the editor. This changes presentation without re-running the object query. Repeated schema links share a logical setting; the togglers and Ctrl/Shift selection work across the tree. Tag search and its clear/reload actions retain the selected tags in the current search tab.
