# EvidenceTrust

A reusable Python [GenLayer Intelligent Contract](https://docs.genlayer.com/developers/intelligent-contracts/first-contract) for source-grounded evidence verification, with no frontend dependency.

Intended repository: [alaminvyn/EvidenceTrust-GenLayer](https://github.com/alaminvyn/EvidenceTrust-GenLayer).

The current **v2 scoped mode** binds each explicit subclaim to a designated authoritative document. The contract retrieves those documents, extracts source findings, and provides custom validator logic for independent retrieval, classification and quotation grounding. Deterministic rules aggregate the results into Pending, Verified, Disputed or Rejected. Legacy v1 whole-claim verification remains available under v1 policies.

**A v2 Verified result means every required source-specific subclaim is supported and the configured publisher-group threshold is met. It does not mean multiple independent publishers corroborated each individual fact.** Source authority and publisher grouping are configured trust decisions, not facts certified by the contract.

## Validation status

| Evidence | Status and scope |
| --- | --- |
| Recorded automated checks | 190 local tests passed: 102 legacy + 88 scoped; zero failures or skips. Ruff, cached GenVM lint, SDK semantic validation and ABI checks passed. These results are from the implementation run, not a new publication-time test run. |
| Studio functional result | The repository owner reports that a v2 record successfully verified and `get_record` returned `status: Verified` and `attempts: 1`. |
| Public execution evidence | No deployment receipt, validator-log bundle or reproducible live-run evidence is archived in this repository. The owner's report has not been independently reproduced by the local test suite. |
| Remaining runtime coverage | The complete Studio scenario matrix, history UI behavior, actual validator participation, appeals, finality and provider accuracy are not established by the local tests. |

The local suite uses the official SDK with mocked web/model responses. It exercises validator callbacks and serialization, not a live committee. The reported Studio result is not a security audit, a guarantee of model accuracy or evidence of independent corroboration per fact. Builder **Intelligent Contracts** review is the intended contribution category; acceptance is not implied.

The documentation includes dated implementation reports and a historical v1 review. Their statements that the agent did not deploy or run live consensus describe those earlier work sessions. The owner-reported Studio result above is a later, separate observation. Example acceptance targets remain conditional; they are not a record that every case ran successfully.

## Run local checks

Requires Python 3.12+. From the project root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/prepare_sdk.py
.venv/bin/python scripts/check_contract.py
.venv/bin/ruff check contracts tests scripts examples
.venv/bin/ruff format --check contracts tests scripts examples
.venv/bin/python -m pytest -q
.venv/bin/python examples/offline_demo.py
```

Installing dependencies and preparing the SDK download public packages and an approximately 129 MiB official runner archive. After preparation, the checks, tests and demo run offline. They require no RPC service, wallet, private key or Docker. The official `deploy_contract` helper in the tests/demo creates an **in-memory test instance**, not an on-chain deployment.

The contract's first-line dependency comment pins its GenVM runtime. `requirements.lock` pins local tooling; it is not a deployment manifest. The RPC client package `genlayer-py` is a transitive test-tool dependency, not a contract import. No deployment, verification service or wallet operation runs automatically.

## Start with scoped v2

Read the [scoped v2 guide](docs/SCOPED_V2.md). Use:

- [V2 policy](examples/studio/v2/policy.json): `studio-robots-v2`, mode `all_required_subclaims`.
- [Constructor arguments](examples/studio/v2/constructor-args.json): escaped positional representation of one policy JSON string.
- [Studio cases](examples/studio/v2/cases.json): scoped inputs, deterministic IDs and conditional acceptance targets.
- [Contract ABI](docs/contract-schema.json): generated using the official SDK schema extractor.

In Studio's individual `policy_json` **string field**, paste the decoded contents of policy.json: text beginning with `{` and ending with `}`. Do not paste the constructor argument array or add transport escaping. A JSON argument-list editor may require the escaped representation instead; preserve that editor's expected structure.

For `submit_scoped`, provide a JSON string containing exactly one entry per required policy source:

```json
[
  {
    "source_id": "nasa_robots",
    "source_url": "https://www.nasa.gov/robots.txt",
    "claim": "NASA robots.txt includes a User-agent: * directive."
  },
  {
    "source_id": "noaa_robots",
    "source_url": "https://www.noaa.gov/robots.txt",
    "claim": "NOAA robots.txt includes a User-agent: * directive."
  }
]
```

These are candidate assertions to evaluate against actual documents, not a guarantee of current source content. In the same call, provide an observation timestamp in `YYYY-MM-DDTHH:MM:SSZ` format no later than transaction time, and metadata_json as a JSON string object with string values, such as `{"category":"website-policy-audit"}`.

The stored combined statement is generated from the complete canonical mappings. Callers cannot supply an unrelated headline that inherits their Verified result. Missing, duplicate, unknown, swapped-ID/URL or substituted-document mappings are rejected. Swapping assertion text while retaining valid URL bindings creates different assertions that still require source-grounded assessment.

NASA and NOAA are distinct agency publishers under a shared US-government trust root. The example demonstrates bounded document-policy verification, not unrestricted fact checking. The synthetic `examples/policy.json`, `examples/scenarios.json` and `examples/offline_demo.py` remain for offline demonstration. `examples/studio/` outside its v2 subdirectory retains the legacy v1 policy and examples.

## Contract API

| Method | Arguments | Result |
| --- | --- | --- |
| constructor | `policy_json: str` | Validates and stores an immutable policy |
| `submit_scoped` | `subclaims_json: str`, `observed_at: str`, `metadata_json: str` | Record ID; v2 policy only |
| `submit` | `claim: str`, `source_urls: list[str]`, `observed_at: str`, `metadata_json: str` | Record ID; v1 policy only |
| `verify` | `record_id: str` | Resulting application status |
| `get_record` | `record_id: str` | JSON string |
| `get_policy` | none | Canonical policy JSON string |
| `list_records` | `offset: int`, `limit: int` (1–50) | Record ID strings |
| `get_history` | `record_id: str`, `offset: int`, `limit: int` (1–8) | List of JSON strings |

Offsets are zero based. Submission starts Pending with attempts=0. Only the original submitter can request verification. Each accepted verification appends a history entry and consumes one of eight allowed attempts. Rechecks may change any previous state without deleting earlier entries. Failed execution or consensus does not append application history.

Use the plain 64-character record ID in a typed Studio string field, without quotes, array brackets or an added `0x`. For history, use `get_history(record_id, 0, 8)`; limit 10 is invalid. A Studio history-read error was reported and has not been reproduced or conclusively diagnosed here. Do not infer a storage fix or a successful history UI test from the reported Verified result.

## V2 decision rules and consensus

Rules apply in this order:

1. Internal source inconsistency or a mix of supported and refuted required subclaims produces **Disputed**. A mixed-result bundle need not mean publishers contradict each other about the same fact.
2. Any required subclaim with unavailable or insufficient evidence produces **Pending**, unless rule 1 already applies.
3. Every required subclaim must support, and distinct authoritative publisher groups must meet min_support, for **Verified**.
4. Every required subclaim must contradict, and the authoritative group count must meet min_refute, for **Rejected**.
5. Otherwise, the result is **Pending**.

Thresholds remain at least two; they were not lowered to force Verified. V1 retains its separate whole-claim rules and original fingerprints/record formats. V2 fingerprints include mode, policy hash, canonical source–subclaim mappings and observation time; history preserves mode and mappings.

The contract uses `gl.vm.run_nondet_unsafe`. The leader retrieves documents and extracts structured findings. Validators independently repeat retrieval/extraction, compare mappings, classifications, retrieval outcomes and exact content hashes, then check the leader's quotations against their own document and the designated subclaim. Malformed output and failed grounding are rejected. Schema checks alone do not constitute agreement.

## Limits and remaining risks

- At most six approved sources; bounded inputs, 48,000-byte UTF-8 source bodies and 600-character quotations. Scoped text and its generated statement must fit the existing claim budget.
- Authority, publisher independence and reference relevance depend on policy configuration. The contract does not discover every conflicting source or authenticate publishers cryptographically.
- Changing page bytes can prevent agreement. PDFs, screenshots, JavaScript rendering, authenticated pages and paywalls are outside this version's scope.
- Observation timestamps are user assertions, not historical snapshots. Model mistakes and prompt injection remain possible despite grounding and independent checks.
- DNS/private-network egress and redirects depend on node infrastructure. The pinned retrieval API exposes no final URL or redirect-control argument.
- Global duplicate protection is not semantic deduplication and permits first-submitter reservation. Lost submitter access prevents rechecks. There is no automatic refresh or recovery service.
- Application Verified is separate from protocol finality. Network resource costs and latency have not been benchmarked here.

## Documentation and repository contents

| Path | Purpose |
| --- | --- |
| `contracts/evidence_trust.py` | Standalone contract; working source retained unchanged during publication preparation |
| `tests/conftest.py`, `tests/direct/*.py` | Official SDK fixtures, legacy and scoped tests |
| `examples/*.json`, `examples/offline_demo.py` | Synthetic offline scenarios and demo |
| `examples/studio/*.json` | Legacy Studio inputs and dated public-source HTTP preflight |
| `examples/studio/v2/*.json` | Scoped v2 policy, constructor arguments and cases |
| `scripts/*.py` | Public SDK preparation and local validation helpers |
| [Architecture](docs/ARCHITECTURE.md), [scoped v2](docs/SCOPED_V2.md) | Design, invariants and assurance model |
| [Threat model](docs/THREAT_MODEL.md), [SDK references](docs/SDK_REFERENCES.md) | Risks, concrete APIs and runtime provenance |
| [Testing](docs/TESTING.md), [Studio guide](docs/STUDIO_TESTING.md) | Recorded local results and manual testing instructions |
| [Historical review](docs/FINAL_REVIEW.md), [ABI](docs/contract-schema.json) | Earlier v1 review and current seven-method interface |
| `pyproject.toml`, `requirements.lock`, `.gitignore`, `README.md` | Tool configuration, dependency pins and repository guidance |

Upload only these reviewed source/documentation files. Exclude `.venv/`, `.cache/`, `.pytest_cache/`, `.ruff_cache/`, every `__pycache__/`, `*.pyc`, `artifacts/` and all `.DS_Store` files. SDK archives, cached source downloads, local backups, test reports and debug/header files are not repository deliverables. Do not upload credentials or private execution data. The .gitignore covers Git staging; it does not filter a manually selected ZIP or GitHub browser upload.

No LICENSE file is supplied. Choose a license before advertising unrestricted reuse; no license choice is implied by this repository preparation.
