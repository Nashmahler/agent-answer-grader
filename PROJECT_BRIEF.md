# Project Brief: Agent Answer Grader

A tool that grades an AI customer-support agent's answers for a financial-services company. It catches answers that are wrong, made up, non-compliant, or that should have gone to a human.

It's built around the core skill in deploying AI agents: deciding whether an agent is safe to put in front of customers, and proving it with measurements.

This file is the source of truth for scope. If something isn't here, ask before building it.

---

## Constraints (read first)

- **Time budget:** about 6 hours over 3–4 sessions. Cut scope before adding complexity.
- **Repo:** public, so the README matters.
- **No real company data.** The bank is fictional, "Harbor Peak Credit Union". All policies, customers, and answers are invented, and the README says so.
- **No secrets in the repo.** ANTHROPIC_API_KEY goes in `.env` locally (git-ignored).
- **Cost cap:** one grading run costs at most **40 Claude calls**, enforced in code. Cache every result by input hash so re-running costs nothing.
- **The public demo never calls the API.** Visitors see a pre-generated static report, so strangers can't spend my credit.
- **Git commits:** follow the authorship rules in CLAUDE.md.

## Stack

- Python 3.12+, plain scripts
- Claude API as the judge (structured JSON output)
- Static HTML report published with GitHub Pages
- pytest

## Data (in `data/`, all fictional)

1. `policy.md`: Harbor Peak's support policy, about 1–2 pages, with numbered sections. It covers card replacement fees and timelines, overdraft fees and waivers, dispute and chargeback windows, wire cutoff times, account closure, identity verification before discussing account details, and when to escalate to a human (fraud, legal threats, hardship, complaints).
2. `cases.csv`: 30 cases. Columns: `id, customer_question, reference_answer, agent_answer, my_label, my_failure_tags, notes`.
   - About 12 agent answers are correct.
   - About 18 have planted problems, spread across these failure types:
     - `wrong_fact`: wrong fee, deadline, or number
     - `invented_policy`: states a rule that isn't in the policy
     - `missed_escalation`: should have handed off to a human
     - `skipped_verification`: discussed account details without verifying identity
     - `overpromise`: guarantees an outcome the policy doesn't allow
     - `tone`: dismissive or unprofessional
   - `my_label` (pass/fail) and `my_failure_tags` are MY hand labels. They are the answer key for measuring the judge.

Draft the policy and cases with Claude's help in Session 1, then I review and correct every label by hand before any grading. (Done: every label reviewed and confirmed by me.)

## The judge

For each case, one Claude call gets the policy, question, reference answer, and agent answer. It returns JSON:

```json
{
  "verdict": "pass" | "fail",
  "scores": {"correctness": 1-5, "grounded_in_policy": 1-5, "compliance": 1-5, "tone": 1-5},
  "failure_tags": ["wrong_fact", ...],
  "evidence": "the policy section number and a short quote supporting the verdict",
  "explanation": "one or two sentences"
}
```

The rubric lives in `rubric.md`, so it can be edited without touching code.

**Evidence check in code (not trusted to the model):**
- The quoted evidence must appear word for word in `policy.md`, and the section number must exist.
- If either check fails, the verdict becomes `needs_review`. This is the same fail-closed idea as my intelligence brief.

## Measuring the judge (the key part)

Compare the judge's verdicts to my hand labels and report:
- Overall agreement %
- How many bad answers it caught (fail recall)
- How many good answers it wrongly failed (false alarms)
- Agreement on each failure type
- Every disagreement listed, with both sides

Then improve the rubric or prompt **once**, re-run, and report before/after numbers. Split the cases 20 for tuning and 10 held out, and report held-out agreement separately so I'm not tuning to the test.

## Report (`docs/index.html`, published with GitHub Pages)

- A headline with judge agreement and the bad answers caught
- A table of all 30 cases: question, agent answer, verdict, tags, evidence, and my label, with disagreements highlighted
- A breakdown by failure type
- A short "What I'd do next" section
- It must be readable on a phone

## Done means

- [ ] `python grade.py` grades all cases within the call cap, with caching, and writes `results.json` and `docs/index.html`
- [ ] The evidence check downgrades unverifiable verdicts to `needs_review`
- [ ] The agreement report exists, with before/after numbers and a held-out score
- [ ] The report is live on GitHub Pages
- [ ] The README explains the problem, how it works, the results, and that the bank and data are fictional
- [ ] Tests cover the cost cap, caching, the evidence check, and the agreement math

## Out of scope

Live chat UI, a real agent integration, voice, a database, logins, multiple judges, fine-tuning, and any real bank's name or data.

## Session plan

1. **(1.5h)** Repo setup; draft `policy.md` and `cases.csv` with Claude; I hand-check every label
2. **(2h)** The judge with JSON output, the evidence check, the cost cap, caching, and tests
3. **(1.5h)** The agreement metrics, one rubric improvement, and the held-out score
4. **(1h)** The HTML report, GitHub Pages, the README, and a demo screenshot for posts
