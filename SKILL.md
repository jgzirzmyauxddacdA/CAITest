---
name: cai-export
description: Export existing Character.AI history and profile data; save Definition only when copyable is explicitly true. No conversation recovery or agent judgment is required.
---

# Character.AI direct export

This repository is the complete skill package. Run commands from its root. Read [workflow rules](references/workflow.md) before execution.

## Run

1. Use the user's Character.AI chat URL. Install dependencies with `uv sync --locked`; Google Chrome is required.
2. Start `uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID"` in a persistent process session.
3. Let the user complete login and CAPTCHA in the script's Chrome window. Keep the browser open and the account unchanged. Let the script handle site operations.
4. Monitor the existing runner until it exits. There are no judgment requests or outgoing message plans in this version.
5. Read `workflow_run.json` and `delivery.zip.report.json`, then deliver the current run's `delivery.zip`. Explain skipped/unavailable Definition and any partial export or failure.

## Mandatory Definition policy

- Only `copyable: true` authorizes saving the API-returned Definition body.
- If `copyable` is false, absent, or not a boolean true, skip the Definition even if its body was returned. Do not persist it in the raw response or delivery archive.
- For copyable characters, save a nonempty body verbatim. If the body is absent/empty and `has_definition: false`, record `no_definition`; otherwise record `unavailable` and partial results.
- Continue exporting existing chat history and profile data when the Definition is skipped.
- Never use the legacy recovery workflow, agent judgment helper, test Persona, test chat, outgoing prompts, or reply editing to obtain missing text. Do not normalize or rewrite direct API text.

`--export-only` and `--direct-only` are compatibility aliases for the default behavior. Normal exports require no restoration or cleanup.

## Cancellation and legacy restoration

On cancellation, send Ctrl+C once and observe the runner's exit. If a previous version left a pending restoration journal, run `uv run --locked python scripts/run.py --restore`, with the original `--state-dir` if specified, before another export. This is only for old pending objects, not new recovery attempts. Do not delete the journal to bypass the guard.

Login state and internal records are not delivery artifacts. Never share them or substitute an old ZIP for this run's result.
