# CAITest 0.4.0

Export existing Character.AI chat history and character profile data into a verified ZIP. Save the Definition only when the character API explicitly returns `copyable: true` and a nonempty Definition. This version does not attempt conversation-based recovery or request agent judgments.

## Start with one prompt

Open the [prompt generator](docs/index.html) locally after cloning the repository. Paste the generated prompt into an agent that can run local commands.

```text
Clone https://github.com/jgzirzmyauxddacdA/CAITest.git into the current workspace, or reuse an existing checkout without overwriting local changes. Read SKILL.md and references/workflow.md, then set up the dependencies as described in README.md.

Use this skill to export existing chat history and character data for: YOUR_CHARACTER_URL

Save the Definition only if the API explicitly returns copyable: true and provides its body. Otherwise skip it; do not attempt Definition recovery or send test messages. If login or a CAPTCHA is required, let me complete it in the Chrome window opened by the script. Wait for the runner to exit, check workflow status and ZIP verification, then return delivery.zip and report any skipped or unavailable Definition.
```

## Installation and usage

Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Google Chrome are required. Run from the repository root:

```powershell
uv sync --locked
uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID"
```

Sign in and complete any CAPTCHA in the script's separate Chrome window. Keep that window open and stay on the same account until the runner exits. Login waits up to 600 seconds by default; `--login-timeout` accepts 1-3600 seconds. Remove `CHARACTER_AI_TOKEN` from the environment to use browser authentication.

All exports use the same read-only workflow. `--export-only` and `--direct-only` remain accepted as compatibility aliases. The runner does not create Personas or chats, send messages, edit replies, or change Persona bindings. It queries the target by ID without opening its chat page.

## Definition policy

| API response | Result |
| --- | --- |
| `copyable` is not exactly `true` (including missing or unknown) | `skipped_not_copyable`; no Definition body is saved, even if one was returned |
| `copyable: true` with nonempty Definition text | Save the API body verbatim, including placeholders |
| `copyable: true`, empty/missing body, and `has_definition: false` | `no_definition` |
| `copyable: true` but no usable body otherwise | `unavailable`; deliver partial results without recovery |

A non-copyable Definition is an intentional skip and does not by itself make an otherwise successful export partial. Chat history and profile data are still exported. The `definition` field is `null` when skipped; the raw character-response file also excludes that body. No regex normalization is applied to direct API text.

## Results

Each run creates `output/<CHARACTER_ID>/<TIMESTAMP-ID>/`:

- `delivery.zip`: `Persona.json` plus the exported history JSON when available.
- `delivery.zip.report.json`: archive integrity checks, file hashes, Definition status, and completeness.
- `workflow_run.json`: workflow status and errors; normal exports record restoration and cleanup as `not_needed`.

Share only `delivery.zip`. A successful skip is reported explicitly; `complete` does not mean a Definition was included. Copyable characters whose Definition body was unavailable, or incomplete history exports, produce `partial` results. Exit codes: 0 complete, 2 partial, 1 failed, 130 cancelled, 3 restoration/cleanup required or failed.

Use `--out` for a new destination directory. Existing runs are never overwritten. `--gold` optionally compares an exported API Definition with a known original file.

## Legacy recovery journals

The previous recovery-capable release is tagged `v0.3.0`. Version 0.4.0 uses direct export only. Legacy internal recovery modules remain for compatibility, but are not imported or invoked by the normal runner.

If an older run left a pending restoration journal, finish it before starting an export:

```powershell
uv run --locked python scripts/run.py --restore
```

Use the same `--state-dir` as the original run when applicable. This explicit legacy repair command may restore the old binding and archive the old test objects. Never delete a pending journal to bypass it. During a normal export, Ctrl+C cancels the run; no new test objects need cleanup.
