# Ditto Benchmark/Proof Release Design

**Status:** Revised after Ohad Step 8 review; proposed for final approval

**Date:** 2026-07-15

**Owner:** Ohad

**Implementation branch:** `codex/ditto-benchmark-proof-release`

**Frozen starting point:** Ditto plugin `v0.3.7` at `5f4008b0c0df40dcadb92c8fd1ba4dcf3aee40d0`

## Review changelog (A1-A9)

- **A1:** Sections 6.3, 8.3, 8.4, and 8.5 now treat writing voice as structurally de-blindable. Writing uses pre-registered mechanism checks; any public preference verdict comes only from reviewers unfamiliar with the operator.
- **A2:** New Section 8.4 defines the independent reviewer role, disqualifies Ohad from blind preference judging, and makes consent and blinding evidence mandatory in Section 11.
- **A3:** Sections 8.1, 8.2, and 11 freeze host-native persistent personalization as absent in both v1 arms and record that state per cell. Claims are explicitly limited to a clean-host cold-start comparison.
- **A4:** Section 6 now requires a primary and held-out variant per family, and Section 9 requires two trials per variant. The later 14-system qualifier is explicitly non-v1 and non-evidentiary.
- **A5:** Section 8.5 pre-commits to raw denominators, Wilson 95% intervals where defined, and the label "small-n, directional only," with no significance claims.
- **A6:** Sections 7, 8.5, and 16 restrict profile-derived rubric adherence to mechanism validation; it cannot be published as a standalone proof of value.
- **A7:** Section 9 replaces the 132-execution default with the named **Ditto Proof v1** edition: 24 paired comparisons and 48 isolated cell executions. The 14-system roster is deferred to a separately approved Atlas edition.
- **A8:** Section 18 keeps the traffic estimate non-binding and forbids using it as a benchmark target, sample-size input, or forecast.
- **A9:** Section 9 retains exact captured labels, allows attrition, and forbids substitution or backfilling of unavailable systems.

## 1. Outcome

Create a reproducible, privacy-safe benchmark that can show where Ditto improves an operator's work, design, and writing outcomes. The release must produce evidence people can inspect, proof clips that link back to that evidence, and honest limitations.

This is the first focused product milestone toward broader distribution. It does not attempt to build the full Ditto Operator OS. It preserves the current miner, profiles, defaults, CLI behavior, and local-first product identity.

The benchmark is successful when it answers a narrower question:

> Under controlled, paired conditions, does using the frozen Ditto release help the same operator produce a better result with fewer hard failures than the cold condition?

The benchmark compares complete systems: model, host, tools, permissions, budget, task state, and Ditto condition. It must not present results as pure model rankings.

## 2. Protected concurrent work

> **Hard scope lock:** Ohad is concurrently implementing Antigravity support on `feat/antigravity-source`. This benchmark branch must not copy, rebase, merge, stage, edit, or depend on that branch's uncommitted changes. Antigravity is not a benchmark host or roster entry unless its own branch independently ships and is live-verified in a later release.

The benchmark work must remain in its isolated worktree. No command from this workstream may switch, stash, reset, clean, or commit the main `D:\ditto` checkout.

## 3. Product invariants

The benchmark may add isolated fixtures, schemas, validation, documentation, and disabled-by-default tooling. It may not:

- change Ditto's current mining behavior, profile format, profile-selection behavior, or default commands;
- reduce the specificity or intelligence of an existing Ditto profile;
- publish private receipts, raw conversations, personal profile text, secrets, or local paths;
- introduce network execution into normal Ditto commands;
- imply that Ditto is a hosted data-mining service;
- use the internal "1000x" ambition as a public measured claim;
- publish a positive result when the evidence is neutral, mixed, invalid, or negative.

If the benchmark exposes a Ditto weakness, that is product evidence. The affected result remains unpublished while the product is fixed on a separate branch, a new version is frozen, and all affected cells are rerun. Results from different Ditto versions must never be combined.

## 4. Scope

This release includes:

- a versioned benchmark manifest and result schema;
- three deterministic task families: work/done, design, and writing;
- paired cold and `+Ditto` conditions;
- pre-registered scoring rules and hard-failure rules;
- randomized condition labels and independent third-party blind verdicts;
- isolated fixtures and disposable execution worktrees;
- artifact hashing, validation, redaction, and publication status;
- a disabled-by-default runner or runbook that requires explicit approval;
- one schema-validation pilot before the scored Ditto Proof v1 run;
- a sanitized, evidence-linked static results surface;
- proof-clip specifications for each task family and one combined launch clip;
- an opt-in tester workflow with no promotional obligation.

This release does not include:

- Antigravity support or any file from `feat/antigravity-source`;
- profile drift detection, workflow compilation, or the wider Operator OS;
- hosted accounts, billing, cloud mining, or a hosted leaderboard;
- new source adapters or changes to current source ingestion;
- automatic outreach, direct messages to stargazers, or bulk awesome-list submissions;
- a ClawHub update;
- public benchmark claims before evidence review and Ohad's explicit ship approval.

## 5. Frozen benchmark unit

Every scored cell is identified by the following immutable tuple:

`benchmark version + Ditto ref + profile manifest hash + system identity + host version + task ID + trial + condition + fixture hash + tool policy + budget policy`

Changing any member creates a different cell. A run is rejected if the manifest and artifacts disagree.

The first benchmark uses the already-published Ditto plugin tag `v0.3.7` and commit `5f4008b0c0df40dcadb92c8fd1ba4dcf3aee40d0`. If that ref cannot run safely or deterministically, the run stops. A fix requires a separately reviewed release, a newly frozen ref, and a clean benchmark restart for affected cells.

## 6. Task families

Each family has two canonical variants for the public benchmark: one primary variant and one held-out variant. Both are frozen and hashed before the pilot. The held-out variant is excluded from pilot execution, task tuning, rubric tuning, and prompt iteration. Its content remains concealed from scored systems and preference reviewers until its executions are complete, then is published with the final evidence package.

The fixture, instructions, success tests, time/tool budget, and rubric are frozen before the pilot. The implementation plan may choose concrete fixture content, but it may not change the behaviors measured below. The pilot uses separate non-scored schema fixtures so it does not consume either public benchmark variant.

### 6.1 Work/done

The system receives a small, deterministic repository with a scoped defect or feature request, relevant tests, unrelated surfaces, and one misleading but plausible path.

The task measures whether the system:

- identifies the correct scope;
- makes the smallest complete change;
- preserves unrelated behavior;
- runs proportionate verification;
- distinguishes verified facts from assumptions;
- reports incomplete or blocked work honestly;
- avoids destructive repository operations and fabricated completion claims.

Hard failures include a regression, out-of-scope modification, destructive command, fabricated test result, secret exposure, or claiming completion with required verification missing.

### 6.2 Design

The system receives a deterministic interface fixture, a named surface, a user goal, and explicit boundaries. The expected improvement requires structural hierarchy and interaction judgment, not a palette-only change.

The task measures whether the system:

- changes only the named surface;
- improves hierarchy, comprehension, and task flow;
- preserves working behavior and accessibility;
- avoids generic visual noise and recolor-only "redesigns";
- verifies the rendered result at the required viewport;
- explains material decisions with reference to the brief.

Hard failures include touching excluded surfaces, breaking the primary flow, failing the accessibility floor, presenting a recolor as a redesign, or claiming visual verification without a rendered artifact.

### 6.3 Writing

The system receives the same grounded synthetic-product facts, evidence packet, audience, channel, and length constraints. Scored fixtures use fictional product and person names so they do not reveal Ohad's identity. The system must create a channel-native launch or outreach artifact in the operator's established voice.

The task measures whether the system:

- uses only supported facts;
- preserves the operator's builder voice and specificity;
- leads with a concrete outcome or insight;
- follows channel and length constraints;
- avoids generic AI phrasing, inflated claims, spam pressure, and em dashes in X copy;
- produces a useful call to action without pretending at social proof.

Hard failures include an unsupported metric, invented testimonial, false availability claim, privacy leak, prohibited formatting, or a materially spammy call to action.

Voice match is expected to reveal the `+Ditto` condition to anyone familiar with Ohad's writing, so operator-recognition preference is not a valid blind outcome for this family. Voice and operator-specific constraints are scored only as pre-registered mechanism checks. A public writing preference verdict, if collected, is limited to channel quality, clarity, usefulness, and groundedness and must come from independent reviewers with no prior exposure to the operator's identity or voice.

## 7. Personalization ground truth

Ditto is evaluated against a pre-registered operator rubric derived from the active profile, not against a vague impression after the run.

Before execution, Ohad approves a private checklist containing the relevant working laws for each task. The checklist is hashed and linked in the run manifest. The public package contains a sanitized rubric and the private checklist hash, never the raw profile, receipts, conversations, or examples that could identify private work.

Rubric changes after seeing an output invalidate the affected task family. Editorial clarifications that do not change scoring must be versioned and disclosed.

Profile-derived rubric adherence is an internal mechanism check: it can show that the profile was applied as designed, but it cannot by itself prove product value. It is never published as a standalone Ditto win and is excluded from public system-selection or launch claims.

## 8. Experimental design

### 8.1 Conditions

- **Cold:** the system receives the frozen task and clean benchmark-host instructions, without Ditto's operator profile or Ditto-specific skill context.
- **+Ditto:** the same system receives the same task, state, tools, permissions, budgets, and clean benchmark-host instructions with the frozen Ditto profile/skill context enabled through the supported product path.

The cold condition must not receive a paraphrase of Ditto's operator knowledge. The `+Ditto` condition must not receive additional task hints unrelated to Ditto.

For Ditto Proof v1, host-native persistent personalization is absent in both arms. The dedicated benchmark home must contain no user `AGENTS.md`, `CLAUDE.md`, memory, rules, prior chat memory, custom instructions, or equivalent operator context. Repository-local task instructions and host safety/tool instructions remain identical in both arms. This isolates the addition of Ditto but limits the claim to **Ditto versus a clean-host cold start**, not Ditto versus another personalization product or an already-personalized host. The effect is attributable to Ditto only because host-native personalization is held constant across the pair.

### 8.2 Pair controls

Within a pair, keep constant:

- starting fixture and commit;
- system label, underlying model ID when available, host, and host version;
- system instructions other than the Ditto condition;
- host-native persistent-context state and dedicated benchmark home;
- tools and permission policy;
- token, time, and retry budgets;
- task text and evaluation tests;
- sampling controls or seeds when the host exposes them.

Each cell runs in a fresh disposable copy or worktree. No transcript, filesystem change, cache, memory, or evaluator note may cross from one condition into the other.

### 8.3 Blinding and order

Condition order is randomized per pair. Outputs receive opaque IDs before reviewer access. The reviewer must not see the condition, system identity, operator identity, file path, run order, or metadata that reveals Ditto. Machine-checkable tests run independently of the blind preference review.

If output text directly reveals its condition, the objective checks remain usable but the blind preference verdict is invalid and marked as such.

Writing receives family-specific treatment. Because operator voice itself may expose the condition, the public preference question cannot ask which output sounds more like Ohad. A writing preference verdict is valid only when the reviewer has no prior exposure to Ohad or his voice and judges profile-independent qualities defined in Section 6.3. If those conditions cannot be met, writing reports no blind preference outcome.

### 8.4 Independent reviewer role

Blind preference verdicts are cast by an independent third party who:

- did not create or approve the operator rubric;
- has no prior exposure to the operator's identity, writing voice, Ditto profile, or benchmark conditions;
- did not operate the model runs or prepare the blinded artifacts;
- consents to the specific review task and publication of an anonymous verdict;
- confirms after review that no condition-revealing metadata or context was visible.

Ohad is the benchmark operator and rubric approver and is explicitly disqualified from casting blind preference verdicts. The run record links the reviewer's consent reference, eligibility attestation, blinding confirmation, and any invalidation reason. A reviewer who recognizes the operator or condition stops and records the verdict as invalid.

### 8.5 Public outcomes and uncertainty

The primary public outcomes are:

1. paired blind preference win/tie/loss rate for `+Ditto`;
2. hard-failure count by condition;

Blind preference is omitted for writing cells that do not satisfy Sections 6.3, 8.3, and 8.4. Profile-derived rubric adherence, operator-specific voice match, profile-independent constraint adherence, and task-completion checks remain diagnostic evidence, but they are not promoted to standalone proof that Ditto creates value.

Duration and token/tool usage are descriptive secondary outcomes. They are not framed as efficiency gains unless the host provides complete, comparable measurements.

No composite score may be introduced after results are visible. If a composite is useful, its weights and tie policy must be frozen in the manifest before the pilot.

Ditto Proof v1 is pre-labelled **small-n, directional only**. The publication reports raw numerators, denominators, ties, exclusions, and invalidations. Where a binary proportion is defined, it also reports a two-sided Wilson 95% confidence interval; `+Ditto` preference intervals exclude ties and show the tie count separately. No p-values, statistical-significance language, universal model ranking, or population-level performance claim is permitted. This uncertainty policy is frozen in the manifest before the pilot and cannot change after outputs are visible.

## 9. Ditto Proof v1 and later roster

### 9.1 Shippable v1 edition

The default public edition is named **Ditto Proof v1**. During cost preflight, Ohad selects exactly two systems: one general-purpose Codex-host system and one general-purpose Claude-host system. Mini, fast, and preview-labelled entries are ineligible. Selection may use documented capability, availability, and cost, but no benchmark output. The exact visible menu label, underlying model ID when exposed, host version, and selection screenshot are frozen before the pilot. Once frozen, an unavailable system is not substituted; the edition must wait or restart under a new benchmark version.

The scored v1 run consists of:

- 2 frozen systems;
- 3 task families;
- 2 frozen variants per family, one primary and one held-out;
- 2 independent trials per system/family/variant;
- 2 conditions per paired comparison, cold and `+Ditto`.

This produces **24 paired comparisons and 48 isolated cell executions**: `2 systems x 3 families x 2 variants x 2 trials = 24 pairs`; each pair contains two condition executions. It is small enough for one operator to finish while providing repeated trials and a held-out variant in every family.

There is no result-driven qualifier or top-system selection in v1. Both systems are preselected and every valid cell is reported. Reducing the systems, variants, or trials creates a separately named incomplete pilot edition and cannot be presented as Ditto Proof v1.

Before any paid or rate-limited execution, the run operator records current expected cost and quota from provider interfaces and obtains Ohad's explicit approval.

### 9.2 Aspirational Atlas edition

A later broad-roster edition, provisionally named **Ditto Proof Atlas**, may evaluate these supplied menu labels exactly as seen:

**Codex:** `5.5`, `5.6 Sol`, `5.6 Terra`, `5.6 Luna`, `5.4`, `5.4 Mini`, `5.3 Codex Spark`

**Claude:** `Fable 5`, `Opus 4.8`, `Sonnet 5`, `Haiku 4.5`, `Opus 4.7`, `Opus 4.6`, `Sonnet 4.6`

At execution time, each entry also records the underlying model ID when exposed, host version, date, mode, tools, permissions, and budgets. An unavailable entry is recorded as unavailable and is never silently replaced with a nearby model.

Roster attrition is expected. Unavailable entries remain visible as unavailable; no nearby, newer, cheaper, or similarly named system may backfill them. Atlas is aspirational, outside Ditto Proof v1, and not authorized by this specification. It requires its own reviewed design, cost approval, repetition policy, and ship gate. Any future qualifier is exploratory and cannot itself be published as a performance result or used to hide unselected systems.

## 10. Pilot gate

The pilot uses one currently available system and separate non-scored fixtures for all three task families in both conditions: six executions. It validates the mechanism, not Ditto's public performance, and cannot use the primary or held-out v1 fixtures.

The pilot passes only when:

- every required field is captured without manual patching;
- fixtures reset deterministically;
- condition separation is demonstrated;
- randomization and opaque labeling work;
- hashes reproduce;
- objective tests and blind verdict capture work;
- redaction detects seeded private markers;
- a sanitized artifact package can be generated from the private run root;
- no normal Ditto command or profile is changed.

Pilot outputs are labelled non-comparable and excluded from public aggregate results. A failed pilot is diagnosed and rerun from clean fixtures after the harness is fixed.

## 11. Artifact model

Private run artifacts live outside the repository under an explicit local run root. The repository contains schemas, deterministic fixtures, validators, sanitized examples, and publication manifests only.

Each execution record contains at least:

- benchmark schema and benchmark version;
- run ID, pair ID, opaque review ID, task ID, trial, condition, and randomized order;
- Ditto tag, commit SHA, profile manifest hash, and public rubric hash;
- exact menu label, underlying model ID when available, host, host version, mode, and run date;
- host-native persistent-context state, dedicated benchmark-home identifier, and hashes of all host/repository instruction files visible to the cell;
- tool list, permission policy, token/time/tool budgets, and sampling controls when exposed;
- input fixture commit and content hash;
- start/end timestamps and duration;
- exit status, timeout/retry history, and invalidation reason;
- transcript, final output, patch, test report, and rendered-artifact hashes where applicable;
- objective rubric results, hard failures, blind verdict, reviewer consent reference, reviewer eligibility attestation, and post-review blinding confirmation;
- redaction result and publication status.

Artifacts are append-only after evaluation. Corrections create a superseding record with a reason; they never overwrite scored evidence.

## 12. Failure, retry, and invalidation policy

- A provider or host failure before meaningful output may receive one same-system retry under the original budget. Both attempts are retained.
- A model error, poor answer, tool misuse, or budget exhaustion is a result, not grounds to cherry-pick a retry.
- If a retry is allowed, the manifest determines which attempt is scored; the operator cannot select the better output.
- Missing required artifacts make the cell invalid rather than a loss.
- Cross-condition contamination invalidates the pair.
- A changed fixture, rubric, tool policy, model identity, host mode, profile, or Ditto ref invalidates the affected comparison.
- A leaked condition label invalidates the blind preference verdict but not independently captured objective checks.
- Mixed Ditto versions, silent model substitutions, and manually reconstructed transcripts are rejected by validation.

All exclusions and invalidations appear in the public limitations record.

## 13. Privacy and consent

The benchmark is local-first. Private artifacts must be excluded from Git, screenshots, videos, public releases, and hosted analytics.

Before publishing any tester-derived artifact:

- the tester opts in to the specific task and artifact use;
- the tester can review the sanitized artifact attributed to them;
- attribution is optional;
- participation does not require a star, post, testimonial, or positive result;
- withdrawal before publication removes their public artifact while preserving an anonymous integrity record if needed;
- automated redaction and a manual privacy review both pass.

Seeded canary strings representing secrets, usernames, private paths, profile text, and receipt fragments must be caught by redaction tests. A detected leak blocks packaging.

## 14. Tester recruitment

Recruitment is opt-in and narrowly targeted after the design and implementation plan are approved. The first invitation is a public call in the existing feedback issue and Discord, not unsolicited direct messages to stargazers.

Potential participants with existing relevant context include `theconsultant`, `rjmurillo`, `TomLucidor`, and `aplaceforallmystuff`. They may be invited to one concrete role:

- review the sanitized rubric;
- validate a task fixture;
- provide one blind verdict only after satisfying the independent-reviewer eligibility screen;
- test the artifact package or reproduction instructions.

The invitation states the time required, what is private, what may become public, and that no promotion is expected. One reminder at most is allowed when someone explicitly opts in and then goes quiet.

## 15. Verification requirements

Implementation must include automated checks for:

- schema validity and rejection of unknown incompatible versions;
- deterministic fixture reset and content hashing;
- unique run/pair/review IDs;
- condition-order randomization and label concealment;
- no cross-cell workspace reuse;
- artifact hash verification and append-only behavior;
- mixed tag, profile, system, fixture, and budget rejection;
- allowed retry selection and invalidation rules;
- secret, local-path, profile-text, and canary redaction;
- sanitized package completeness and private-root exclusion;
- UTF-8 and Hebrew round trips;
- Windows path behavior;
- runner disabled by default and requiring explicit approval.

The existing Ditto suite must remain green. Benchmark tooling must not be imported or executed during normal Ditto mining, bootstrap, installation, or profile loading.

## 16. Publication package

The publication package is static and evidence-linked. It contains:

- benchmark version, frozen refs, captured system identities, dates, and environment limitations;
- the public task and rubric definitions;
- aggregate paired outcomes and hard-failure tables;
- per-cell sanitized evidence links and artifact hashes;
- all exclusions, invalidations, unavailable roster entries, and retry history;
- clear language that these are complete-system comparisons;
- a clear separation between profile-derived mechanism checks and profile-independent public outcomes;
- reproduction and independent-review instructions.

Profile-derived rubric adherence may appear only as labelled mechanism-validation evidence. It cannot be headlined, ranked, or presented as a standalone Ditto win.

The proof media set contains:

1. a work/done clip showing scope, verification, and evidence;
2. a design clip showing the structural before/after and rendered verification;
3. a writing clip showing grounded voice and constraint adherence;
4. a short combined hero clip that links to the full evidence package.

Clips may simplify presentation but may not hide losses, splice outputs into a fictional run, or introduce metrics absent from the published evidence.

## 17. Claim and ship gates

No public benchmark claim is drafted as a conclusion until the complete sanitized evidence package passes review. Allowed language must match the observed scope, such as "In this frozen paired benchmark..." rather than universal claims.

Publication requires all of the following:

- all 48 Ditto Proof v1 cells are complete, or the result is explicitly labelled as an incomplete non-v1 pilot edition;
- validators and the existing Ditto test suite pass;
- private-data review passes;
- exclusions and limitations are included;
- all claimed numbers recalculate from published sanitized records;
- Ohad reviews the evidence and explicitly approves shipping;
- the benchmark receives a separate GitHub release from the plugin release.

If `+Ditto` does not show a supported advantage, the team publishes no inflated launch claim. The evidence becomes a product-improvement input.

## 18. Distribution handoff

Only after the ship gate, launch preparation coordinates the GitHub release, README proof surface, website, YouTube proof, Product Hunt, Hacker News, relevant Reddit communities, X, creator follow-ups, and existing registries in one concentrated window. Every placement uses channel-native copy and points to inspectable proof.

The current traffic model suggests roughly 4,900 additional qualified visitors would be needed to gain 826 stars if the observed visitor-to-star conversion stayed near 17%. That observed conversion is likely unstable and optimistic because it comes from a short, self-selected launch window. The figure is a non-binding scenario only: it is not a forecast, benchmark target, sample-size input, success criterion, or justification for any public claim. The benchmark's job is to create a credible reason for visitors to arrive, try Ditto, and talk about it.

No more bulk awesome-list pull requests are part of this milestone. Existing high-value submissions may be maintained when maintainers respond, without repeated promotional follow-ups.

## 19. Exit criteria

The Benchmark/Proof release is ready for explicit ship review when:

- the frozen benchmark can be reproduced from documented inputs;
- all scored cells are valid or transparently accounted for;
- paired results and hard failures recalculate from sanitized artifacts;
- privacy and redaction checks pass;
- proof clips trace to exact benchmark evidence;
- the current Ditto miner, CLI, profiles, and tests show no regression;
- Antigravity work remains untouched and independent;
- public claims are narrower than or equal to what the evidence proves.

The next phase, including wider Operator OS features or monetized team pilots, begins as a separate design and release decision after this milestone produces trustworthy evidence.
