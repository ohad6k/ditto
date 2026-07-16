"""Print high-severity findings from a scanner SARIF report.

Temporary diagnostic: the HOL scan step exits non-zero before its SARIF is
uploaded, so high findings never reach code scanning and are invisible.
"""

import glob
import json


def severity_of(rule):
    props = rule.get("properties", {}) or {}
    raw = props.get("security-severity")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def main():
    paths = glob.glob("*.sarif") + glob.glob("**/*.sarif", recursive=True)
    if not paths:
        print("no sarif files found")
        return
    for path in sorted(set(paths)):
        print(f"=== {path} ===")
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
        for run in doc.get("runs", []):
            driver = run.get("tool", {}).get("driver", {})
            rules = {r.get("id"): r for r in driver.get("rules", [])}
            print(f"  tool: {driver.get('name')}  results: {len(run.get('results', []))}")
            for res in run.get("results", []):
                rule_id = res.get("ruleId")
                level = res.get("level")
                rule = rules.get(rule_id, {})
                sev = severity_of(rule)
                try:
                    loc = res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
                except (KeyError, IndexError):
                    loc = "?"
                msg = (res.get("message", {}) or {}).get("text", "")
                flag = "HIGH>>" if level == "error" or (sev is not None and sev >= 7.0) else "      "
                print(f"  {flag} level={level} sev={sev} rule={rule_id} file={loc}")
                if flag.strip():
                    print(f"          {msg[:400]}")


if __name__ == "__main__":
    main()
