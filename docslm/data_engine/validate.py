"""Dataset validation: schema, message integrity, quotas, dedup.

  python3 -m data_engine.validate            # validates datasets/ against manifest
Writes datasets/validation_report.json and prints a summary. Exit 1 on failure.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED_TRAJ_KEYS = {"id", "spec", "context_pack", "tools", "messages", "verification", "lineage"}
ROLE_SEQ = re.compile(r"^(system user (assistant tool)+ assistant)$")
CODE_FENCE = re.compile(r"```")


def _ngram(text: str, n: int = 8) -> set:
    toks = re.sub(r"\s+", " ", text).strip().split(" ")
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def validate(out: Path) -> tuple[dict, bool]:
    problems, warnings = [], []
    manifest = json.loads((out / "manifest.json").read_text())

    # ---------- SFT trajectories ----------
    sft, ids = [], set()
    final_code_hashes = Counter()
    with (out / "sft_trajectories.jsonl").open(encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"sft line {ln}: invalid json: {e}")
                continue
            missing = REQUIRED_TRAJ_KEYS - set(rec)
            if missing:
                problems.append(f"{rec.get('id', ln)}: missing keys {sorted(missing)}")
                continue
            if rec["id"] in ids:
                problems.append(f"{rec['id']}: duplicate id")
            ids.add(rec["id"])
            roles = " ".join(m["role"] for m in rec["messages"])
            if not (roles.startswith("system user") and roles.endswith("assistant")):
                problems.append(f"{rec['id']}: bad role sequence: {roles[:60]}")
            if rec["verification"]["exec"] != "pass":
                problems.append(f"{rec['id']}: non-passed verification in SFT")
            call_ids, result_ids = [], []
            for m in rec["messages"]:
                if m["role"] == "assistant" and m.get("tool_calls"):
                    for tc in m["tool_calls"]:
                        call_ids.append(tc["id"])
                        json.loads(tc["function"]["arguments"])  # raises if malformed
                if m["role"] == "tool":
                    result_ids.append(m["tool_call_id"])
                    json.loads(m["content"])
            if sorted(call_ids) != sorted(result_ids):
                problems.append(f"{rec['id']}: tool_call ids unmatched")
            # reasoning contract: every assistant tool-call turn carries a <think> block
            grounded = ("route:", "postcheck", "/skills/", "plan",
                        "failure analysis", "script reported success")
            for m in rec["messages"]:
                if m["role"] == "assistant" and m.get("tool_calls"):
                    c = m.get("content") or ""
                    if not c.startswith("<think>") or "</think>" not in c:
                        problems.append(f"{rec['id']}: assistant turn missing <think> reasoning")
                    elif len(c) < 120:
                        problems.append(f"{rec['id']}: reasoning too shallow ({len(c)} chars)")
                    elif not any(t in c.lower() for t in grounded):
                        problems.append(f"{rec['id']}: reasoning lacks grounded content")
            # assistant turns must be non-trivial
            asst_text = [m for m in rec["messages"]
                         if m["role"] == "assistant" and m.get("content")]
            if not asst_text or len(asst_text[-1]["content"]) < 20:
                problems.append(f"{rec['id']}: missing final assistant summary")
            v = rec["verification"]
            if v["repair_turns"] and not v["mutation"]:
                problems.append(f"{rec['id']}: repair trajectory without mutation name")
            if v["repair_turns"] == 0 and v["mutation"]:
                problems.append(f"{rec['id']}: mutation on clean trajectory")
            # near-dup detection on user request
            final_code_hashes[_hash(rec["messages"][2]["tool_calls"][0]["function"]
                                    ["arguments"])] += 1
            sft.append(rec)
    dup_code = {h: c for h, c in final_code_hashes.items() if c > 1}
    if dup_code:
        warnings.append(f"sft: {len(dup_code)} identical turn-1 scripts (content differs)")

    # ---------- preference pairs ----------
    prefs = []
    with (out / "preference_pairs.jsonl").open(encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            rec = json.loads(line)
            if rec["chosen"] == rec["rejected"]:
                problems.append(f"pref line {ln}: chosen == rejected")
            if not rec["meta"]["rejected_failure"]["violations"] and \
               rec["meta"]["rejected_failure"]["exit"] in (0, None):
                problems.append(f"pref line {ln}: rejected side has no measured failure")
            if not rec["chosen"]["content"].startswith("<think>"):
                problems.append(f"pref line {ln}: chosen side missing reasoning")
            if rec["rejected"]["content"] not in ("",) and \
               len(rec["rejected"]["content"]) >= len(rec["chosen"]["content"]):
                problems.append(f"pref line {ln}: rejected reasoning not contrastive")
            prefs.append(rec)

    # ---------- routing ----------
    routes, label_counts = [], Counter()
    with (out / "routing.jsonl").open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            content = rec["messages"][-1]["content"]
            if "</think>" in content:   # routing answers reason, then emit JSON
                content = content.split("</think>", 1)[1].strip()
            label = json.loads(content)
            assert set(label) == {"skill", "route", "scene"}
            label_counts[label["skill"]] += 1
            routes.append(rec)

    # ---------- quotas vs spec targets ----------
    strat = Counter(f"{r['spec']['skill']}/{r['spec']['route']}/{r['spec']['lang']}"
                    f"/L{r['spec']['difficulty']}" for r in sft)
    repairs = sum(1 for r in sft if r["verification"]["repair_turns"] > 0)
    repair_share = repairs / max(len(sft), 1)
    en = sum(1 for r in sft if r["spec"]["lang"] == "en-US") / max(len(sft), 1)
    quota = {
        "repair_share": {"value": round(repair_share, 3), "target_min": 0.25},
        "en_share": {"value": round(en, 3), "target_min": 1.0},
    }
    for k, q in quota.items():
        if q["value"] < q["target_min"]:
            problems.append(f"quota {k}: {q['value']} < {q['target_min']}")

    # ---------- capability coverage (uniform function coverage contract) ----------
    from .taxonomy import CAPABILITIES
    cap_counts = Counter((r["spec"]["skill"], r["spec"]["route"]) for r in sft)
    expected = {(s, rt) for s, rt, _ in CAPABILITIES}
    missing_caps = sorted(expected - set(cap_counts))
    if missing_caps:
        problems.append(f"capability coverage: missing {missing_caps}")
    spread = (max(cap_counts.values()) - min(cap_counts.values())
              if not missing_caps and cap_counts else -1)
    if cap_counts and spread > 3:
        problems.append(f"capability spread {spread} > 3 (counts not equal)")
    diff_counts = Counter(r["spec"]["difficulty"] for r in sft)
    n = max(len(sft), 1)
    for d, c in sorted(diff_counts.items()):
        if abs(c - n / 3) > n * 0.06:
            problems.append(f"difficulty {d} share off: {c}/{n} (target ~{n // 3})")

    # cross-check manifest counts
    if manifest["counts"]["sft_ok"] != len(sft):
        problems.append(f"manifest sft_ok {manifest['counts']['sft_ok']} != {len(sft)}")
    if manifest["counts"]["routing"] != len(routes):
        problems.append("manifest routing count mismatch")

    report = {
        "valid": not problems,
        "counts": {"sft": len(sft), "preference": len(prefs), "routing": len(routes)},
        "quota": quota,
        "capability_coverage": {
            "distinct_capabilities": len(cap_counts),
            "expected": len(expected),
            "min_per_capability": min(cap_counts.values()) if cap_counts else 0,
            "max_per_capability": max(cap_counts.values()) if cap_counts else 0,
            "difficulty_distribution": dict(sorted(diff_counts.items())),
        },
        "label_distribution": {"routing_skill": dict(label_counts),
                               "strata": dict(sorted(strat.items()))},
        "problems": problems,
        "warnings": warnings,
    }
    (out / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False))
    return report, not problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "datasets")
    args = ap.parse_args()
    report, ok = validate(args.out)
    print(json.dumps({k: v for k, v in report.items() if k != "label_distribution"},
                     indent=2, ensure_ascii=False))
    print("routing skill distribution:", report["label_distribution"]["routing_skill"])
    if not ok:
        print(f"VALIDATION FAILED: {len(report['problems'])} problems")
        sys.exit(1)
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
