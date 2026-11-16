"""Static, phone-friendly HTML report. Built from saved results, so the public page never calls the API."""
from __future__ import annotations

import html

from .core import TAGS, Case

NEXT_STEPS = [
    "Grade whole conversations, not single replies: most agent failures happen across several turns.",
    "Add harder, ambiguous cases where two policy rules interact, since clear-cut cases don't stress the judge.",
    "Use a cheaper model as a first pass and send only uncertain cases to the stronger judge.",
    "Track agreement over time, so a policy or model change that hurts the judge shows up right away.",
]
LEARNED = [
    "Pass/fail was the easy part: the judge got every verdict right on the first try. My planted problems were clear-cut; real conversations won't be.",
    "Naming the problem was the hard part. v1 piled on tags, so the one rubric change (v2) tells the judge to tag each distinct problem once. On the 10 held-out cases, exact tags went from 2 of 6 to 6 of 6.",
    "The fail-safe caught my own bug: one cut-off reply was flagged for review instead of guessed. I fixed the parser and re-graded; the rubric didn't change.",
]


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _pct(x) -> str:
    return "n/a" if x is None else f"{x:.0f}%"


def render(runs: list[dict], cases: list[Case]) -> str:
    final = runs[-1]
    m = final["metrics"]
    first = runs[0]
    by_id = {v["case_id"]: v for v in final["verdicts"]}
    pretty = {t: t.replace("_", " ") for t in TAGS}

    rows_ba = "".join(
        f"<tr><td>{_e(r['label'])}</td><td>{_pct(r['metrics']['all']['agreement_pct'])}</td>"
        f"<td>{_pct(r['metrics']['held_out']['agreement_pct'])}</td>"
        f"<td>{r['metrics']['all']['bad_caught']}/{r['metrics']['all']['bad_total']}</td>"
        f"<td>{r['metrics']['all']['false_alarms']}</td>"
        f"<td>{r['metrics']['all'].get('tags_exact', 'n/a')}/{r['metrics']['all']['bad_caught']}</td>"
        f"<td>{r['metrics']['all'].get('extra_tags', 'n/a')}</td><td>{r['metrics']['all']['needs_review']}</td></tr>"
        for r in runs)
    tag_rows = "".join(
        f"<tr><td>{_e(pretty[t])}</td><td>{d['caught']}/{d['cases']}</td><td>{d['tag_matched']}/{d['cases']}</td></tr>"
        for t, d in m["all"]["by_tag"].items())

    cards = []
    for c in cases:
        v = by_id.get(c.id, {})
        verdict = v.get("verdict", "not graded")
        agree = verdict == c.my_label
        tags = ", ".join(pretty.get(t, t) for t in v.get("failure_tags", []))
        mine = c.my_label + (f" ({', '.join(pretty.get(t, t) for t in c.my_failure_tags)})" if c.my_failure_tags else "")
        ev = (f"<p class='ev'>§{_e(v.get('section'))}: “{_e(v.get('quote'))}”</p>" if v.get("quote") else "")
        err = f"<p class='err'>Evidence check: {_e(v.get('check_error'))}</p>" if v.get("check_error") else ""
        cards.append(f"""<div class="case {'agree' if agree else 'disagree'}">
<div class="top"><b>#{c.id}</b><span class="split">{'held out' if c.split == 'held_out' else 'tuning'}</span>
<span class="pill {_e(verdict)}">judge: {_e(verdict)}{(' · ' + _e(tags)) if tags else ''}</span>
<span class="pill mine">me: {_e(mine)}</span>{'' if agree else '<span class="flag">disagree</span>'}</div>
<p><span class="k">Member</span> {_e(c.customer_question)}</p>
<p><span class="k">Agent</span> {_e(c.agent_answer)}</p>
<p class="why"><span class="k">Judge</span> {_e(v.get('explanation'))}</p>{ev}{err}</div>""")

    a, h = m["all"], m["held_out"]
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Answer Grader: results</title>
<meta property="og:title" content="Agent Answer Grader: can an AI judge catch a support agent's mistakes?">
<style>
body{{font:16px/1.5 -apple-system,Segoe UI,Arial,sans-serif;max-width:860px;margin:0 auto;padding:18px;color:#1b1b1b;background:#f7f6f3}}
h1{{font-size:26px;margin:6px 0 4px}} h2{{font-size:19px;margin:28px 0 8px}} .lede{{color:#444}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}}
.stat{{background:#fff;border-radius:12px;padding:12px}} .stat b{{display:block;font-size:26px}} .stat span{{color:#555;font-size:13px}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:12px;overflow:hidden;font-size:14px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #eee}} th{{background:#efede8}}
.case{{background:#fff;border-radius:12px;padding:12px 14px;margin:10px 0;border-left:5px solid #2e7d4f}}
.case.disagree{{border-left-color:#d08a00;background:#fffaf0}}
.top{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px}}
.pill,.split,.flag{{font-size:12px;border-radius:99px;padding:2px 9px}} .split{{background:#eee;color:#555}}
.pill.pass{{background:#e3f3e8;color:#1e6b3f}} .pill.fail{{background:#fbe5e2;color:#9d2a1d}}
.pill.needs_review{{background:#fff1cc;color:#7a5a00}} .pill.mine{{background:#eef1f7;color:#334}}
.flag{{background:#d08a00;color:#fff;font-weight:700}}
p{{margin:4px 0}} .k{{font-weight:600;color:#555;margin-right:4px}} .ev{{font-size:14px;color:#3a5a40}} .err{{font-size:14px;color:#9d2a1d}}
.why{{font-size:14px;color:#333}} .note{{font-size:14px;color:#555}} footer{{margin:30px 0 10px;color:#666;font-size:14px}}
</style></head><body>
<h1>Agent Answer Grader</h1>
<p class="lede">Can an AI judge reliably catch an AI support agent's mistakes? I wrote a policy for a fictional credit union, 30 agent replies (18 with planted problems), and labeled every one by hand. Then Claude graded them and had to quote the exact policy line behind each verdict. Code checks the quote; if it isn't real, the verdict becomes "needs review."</p>
<div class="stats">
<div class="stat"><b>{_pct(a['agreement_pct'])}</b><span>agreement with my labels (all 30)</span></div>
<div class="stat"><b>{_pct(h['agreement_pct'])}</b><span>agreement on the 10 held-out cases</span></div>
<div class="stat"><b>{a['bad_caught']}/{a['bad_total']}</b><span>bad answers caught</span></div>
<div class="stat"><b>{a['false_alarms']}</b><span>good answers wrongly failed</span></div>
</div>
<h2>Before and after one rubric change</h2>
<table><tr><th>Version</th><th>Agreement</th><th>Held-out</th><th>Bad caught</th><th>False alarms</th><th>Tags exactly right</th><th>Extra tags</th><th>Needs review</th></tr>{rows_ba}</table>
<p class="note">I changed the rubric once, using only the 20 tuning cases. The 10 held-out cases were never used for tuning, so their score is the honest one.</p>
<h2>What I learned</h2><ul>{''.join(f'<li>{_e(s)}</li>' for s in LEARNED)}</ul>
<h2>By failure type</h2>
<table><tr><th>Problem planted</th><th>Caught (failed)</th><th>Named correctly</th></tr>{tag_rows}</table>
<h2>Every case</h2>
<p class="note">Orange cards are cases where the judge and I disagreed.</p>
{''.join(cards)}
<h2>What I'd do next</h2><ul>{''.join(f'<li>{_e(s)}</li>' for s in NEXT_STEPS)}</ul>
<footer>Harbor Peak Credit Union, its policy, and every conversation here are fictional. Judge: {_e(final.get('model'))}, {final.get('calls_used')} new calls on the last run (cap {final.get('call_cap')}). First run: {_e(first.get('date'))}. Code: <a href="https://github.com/Nashmahler/agent-answer-grader">github.com/Nashmahler/agent-answer-grader</a> · More builds: <a href="https://nashmahler.github.io/builds">nashmahler.github.io/builds</a></footer>
</body></html>"""
