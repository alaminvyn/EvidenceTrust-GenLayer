# Final review and Studio readiness

**Historical v1 review:** the 18-file review and 102-test results below describe the original version. The current source also includes the scoped v2 extension; see [SCOPED_V2.md](SCOPED_V2.md), [TESTING.md](TESTING.md) and the regenerated ABI for current behavior and counts. Seven public methods now include submit_scoped. No live execution is claimed for this extension.

Review date: 2026-11-16. Result: **ready for manual Studio compatibility and execution testing; live-runtime compatibility and Builder execution evidence remain outstanding**. No contract code changes were needed during this review. No deployment, funds, private credentials or live model calls were used.

## Original 18-file review

| Original file | Review result |
| --- | --- |
| contracts/evidence_trust.py | Complete standalone contract; typed storage, six public methods, validated immutable policy, bounded input/rechecks, deterministic status rules and independently grounded custom validator |
| tests/conftest.py | Pinned project cache, offline preflight and documented test-only SDK registry isolation; RPC plugin disabled in project config |
| tests/direct/conftest.py | Official direct-mode fixtures, isolated source/model mocks, explicit double-encoding adaptation for the official mock layer |
| tests/direct/test_registry.py | Submission, timestamps, duplicate/URL/policy validation, pagination and combined source-budget cases reviewed |
| tests/direct/test_verification.py | Four states, history, authorization, transport failures, hostile proposals, grounding and official serialization cases reviewed |
| examples/policy.json | Valid synthetic policy; deliberately unsuitable for live public retrieval; retained for offline demonstration |
| examples/scenarios.json | Five clearly synthetic scenarios with mock-only expected outcomes |
| examples/offline_demo.py | Executable official SDK in-memory example; no RPC or on-chain deployment |
| scripts/prepare_sdk.py | Official asset pin and release checksum; project-local legacy filename adapter, no installed SDK edits |
| scripts/check_contract.py | Official lint plus SDK semantic validation using the pinned cache |
| docs/ARCHITECTURE.md | Models, execution boundary, decision precedence, history and invariants match implementation |
| docs/THREAT_MODEL.md | Trust-policy, injection, DNS/redirect, availability, timestamp and duplicate-squatting limitations are disclosed |
| docs/SDK_REFERENCES.md | Concrete SDK APIs inspected, runner mismatch and local test adaptations documented |
| docs/TESTING.md | Reproduction instructions and 102 passing tests; unexecuted integration criteria clearly separated |
| pyproject.toml | Python >=3.12, pinned direct tools, official direct pytest plugin retained, RPC plugin disabled |
| requirements.lock | Exact tested transitive environment; RPC client is tooling-only, not a contract dependency |
| .gitignore | Environment, secrets-pattern, generated artifact and cache exclusions present |
| README.md | Setup, all API parameters, semantics, limitations and inventory complete; linked new Studio materials |

## Official contract and deployment checks

Checked against the [official first-contract requirements](https://docs.genlayer.com/developers/intelligent-contracts/first-contract), [storage documentation](https://docs.genlayer.com/developers/intelligent-contracts/storage), [equivalence-principle guidance](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) and the actual pinned SDK.

- First-line JSON dependency comment present; runner is pinned to `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
- Exactly one `gl.Contract` subclass; public methods use supported decorators. Two write methods are nonpayable; four methods are views.
- Persistent fields use supported typed TreeMap/DynArray/str storage. Constructors do not manually instantiate runtime-owned collections.
- Contract imports only GenLayer and deterministic Python standard-library modules. Local tests, clients, caches and requirements.lock must not be uploaded into GenVM.
- Source access and prompts are executed through custom nondeterministic leader/validator functions. Plain snapshots are captured, not storage objects.
- Validator independently retrieves/extracts findings, compares substantive fields/content hashes and checks the leader's quotations in context. It does not approve a decision from JSON shape or enum membership alone.
- Constructor ABI has **one positional string**, `policy_json`. Source arrays/bools/thresholds are nested inside that JSON string, not separate constructor arguments.
- Extracted SDK schema saved as `docs/contract-schema.json`: one constructor argument, six methods, correct readonly/payable flags.
- Runtime dependency exists in the inspected GenVM v0.3.0-rc7 archive. This proves artifact availability, **not** that a particular Studio host supports it. Confirm via Studio schema import and actual local execution.
- Local environment uses Python 3.12.16 with genlayer-test 0.29.2 and genvm-linter 0.11.0. GenVM's own runtime is selected by the runner hash; requirements.lock is not a deployment manifest.

## Checks rerun

- pytest: **102 passed, 0 failed, 0 skipped**.
- Official lint: passed, three checks.
- Official SDK semantic validation and schema extraction: passed.
- Ruff static checks and format check: passed.
- Offline demo: five scenarios and captured-validator checks passed.
- Studio public-input constructor, submission IDs and JSON argument shapes: checked locally with the official SDK, without live retrieval or model calls.
- Public HTTP source preflight only: NASA and NOAA returned 200 with small UTF-8 bodies. This is explicitly separate from node connectivity and contract execution.
- GenVM WASM, Studio deployment, live models, multi-validator execution, appeals and finality: **not run**.

## Remaining issues and review gates

| Priority | Remaining issue | Before presenting the project as tested in Studio |
| --- | --- | --- |
| Execution gate | Pinned runner has not executed in the target Studio/GenVM instance | Confirm import/schema and constructor, then run submit/verify and inspect actual receipts |
| Evidence gate | No live validator or model accuracy evidence | Capture actual multi-validator logs and source-grounded results; otherwise state only local tests passed |
| Liveness | Exact source hashes can reject otherwise equivalent changing pages | Use stable endpoints, record hashes, and preserve this safety tradeoff in submission notes |
| Trust policy | Authority/group assignments are configured, not independently certified | Explain reviewer-selected policy and shared trust roots; source credibility is not cryptographic publisher authentication |
| Network boundary | SDK exposes no final URL, redirect switch or DNS inspection | Confirm node-level redirect/private-network egress controls before relying on authority attribution |
| Scope | Fixed reference set cannot discover every contradictory claim or prove historical page contents | Describe the project as policy-bounded evidence verification; keep observation times distinct from provenance |
| Access/lifecycle | Only submitter can consume eight rechecks; global deduplication permits first-submitter reservation | Disclose lost-access, front-running and stale-result limits; no recovery mechanism is implied |
| Resources | Up to six web requests and six extraction calls per leader, plus up to six grounding calls per validator after independent extraction | Measure actual time/resource budgets in Studio; no measured fee or latency claims yet |
| Reuse preparation | No LICENSE file is supplied | Choose and add an explicit license before presenting unrestricted public reuse terms |
| Submission package | No public repository URL or recorded Studio run has been supplied here | Publish/share the intended source and actual run evidence when ready; verify current program fields directly |

No current source-level or SDK-schema blocker was identified. This is not a security audit or a certification of deployment compatibility. Builder category fit is supported by the standalone Intelligent Contract and custom validation design; acceptance and current program-specific requirements remain external decisions.

## Final checklist

- [x] Review all original 18 files.
- [x] Verify SDK conventions against official documentation and concrete SDK source.
- [x] Check constructor, dependency manifest, public ABI and persistent storage.
- [x] Rerun 102 automated tests and local lint/schema/style checks.
- [x] Prepare Studio import/run instructions without executing them.
- [x] Prepare a public-source policy, escaped constructor arguments, four scenario inputs and expected IDs.
- [x] Separate expected results, host HTTP observations and actual local test results.
- [x] Preserve no-deployment/no-spend/no-private-credential constraints.
- [ ] Confirm target Studio supports the pinned runner and actual constructor execution.
- [ ] Run the public-source cases through real GenVM and inspect validator logs/finality.
- [ ] Record actual resource/latency behavior and unexpected abstentions or errors.
- [ ] Confirm network egress/redirect controls and policy trust assumptions.
- [ ] Choose a license, supply the intended repository/demo evidence and confirm current Builder submission fields.
