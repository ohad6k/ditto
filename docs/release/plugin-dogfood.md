# Ditto plugin bounded-mining dogfood

Date: 2026-07-11

## Verdict

No bounded starter candidate passed the frozen private calibration gate. Candidate 2 was the final evaluated candidate; there is no smallest passing default. The Plugin release is stopped before fresh host probes, publication, tagging, or benchmark work.

The frozen checklist was not changed after candidate output was seen.

## Private calibration identity

- Checklist schema: `1`
- Checklist SHA-256: `9778cb1eb2fcdbd7aafed01600fc7a1ceaf59f99943d54b692b0aaff9efaab09`
- Required items: work `10`, design `5`, write `7`
- Private reports, receipts, profiles, and checklist contents committed to Git: `0`

## Candidate results

| Candidate | Selected source tokens | Cache hits at prepare | Planned workers | Actual worker passes | Planned reducers | Actual reducer passes | Frozen recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 70,902 | 0 | 4 | 5 | 1 | 1 | work 2/10, design 0/5, write 0/7 |
| 1 | 116,387 | 3 | 3 | 3 | 1 | 1 | work 2/10, design 0/5, write 2/7 |
| 2 | 147,277 | 4 | 4 | 4 | 1 | 2 | work 0/10, design 0/5, write 0/7 |

Candidate 0 used one corrective worker after the first report failed strict receipt validation. Candidate 2 used one corrective reducer after the first reducer hit the host timeout with an invalid draft. These passes are included in the actual counts.

Total calibration model passes: `16` (`12` worker passes and `4` reducer passes). Successful validated reports were cached and reused; no worker was repeated after its report entered the cache.

## Final validated pack

- Profile version: `17d9cbe650b51ce64600`
- Active profile manifest SHA-256: `0b786fd798829cb41b32c68bab7aa669089cacad2bdab4df71ae603e4978804d`
- Report-set SHA-256: `2a291fe73f49cd0076b07670997e57b0a380166d3c976de4b4599dce88578403`
- Work domain: active, but `0/10` frozen requirements recovered
- Design domain: inactive, `0/5`
- Write domain: inactive, `0/7`

The final pack is structurally and evidentially valid. It is not representative enough to satisfy the product-quality contract.

## Host-task probes and human verdicts

Fresh installed-plugin host tasks: `0`.

- Work verdict: not run; the frozen checklist failed first.
- Design verdict: not run; the domain was inactive and the frozen checklist failed first.
- Write verdict: not run; the domain was inactive and the frozen checklist failed first.

This preserves the gate order and avoids spending three host interactions on a candidate that already failed objective recall.

## Findings

- The original `4x25K -> 6x20K -> 8x20K` ladder was not monotonic: smaller segmentation excluded 20K-25K sessions and invalidated all earlier cache keys. Dogfood changed the ladder to one immutable 25K segmentation expanded from four to six to eight selected segments under the unchanged 160K-token ceiling.
- Live source churn changed one selected segment between candidate-2 preflight and preparation. Cost was re-disclosed and approved before the extra worker ran.
- Read-only report and pack validators now let a worker or reducer correct its own output inside the same model pass. This was added after a real invalid receipt-date failure exposed avoidable retry cost.
- Wider bounded sampling activated all three domains at candidate 1, but the result still missed most frozen requirements and included a contextual design preference that conflicted with the frozen taste profile.
- Candidate 2 correctly omitted unsupported design and writing profiles, but recovered none of the frozen must-recover requirements.

## Release consequence

Do not set `DEFAULT_CANDIDATE_INDEX` to candidate 0, 1, or 2 based on this dogfood. Do not proceed to Task 17, publish the plugin release, run the benchmark, or claim bounded starter mining is sufficient. The architecture needs a revised recall strategy and a newly approved calibration plan while preserving the frozen evidence and cost-honesty requirements.
