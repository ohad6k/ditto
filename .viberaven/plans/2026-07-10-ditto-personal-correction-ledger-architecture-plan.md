Architecture plan:

# Ditto Personal Correction Ledger Architecture Plan

## Objective

Build the smallest trustworthy weekly Ditto loop that can turn repeated, explicit user corrections into user-approved agent behavior without changing the current one-shot profile flow, losing evidence, leaking full assistant histories by default, or claiming retention before it is measured.

The 14-day outcome is an **engineering and efficacy gate**, not proof of retention or a public standard. A provisional pass means one correction can move safely through evidence, approval, isolated installation, and a controlled efficacy test. The genuine return observation happens seven days after the first completed real review, expected around day 21; Ditto only suggests the date and sends no reminder. Only that loop-completion check can unlock two opt-in pilots. Neither gate supports a retention claim.

## Product Path

The user-facing path is one sentence: **“Review my Ditto corrections.”** The installed Ditto skill orchestrates the internal commands, but the person should experience:

1. one invocation;
2. a clear privacy boundary before any assistant text is shown to a model;
3. a compact local review page with evidence;
4. at most one approve, edit, reject, refine, or retire decision;
5. explicit proof of what was written and where it was installed;
6. a return seven days later that reports new evidence, recurrence, and pending corrections without calling silence success.

The recurring value has two lanes:

- **Recurrence lane:** Did an already-approved correction appear explicitly again? If yes, refine or retire the rule.
- **Discovery lane:** Did a pending correction gain independent evidence, or did a new repeated correction become eligible for approval?

Without the discovery lane, the loop only reports failure or uncertainty and is not a credible habit mechanism.

## User Answers Translated

- Ditto should become a “living mirror,” not only a prettier one-shot profile.
- The smart behavior is concrete translation: learn what the user means by phrases such as “done,” how they debug, design, verify, and reject work, then make agents act on those rules.
- The four longer-term ideas remain one product: mirror, correction/evaluation loop, workflow-to-skill compiler, and adapters/plugins that carry the result into other tools.
- The next build must prove the correction loop first. Workflow mining, broad adapters, elicitation, profile diffing, background hooks, and automatic self-editing stay outside the 14-day implementation.
- The current Reddit momentum is distribution evidence, not evidence that users will return. The product gate must measure behavior separately from launch attention.
- Four focused hours per day and an AI crew make a 56-hour implementation envelope. The architecture therefore preserves the one-file distribution and avoids a packaging migration.

## Current Repo Evidence

Evidence type: direct repository inspection and passing local tests.

- `ditto.py` is a 606-line, one-file standard-library CLI. Its default Claude/Codex/Copilot pipeline writes a redacted user-only corpus, chunks, and stats.
- The flat CLI's current behavior is covered by nine passing tests. Its permissive `user_messages` parser, direct installer writes, remote card fallback, and incomplete security documentation are not safe foundations for correction receipts.
- Content-free Claude row sampling found native `sessionId`/`uuid` plus agent, sidechain, and meta rows; paths/prefixes are unsafe identity/filter boundaries.
- The superseded plan overwrote evidence/history and used a global timestamp cursor, risking deletion and skipped events.
- The example rule “done means it runs live” already appears in an existing example profile. It cannot be the efficacy benchmark target unless the experiment is explicitly reframed as a salience test.

## Architecture Boundaries

### Preserved exactly

- `python ditto.py`, legacy flags, default source discovery, default user-only extraction, output names, and current install destinations.
- One-file, standard-library distribution.
- No network calls from `ditto.py`.
- Human approval before any correction becomes an installed instruction.

### New, explicitly experimental

- A `corrections` command family dispatched before the legacy parser:
  - `corrections extract`
  - `corrections expand`
  - `corrections consent`
  - `corrections review-candidates`
  - `corrections review-week`
  - `corrections review-queue`
  - `corrections status`
  - `corrections install`
  - `corrections uninstall`
  - `corrections abort`
  - `corrections recover`
  - `corrections recover-lock`
  - `corrections source-reset`
  - `corrections purge`
  - `corrections benchmark-validate`
- Claude Code main-session logs only.
- Private run batches, private operational state, an experimental ledger, and a derived `ditto-corrections` skill.
- A local static review page that contains escaped, redacted evidence and no remote assets.

### Deferred

- Codex, Copilot, Cursor, Cline, Continue, or Windsurf correction traces.
- Background file watchers, persistent hooks, automatic rule edits, and automatic claims that a rule “worked.”
- Generalized named installers or host adapters beyond a fixed Claude Code experiment.
- Public stable ledger v1, remote sync, team accounts, billing, and hosted services.
- Workflow mining, profile `--diff`, elicitation, and visual profile redesign.

## Options Considered

### Option A: Add more flat flags to `ditto.py`

Rejected because flat flags permit contradictory/ignored states and leaked `--no-redact` into correction mode.

### Option B: Split Ditto into a package immediately

Rejected because packaging breaks the one-file path before the thesis is proven. Use logical seams now; extract modules after the gate.

### Option C: One-file CLI with a separate corrections parser and private run store

Chosen. Early dispatch preserves legacy parsing; immutable runs and explicit state replace shared mutable evidence.

### Option D: Export all user and assistant prose in one trace

Rejected because it overexposes assistant code/project detail and conflates local extraction with provider disclosure.

### Option E: Two-stage, bounded evidence expansion

Chosen. Mine anchors from a redacted user-only index, locally expand bounded causal chains, then require separate provider consent.

## Recommended Architecture

### 1. Logical components inside `ditto.py`

Keep one physical file but enforce these pure boundaries:

- `legacy_main(argv)`: current behavior, changed only for shared atomic installer safety and card privacy.
- `corrections_main(argv)`: dedicated subcommands and dependency validation.
- `ClaudeCorrectionReader`: strict allowlisted parser for main-session Claude rows.
- `CorrectionStore`: paths, lock, atomic UTF-8/JSON/JSONL writes, backups, and recovery.
- `RunBuilder`: user-only index, private source map, bounded evidence expansion, and manifests.
- `ContractValidator`: exact runtime validation for anchors, candidates, recurrence reviews, state, and ledger.
- `ReceiptValidator`: native causal chain and independent-session checks.
- `LedgerService`: idempotent merge, rule revisions, pending evidence, rejection persistence, and recurrence history.
- `SkillCompiler`: deterministic local Agent Skill output from active approved ledger rules.
- `CorrectionInstaller`: fixed Claude personal-skill destination with frontmatter validation, byte comparison, backup, and atomic replace.
- `ReviewRenderer`: private, offline, escaped HTML; raw evidence never prints to stdout.

### 2. Store layout

Default root: `ditto-out/corrections/`.

```text
corrections/
  .ditto-correction-store.json      ownership sentinel with store ID
  store-meta.json                   immutable store ID and ID algorithm
  state.json                       private operational state
  install-receipt.json             installed path, bytes hash, and ledger revision
  ledger.experimental.json         canonical user decisions and rule history
  SKILL.md                          deterministic derived artifact
  review.html                       replaceable private local review surface
  .lock                             held only during mutation
  backups/
    <utc>-ledger-r<revision>.json
  operations/
    <operation_id>/
      operation.pending.json        private deterministic journal
      ledger-applied.json           target ledger hash/generation marker
      decision.json                 deterministic human decision result
  runs/
    <run_id>/
      index.jsonl                   redacted user-only events, provider-readable
      index-manifest.json           immutable digest and parser facts
      consent-index.json            run/digest/provider-bound invocation consent
      source-map.json               private local path/line map, never sent to a model
      anchors-pass-1.json           first independent anchor output
      anchors-pass-2.json           second independent anchor output
      evidence.jsonl                bounded redacted conversation windows
      evidence-manifest.json        immutable digest and chain facts
      consent-evidence.json         separate assistant-evidence disclosure consent
      candidates.json               agent output bound to evidence digest
      weekly-review.json            agent output bound to run and ledger revision
      cursor-after.json             private proposed checkpoint
```

Every run is immutable after each artifact is sealed. A new extraction creates a new directory. Old receipts always reference `(run_id, event_id)` and remain resolvable.

### 3. Identity and causal receipts

- Exclude `agent-*.jsonl`, `isSidechain=true`, `isMeta=true`, tool result, tool use, thinking, and unknown content-block types.
- Require the row type and embedded message role to agree.
- Require native `sessionId` for session identity and `uuid + text_block_index` for event identity during the gate.
- Domain-separate and hash native identifiers before writing provider-facing artifacts.
- If native identity is absent, fail that source with a structural diagnostic. Fallback identity is deferred; a path or content guess cannot qualify as gate evidence.
- Require `parentUuid` relationships to prove the direct user request → assistant response → user correction chain during the gate. Missing native linkage fails the selected anchor; three merely increasing events never form a receipt.
- Reject duplicate event IDs, duplicate receipts, repeated correction events, modified trace digests, unrelated chains, copied sessions, and candidate bundles from another run.
- Candidate IDs are generated by Ditto from canonical evidence; model-proposed slugs are display labels only.

### 4. Cursor and run state

Timestamps are display metadata only. The authoritative novelty cursor is the set of committed, hashed native user-message event IDs. A copied export with the same native UUID is therefore not new, while a newly discovered old message is new regardless of its timestamp. For the 14-day scale, the correctness and auditability of an explicit ID set outweigh a more compact but lossy timestamp or max-sequence cursor.

`state.json` also stores per-source checkpoints containing the last observed line number and raw-line digest. They detect truncation/rewrite and accelerate scans but never decide novelty. A source missing after all referencing runs committed becomes retired and does not block other sources; a pending run still requires its source. Rewrite/truncation requires explicit `source-reset`, which preserves committed IDs. Before evidence expansion, every selected source line is reverified. The provisional cursor becomes authoritative only after complete commit.

`pending_run` stores run ID, phase, sealed digests, base revision, and start time. Separate `pending_operation` stores operation/action/run identity, journal digest, and target generation. Legal phases and transitions are validated.

`abort` clears pre-ledger pending work without advancing the cursor. It refuses an operation already in `applied_operations` and routes to recovery. `review-queue` may decide one stable `action_id` while idle, without new events or cursor movement. This separates one-time `processed_runs` from multiple `applied_operations` originating in a run.

### 5. Atomicity, idempotency, and recovery

All correction-store writes use a same-directory temporary file, UTF-8 with `ensure_ascii=False`, flush, `fsync`, close, and `os.replace`. On POSIX, create/replace/rename also receives best-effort parent-directory `fsync`. On Windows, `os.replace` receives a short bounded retry for transient `PermissionError`; the old file is never deleted first.

Mutations hold an exclusive `.lock` created with `O_CREAT | O_EXCL`, containing PID, hostname, and UTC time. A stale lock is never removed automatically. `corrections recover-lock --confirm` shows metadata before removal.

Commit order is intentional:

1. validate every input and gather all human decisions in memory;
2. acquire the lock and re-read the complete generation;
3. atomically write an operation-scoped journal with decisions, telemetry, expected hashes, base revision, bundle digest, and operation/action/run identity;
4. write a revision-paired ledger/state backup plus a manifest containing both hashes;
5. atomically write the merged ledger with an `applied_operations` record and add `processed_runs` only when the operation owns cursor advancement; then seal the ledger-applied marker;
6. atomically regenerate/remove local `SKILL.md`; if an install receipt exists, update/remove the installed copy and receipt as an explicit consequence of the approved decision;
7. atomically derive `decision.json` from the journal;
8. atomically commit cursor/candidate state, set the same `commit_generation`, and clear `pending_run` last.

Recovery scans journals, applied-operation/processed-run records, generation metadata, artifacts, install receipts, and missing decisions. Pre-commit backups are reconstruction inputs only: after ledger application is observed, recovery replays the journal and never exposes the old generation as final. A sealed unreferenced run is quarantined. Replaying identical bytes is a no-op; conflicts fail. Installed-rule changes synchronize before completion.

### 6. Ledger versus private state

Immutable `store-meta.json` owns store ID and ID algorithm. `state.json` owns committed event IDs, source checkpoints, candidate/action queues, generation, and recovery. There is one status source per lifecycle. Neither file is a dependency contract.

`ledger.experimental.json` owns approved rule history and opaque receipt references. It contains no raw quotes or local paths. Each rule has:

- Ditto-generated immutable correction ID;
- active, retired, or superseded status;
- current single-line rule text and rule revision;
- first/last observed time as display metadata;
- independent receipt count and `(run_id, event_id)` references;
- explicit user decision history;
- recurrence reviews and refinements;
- created/updated timestamps, producer version, ID algorithm, and ledger revision.

Rejected and merely pending text stays in private state. The ledger schema is labeled experimental until two external pilots complete. Other tools may consume active rule text, scope, revision, and status, but must not depend on private state or raw evidence layout.

### 7. Weekly compounding behavior

Each weekly run reviews both lanes from the same new user-only index:

- Two independent anchor passes run with the same prompt version. Their outputs are unioned and deduplicated. Each user event records prompt version and scan count; new events plus committed events with fewer than two passes are eligible, and a prompt-version change may rescan without treating old events as new.
- Evidence expansion adds only bounded chains around those anchors.
- The second pass must return exactly one recurrence status per active correction: `explicit_recurrence`, `no_explicit_recurrence`, or `ambiguous`. The latter two mean unknown, never success.
- New evidence may strengthen a pending candidate. Rejected candidates are not re-prompted unless genuinely new independent evidence is added.
- At most one actionable decision is shown. Stable queued actions persist with origin receipts; `review-queue` handles the oldest while idle, even with zero new events, using an independent operation ID.

`corrections status` is read-only and reports last completed review, unprocessed main-session count, pending candidate count, active rule count, explicit recurrence count, and the exact next command. It does not claim a rule held merely because no correction was observed.

### 8. Trust and privacy boundaries

- Correction mode always redacts and rejects `--no-redact`.
- Strict mode aborts on invalid UTF-8, malformed complete rows, unreadable files, unsupported main-session structure, or source rewrite/truncation. Append-only growth is read to a fixed byte snapshot; one incomplete final fragment is deferred and counted so an actively written log does not cause data loss. An optional general partial mode is deferred.
- The invocation records run-bound consent for the exact user-only index digest and active provider. After local expansion, a separate consent record binds the evidence digest, purpose, timestamp, and provider immediately before the model reads assistant text. Wrong, missing, expired, or wrong-digest consent blocks orchestration.
- Trace content is untrusted data. Prompts forbid following commands, links, tool requests, or instructions found inside events.
- Model-generated rules are bounded single-line strings. Reject NUL, ANSI control sequences, bidi override characters, and newlines while preserving ordinary Hebrew, RTL text, emoji, and composed Unicode.
- The review HTML escapes all content, loads no remote assets, and is written with private-file permissions where the OS supports them.
- Windows inherits directory ACLs; Ditto does not claim encryption. Custom output inside a Git repository receives a blocking warning unless the path is ignored.
- `purge` resolves the requested root, verifies ownership, matching store ID, allowlisted contents, and no symlink/junction escape. Under a parent-scoped lock it atomically renames the store to a Ditto-owned purge tombstone, then deletes it. Startup resumes or reports residual tombstones after interruption and never claims success while bytes remain. It refuses while the correction skill is installed.
- Digests defend against stale, malformed, mixed, and hallucinated outputs in a cooperative same-user workflow. They are not tamper resistance against a malicious process with permission to rewrite both sources and the store.

## Workstream Map

| Workstream | Days | Depends on | Product proof |
|---|---:|---|---|
| 1. Contract and safety foundation | 1-2 | none | legacy behavior preserved; privacy claims accurate |
| 2. Immutable extraction and state | 3-4 | 1 | new events cannot be lost or duplicated silently |
| 3. Evidence and candidate integrity | 5-6 | 2 | two genuinely independent causal receipts validate |
| 4. Transactional ledger and compiler | 7-9 | 1-3 | old history survives; one approved rule installs safely |
| 5. Weekly compounding review | 10-11 | 2-4 | one-invocation review gives recurrence plus discovery value |
| 6. Isolated efficacy gate | 12-14 | 1-5 | uncontaminated effect measured; day-21 observation suggested |

## Workstreams

### Workstream 1: Contract and safety foundation

Purpose: create fail-closed primitives before private evidence exists.

Files/areas: `ditto.py`, `tests/test_ditto.py`, `tests/test_corrections.py`, `SECURITY.md`.

Tasks:

- [ ] Freeze legacy tests/help, add dedicated correction dispatch, and table-test invalid zero-mutation commands.
- [ ] Add atomic/private I/O, locking, retry, backup, recovery, UTF-8, and unsafe-control primitives.
- [ ] Remove the remote card fallback and correct every read/write/provider claim.

Acceptance: all legacy tests pass; card HTML has no network URL; simulated write and lock failures preserve prior bytes.

### Workstream 2: Immutable extraction and state

Purpose: produce complete, stable new-event batches without timestamps as cursors.

Files/areas: `ditto.py`, `tests/test_corrections.py`, synthetic `tests/fixtures/claude/*.jsonl`.

Tasks:

- [ ] Parse only native-ID main-session text; exclude agents, sidechains, meta/tool/thinking, and mismatched roles.
- [ ] Seal user-only index, private source map, manifest, and provisional cursor in a unique pending run.
- [ ] Verify sources, refuse concurrent runs, and implement no-advance abort plus idempotent recovery.

Acceptance: moved/copied files do not become independent sessions; equal/missing timestamps and late old logs are processed once; malformed or mutated input creates no committed run.

### Workstream 3: Evidence and candidate integrity

Purpose: minimize assistant exposure and prevent a model from inventing evidence.

Files/areas: `ditto.py`, `CORRECTION_ANCHOR_PROMPT.md`, `CORRECTION_PROMPT.md`, schemas, tests.

Tasks:

- [ ] Validate two run/digest-bound anchor passes and expand only selected native causal chains.
- [ ] Seal evidence and strictly validate typed, bounded, unique two-session candidate receipts.
- [ ] Generate IDs in Ditto and reject injected, distant, copied, stale, modified, or reordered evidence.

Acceptance: two valid independent chains pass; every forged, stale, duplicated, unrelated, injected, or malformed bundle fails before human prompting and without state mutation.

### Workstream 4: Transactional ledger and compiler

Purpose: preserve all prior decisions while safely compiling only active approved behavior.

Files/areas: `ditto.py`, ledger/state schemas, `tests/test_corrections.py`.

Tasks:

- [ ] Validate full state/ledger, render escaped local review, and gather one retryable/cancellable decision.
- [ ] Merge by CLI identity, preserve/version history, and commit through journal, paired backup, generation, and recovery.
- [ ] Deterministically compile and safely install/synchronize only the fixed Claude correction skill.

Acceptance: a second run cannot delete the first; replay is idempotent; concurrency conflicts instead of losing updates; local derived skill is repaired after recovery; any stale installed copy is detected and cannot be reported current.

### Workstream 5: Weekly compounding review

Purpose: create a reason to return beyond checking whether the first rule failed.

Files/areas: `ditto.py`, `CORRECTION_REVIEW_PROMPT.md`, `skills/ditto/SKILL.md`, tests.

Tasks:

- [ ] Run discovery/recurrence lanes, require complete new-only checks, and strengthen pending evidence.
- [ ] Queue one keep/refine/retire/approval decision and make review replay idempotent.
- [ ] Add stable read-only status, one-invocation orchestration, and no-text dogfood telemetry.

Acceptance: a complete review commits the cursor once; empty/incomplete/cancelled reviews never advance it; the human completes the path without opening or editing JSON.

### Workstream 6: Isolated efficacy and loop gate

Purpose: separate workflow completion, model efficacy, and retention evidence.

Files/areas: `docs/experiments/correction-benchmark.md`, `README.md`, `ROADMAP.md`, private benchmark artifact outside Git.

Tasks:

- [ ] Freeze a baseline-novel target, exact 8+4 tasks, two repetitions, randomization, and blind rubric.
- [ ] Isolate every run; prove treatment absence/presence and score efficacy, correctness, friction, and severe regression.
- [ ] Validate a private reproducibility artifact, then observe a day-21 exposure-qualified loop completion without a retention claim.

Acceptance: all pass gates below hold; a pass unlocks two external pilots only.

## Execution Tasks

- [ ] Implement Workstream 1 and stop if any legacy regression or privacy-contract mismatch remains.
- [ ] Implement Workstream 2 and fault-test cursor, pending-run, and recovery behavior before any model sees trace output.
- [ ] Implement Workstream 3 and complete the adversarial receipt suite before human review exists.
- [ ] Implement Workstream 4 and run merge/concurrency/crash tests before dogfooding.
- [ ] Implement Workstream 5 and time the one-invocation path.
- [ ] Freeze the experiment before the first benchmark output is generated.
- [ ] Execute Workstream 6 and record a pass, fail, or inconclusive result without changing thresholds afterward.

## Implementation Sequence

1. Ship the unrelated card/security correction as prerequisite hygiene; start the 14-day experiment clock after it passes.
2. Add the corrections parser and store primitives.
3. Add strict user-only indexing and cursor state.
4. Add bounded evidence expansion and contract validation.
5. Add transactional review, ledger, compiler, and fixed Claude install.
6. Add weekly dual-lane review and status.
7. Dogfood one real correction without globally installing it before the benchmark.
8. Freeze tasks, isolate environments, run the benchmark, then install only if the gate passes.
9. Complete the day-seven review and decide whether to invite two pilots.

## Data, Auth, Provider, And Deploy Boundaries

- Data is local filesystem data. There is no authentication layer, database, hosted provider, migration, or deploy in this experiment.
- Privacy relies on OS account/directory permissions; files are not encrypted.
- `ditto.py` performs no network request. The active coding agent/provider may receive `index.jsonl` and, after separate consent, bounded `evidence.jsonl`.
- No raw personal trace, real ledger, generated skill, source map, or benchmark output is committed to Git.
- Schema evolution is fail-closed. There is no automatic migration in the experiment. Unknown versions remain byte-identical; future migration must back up and atomically replace.
- GitHub stars, Reddit votes, and repository traffic are separate launch metrics and are not inputs to the product gate.

## Test Matrix

| Area | Happy path | Failure/abuse path | Regression evidence |
|---|---|---|---|
| Legacy CLI | current mine/card/install tests | corrections args do not alter legacy parsing | all nine baseline tests plus snapshots |
| Claude parsing | native IDs, text blocks, Hebrew/emoji, CRLF | meta, sidechain, agent file, unknown blocks, invalid UTF-8/JSON, permission error | no partial committed run |
| Identity | append and moved path keep IDs | copied export, duplicate UUID/event, reordered/modified trace | duplicate session cannot satisfy gate |
| Cursor | new row and late old session included | same/missing/offset timestamp, truncation, line rewrite | state advances only after commit |
| Contracts | valid anchor/candidate/review | wrong types, extra keys, oversize, newline/NUL/ANSI/bidi override, stale digest | every failure leaves bytes unchanged |
| Receipts | direct native parent chain in two sessions | distant turns, same session, same chain copied, old receipt reused | human prompt starts only after validation |
| Review | approve/edit/reject/defer | typo retry, EOF, Ctrl-C, stale revision | cancellation writes nothing |
| Ledger | append rule and review | second run, same slug/different evidence, unknown version, duplicate run | prior history and receipts remain |
| Atomicity | normal replace | failure after each commit stage, Windows transient/permanent replace failure | old valid revision recoverable |
| Concurrency | one writer | second lock and stale lock | explicit conflict/recovery, no last-writer wins |
| Compiler/install | exact name, identical no-op | mismatch, traversal, changed content, zero active rules | profile `you` remains untouched |
| Weekly review | all active rules checked once | missing/duplicate check, empty bundle, prior evidence reuse | cursor and history unchanged on failure |
| Privacy | user-only index then bounded evidence | no provider consent, `--no-redact`, repo output not ignored | stdout contains no raw evidence; HTML offline |
| Deleted/archived source | completed old run remains verifiable | completed source missing; pending source missing; source rewritten | completed deletion retires checkpoint, pending deletion blocks, explicit reset preserves committed IDs |
| Provider/model failure | valid agent JSON | malformed, empty, unavailable, prompt-injected output | pending run is resumable or abortable |
| Benchmark | isolated A/B and controls | skill leakage, baseline overlap, missing hashes/mapping | automatic fail or inconclusive, never silent pass |

## Verification Plan

Run after every workstream:

```powershell
python -m unittest discover -s tests -v
python ditto.py --help
python ditto.py corrections --help
git diff --check
git status --short
```

Before dogfood, additionally prove:

- every private artifact is ignored or outside the repository;
- no generated HTML contains `http://` or `https://`;
- correction mode rejects unredacted extraction;
- a synthetic copied-session fixture fails the two-session gate;
- a simulated crash between ledger and state commit recovers idempotently;
- the second run preserves first-run evidence and ledger history;
- Unicode and Windows path/replace tests pass;
- no raw event text is printed by correction commands.

Benchmark pass requires all of the following:

1. Two distinct, non-duplicate causal correction chains validate.
2. The user explicitly approves or edits the rule after local evidence review.
3. Ledger merge, replay, locking, atomicity, cursor, and recovery tests pass.
4. The target rule is absent from the baseline profile, or the test is labeled salience and cannot count as efficacy proof.
5. A is proven unable to load the treatment and B is proven able to load it.
6. Exactly eight positive and four negative-control tasks run twice per variant. At least five positive tasks are baseline-fail/treatment-correct-pass in both repetitions; zero positive repetition regresses; treatment correct completions are non-inferior across all 24 runs; every negative treatment run is correct and adds no friction; severe regressions are zero.
7. Every run uses a fresh worktree, config clone, and session; effective context/config proof is complete and treatment is the only difference.
8. The one-invocation review finishes in under five minutes with no commands/paths/JSON edits and at most three responses after invocation: assistant-evidence consent, one correction decision, and optional first-install confirmation.
9. Post-window unlock: a second review completes after at least seven days plus five new native main sessions and twenty new user events; otherwise record insufficient exposure and wait.
10. A complete private reproducibility manifest exists.

`no_explicit_recurrence` is unknown and never satisfies an efficacy or retention gate.

## Rollout And Rollback

### Rollout

1. Keep commands under the explicit `corrections` namespace and label outputs experimental.
2. Dogfood with a synthetic fixture first, then one private real run.
3. Do not globally install the treatment until the isolated benchmark is complete.
4. If the day-14 gate passes provisionally, freeze scope and wait for the day-21 loop-completion review. Only then invite no more than two opt-in pilots.
5. Promote the ledger contract from experimental only after two pilot reruns expose no incompatible lifecycle changes.

A pilot rerun is retention evidence only when the pilot initiates it at least seven days later without the operator running commands or sending a one-off reminder after onboarding. Researcher-reminded reruns support usability, not retention.

### Rollback

- `corrections abort` clears a pending run without advancing cursors.
- `corrections purge` removes local private batches/state only after confirmation and only after any installed correction skill is explicitly uninstalled.
- The fixed Claude skill install is backed up before replacement and can be restored from the displayed backup path. `corrections uninstall` removes only the exact `ditto-corrections` file after verifying its frontmatter and preserves a backup.
- The existing `you` skill/profile is never overwritten by the correction compiler.
- If current state is corrupt, use only a hash-valid paired backup as the base for journal replay. Once ledger application was observed, never publish the pre-commit backup as the final generation.
- If the efficacy or loop gate fails, leave the current one-shot Ditto product intact and stop correction expansion. Record whether the failure was evidence scarcity, UX friction, model efficacy, or architecture integrity.

## Risks And Fallbacks

- **Native Claude fields change:** fail closed and add a sanitized fixture before adapting.
- **Two-stage flow feels heavy:** measure it behind one invocation; simplify orchestration, not evidence integrity.
- **Redaction removes context:** mark ambiguity; never disable correction redaction.
- **Few repeated corrections exist:** keep the threshold; scarcity is product evidence.
- **Skill invocation is unreliable:** invoke explicitly for efficacy and measure auto-invocation separately.
- **Single-file code grows:** keep logical seams; package only after proof.
- **No benchmark opportunity:** return inconclusive, not pass.
- **Founder return is biased:** call it loop completion until external pilots return.

## Open Questions

No question blocks implementation. The experiment uses these defaults:

- Claude main-session logs only.
- Separate consent before bounded assistant evidence is shown to the active model.
- Fixed on-demand Agent Skill for the experiment; always-on host adapters deferred.
- One user decision per weekly review.
- Experimental private ledger, not a public standard claim.
- Local dogfood pass unlocks two pilots, not roadmap expansion.

Questions to revisit only after the gate:

- Should active corrections compile to an always-on marked Claude instruction block instead of an on-demand skill?
- Which minimal public rule contract should borg, cerebro, or other tools consume?
- Does weekly discovery surface enough new value to justify profile diffing next, or should workflow mining become the next return loop?

## Decision Log

- 2026-07-10: preserve one-file standard-library distribution for the experiment.
- 2026-07-10: use a dedicated corrections subcommand family instead of flat flags.
- 2026-07-10: replace mutable shared event files with immutable run batches.
- 2026-07-10: replace global timestamp watermarks with a committed native event-ID set; source checkpoints detect mutation but do not decide novelty.
- 2026-07-10: use native Claude session/message identity and exclude sidechain/meta/agent logs.
- 2026-07-10: minimize assistant exposure through user-only anchors and bounded expansion.
- 2026-07-10: separate private state, experimental ledger, and derived skill.
- 2026-07-10: separate processed runs from applied operations; make ledger/marker plus journal drive idempotent recovery.
- 2026-07-10: keep discovery and recurrence in the weekly loop.
- 2026-07-10: classify local day-seven return as loop viability, not retention.
- 2026-07-10: require isolated benchmark homes/worktrees and stronger repeated-task controls.
- 2026-07-10: a provisional day-14 pass plus a real day-21 loop completion unlocks two pilots only.

## VibeRaven Route

No provider dashboard, deployment, auth, billing, or database action is needed. Implementation remains local to the Ditto worktree. Evidence from real runs and benchmarks stays private and is represented in Git only by synthetic fixtures, schemas, and reproducibility rules.

## Next Skill

Next skill: `superpowers:writing-plans` to execute the six-workstream architecture as a test-driven 14-day implementation plan, followed by `superpowers:subagent-driven-development` only after Ohad approves execution.
