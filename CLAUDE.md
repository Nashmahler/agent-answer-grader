# Agent Answer Grader (public repo)

Read PROJECT_BRIEF.md first; it's the source of truth for scope. Public portfolio project: never mention job searching, applications, or resumes, and never commit secrets (the API key lives in GitHub Actions secrets or a local .env).

## Rules
- Harbor Peak Credit Union and all data are fictional. Never use a real institution's name or data.
- data/cases.csv `my_label` and `my_failure_tags` are Nash's hand labels. Never change them without his explicit say-so.
- The evidence check stays in code: a verdict whose quote isn't word for word in the cited policy section becomes needs_review. Never loosen it to improve the numbers.
- At most 40 Claude calls per run (grader/core.py), with results cached by input hash.
- Tune the rubric on the 20 tuning cases only (ids 1-20). Never tune on the held-out cases (ids 21-30).
- The public report (docs/) is pre-generated; it never calls the API.

## Git commits
- Always commit as the author Nash Mahler <mahler.nash@gmail.com>.
- Never set the commit author to Claude or noreply@anthropic.com.
- Before the first commit in a session, run `git config user.name` and `git config user.email`; if they aren't mine, set them for this repo.
- A "Co-Authored-By: Claude" line at the end of the message is fine.
- Exception: the GitHub Actions "Save results and report" step commits as github-actions[bot] <41898583+github-actions[bot]@users.noreply.github.com>. These rules cover my own work, not automated runs.
