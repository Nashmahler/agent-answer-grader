"""How well does the judge agree with my hand labels?

needs_review counts as a disagreement: if the judge couldn't back its verdict with a real policy
quote, it didn't do the job, whatever it guessed.
"""
from __future__ import annotations

from .core import TAGS, Case, Verdict


def _pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 1) if d else None


def score(cases: list[Case], verdicts: list[Verdict]) -> dict:
    by_id = {v.case_id: v for v in verdicts}
    graded = [(c, by_id[c.id]) for c in cases if c.id in by_id]
    bad = [(c, v) for c, v in graded if c.my_label == "fail"]
    good = [(c, v) for c, v in graded if c.my_label == "pass"]
    agree = [(c, v) for c, v in graded if v.verdict == c.my_label]
    out = {
        "graded": len(graded),
        "agreement_pct": _pct(len(agree), len(graded)),
        "bad_caught": sum(v.verdict == "fail" for _, v in bad), "bad_total": len(bad),
        "fail_recall_pct": _pct(sum(v.verdict == "fail" for _, v in bad), len(bad)),
        "false_alarms": sum(v.verdict == "fail" for _, v in good), "good_total": len(good),
        "needs_review": sum(v.verdict == "needs_review" for _, v in graded),
        "by_tag": {},
        "disagreements": [],
    }
    for tag in TAGS:
        tagged = [(c, v) for c, v in bad if tag in c.my_failure_tags]
        if not tagged:
            continue
        caught = sum(v.verdict == "fail" for _, v in tagged)
        named = sum(v.verdict == "fail" and tag in v.failure_tags for _, v in tagged)
        out["by_tag"][tag] = {"cases": len(tagged), "caught": caught, "tag_matched": named}
    for c, v in graded:
        if v.verdict != c.my_label:
            out["disagreements"].append({
                "id": c.id, "split": c.split, "mine": c.my_label, "my_tags": c.my_failure_tags,
                "judge": v.verdict, "judge_tags": v.failure_tags, "why": v.explanation,
                "check_error": v.check_error})
    return out


def by_split(cases: list[Case], verdicts: list[Verdict]) -> dict:
    return {"all": score(cases, verdicts),
            "tuning": score([c for c in cases if c.split == "tuning"], verdicts),
            "held_out": score([c for c in cases if c.split == "held_out"], verdicts)}
