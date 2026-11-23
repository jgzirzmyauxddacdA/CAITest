# CAITest

Provide a Character.AI character link, sign in once, export existing chat history, attempt to recover the Definition, and receive a ZIP archive.

## Start with one prompt

**[Open the prompt generator](https://hlm-wztxm.github.io/CAITest/)** → Paste a character link → Generate the prompt → Copy it into the Codex desktop app or another agent that can run local commands.

The generator creates an English prompt entirely in your browser. It does not submit your character link or start an export. When the workflow runs, follow the prompts to sign in to Character.AI in Chrome. GitHub READMEs do not support interactive forms, so the generator is hosted on a separate page. After downloading the repository, you can also open [docs/index.html](docs/index.html) locally to use it offline.

Alternatively, copy the following prompt and replace `YOUR_CHARACTER_URL` with a character link, such as `https://character.ai/chat/CHARACTER_ID`:

```text
Clone https://github.com/HLM-wztxm/CAITest.git into the current workspace, or reuse an existing checkout without overwriting local changes. Read SKILL.md and references/workflow.md, then set up the dependencies as described in README.md.

Use this skill to run the full reverse-engineering and export workflow for this Character.AI character: YOUR_CHARACTER_URL

Export the existing chat history, retrieve the character data, and attempt Definition recovery when needed, following the skill. Handle each agent judgment request and continue until the runner exits. If login or a CAPTCHA is required, let me complete it in the Chrome window opened by the script. Check the final workflow status, restoration, cleanup, and ZIP verification, then return the delivery.zip path. Clearly report partial results and any unverified Definition content.
```

Git, uv, and Google Chrome are required. The agent can set up dependencies using the instructions below. A regular web chat without local command execution cannot run this skill directly.

**The current Codex agent makes semantic judgments and plans outgoing messages; the scripts execute the workflow deterministically.** The bundled scripts handle browser operations, history export, text extraction, packaging, and cleanup. This repository is a complete skill package: see [SKILL.md](SKILL.md) for the entry point and the [workflow rules](references/workflow.md) for judgment criteria.

Ask Codex to use this directory's `SKILL.md` to process a character link. The agent will run:

```powershell
uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID"
```

This command starts the full workflow: history export, character data retrieval, Definition recovery through conversation when needed, and packaging. The script automatically opens a separate Chrome window. On first use, or when your session expires, complete the Character.AI login and CAPTCHA manually. When a candidate judgment or message plan is required, the script stays running and waits for the current agent to submit its decision before continuing.

## 1. Installation

You need Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Google Chrome. Run the following commands in Windows PowerShell:

```powershell
git clone https://github.com/HLM-wztxm/CAITest.git
cd CAITest
uv sync --locked
```

If you already have the repository, run `uv sync --locked` from its root directory. You do not need to manually install Python, a Chrome extension, or Playwright browsers.

To install it as a personal skill, place the entire repository in `~/.agents/skills/cai-export/`; copying only `SKILL.md` is not sufficient. Install dependencies in the skill directory with `uv sync --locked`. Login state and output files are not part of the distribution.

Directory structure:

```text
cai-export/
├── SKILL.md
├── agents/openai.yaml
├── references/workflow.md
├── scripts/
│   ├── run.py
│   ├── agent_judge.py
│   ├── history_export/
│   └── other execution modules
├── tests/test_agent_judge.py
├── pyproject.toml
├── uv.lock
└── README.md
```

Run all commands from the skill root. Results are saved under `output/` in that directory.

## 2. Choose a mode

### Default: full workflow with judgments by the current agent

By default, omit `--export-only`. The workflow exports history, retrieves character data, and attempts recovery through conversation when the API does not return the Definition text. Conversation recovery is skipped if the text is returned or the API explicitly indicates that the character has no Definition.

Requests to reverse-engineer and export, character exports without an explicit scope restriction, and additional character links in the same task follow the [mode selection rules in SKILL.md](SKILL.md#mode-selection). Any explicit restriction to export-only mode remains in effect.

Have Codex start the script according to [SKILL.md](SKILL.md) and keep handling its judgment requests until delivery is complete.

```powershell
uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID"
```

### Explicit option: export existing data only

Use `--export-only` only when the user explicitly requests existing chats and readable character data, or prohibits conversation recovery, test chats, or sending messages.

```powershell
uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID" --export-only
```

This exports existing history and character data readable by the current account. Existing history is still delivered if the Definition cannot be read. The archive is always named `delivery.zip`; partial-result status is recorded in the JSON data and verification report.

### Agent handoff during the full workflow

Requests and decisions are stored in `output/<CHARACTER_ID>/<TIMESTAMP-ID>/agent-judge/`. Whenever the runner waits for a decision, the terminal prints `waiting_for_judgment`, `kind`, and a unique `request_file`. A `candidate` request requires an eight-field judgment, including completeness and marker evidence. A `message` request requires a five-field plan, including the actual message and continuation anchor. Follow the `decision_schema` in that request:

```powershell
uv run --locked python scripts/agent_judge.py submit --request "REQUEST_FILE_PATH" --decision "DECISION_FILE_PATH"
```

The script validates the request type, request ID, run ID, evidence digest, and source line numbers or message template. Each response can be submitted only once. Initial messages and fallback text use the fixed values defined in the workflow. The agent supplies continuation anchors and complete outgoing messages; the script validates and sends them unchanged. If an ending cannot be confirmed and there is no identifiable truncation point at the end, use `accept_partial` to retain valid text and finish.

Each judgment has a default timeout of 600 seconds; use an option such as `--agent-timeout 900` to change it. Timeouts, cancellations, and invalid responses follow the existing recovery path. In agent mode, `judge_usage` is `{}` because the script cannot measure the host agent's token usage. Candidate judgments and message plans are counted separately. The generation budget remains at most six steps, with three candidates per step.

The site request timeout is 120 seconds.

## 3. Run

Replace the character link below:

```powershell
uv run --locked python scripts/run.py "https://character.ai/chat/CHARACTER_ID"
```

Sign in to your Character.AI account and complete any CAPTCHA in the separate Chrome window opened by the script. The default login timeout is 600 seconds. Open email verification links in that same window as well. Keep the window open and stay signed in to the same account throughout the run. Later runs reuse the login state. Run only one task per account at a time.

Use the terminal output to track progress; it is normal for the browser page not to update with each request. At the end, the workflow restores the original Persona binding, archives the test chat, and removes the test Persona when those objects were created.

When using Codex, ask it to follow `SKILL.md` and continue handling judgment requests. If login is required, complete it manually in the separate Chrome window. Codex returns the ZIP path when the task finishes.

## 4. Results

Results are saved in `output/<CHARACTER_ID>/<TIMESTAMP-ID>/`:

- `delivery.zip`: the delivery archive, containing the retrieved character data and chat history. Check the JSON data and verification report for completeness status.
- `workflow_run.json`: run status and error details.

Share only the delivery ZIP. A Definition recovered from model responses may be incomplete or inaccurate; `unverified` means its authenticity has not been verified. Agent judgments use your existing Codex usage allowance.

For conversation recovery, `Persona.json` also includes `definition_normalized`. A regex replaces the current run's test Persona name and account username with `{{user}}`, without agent judgment. Matching is case-sensitive and requires complete names with no adjacent Unicode word characters (letters, numbers, or underscores). Existing `{{...}}` placeholders are preserved, and regex special characters in names are treated literally.

The `definition` field and continuation anchors retain the original accepted text. `definition_normalization` records the names actually replaced, their counts, and an `unverified` authenticity status. Fictional characters sharing those names may also be replaced, so normalization does not prove the original placeholders have been recovered. Definitions returned directly by the API are not normalized.

## Interruptions and cleanup failures

While the runner is waiting for an agent judgment, cancel with the following command, then wait for the original runner to finish restoration and cleanup:

```powershell
uv run --locked python scripts/agent_judge.py cancel --request "CURRENT_REQUEST_FILE_PATH"
```

During other phases, press Ctrl+C once. Neither `submitted` nor `resolved` means the entire run has finished. Check the runner's exit status and `workflow_run.json` for the final outcome.

If the script reports a pending restoration or exits with code `3`, first run:

```powershell
uv run --locked python scripts/run.py --restore
```

If the original run used `--state-dir`, pass the same directory when restoring. Do not delete recovery records to bypass a blocked run.

Persona cleanup saves the archive API's success receipt and confirms removal by refreshing the Persona list. An archived Persona's detail endpoint may return HTTP 400, so cleanup does not use that endpoint to verify removal. Recovery tasks left by older versions also check the list: `absent` means the object is confirmed missing from the list but there is no original archive receipt; `archived` means a success receipt is also available. API errors or unexpected list formats leave the recovery record in place. Check `definition/cleanup-result.json` in the run directory for retry results.

Do not commit or share login data or run data. If the `CHARACTER_AI_TOKEN` environment variable is set, remove it from the terminal environment before running so the workflow uses the browser login session.

## Development checks

Run the offline tests from the skill root:

```powershell
uv run --locked python -m unittest discover -s tests -v
```
