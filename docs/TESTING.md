# Testing and recorded results

## Reproduce

Use Python 3.12+ and the commands in the root README. After dependency installation:

```sh
.venv/bin/python scripts/prepare_sdk.py
.venv/bin/python scripts/check_contract.py
.venv/bin/ruff check contracts tests scripts examples
.venv/bin/ruff format --check contracts tests scripts examples
.venv/bin/python -m pytest -q
.venv/bin/python examples/offline_demo.py
```

SDK preparation downloads the pinned official release artifact and verifies the release-published SHA-256. It can instead use an existing download with `--archive /absolute/path/genvm-runners-all.tar.xz`. No deployment occurs. After preparation, all listed checks and tests are offline.

The pytest suite uses the **official GenLayer direct-mode SDK fixtures**, real typed storage and calldata, and mocked web/model responses. It does not replace `genlayer` with a homemade fake. `-p no:gltest` disables the unrelated RPC plugin so pytest does not load environment files, configure accounts or contact a network. The official `gltest_direct` plugin remains active. Tooling compatibility adaptations are described in SDK_REFERENCES.md.

## Final local results

Recorded on 2026-11-16 using Python 3.12.16, macOS ARM64, pinned GenVM v0.3.0-rc7 runner, genlayer-test 0.29.2 and genvm-linter 0.11.0.

| Check | Result |
| --- | --- |
| pytest complete suite | **190 passed; 0 failed; 0 skipped** (102 unchanged legacy + 88 scoped) |
| Official GenVM AST lint | Passed, three checks |
| Official SDK semantic validation | Passed; seven methods, four view and three write |
| Ruff static checks | Passed |
| Ruff formatting | Passed |
| Offline synthetic demo | All five scenarios and captured-validator checks passed; five history entries retained |
| Official closure and calldata serialization | Passed inside the pytest suite |
| GenVM WASM execution | **Not run** |
| Live model evaluations / GenVM web retrieval | **Not run** |
| Public-source host HTTP preflight | Two public GETs passed; source sizes 69 and 2,631 bytes; not contract execution |
| Studio input packs | V1 input check retained; v2 constructor and four deterministic submit_scoped IDs checked by pytest without verification calls |
| Live multi-validator network consensus, appeals and finality | **Not run** |

The official linter prints an informational runner-version advisory; the exact pinned tutorial runner is intentionally retained, as described in SDK_REFERENCES.md. Earlier implementation test failures were corrected; no known failing test remains in the final suite.

## Coverage

- Submission defaults, typed storage, identity, observation and submission times, metadata, pagination and missing IDs.
- Duplicate claims across callers, metadata and URLs, canonical host casing, repeated URLs and different observation times.
- Claim/metadata/policy limits, strict JSON and duplicate keys, invalid dates, future observations, unsafe URL syntax, localhost/IP/credential/port tricks, path traversal and malformed encoding.
- Immutable source policy, authority/threshold types, publisher groups, reference host matching and combined source budgets at submission.
- Verified, Rejected, Disputed and Pending rules with explicit independent validator calls.
- Rechecks preserving original fields and all earlier history, caller authorization and eight-attempt limit.
- HTTP errors/redirect status, empty/oversized/non-UTF-8 bodies and request exceptions becoming unavailable, not false claims.
- Malformed model output, invented/short/non-string quotes, invalid labels and duplicate model keys failing without history writes.
- Independent validator disagreement, changed documents despite equal classifications, tampered state/explanations/source identity/authority/group/quotes, irrelevant existing excerpts, leader exceptions and malformed grounding answers.
- Independent publisher-group counting and non-authoritative source exclusion from authoritative quorum.
- 625 combinations of four source classifications exercising conflict and abstention precedence within one exhaustive test.
- Distinct grounded excerpts, Unicode excerpts, real SDK cloudpickle closure roundtrips and calldata encoding/decoding.
- Five externally stored synthetic example scenarios.

The prompt-injection fixture asserts behavior for a mocked abstaining model response; it does **not** prove a live model resists that attack. Similarly, a mocked grounding verdict tests enforcement of the verdict, not the accuracy of a model's judgment.

## What local direct tests cannot establish

Direct mode executes a leader immediately, then exposes a captured validator function for separate calls. It does not require committee votes before committing its in-memory changes. Disagreement tests therefore assert the validator returns false; they do not claim protocol rollback or real consensus occurred. Production `run_nondet_unsafe` returns an accepted leader result only after the executor's consensus path permits it.

Serialization tests exercise official cloudpickle and calldata under host Python, not the WebAssembly boundary. SDK semantic validation checks the contract schema and storage compatibility, not every runtime path. Full GenVM execution, model-provider behavior, network egress enforcement, gas/resource budgets and finality remain unvalidated here.

## Future integration acceptance criteria

No integration deployment was performed or automated because deployment is outside this task's authorization. Before relying on the contract in a network, a separately authorized local Studio/GenVM test should verify:

1. The target executor supports the pinned runner and imports the contract.
2. Valid submission persists Pending; duplicate/invalid submission reverts without state changes.
3. Independent validators retrieve controlled public fixtures and accept corroborated/refuted scenarios.
4. A deliberately dishonest leader is rejected; no application history is committed for a failed consensus transaction.
5. Changing source responses produce rejection/undetermined behavior rather than silently accepting stale hashes.
6. Failed model/provider execution does not consume attempts; successful rechecks append exactly one revision.
7. Real adversarial pages and historical claims trigger conservative abstention or a supported conflict decision.
8. Source redirects and DNS rebinding are blocked by node infrastructure; request/download budgets hold.
9. Receipts, finality and any protocol appeal are handled separately from application status.

These are unexecuted acceptance criteria, not passing integration tests or evidence of production readiness.

## Studio preparation follow-up

The final review reran all 102 tests and local checks. `docs/STUDIO_TESTING.md` provides unexecuted manual Studio steps and a public-source acceptance matrix. `examples/studio/` contains the policy, escaped constructor argument, four submit/verify input sets with expected IDs, and a separate public HTTP preflight report. None of these new materials changes the contract or establishes live consensus.

## Scoped v2 results

The extension's final local run passed **190 tests: 102 existing legacy tests plus 88 scoped tests**, with zero failures or skips. The original v1 registry/verification tests and fixtures, and `examples/studio/policy.json`, were checksum-checked unchanged. Official cached GenVM lint and semantic validation passed; schema extraction confirms all six v1 method ABIs and the constructor remain unchanged, with only submit_scoped added. Ruff static/format checks passed. No dependency or runner update was needed.

New coverage includes all 25 two-source label combinations, exact required mappings and source IDs, swapped/replaced URLs, duplicate/oversized/invalid payloads, separate mode entry points, unchanged thresholds, identity canonicalization, claim-text swaps assessed against the designated document, source-specific extraction and grounding, fabricated/tampered findings and mode, independent disagreement and document changes, malformed model output, history/authorization/eight-attempt limits, the six-source bound, official closure/calldata serialization, and all four shipped v2 Studio input IDs. A three-source test prevents two supporting groups from overriding an insufficient third required subclaim.

The updated [scoped guide](SCOPED_V2.md) specifies the new assurance model and exact Studio handoff. The standalone v2 policy and input pack are at `examples/studio/v2/`. Their four verification statuses are unexecuted acceptance targets. This extension performed no network calls, source refreshes, wallet access, RPC transaction submission or deployment. All automated model/retrieval evaluations use mocks; the schema/serialization checks use the cached official SDK on host Python. Actual GenVM WASM execution, provider accuracy, committee consensus, network egress and finality remain untested here.
