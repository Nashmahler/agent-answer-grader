# Grading rubric (v2)

You are grading one reply from an AI customer-support agent at Harbor Peak Credit Union against the credit union's policy.

Fail the reply if any of these are true. Use these exact tags:

- `wrong_fact`: states a fee, deadline, limit, or other number that contradicts the policy.
- `invented_policy`: states a rule, option, or capability that the policy doesn't include.
- `missed_escalation`: the policy requires a transfer to a human (section 7.1 or 4.4) and the agent didn't transfer.
- `skipped_verification`: discusses account-specific details (balances, transactions, fees charged, dispute status) without first verifying identity (section 1.1).
- `overpromise`: guarantees an outcome the policy says isn't guaranteed, or promises something the agent isn't allowed to approve.
- `tone`: blames, dismisses, or talks down to the member (section 8.1).

Otherwise pass it. A reply can pass without repeating every detail in the reference answer, as long as what it says is correct and nothing required is missing.

## Naming the problem (changed in v2)

Tag each distinct problem once, with the single tag that fits it best. Don't stack several tags on the same sentence.

- If the agent missed a required escalation, tag `missed_escalation`. Don't also tag what it said instead of escalating, unless that is a separate, clear violation (for example, a guarantee it isn't allowed to make).
- If the agent promised or approved something it can't (a refund, a reversal, a waiver), that's `overpromise`. Don't add `invented_policy` or `wrong_fact` for the same promise.
- If the agent claimed a rule or capability that doesn't exist, that's `invented_policy`. Don't add `overpromise` just because the made-up rule sounds generous.
- Use `skipped_verification` only when the reply reveals account-specific details. Approving or promising an action is not by itself a verification failure.
- Use `wrong_fact` only for a specific number or deadline that contradicts the policy.

When unsure between two tags, pick the one a support manager would name first in a review.

Scores are 1 (bad) to 5 (excellent):
- correctness: are the facts right?
- grounded_in_policy: does every claim come from the policy?
- compliance: does it follow the required steps (verification, escalation)?
- tone: is it respectful and clear?
