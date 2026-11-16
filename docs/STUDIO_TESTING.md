# GenLayer Studio testing guide

Prepared on 2026-11-16. This guide is a manual handoff. No Studio deployment, transaction submission, model call or live validator consensus was performed during preparation. Two ordinary public HTTP requests were made to inspect test-source accessibility; they are not contract verification.

## Scoped extension notice

The current source adds a third write method, submit_scoped, behind an explicit v2 policy. For the scoped fix use [SCOPED_V2.md](SCOPED_V2.md) and `examples/studio/v2/`; the v1 policy below remains unchanged. A literal combined claim about both files cannot reasonably be expected to verify from isolated whole-claim assessments in v1. Earlier per-source-relative acceptance targets are conditional examples, not a workaround for that scope mismatch.

## 1. Choose the environment

For testing without on-chain fund spending, prefer an existing **local GenLayer Studio** instance with local test accounts and locally provided model inference. Hosted Studio is available at [studio.genlayer.com](https://studio.genlayer.com), but its active network and provider configuration must be checked rather than assumed. Nonpayable methods still have protocol/inference costs on environments that charge for them.

If you later choose to initialize local Studio, the [official development setup](https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup) documents the CLI, Docker requirements and local UI at `http://localhost:8080/`. Environment initialization/startup and deployment are intentionally not automated by this project. Do not import a funded wallet or private credentials for these tests.

In Studio's Validators panel, inspect the available validators and model/provider configuration. Use a multi-validator setup with leader-only execution disabled when collecting consensus evidence; multiple source URLs are not multiple validators. Five validators is the documented local default, not a guarantee about an arbitrary hosted session. See the [official validator guide](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/validators).

## 2. Import the single contract file

1. Open the Contracts sidebar.
2. Choose New Contract / `+`, then **Add From File**.
3. Select `contracts/evidence_trust.py`; do not upload the repository or install requirements.lock in Studio.
4. Open the uploaded file in the editor. Check its first-line dependency comment is preserved exactly:

   ```python
   # { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
   ```

5. Select Run and Debug / the play icon to inspect the detected contract interface. If your Studio version's play action proceeds directly to a transaction, stop at the constructor panel until you deliberately choose the later manual execution step.
6. Confirm the class is `EvidenceTrust`, the constructor has one string field named `policy_json`, there are three write methods and four view methods (submit_scoped requires a v2 policy). Compare `docs/contract-schema.json`, generated with the official SDK schema extractor.

These navigation labels come from the [official loading guide](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/loading-contract); deployed Studio versions may arrange panels differently. The UI itself was not operated during this review.

**Runtime compatibility gate:** local lint/schema validation passed against the pinned runner. Actual hosted/local Studio support for this hash remains untested. If Studio reports an unknown runner, missing dependency, syntax/runtime mismatch or schema error, record that error and the Studio/GenVM version. Do not silently replace the hash with `latest`, remove it, or switch to an older SDK API.

## 3. Supply the constructor argument correctly

The actual ABI is:

```python
def __init__(self, policy_json: str)
```

Use `examples/studio/policy.json` for the public-source test contract. It approves exactly `www.nasa.gov` and `www.noaa.gov`, assigns them distinct publisher groups, sets both thresholds to two, and always retrieves both robots.txt files. These are different agency publishers under a shared US-government trust root, not fully independent political or infrastructure authorities.

In the typed `policy_json` string input, paste the **contents** of policy.json, not its filename. The string begins with `{` and ends with `}`. Do not pass a Python dictionary or add extra constructor parameters.

If using a JSON editor that represents a string value, encode the policy as one JSON string. `examples/studio/constructor-args.json` contains a one-element positional argument array with the escaping already prepared. It documents the ABI representation; Studio's JSON panel may instead wrap values in its own named-parameter structure. Preserve the detected panel structure and insert the string value, rather than assuming the entire array is accepted by every Studio version. The [official constructor guide](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/deploying-contract) describes detected inputs and the JSON toggle.

Do **not** use `examples/policy.json` here: that file intentionally uses synthetic domains for offline mocks.

The constructor only validates/stores the immutable policy. It performs no source fetch or model evaluation. A successfully created fresh instance should expose `get_policy()` equal to the supplied policy after canonicalization, and `list_records(0, 50)` equal to `[]`.

## 4. Manual execution, only when you choose to test

The following steps necessarily create a local instance and execute writes. They were **not executed** in this review. Use the intended local simulation, select its local test account, and leave transferred value at zero. Do not approve a transaction or model-provider action that would spend real funds under a no-spend constraint.

1. In the constructor panel, select the deployment action only when ready to create the local test instance. Record the resulting local address and execution result.
2. Call `get_policy()` and `list_records(offset=0, limit=50)` under view/read methods. Compare the policy and fresh empty registry.
3. Open `examples/studio/cases.json`. For each case, expand **Write Methods → submit**.
4. Copy the four `submit_args` in order. Enter the claim as text, source_urls as a two-item string array, observed_at as the supplied UTC timestamp, and metadata_json as a **string containing JSON**. Use the case metadata string value, not a nested object.
5. Execute submit. Inspect both transaction execution success and protocol status. The application record should now be Pending with attempts=0. Record ID is deterministic and supplied in `expected_record_id`.
6. If Studio does not expose a write's returned ID, use `list_records(0, 50)` and find the supplied expected ID. Call `get_record(record_id)` to confirm the claim.
7. Keeping the **same active account**, call `verify(record_id)`. The constructor/deployer account need not be the submitter; the submitter account is the one that must verify.
8. Inspect the receipt/transaction result and validator logs. A timeout is not proof the transaction failed. Read current state before retrying to avoid consuming another accepted attempt.
9. Call `get_record(record_id)` and `get_history(record_id, 0, 8)`. The return values are JSON **strings** (history is a list of strings), so escaped JSON in the UI is expected.
10. On an accepted first verification, attempts becomes 1, one history entry is added, revision is 1, previous_status is Pending, and the history includes two source findings, hashes, retrieval codes, policy identity and verification time.

See the [official transaction guide](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/execute-transaction). Application Verified is separate from protocol acceptance/finality. If consensus cannot accept a result or execution fails, the earlier record and history remain unchanged; the contract does not automatically write Disputed for validator disagreement.

## 5. Public-source acceptance targets

Read-only transport preflight obtained HTTP 200 from both sources: NASA 69 bytes and NOAA 2,631 bytes, both valid UTF-8 and below 48,000 bytes. No redirects were followed by this host preflight. Hashes and scope are recorded in `examples/studio/source-preflight.json`. Node requests may behave differently; do not treat host HTTP success as GenVM connectivity proof.

The public evidence is [NASA robots.txt](https://www.nasa.gov/robots.txt) and [NOAA robots.txt](https://www.noaa.gov/robots.txt). NASA includes `User-agent: *` followed by `Allow: /`. NOAA includes the wildcard group, an Allow rule for `/core/*.css$`, and a Disallow rule for `/admin/`.

| Case | Claim topic | Expected per-source labels, NASA then NOAA | Target result |
| --- | --- | --- | --- |
| wildcard_directive | The source document includes a wildcard User-agent directive | supports, supports | Verified |
| css_forbidden | The wildcard policy forbids `/core/example.css` | contradicts, contradicts | Rejected |
| admin_permitted | The wildcard policy permits `/admin/` | supports, contradicts | Disputed |
| invoice_unsubstantiated | robots.txt proves payment of an unrelated invoice | insufficient, insufficient | Pending |

Exact claims, timestamps, JSON metadata strings, positional method arguments and deterministic IDs are in cases.json. These comparisons concern the policy **in each source**, so a disputed result identifies different website policies, not a false assertion that either publisher is lying. Robots policy is a compact, real-world compliance-document exercise; it is not evidence about astronomy, invoice settlement or universal truth.

All four verification outcomes are **unexecuted acceptance targets**, conditional on current source content, model extraction, valid quotations and validator agreement. CSS precedence and the admin case require semantic interpretation. A conservative model can abstain, yielding Pending; malformed model JSON can fail a transaction; changing bytes can prevent consensus. Investigate such results rather than changing expected results or hardcoding a verdict. Source changes may also legitimately change a status.

## 6. Deterministic negative and history tests

| Action | Expected result |
| --- | --- |
| Repeat the exact wildcard_directive submit, including observation time | Revert: Duplicate claim and observation timestamp; no new record |
| Use another local account to verify that submitted ID | Revert: Only submitter can spend verification attempts |
| Supply `http://www.nasa.gov/robots.txt` | Revert: Use an unambiguous public HTTPS URL |
| Supply `https://example.com/robots.txt` | Revert: Host is not approved by source policy |
| Use metadata_json `{"category":123}` | Revert: Metadata values must be strings up to 512 characters |
| Use observed_at `2099-01-01T00:00:00Z` while chain time is earlier | Revert: Observation timestamp is in the future |
| Call verify on `missing` | Revert: Unknown evidence record |
| Recheck a valid ID from its original account | If accepted, append revision 2, attempts=2; preserve revision 1 and original submission fields |
| Attempt a ninth accepted verification on one record | Revert: Verification attempt limit reached |

Do not run eight unnecessary live-model rechecks merely to demonstrate the limit; that limit already has an offline test. Every successful check consumes an attempt even if the result remains Pending. Invalid constructor checks can use min_support=1 or a mismatched reference host; each should fail before creating usable contract state.

## 7. Capture evidence for contribution review

Keep the source hash, policy, Studio/GenVM version, ABI, local address, active account role, validator/model configuration, transaction IDs, execution results, validator logs and before/after history. Report actual observed statuses and failures. Scrub credentials from screenshots/logs. No such execution evidence is claimed by the current project.

Before submission, use the checklist in FINAL_REVIEW.md and confirm current Builder submission fields directly in the program's official interface. This guide does not certify eligibility or guarantee acceptance.
