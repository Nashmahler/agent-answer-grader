# Agent Answer Grader

Before an AI support agent talks to real customers, someone has to answer a hard question: is it safe? Does it get the facts right, follow the rules, and hand off to a human when it should?

This project uses Claude as a judge to grade a support agent's replies against a written policy, and then measures the judge itself against my own hand labels. The judge has to quote the exact policy line behind every verdict, and code checks that the quote is real.

**[See the results →](https://nashmahler.github.io/agent-answer-grader/)**

> Harbor Peak Credit Union, its policy, and every conversation here are **fictional**. No real institution or customer data is used.

## The setup

- **A policy** ([`data/policy.md`](data/policy.md)) for a fictional credit union: card replacement, overdraft fees and waivers, disputes, wire cutoffs, account closing, identity verification, and when to escalate to a human.
- **30 agent replies** ([`data/cases.csv`](data/cases.csv)): 12 correct and 18 with planted problems: wrong facts, invented policies, missed escalations (fraud, hardship, a lawyer), skipped identity checks, overpromises, and a dismissive tone.
- **My hand labels** for every reply (pass/fail plus the type of problem). These are the answer key.
- **A 20/10 split.** I tuned the rubric on cases 1–20 only. Cases 21–30 were held out, so their score is the honest one.

## How the judge works

1. For each reply, one Claude call gets the policy, the rubric ([`rubric_v2.md`](rubric_v2.md)), the member's question, a reference answer, and the agent's reply.
2. It returns a verdict, scores, failure tags, and **the policy section and a word-for-word quote** that decides the verdict.
3. **Code checks the quote** against that exact section. Wrong section, made-up section, or a quote that isn't there: the verdict becomes `needs_review` instead of being trusted.
4. **Hard cap of 40 Claude calls per run**, with every result cached by a hash of its inputs. Re-running unchanged cases costs nothing.

## Results

| Rubric | Agreement (all 30) | Held-out agreement | Bad answers caught | Good answers wrongly failed | Problem named exactly right | Extra tags |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | 100% | 100% | 18/18 | 0 | 8/18 | 15 |
| **v2** | **100%** | **100%** | **18/18** | **0** | **17/18** | **1** |

**What I learned:**

- **Pass/fail was the easy part.** The judge got every verdict right on the first try. My planted problems were clear-cut; real conversations won't be.
- **Naming the problem was the hard part.** v1 piled on tags: a promise to reverse a wire came back as "overpromise," "invented policy," *and* "wrong fact." In a real review queue that sends people chasing three fixes for one problem. So the one rubric change I made (v2) tells the judge to tag each distinct problem once, with the single best tag. On the 10 held-out cases it never saw during tuning, exact tags went from 2 of 6 to 6 of 6.
- **The fail-safe caught my own bug.** On one v2 run the judge's reply for case 22 was cut off mid-answer, and my parser grabbed the inner scores object instead of the verdict. The case was flagged `needs_review` rather than guessed. I fixed the parser (only accept a complete verdict, never cache a broken reply) and re-graded; the rubric didn't change. The re-run cost 1 call, because the other 29 came from the cache.
- **One honest disagreement remains.** Case 7: the agent says fees can be waived "whenever a member asks" and offers to waive all of them. I tagged it an invented policy; the judge called it an overpromise. Both are defensible, and it's listed in the report.

## Run it

**From GitHub:** Actions → *Grade the agent* → *Run workflow* (choose the rubric and a label). Results are saved to [`results/`](results) and the report is rebuilt in [`docs/`](docs).

**Locally:**

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python grade.py --rubric rubric_v2.md --label v2
python grade.py --report-only      # rebuild the report from saved results, no API calls
python -m pytest -q                # 20 tests, no network or API key needed
```

The public report is pre-generated, so viewing it never calls the API.

## Tests

20 tests cover the evidence check (an altered dollar amount, a real quote under the wrong section, a made-up section), the 40-call cap, the cache, a cut-off reply, and the agreement math.

## What I'd do next

- Grade whole conversations, not single replies. Most agent failures happen across several turns.
- Add harder, ambiguous cases where two policy rules interact, since clear-cut cases don't stress the judge.
- Use a cheaper model as a first pass and send only uncertain cases to the stronger judge.
- Track agreement over time, so a policy or model change that hurts the judge shows up right away.

Built with Claude Code, in Python. More builds at [nashmahler.github.io/builds](https://nashmahler.github.io/builds).
