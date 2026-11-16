# Scoped subclaims v2

## Contract and assurance model

`all_required_subclaims` is an explicit opt-in policy mode. It verifies the conjunction of source-specific assertions, each grounded in its designated authoritative document. It does **not** claim two independent publishers corroborated each individual assertion. Existing policies without verification_mode retain the original whole-claim assessment and decision rules.

The v2 policy at `examples/studio/v2/policy.json` is versioned `studio-robots-v2`. `examples/studio/policy.json` remains byte-for-byte `studio-robots-v1`. The constructor ABI is still one JSON string, `policy_json`; the pinned SDK dependency and persistent storage field types are unchanged.

V2 adds `verification_mode: "all_required_subclaims"` and a unique source_id on every source entry. Every configured source must be authoritative and have a nonempty fixed reference URL. All are required. Existing support/refutation thresholds remain integers >= 2 and cannot exceed the configured authoritative publisher-group count.

## Submission API

```python
submit_scoped(subclaims_json: str, observed_at: str, metadata_json: str) -> str
```

`subclaims_json` is a JSON string containing exactly one entry per policy source:

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

This is an **unexecuted candidate assertion**, not a statement that current sources were inspected for v2. Confirm actual content in a separately authorized test.

IDs must bind to their exact canonical policy reference URLs. Missing, duplicate, unknown, swapped-ID/URL, same-host replacement-path and extra mappings are rejected before storage writes. Source authority/group flags come from policy, never submission or model output. Reordering entries does not change identity.

Swapping the natural-language claim texts while keeping valid ID/URL pairs creates different assertions; it cannot be deterministically recognized as an accidental swap. The assessor evaluates each resulting assertion only against its designated document. Independent grounding must reject unsupported claims; the API never automatically approves text merely because a mapping is valid.

There is no free-text overall claim parameter. The stored combined statement is exactly `ALL_REQUIRED_SUBCLAIMS ` followed by the sorted structured mappings serialized with sorted keys, compact separators and Unicode preserved. This represents an AND conjunction with no unverified headline. Entries sort by canonical source_url; source IDs and normalized text are stored intact.

Limits remain conservative: at most six sources/subclaims; subclaims JSON <= 12,000 characters; combined normalized subclaim text <= 2,000 characters; the complete generated statement, including IDs/URLs/structure, must also fit the original 2,000-character claim limit. Existing URL, timestamp, metadata, body-size, quotation, pagination, authorization and eight-accepted-attempt limits remain enforced.

On scoped policies, use submit_scoped; submit rejects rather than bypassing scope checks. On legacy policies, use submit; submit_scoped rejects. Existing v1 method signatures, fingerprints, record shape and history shape remain unchanged.

## Assessment and independent validation

Verification derives the exact required targets from immutable policy and canonical stored mappings, checking their completeness again. Each extraction prompt contains only the corresponding subclaim, document URL, observation time and fetched document. It never asks one document to prove the entire conjunction. Findings add source_id and subclaim to the existing source identity, retrieval outcome, hash, label and quotation fields.

The same `gl.vm.run_nondet_unsafe` leader/validator mechanism remains in place. Validators independently re-fetch and re-extract every required document. They require identical ordered mappings, source identities, classifications, retrieval outcomes and document hashes. Every decision-bearing leader quotation must be verbatim in the validator's document and independently grounded against the **same** source-specific subclaim. Malformed output, failed grounding, omitted/duplicated/swapped findings, changed mappings or validator exceptions fail closed. Local direct tests exercise these functions; they are not committee execution.

## Aggregation, in order

1. Any internal inconsistency or any mixture of supporting and contradicting required subclaims: **Disputed**. This is a mixed-result bundle, not necessarily conflicting accounts of one fact.
2. Any unavailable or insufficient required subclaim: **Pending**. Meeting the group threshold elsewhere cannot skip it. Rule 1 still has precedence, matching the existing conservative ordering.
3. Every required subclaim supports, and distinct authoritative supporting groups meet min_support: **Verified**.
4. Every required subclaim contradicts, and distinct authoritative refuting groups meet min_refute: **Rejected**.
5. Otherwise: **Pending**.

A failed consensus transaction does not become a committed Disputed record. Existing attempt, recheck, append-only history and finality distinctions remain unchanged.

## Identity and history

The scoped fingerprint is SHA-256 of canonical JSON containing mode, full canonical policy hash, source–subclaim mappings and observed_at. Claims are casefolded in the fingerprint, as in v1 duplicate protection. Original normalized claim text remains in records/history. Source mappings are included, so changing which assertion is bound to which source changes identity. Metadata, caller and input entry order cannot bypass duplicate protection.

Every scoped history entry records mode and the canonical complete mappings, alongside the existing policy hash/version, previous/current states, time, requester and findings. V1 fingerprint and history formats are not retroactively changed. Read consumers must accept the extra scoped fields and use mode to interpret assurance correctly.

## Exact Studio preparation

No deployment, transaction, wallet access or live network verification was performed for this extension.

1. Import the updated `contracts/evidence_trust.py` into your intended Studio environment. Confirm the pinned runner is supported and the interface exposes submit_scoped plus the six existing methods.
2. Prepare a **new instance** using `examples/studio/v2/policy.json` as the single policy_json string. `examples/studio/v2/constructor-args.json` supplies the escaped one-element positional argument array; preserve any Studio-specific editor wrapper. Do not use the v1 policy for this mode.
3. In `examples/studio/v2/cases.json`, choose a case and enter its three `submit_scoped_args`: subclaims_json as a string containing JSON, observed_at as UTC text and metadata_json as a string containing JSON. No separate claim or source_urls argument is needed.
4. After an independently authorized local submission, confirm the expected record ID, generated conjunction, mappings, Pending status and attempts=0 using get_record. IDs and constructor/input shapes are checked locally by the automated suite.
5. From the original submitter account, use the case's verify_args. Inspect actual execution/consensus status and get_history_args. Successful first verification appends revision 1; scoped mode and complete mappings must appear.
6. Treat `unexecuted_acceptance_target` as a conditional target, not a recorded live result. Wildcard directives target Verified; CSS-forbidden assertions target Rejected; mixed admin permissions target Disputed; unrelated invoice-payment assertions target Pending. Actual source content, quotation quality and model/validator agreement must establish the result. No current directive or outcome is assumed by the contract.
7. Record Studio/GenVM version, actual validators/models, receipts, findings and history before claiming live verification. No upgrade/migration of an existing v1 deployment is provided.

The old Studio import instructions still describe navigation and protocol status inspection. Their v1 examples are retained for compatibility; scoped claims must use the new v2 pack.

## Remaining limitations

Exact hashes may prevent agreement on changing pages. Authority and publisher grouping remain configured trust decisions, including the shared government trust root of the sample agencies. Prompt injection, model mistakes, historical provenance and node DNS/redirect controls retain their earlier limitations. Scoped mapping validation cannot prove a natural-language assertion belongs to its intended subject; source-grounded assessment and validators must do that. Fixed required references constrain the subject of a policy and cannot discover every external contradiction.
