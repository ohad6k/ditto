from emulo_autopilot import contracts


def candidate_fixture(
    evidence=3,
    strata=2,
    contradiction_count=0,
    risk_categories=None,
    kind="directive",
    statement=None,
):
    receipts = []
    for index in range(evidence):
        month = 6 + (index % max(strata, 1))
        receipts.append(
            {
                "receipt_id": "rcpt_" + format(index + 1, "020x"),
                "session_id": format(index + 1, "016x"),
                "observed_at": "2026-{0:02d}-16T10:00:00Z".format(month),
                "time_stratum": "2026-{0:02d}".format(month),
            }
        )
    candidate = {
        "schema_version": contracts.CANDIDATE_SCHEMA,
        "candidate_id": "",
        "kind": kind,
        "domain": "work",
        "statement": statement
        or "Verify the live URL before claiming deployment is complete.",
        "scope": ["shipping"],
        "evidence": receipts,
        "contradiction_count": contradiction_count,
        "risk_categories": sorted(risk_categories or []),
        "source_packet_hash": "a" * 64,
        "prompt_contract_version": "emulo.autopilot-candidate-prompt/v1",
        "created_at": "2026-07-16T10:01:00Z",
    }
    candidate["candidate_id"] = contracts.candidate_identity(candidate)
    return candidate
