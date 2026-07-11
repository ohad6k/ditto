# Ditto plugin bounded-mining dogfood

Date: 2026-07-11

## Verdict

No bounded starter candidate passed the frozen private calibration gate. Candidate 2 was the final evaluated candidate, so there is no smallest passing default. The plugin release is stopped before Task 17 host probes, Task 18 reviews, Task 19 release preparation, publication, tagging, or benchmark work.

The frozen checklist was not changed after candidate output was seen.

## Private calibration identity

- Checklist schema: `1`
- Checklist SHA-256: `9778cb1eb2fcdbd7aafed01600fc7a1ceaf59f99943d54b692b0aaff9efaab09`
- Required items: work `10`, design `5`, write `7`
- Private reports, receipts, profiles, and checklist contents committed to Git: `0`

## Candidate results

| Candidate | Selected source tokens | Cache hits at prepare | Planned workers | Actual worker passes | Planned reducers | Actual reducer passes | Frozen recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 59,473 | 3 | 1 | 3 | 1 | 1 | work 2/10, design 0/5, write 0/7 |
| 1 | 109,245 | 4 | 2 | 2 | 1 | 1 | work 2/10, design 0/5, write 0/7 |
| 2 | 159,919 | 5 | 3 | 3 | 1 | 1 | work 2/10, design 2/5, write 1/7 |

Candidate 0 needed two replacement host attempts because the first two worker environments were read-only. Candidate 1's first worker report was filtered locally and fail-closed: only evidence with valid verbatim receipts was retained, with no additional model pass. Candidate 2 used exactly the approved three workers and one reducer, with no retry.

Total calibration model passes: `11` (`8` worker passes and `3` reducer passes). Separately counted host-task interactions: `11`. Local preflight, preparation, validation, caching, activation, and checklist comparison were not counted as model passes or host-task interactions.

## Final validated pack

- Frozen run: `20260711T154238Z-7258a239`
- Profile version: `dc2507ed1e0f123ea46f`
- Active profile manifest SHA-256: `c425ca9c8319d069552f5b73f0ecdff3611974dbe74e6ad606d3a947b889af1f`
- Report-set SHA-256: `427a4a12a121a32355970834a9702e260c35baa08c1e47881c7bf5594ecbee8d`
- Work domain: active, `2/10` frozen requirements recovered
- Design domain: active, `2/5` frozen requirements recovered
- Write domain: active, `1/7` frozen requirements recovered

The final pack is structurally and evidentially valid. Recovering `5/22` requirements does not satisfy the product-quality contract.

## Host-task probes and human verdicts

Fresh installed-plugin host tasks: `0`.

- Work verdict: not run; the frozen checklist failed first.
- Design verdict: not run; the frozen checklist failed first.
- Write verdict: not run; the frozen checklist failed first.

This preserves the gate order and avoids spending host interactions on a candidate that already failed objective recall.

## Findings

- Live source churn changed candidate 2 from two planned workers at preflight to three at preparation. The revised cost was disclosed and approved before model work.
- Candidate 1's selected source and validated reports contained design and writing material, but the reducer could not form supported active design and write profiles. Its failure was not merely a work-only selection.
- Candidate 2 activated all three domains but still recovered only `5/22` frozen requirements. Partial thematic overlaps were not counted as passes.
- Every worker and reducer output was validated. Invalid non-verbatim evidence was dropped fail-closed, and the private checklist was not loosened or edited.
- Extraction and redaction happened locally. The selected redacted text was processed by the user-chosen cloud model; `ditto.py` made no network calls, and worker tool network access was disabled while corpus content was present.

## Release consequence

Do not set `DEFAULT_CANDIDATE_INDEX` to candidate 0, 1, or 2 based on this dogfood. Do not proceed to Tasks 17-19 or claim bounded starter mining is sufficient. Adaptive recall remains experimental and outside the default release path. The next release decision requires an explicitly approved fallback, without changing this frozen result.
