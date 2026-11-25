# Direct export workflow (v0.4.0)

1. Verify the signed-in account and export the target character's existing chat history.
2. Recheck the account and query character data by ID.
3. Apply the deterministic Definition policy below. No agent judgment is involved.
4. Package the profile and available history, verify archive bytes and hashes, and report the final status.

| Condition | Definition status | Save body? |
| --- | --- | --- |
| `copyable` is not boolean `true` | `skipped_not_copyable` | No, including raw response files |
| `copyable: true` and nonempty string body | `complete` | Yes, exact API text |
| `copyable: true`, absent/empty body, `has_definition: false` | `no_definition` | No |
| `copyable: true` with any other unusable/missing body | `unavailable` | No; report partial results |

History/profile export continues when Definition is skipped. A deliberate `skipped_not_copyable` result can coexist with workflow `complete`; completeness describes the permitted export scope. An API or login failure is a failure, not proof of no Definition.

Existing placeholders remain exactly as returned by the API. Direct exports never use recovered text or name normalization. Normal runs do not create test objects, change bindings, generate responses, or invoke archival cleanup. Restoration and cleanup are `not_needed`.

The recovery-capable workflow is preserved in tag `v0.3.0`. Legacy internal modules must not be used by this version's export workflow. Only `--restore` may perform writes to repair a pre-existing restoration journal.

The delivery is always `delivery.zip`; inspect `workflow_run.json` and `delivery.zip.report.json` before reporting success. State explicitly when Definition was skipped or unavailable. Login/browser data and internal records stay outside the ZIP.
