# Run configuration: worker, reviewer, and the Go plan

Fixes open parameters 2 and 3 of the [preregistration](02-preregistration.md). Two separate agents exist here and they are easy to confuse:

| Role | What it is | Pinned? |
| --- | --- | --- |
| **Worker** | The coding agent that turns a task into a diff. Runs at every rung | Yes |
| **Reviewer** | The G3 gate that comments on or blocks the diff | Yes |

Decided: `opencode` as the worker client, `omp` (Oh My Pi) as the validated alternative, DeepSeek V4.1 Flash as the primary worker model, and the **Go plan ($10/month)** as the budget envelope.

---

## 1. What G3 means

**G3 is the review platform and its policy, not the model.** A "vendor AI reviewer" in the original design meant a product such as Copilot code review, CodeRabbit or Greptile: a system that owns the prompt, the diff curation, the severity heuristics and the blocking decision. The model underneath is an implementation detail, and with a real vendor bot it is not pinnable.

That matters for the study rather than being pedantry. If G3 is unpinnable, the vendor can swap models mid-sweep and the change is invisible in the data; gate yield cannot be attributed, because prompt quality and model quality are confounded; and "the AI review gate raised round trips by 30%" becomes unfalsifiable.

So the rung is a **configuration record**: reviewer model id, prompt, blocking threshold, and alert-suite policy.

| | Vendor bot | Scripted reviewer |
| --- | --- | --- |
| Realism | High; it is what teams deploy | Medium; a proxy for the class |
| Pinning | Model changes underneath you | Full control; prompt is an artifact |
| Attribution | Prompt and model confounded | Separable |
| Availability here | Not assumed | Available on existing model access |

**Decision: scripted reviewer for the pilot.** The writeup must then say plainly that results characterise *an automated review gate of this configuration*, not commercial review bots, and that a low yield is a lower bound rather than an indictment of the category.

### Reviewer configuration to pin

- **Model: Claude Haiku 5.5** (`opencode-go/claude-haiku-5-5`), deliberately a different vendor from the DeepSeek worker so the two do not share blind spots. Candidate volume is one to three calls per run, roughly 200-500 total, against an allowance of ~19,000 requests a month. Cost is not a consideration here; independence is.
- Alternative if Anthropic access is unavailable: GPT 6 Luna (`opencode-go/gpt-6-luna`).
- The prompt, committed and hashed before the pilot. This is what makes gate yield attributable.
- Blocking rule as an explicit threshold: block if any comment is tagged severity >= major.
- The reviewer never sees the hidden oracle.

---

## 2. Worker model

**Primary: DeepSeek V4.1 Flash** (`opencode-go/deepseek-v4.1-flash`).

| Property | Value |
| --- | --- |
| Monthly limit on Go | $100 |
| Estimated requests/month | ~216,000 |
| Price off-peak | $0.15 in / $0.60 out / $0.003 cached read per 1M |
| Price peak | double |
| Training on data | Not used |
| Retention | 0 days, under a ZDR agreement renewed monthly |

It has the largest allowance on the plan by a wide margin, the best privacy profile of any high-capacity model, and the terms renew rather than lapse, so it is a defensible primary rather than a stopgap.

**Two prerequisites**, both easy to miss:

- **Workspace owner or admin must set Regions to `Global`** in Settings › Privacy. Without it the model is blocked, and the failure surfaces as a run error rather than a configuration error.
- **Schedule off-peak.** Peak is 01:00-04:00 and 06:00-10:00 UTC, Monday to Friday; everything else, including weekends, is off-peak at half price. This doubles the effective allowance and costs nothing but cron discipline.

### Cost, estimated rather than assumed

A 30-minute repository-level run plausibly consumes something like 50k new input, 20k output and 500k cached-read tokens. At off-peak prices that is roughly **$0.02 per run**, so 180 runs is **$4-8**, against a $100 allowance and a $20 per-five-hour window cap. Budget is therefore **not** the binding constraint on this plan; capability and calendar time are.

That figure is an estimate with stated assumptions. The harness should not rely on it: every OpenCode Go response reports how much the request counted as `opencode.allowance`, so the runner records actual spend per run. RQ5's cost metric then becomes measured rather than modelled, which is a small but real improvement to the study.

---

## 3. Selecting the worker without flooring the study

Two failure modes, and only one is obvious:

- **Over budget.** Visible, fixable.
- **Floor effect.** A model too weak for repository-level tasks completes almost nothing at every rung. Differences between rungs become unmeasurable, and the pilot produces a number that looks like a null result when it is really a capability failure. **This is the dangerous one.**

The $10 plan keeps DeepSeek in budget but does not tell us it can solve click tasks. So the worker is chosen by measurement.

### Smoke test, on holdout tasks only

- 2 holdout tasks x 4 attempts at G0, per candidate. **24 runs total.**
- Candidates, chosen to span the capacity/capability tradeoff:
  - DeepSeek V4.1 Flash — capacity and privacy, capability unproven
  - Kimi K2.7 Code — plausibly the strongest coding model that still fits on Go at ~6,750 requests, which covers only ~85-170 agent runs at 40-80 requests each
  - MiMo-V2.6-Flash — capacity, capability unproven
- Holdout tasks only, so the 12 pilot tasks stay unseen and the choice does not flatter the model on the tasks it is measured against.

### Selection rule, preregistered

1. **Floor check.** A candidate must complete at least 2 of 8. Candidates below that are disqualified regardless of cost.
2. **Fit check.** Estimate requests per run from the smoke test, then require `180 x requests_per_run` to fit inside the model's monthly capacity.
3. **Order of preference.** Highest completion among candidates passing both. On a tie, the larger allowance wins.
4. **If no candidate passes the floor**, do not proceed to the pilot. Either reduce task difficulty to tier 1 and 2 only, or accept a smaller N with the shortfall disclosed. Do not run the pilot on a floored model and report the result as a finding.
5. **If the best-capability candidate fails the fit check**, reduce k from 3 to 2 (120 runs) rather than switching to a weaker model. Capability first, repetition second.

The chosen model and the smoke test table are released. Selecting the worker on holdout data is mildly optimistic and is disclosed as a limitation; using the holdout rather than pilot tasks is the mitigation.

---

## 4. Client

**Primary: `opencode`, driven headless.** It is the native client, it sends the `x-opencode-session` header that the plan's routing and prompt caching depend on, and it is the configuration the vendor validates.

**Alternative: `omp` (Oh My Pi).** Kept as the second driver so the harness is not wedded to one client: if `opencode` changes its headless interface, or a run's behaviour looks client-specific, omp is the cross-check. The harness should treat the client as a swappable adapter from the start, since the arity of the experiment is "rungs", not "clients".

Whatever client runs, the version is pinned and recorded per run. A client upgrade mid-sweep is a deviation.

---

## 5. Configuration record

One `config.json` per run under `runs/<run-id>/`:

| Field | Note |
| --- | --- |
| Task id, tier, class | `logic` or `security` |
| Rung | G0-G4 |
| Worker | client name and version, `opencode-go/<model-id>` |
| Reviewer | model id, prompt hash, blocking threshold |
| Subject | tag `8.5.0`, commit `8b19813` |
| Image | digest, not tag |
| Timing | dispatch, gate verdict, review session, merge |
| Outcome | gate-green, independent completion, gate escape, adjudication |
| **Spend** | `opencode.allowance` per request, summed per run |
| Peak or off-peak | Determines the price actually applied |

Anything not in this file did not happen.

---

## 6. Open

- [ ] `Global` region enabled for DeepSeek in workspace privacy settings
- [ ] `opencode` headless invocation verified; version pinned
- [ ] Reviewer prompt written, hashed, committed before the pilot
- [ ] Smoke test on holdout tasks; worker model recorded against the selection rule
- [ ] Pacing: off-peak window chosen; 180 runs spread inside the 5-hour and weekly caps
