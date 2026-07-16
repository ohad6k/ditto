import collections

from .contracts import validate_candidate


PolicyResult = collections.namedtuple("PolicyResult", "policy_class reason")

PROHIBITED_RISKS = frozenset(
    {
        "security",
        "credentials",
        "permissions",
        "destructive",
        "purchase",
        "legal",
        "medical",
        "financial",
        "external-communication",
    }
)


def classify_candidate(candidate, auto_activate_enabled=False):
    candidate = validate_candidate(candidate)
    if not isinstance(auto_activate_enabled, bool):
        raise ValueError("auto_activate_enabled must be a boolean")
    risks = set(candidate["risk_categories"])
    if risks - PROHIBITED_RISKS:
        return PolicyResult("reject", "unknown-risk-category")
    if risks:
        return PolicyResult("review", "prohibited-risk")
    if candidate["kind"] == "retirement":
        return PolicyResult("review", "retirement")
    if candidate["contradiction_count"]:
        return PolicyResult("review", "contradiction")
    sessions = {item["session_id"] for item in candidate["evidence"]}
    strata = {item["time_stratum"] for item in candidate["evidence"]}
    if len(sessions) < 3:
        return PolicyResult("review", "insufficient-sessions")
    if len(strata) < 2:
        return PolicyResult("review", "insufficient-time-strata")
    if not auto_activate_enabled:
        return PolicyResult("review", "auto-disabled")
    return PolicyResult("safe", "repeated-explicit-low-risk")
