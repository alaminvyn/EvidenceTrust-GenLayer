# SDK provenance and supported conventions

Research date: 2026-11-16. These are official GenLayer references; implementation was checked against the actual SDK in the published release archive.

| Area | Official reference | APIs/convention used |
| --- | --- | --- |
| Contract definition | [Your First Contract](https://docs.genlayer.com/developers/intelligent-contracts/first-contract) | First-line dependency comment, `from genlayer import *`, `gl.Contract` |
| Storage | [Contract Storage](https://docs.genlayer.com/developers/intelligent-contracts/storage) | Typed `TreeMap`, `DynArray`, runtime-owned collection allocation |
| Consensus | [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) | `gl.vm.run_nondet_unsafe`, `gl.vm.Return`, `leader_result.calldata`, independent validator execution |
| Retrieval | [Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access) | `gl.nondet.web.get` within nondeterministic execution |
| Time and sender | [Transaction Context](https://docs.genlayer.com/developers/intelligent-contracts/features/transaction-context) | `gl.message.sender_address`, deterministic `datetime.datetime.now` |
| Testing | [Development Setup](https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup), [Direct Mode](https://docs.genlayer.com/api-references/genlayer-test/direct) | `direct_deploy`, `direct_vm`, `mock_web`, `mock_llm`, `run_validator`, `warp`, `expect_revert` |
| Runtime | [Official GenVM releases](https://github.com/genlayerlabs/genvm/releases/tag/v0.3.0-rc7) | Published archive and exact dependency manifests |

## Exact version choice

- GenVM release: `v0.3.0-rc7`, the latest release returned by GitHub during this implementation.
- Contract runner: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`, also shown in the current first-contract tutorial.
- Transitive SDK: `py-lib-genlayer-std:11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v`, resolved from that runner's actual `runner.json`.
- Official release asset: `genvm-runners-all.tar.xz`.
- Asset SHA-256: `e218a1854214681560351051f76fe2b878545cf3409455ef372d57014a88ca67`, matching the release API digest.
- Tested tools: `genlayer-test==0.29.2`, `genvm-linter==0.11.0`, `pytest==9.2.0`; Python 3.12.16 on macOS ARM64.

The SDK executor-reference site advertised newer rc9/rc10 documentation and a runner absent from the downloadable rc7 asset. That unavailable runner was not substituted into this project. The linter emits an advisory naming another bundled runner as newer; this project deliberately retains the pinned tutorial runner whose concrete APIs were inspected and tested. A future update requires explicit compatibility checks, not simply replacing a hash with `latest`.

In the pinned SDK, `web.Response` has `status`, `headers` and `body`, and `web.get` accepts only URL and optional headers. The higher-level web guide includes `status_code` examples that do not match this pinned implementation; EvidenceTrust uses the actual supported `response.status`. There is no invented timeout, search, final-URL, redirect-control, validator-selection or vote-count API.

## Local tooling compatibility

`genlayer-test` 0.29.2 expects a bundle named `genvm-universal.tar.xz`; the release renamed it `genvm-runners-all.tar.xz`. `scripts/prepare_sdk.py` verifies the official asset checksum and caches its unchanged bytes under the old filename inside the project. Tests and the lint wrapper select that project-local cache. No installed package or SDK source is edited.

The SDK registers one contract class per process, as GenVM normally imports one contract. The direct-test loader re-imports the contract between tests without clearing that registration. `tests/conftest.py` resets only this SDK registry between tests. Storage, decorators, calldata, web/model dispatch and captured validators remain the official implementations. This test-only shim is documented and does not execute in a contract.

The official mock layer auto-parses JSON strings even when `exec_prompt` requests text. Fixtures JSON-encode the mock text response once more to preserve the production text-return contract and exercise duplicate-key detection. No change to contract parsing is made to accommodate a mock bug.

The direct test suite disables the unrelated RPC pytest plugin with `-p no:gltest`; the official direct-mode plugin remains enabled. Tests do not load `.env`, contact a chain, configure wallets or read private credentials.

## Scoped extension compatibility

The v2 extension uses the same pinned SDK, `run_nondet_unsafe`, extraction, web retrieval and grounding APIs. It introduces no new SDK function or runtime dependency. Constructor ABI and all six v1 method ABIs are unchanged; the official schema extractor adds only `submit_scoped(string, string, string) -> string` as a nonpayable write. Scoped policy parsing is explicit; policies without verification_mode retain their original interpretation. The current generated ABI is `docs/contract-schema.json`.
