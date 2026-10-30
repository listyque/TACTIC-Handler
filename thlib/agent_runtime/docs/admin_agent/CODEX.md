# Codex as the external administrator host

This is a host setup recipe, not a TS provider integration or a TH runtime
bridge. Codex CLI launches the optional stdio adapter using its own login and
model. TS receives ordinary authenticated API requests. Start with
[CONNECTION](CONNECTION.md) for adapter installation, rights and version gates.
The [official Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp)
describes the host configuration; check `codex --version` and `codex login status`
on the operator's computer. Existing ChatGPT login can be used by the CLI;
neither TACTIC product needs an OpenAI API key.

On Windows the host prefers `codex.exe` from PATH and uses `codex.cmd` only
when no native executable is available. An older npm CLI can return an older
model catalogue than the desktop application's bundled executable. Use the
same current executable for discovery and execution; never add model IDs to
the selector by hand. The catalogue comes from that executable's `model/list`.

## Dedicated administrator workspace

Use an empty directory separate from both source repositories. Configure its
trusted `.codex/config.toml` with absolute paths for that installation:

```toml
sandbox_mode = "read-only"
web_search = "disabled"
project_doc_max_bytes = 0

[features]
shell_tool = false
apps = false
multi_agent = false

[mcp_servers.tactic]
command = "<absolute Stream Python executable>"
args = ["-B", "-X", "utf8", "-m", "tactic_stream.admin_agent", "--server", "http://<host>:8081", "--project", "<existing project>", "--stream-root", "<TS/tactic_stream>", "--handler-root", "<TH>"]
cwd = "<TS/tactic_stream>"
env_vars = ["TACTIC_AGENT_TICKET"]
required = true
startup_timeout_sec = 30
tool_timeout_sec = 60
default_tools_approval_mode = "writes"
```

The host's private environment supplies `TACTIC_AGENT_TICKET` before Codex
starts. Never add its value to TOML, prompts, command arguments or Git. This
uses the editable adapter installation from CONNECTION; reference roots are
documentation only. Keep unrelated MCP servers/plugins disabled in this
administrator workspace. Start Codex in that directory and verify that only
the intended TACTIC tools are available.

The example exposes discovery/preview only. Add only the adapter flags needed
for the requested operation to `args`: `--allow-naming-save`,
`--allow-page-save`, `--allow-project-create`, `--allow-automation-draft`, or
`--allow-automation-activate`. Host approval and server ACLs remain separate.
Review exact automation source/binding before exposing activation; an inactive
draft does not execute. Activation also requires [the isolated runner](SCRIPT_TRIALS.md)
and matching passed trials. Add its `--trial-image` and `--trial-directory` args,
and set `tool_timeout_sec = 180`. Read-only filesystem mode does not restrict a tool's
remote writes or the future permissions of an activated native TH script.

With noninteractive `codex -a never exec`, a tool requiring approval fails; a
user sentence in the prompt cannot approve it. The disposable acceptance below
explicitly preapproves its narrowly exposed tools for its owned server. Do not
copy that preapproval to an unrelated or production MCP server.

## Initial administrator message

Ask the host to use only TACTIC MCP tools, read `agent_capabilities`, `ts.start`
and `ts.model`, and retrieve the task recipe (`ts.pages`, `ts.projects`, or
`th.automation`) as needed. Then give the business request in ordinary language.
Do not attach source trees, repository AGENTS, backlog or ready-made API payloads.
Inspect actual tool calls and read-back, rather than trusting the final prose.
Naming/page tools remain bound to the selected project; rebind the adapter after
creating a project. Knowledge for TH execution and TS storage remains separate.

## Reproducible five-scenario acceptance

From a source checkout, with the `agent` extra, a logged-in `codex.cmd`, the
adjacent TH dependencies and the installed browser test dependencies/cache:

```text
python -B -X utf8 tools/check_external_agent.py --handler-root <TH> --trial-image <trusted immutable image ID> --output-dir <new private directory outside both repositories>
```

This runs a real model, not predetermined tool requests. Each phase starts an
ephemeral Codex session with invocation-only MCP configuration, existing CLI
authentication, no source context, and no shell/apps/web access. No global
Codex configuration is changed. The harness owns a disposable SQLite HTTP
server, generated program fixtures, databases and repositories; normal running
TACTIC servers and user records are untouched. Model usage is incurred.

Checks cover native project/schema/workflow creation, template reinstallation
and destination check-in; revision-checked naming with identical retry and
two real upload versions; a filtered page opened through browser navigation
and reload, native dock geometry and independent TH configuration consumers;
then before/after check-in programs and a real native TH shelf click opening a
modal Frame with captured selection and correct close cleanup.

After draft creation, inspect `03-drafts-for-review.json`. The harness prints
its SHA-256. Only after reviewing the exact source, paths, arguments and bindings,
write that hash to `review-approved.txt` in the output directory. The harness
then enables guarded configuration activation after fresh isolated trials.
The review wait is bounded to 30 minutes. Failure stops the run; no success is
inferred from the model's summary. Output contains prompts, actual MCP JSONL,
read-back, screenshots and consumer logs, and stays outside version control.
Owned server/runtime data are cleaned on normal completion or exception.

Inactive drafts are tested in separate verified OCI containers before activation.
Generated Python stays in OCI trials; activation saves the real native bindings
but does not execute that Python on the host. Review reports in the ordinary
Script Editor; manually accept the published result in its owning TH/TS UI.
No EXE installation or fresh paired TH/TS visual parity is implied. API-only
check-in can bypass client hooks; those hooks are not server enforcement. Model
choices vary, so this opt-in live acceptance is not a deterministic CI unit test.
