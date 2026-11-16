# Threat model

## Assets and trust boundaries

Protect record integrity, audit history, bounded verification attempts, source-policy integrity and the distinction between corroboration and factual certainty. All records and excerpts are public. Do not submit secrets, personal documents or confidential URLs. Consumers must escape claims, metadata and excerpts when rendering them; returned strings are untrusted content, not safe HTML.

Potential adversaries include submitters, hostile source pages, compromised publishers, misleading models, a malicious leader, colluding evaluators and hostile network infrastructure. Policy authors are explicitly trusted to select relevant authorities and accurately group common ownership. Node operators and the GenLayer protocol secure network access and consensus; the contract cannot replace those protections.

## Controls and residual risks

| Threat | Implemented control | Remaining risk |
| --- | --- | --- |
| Invented model evidence | Strict schema, verbatim excerpts, independent retrieval/extraction and independent grounding of leader excerpts | Independent models may share the same semantic mistake or training bias |
| Leader fabrication | Compare every decision-bearing source field against independent results; reject exceptions and malformed payloads | Committee honesty, provider diversity and protocol execution are external assumptions |
| Prompt injection | Separate instructions from JSON evidence; exclude metadata; restrict outputs; quote checks and independent judging | No prompt boundary is a formal defense; malicious sources can still mislead models |
| Publisher spoofing | Exact reviewed host policy, HTTPS-only narrow URL grammar, no credentials, IP literals, ports or ambiguous paths | DNS poisoning/rebinding, compromised TLS/publishers and redirects remain infrastructure risks |
| SSRF | No arbitrary hosts; reject local-name suffixes, encoded host tricks and ambiguous URL syntax | Public DNS can resolve to private addresses. The pinned SDK has no documented redirect-disable, final-URL or DNS-inspection parameter. Nodes must enforce private-network egress and redirect restrictions |
| Duplicate spam | Global canonical claim/time fingerprint; repeated source URLs rejected | Paraphrases, changed timestamps and URI aliases are not semantic duplicates. First-submitter front-running can reserve a claim/time; consumers can still read the shared ID |
| Fake corroboration | Count configured publisher groups, not pages or model votes | Wrong group assignments, syndication and shared upstream sources can still create apparent independence |
| Cherry-picked sources | Always include configured independent reference endpoints; validator checks quotes in full context | Coverage is bounded, fixed references may be irrelevant, and contradictory material outside the target set is not discovered |
| Date manipulation | Strict UTC timestamp parsing, future-time rejection, separate transaction-context audit times | Observation time is user-asserted. Current source content is not a historical snapshot, and quoted dates can be ambiguous |
| Forced negative verdicts | Retrieval failures become unavailable/Pending; explicit authoritative refutation quorum required for Rejected | Hostile or failing configured sources can deliberately keep records Pending |
| Attempt exhaustion | Only the original submitter can consume up to eight accepted verification attempts | Lost submitter access prevents rechecks; submitter may decline to recheck outdated results; no ownership recovery |
| Resource exhaustion | Bounded source count, policy, inputs, excerpts, output schemas, attempts and pagination | SDK retrieval happens before the contract inspects body length. Node timeout/download/compute limits are required; global storage remains unbounded and transactions have protocol costs |
| History rewriting | No edit/delete entry points; immutable submission fields and append-only revisions | Chain reorganization/finality and platform upgrade behavior are outside the application |
| Stale results | Explicit verification times, hashes and preserved recheck history | No scheduler, autonomous refresh or freshness guarantee; applications must enforce their own freshness policy |

## Failure semantics

Transport failure is an auditable observation; it is never evidence that a claim is false. Invalid model output fails the transaction. Validators fail closed if their own data or the leader's proposal cannot be validated. `run_nondet_unsafe` does not provide an extra validator error sandbox; the validator catches ordinary exceptions and returns false. Executor-level failures and resource limits remain protocol concerns.

The application persists only **accepted** verification attempts. It cannot store failed protocol attempts in a transaction that does not commit. Inspect transaction receipts and protocol traces separately for those failures. Direct tests do not validate full-chain rollback or finality behavior.

## Operational requirements before future deployment

Review every hostname, fixed endpoint and publisher group; choose stable, relevant public text endpoints. Confirm the target chain supports the pinned runner. Audit redirect/DNS/egress enforcement in the node environment, response budgets and fees. Validate actual model behavior with adversarial and historical claims, then conduct full GenVM and multi-validator testing under separately authorized local deployment conditions. Observe protocol finality before relying on a result.

The current work includes no deployment, credential access, funds, autonomous verification service, bonds, token economics, slashing logic or custom appeals mechanism. GenLayer protocol appeals are distinct from the contract's bounded rechecks.

## Scoped v2 boundaries

The scoped mode rejects incomplete, duplicate, swapped-ID/URL or substituted-document mappings and checks complete required coverage again at verification. It cannot deterministically detect that a caller accidentally exchanged two natural-language assertion texts; those become different assertions and must be evaluated against the bound documents. Independent validators check each source/subclaim binding and ground the leader quotation for that exact assertion. Valid structure alone never grants Verified.

The overall statement is generated from the mappings, preventing an unchecked headline from borrowing their result. Fingerprints and history bind mode and mappings. This mode establishes coverage of each required source-specific assertion, not two-source corroboration per assertion. Reusing the old whole-claim assurance label for scoped results would mislead consumers: inspect mode. Input/body/quote budgets, at most six required sources and eight accepted attempts remain bounded. Existing v1 policies/deployments are not silently migrated.
