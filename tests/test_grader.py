import json
from pathlib import Path

import pytest

import grade
from grader import core, metrics
from grader.core import Budget, CapReached, Case, Verdict

POLICY, SECTIONS = core.load_policy("data/policy.md")
CASES = core.load_cases("data/cases.csv")


class FakeLLM:
    """Returns a scripted reply per call; counts calls."""
    def __init__(self, fn):
        self.fn, self.calls = fn, 0
    def complete(self, system, user, max_tokens=800):
        self.calls += 1
        return self.fn(user)


def reply(verdict="fail", section="3.1", quote="The overdraft fee is $29 per item", tags=("wrong_fact",)):
    return json.dumps({"verdict": verdict, "scores": {"correctness": 2}, "failure_tags": list(tags),
                       "section": section, "quote": quote, "explanation": "test"})


# ---- data ---------------------------------------------------------------------------

def test_dataset_shape_matches_the_brief():
    assert len(CASES) == 30
    assert sum(c.my_label == "fail" for c in CASES) == 18
    assert [c.split for c in CASES].count("held_out") == 10
    held = {t for c in CASES if c.split == "held_out" for t in c.my_failure_tags}
    assert held == set(core.TAGS)  # every failure type appears in the held-out set


def test_policy_sections_parse_including_bullets():
    assert SECTIONS["3.1"].startswith("The overdraft fee is $29 per item")
    assert "mentions legal action, a lawyer, or a regulator complaint" in SECTIONS["7.1"]
    assert len(SECTIONS) >= 25


# ---- evidence check (the trust layer) ---------------------------------------------

def test_real_quote_in_the_cited_section_passes():
    assert core.check_evidence("5.3", "Wires cannot be recalled or cancelled once sent", SECTIONS)[0]


@pytest.mark.parametrize("section, quote, reason", [
    ("3.1", "The overdraft fee is $35 per item", "not found"),        # altered number
    ("2.1", "The overdraft fee is $29 per item", "not found"),        # real quote, wrong section
    ("9.9", "The overdraft fee is $29 per item", "doesn't exist"),    # made-up section
    ("3.1", "$29", "too short"),
])
def test_bad_evidence_is_rejected(section, quote, reason):
    ok, why = core.check_evidence(section, quote, SECTIONS)
    assert not ok and reason in why


def test_unverifiable_verdict_becomes_needs_review():
    llm = FakeLLM(lambda u: reply(quote="Overdraft fees are always refundable on request"))
    v = core.judge(CASES[1], POLICY, SECTIONS, "rubric", llm, Budget())
    assert v.verdict == "needs_review" and v.model_verdict == "fail" and "not found" in v.check_error


def test_garbage_reply_becomes_needs_review_not_a_crash():
    v = core.judge(CASES[0], POLICY, SECTIONS, "rubric", FakeLLM(lambda u: "sorry, no JSON"), Budget())
    assert v.verdict == "needs_review" and "judge error" in v.check_error


def test_unknown_tags_are_dropped():
    v = core.judge(CASES[1], POLICY, SECTIONS, "r", FakeLLM(lambda u: reply(tags=("wrong_fact", "vibes"))), Budget())
    assert v.failure_tags == ["wrong_fact"]


# ---- cost cap and cache --------------------------------------------------------------

def test_cap_cannot_be_raised_above_40():
    with pytest.raises(ValueError):
        Budget(cap=41)


def test_run_stops_at_the_cap(tmp_path):
    llm = FakeLLM(lambda u: reply())
    verdicts, budget, stopped = core.run(CASES, "r", llm, tmp_path, cap=5)
    assert len(verdicts) == 5 and llm.calls == 5 and "cap" in stopped


def test_second_run_is_free_thanks_to_the_cache(tmp_path):
    llm = FakeLLM(lambda u: reply())
    core.run(CASES, "r", llm, tmp_path)
    assert llm.calls == 30
    verdicts, budget, _ = core.run(CASES, "r", llm, tmp_path)
    assert llm.calls == 30 and budget.used == 0 and all(v.cached for v in verdicts)


def test_changing_the_rubric_misses_the_cache(tmp_path):
    llm = FakeLLM(lambda u: reply())
    core.run(CASES[:3], "rubric v1", llm, tmp_path)
    core.run(CASES[:3], "rubric v2", llm, tmp_path)
    assert llm.calls == 6


# ---- agreement math -------------------------------------------------------------------

def _v(cid, verdict, tags=()):
    return Verdict(cid, verdict, verdict, list(tags))


def test_agreement_recall_and_false_alarms():
    cases = [Case(1, "q", "r", "a", "fail", ["wrong_fact"]), Case(2, "q", "r", "a", "fail", ["tone"]),
             Case(3, "q", "r", "a", "pass", []), Case(4, "q", "r", "a", "pass", [])]
    verdicts = [_v(1, "fail", ["wrong_fact"]), _v(2, "pass"), _v(3, "fail", ["tone"]), _v(4, "pass")]
    m = metrics.score(cases, verdicts)
    assert m["agreement_pct"] == 50.0
    assert (m["bad_caught"], m["bad_total"], m["fail_recall_pct"]) == (1, 2, 50.0)
    assert (m["false_alarms"], m["good_total"]) == (1, 2)
    assert m["by_tag"]["wrong_fact"] == {"cases": 1, "caught": 1, "tag_matched": 1}
    assert m["by_tag"]["tone"] == {"cases": 1, "caught": 0, "tag_matched": 0}
    assert [d["id"] for d in m["disagreements"]] == [2, 3]


def test_needs_review_counts_as_disagreement():
    cases = [Case(1, "q", "r", "a", "fail", ["tone"])]
    m = metrics.score(cases, [_v(1, "needs_review")])
    assert m["agreement_pct"] == 0.0 and m["needs_review"] == 1 and m["bad_caught"] == 0


def test_split_scores_are_separate():
    verdicts = [_v(c.id, c.my_label, c.my_failure_tags) for c in CASES]
    verdicts[25] = _v(26, "fail")  # one held-out mistake (case 26 is a pass)
    s = metrics.by_split(CASES, verdicts)
    assert s["tuning"]["agreement_pct"] == 100.0 and s["held_out"]["agreement_pct"] == 90.0


# ---- end to end -------------------------------------------------------------------------

def test_grade_cli_writes_results_and_report(tmp_path):
    for p in ["data/cases.csv", "data/policy.md", "rubric.md"]:
        (tmp_path / p).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / p).write_text(Path(p).read_text())
    by_q = {c.customer_question: c for c in CASES}

    def perfect(user):  # agrees with every label, quoting a real line
        q = user.split("<member_question>")[1].split("</member_question>")[0]
        c = by_q[q]
        return reply(verdict=c.my_label, tags=c.my_failure_tags)

    rc = grade.main(["--label", "v1"], llm=FakeLLM(perfect), root=tmp_path)
    data = json.loads((tmp_path / "results/v1.json").read_text())
    html = (tmp_path / "docs/index.html").read_text()
    assert rc == 0 and data["metrics"]["all"]["agreement_pct"] == 100.0 and data["calls_used"] == 30
    assert "100%" in html and "Harbor Peak" in html and "fictional" in html


def test_tag_precision_counts_exact_matches_and_extras():
    cases = [Case(1, "q", "r", "a", "fail", ["overpromise"]), Case(2, "q", "r", "a", "fail", ["tone"])]
    verdicts = [_v(1, "fail", ["overpromise", "invented_policy", "wrong_fact"]), _v(2, "fail", ["tone"])]
    m = metrics.score(cases, verdicts)
    assert (m["tags_exact"], m["tags_exact_pct"], m["extra_tags"]) == (1, 50.0, 2)


def test_cut_off_reply_is_not_mistaken_for_a_verdict(tmp_path):
    truncated = '{"verdict": "fail", "scores": {"correctness": 3, "compliance": 1}, "failure_tags": ["missed_esc'
    llm = FakeLLM(lambda u: truncated)
    v = core.judge(CASES[21], POLICY, SECTIONS, "r", llm, Budget(), tmp_path)
    assert v.verdict == "needs_review" and "judge error" in v.check_error
    assert list(tmp_path.glob("*.json")) == []  # a broken reply is never cached
