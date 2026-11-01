# Saturation diagnostic: what each outcome would change

**Written before the diagnostic runs.** If the interpretation is chosen after
seeing the scores, the diagnostic is worthless.

## What is being measured

12 pilot tasks x 1 attempt each, at **G0** (no gate), with DeepSeek V4.1 Flash,
sandboxed with the per-run probe. The hidden oracle decides. No repetitions.

Cost: roughly one hour and $0.12. It answers one question: **does the task set
leave any headroom at G0?**

## Pre-registered interpretation

| G0 completion | Reading | Action |
| --- | --- | --- |
| **12 / 12** | No headroom observed on one attempt | Do **not** change the model, the timebox or the gates. Add difficulty by authoring additional tier-3 tasks whose oracles constrain behaviour click's suite does not. Log as a task-set revision. Re-run this diagnostic on the new set. **Keep the saturated tasks** as the ceiling control |
| **10-11 / 12** | Thin headroom | Proceed to M3 unchanged. Report the failing tasks as the discriminating ones and state that completion variance is thin |
| **9 or fewer** | Adequate headroom | Proceed to M3 unchanged |

## What a saturated result would and would not mean

**Would:** make H1 and H2 (completion falls as strictness rises) uninformative at
G0, because there is little room to fall.

**Would not:** invalidate the guardrail question. Stricter gates can still reduce
completion and still catch, block and rework. RQ3 (gate yield), RQ2 (human
minutes), round trips, latency and cost remain measurable with completion flat.
A saturated G0 bounds what completion can say about a gate; it says nothing about
what the gate does.

## Prohibitions, binding on the operator

1. **No tightening the timebox to manufacture failures.** The 30-minute box is a
   budget, not an independent variable.
2. **No iterative re-authoring until the spread looks interesting.** One revision
   maximum before M3.
3. If the second set also saturates, **report saturation as the finding** and stop
   escalating difficulty.
4. **No changing the worker model to move the numbers.**
5. This diagnostic is **not a result.** One attempt per task, no repetitions, no
   completion-rate claim. Its only output is a go/no-go on task difficulty.

## If it saturates, the scope note that follows

M3's primary outcome would shift from *completion* to *gate yield and human cost*,
with completion reported as bounded. That is a scope note to record in the
preregistration before the sweep, not a silent substitution.
