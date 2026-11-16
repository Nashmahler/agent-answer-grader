"""Grade every case with one rubric version, score it against my labels, and rebuild the report.

    python grade.py                          # rubric.md, saved as results/v1.json
    python grade.py --rubric rubric_v2.md --label v2
    python grade.py --report-only            # rebuild docs/index.html from saved results

Calls are capped at 40 per run and cached by input hash in cache/, so re-running is free.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from grader import core, metrics, report


def main(argv=None, llm=None, root: Path = Path(".")) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default="rubric.md")
    ap.add_argument("--label", default="v1", help="name for this run, e.g. v1 or v2")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)

    results_dir = root / "results"
    if not args.report_only:
        cases = core.load_cases(root / "data/cases.csv")
        rubric = (root / args.rubric).read_text()
        verdicts, budget, stopped = core.run(cases, rubric, llm or core.Claude(), root / "cache",
                                             policy_path=root / "data/policy.md")
        scored = metrics.by_split(cases, verdicts)
        results_dir.mkdir(exist_ok=True)
        (results_dir / f"{args.label}.json").write_text(json.dumps({
            "label": args.label, "rubric": args.rubric, "model": core.MODEL, "date": date.today().isoformat(),
            "calls_used": budget.used, "call_cap": budget.cap, "stopped_early": stopped,
            "metrics": scored, "verdicts": core.to_json(verdicts)}, indent=1))
        a = scored["all"]
        print(f"{args.label}: {len(verdicts)}/{len(cases)} graded, {budget.used} new calls "
              f"(cap {budget.cap}); agreement {a['agreement_pct']}%, caught {a['bad_caught']}/{a['bad_total']} "
              f"bad answers, {a['false_alarms']} false alarms, {a['needs_review']} needs review; "
              f"held-out agreement {scored['held_out']['agreement_pct']}%")
        if stopped:
            print(f"stopped early: {stopped}", file=sys.stderr)

    runs = [json.loads(p.read_text()) for p in sorted(results_dir.glob("*.json"))] if results_dir.exists() else []
    if runs:
        cases = core.load_cases(root / "data/cases.csv")
        for r in runs:  # recompute from saved verdicts, so older runs get any newer metrics too
            r["metrics"] = metrics.by_split(cases, [core.Verdict(**v) for v in r["verdicts"]])
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs/index.html").write_text(report.render(runs, cases))
        print("wrote docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
