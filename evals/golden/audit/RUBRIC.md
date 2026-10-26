# Historical audit rubric and limitations

Sample: latest 50 currently `type: bug` labelled pytest issues created before
2026-10-01, sorted by creation descending. No expansion was needed for 15
reconstructable cases. Search results and API responses are preserved unchanged.

First response: earliest comment by another login, excluding GitHub `Bot` users
and `[bot]` suffixes. It is not necessarily a maintainer response or helpful work.
No response is unresolved, never zero hours. Collection time is in provenance.json;
responses after the creation cutoff are included through collection time.

Clarification: a human account explicitly asks the reporter for missing debugging
information or a confirming retest. Exclude offers to contribute, assignment
requests, rhetorical questions, implementation proposals and developer discussion.
Categories: reproducer (triggering example), versions (specific runtime/release),
configuration (flags/layout/plugins), traceback (failure diagnostic),
expected_actual (observable behaviour/expectation). Multiple categories allowed.

AI-assisted draft coding after reading sampled comment excerpts:

| Report | Comment evidence | Categories | Basis |
|---|---|---|---|
| 13634 | issuecomment-3188638798 | reproducer | Explicitly says more information/reproducer is required. |
| 13835 | issuecomment-4412776337 | versions, reproducer | Asks reporter to retest a current version and supply a fresh repro if needed. |
| 13885 | issuecomment-3503352556 | configuration | Asks for a clean-directory run without project configuration. |

Evidence URLs use https://github.com/pytest-dev/pytest/issues/NUMBER#COMMENT.
This coding is not independent human ground truth. Student must inspect all 50
raw records before accepting the draft count (3/50). Only keyword-matching
comment excerpts were reviewed by the authoring assistant; nonmatching comments
may contain missed requests. No claim of exhaustive manual coding is made.

Current labels may have changed since submission. Edited issue bodies can differ
from what the first responder saw. All comments are current snapshots and can
also have been edited. Pagination is capped at 100 comments/events per issue;
check counts before treating a record as complete. Bot detection misses human
accounts using automation and bots without explicit type/suffix indicators.
Elapsed time includes weekends, timezone differences and volunteer availability;
it cannot establish maintainer effort saved or causation. The draft 6% request
rate is weak evidence of a broad need, not a deployment justification by itself.
