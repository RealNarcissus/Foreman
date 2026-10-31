# Run configuration: the two agents in the design

Fixes open parameters 2 and 3 of the [preregistration](02-preregistration.md). Two separate "agents" exist in this study and they are easy to confuse:

| Role | What it is | Pinned? |
| --- | --- | --- |
| **Worker** | The coding agent that turns a task into a diff. Runs at every rung | Yes |
| **Reviewer** | The G3 gate that comments on or blocks the diff | Yes |

---

## 1. What G3 means (the clarification)

**G3 is the review platform and its policy, not the model.** A "vendor AI reviewer" in the original design meant a product such as Copilot code review, CodeRabbit or Greptile: a system that owns the prompt, the diff curation, the severity heuristics and the blocking decision. The model underneath is an implementation detail, and it is usually not pinnable.

That distinction matters for the study rather than being pedantry. If G3 is an unpinnable product:

- the vendor can swap models mid-sweep, and the change is invisible in the data;
- gate yield cannot be attributed, because prompt quality and model quality are confounded;
- "the AI review gate raised round trips by 30%" becomes unfalsifiable, since nobody can say what the gate was.

So the rung is defined by a **configuration record**: reviewer identity, prompt, blocking threshold, model id, and suite/severity policy. Two valid instantiations:

| | Vendor bot | Scripted reviewer |
| --- | --- | --- |
| Realism | High; it is what teams deploy | Medium; a proxy for the class |
| Pinning | Model changes underneath you | Full control; prompt is an artifact |
| Cost | Subscription, quota risk, org settings | Marginal, on existing model access |
| Attribution | Prompt and model confounded | Separable |
| Availability here | Not assumed | Available via OpenCode Go |

**Recommendation: scripted reviewer for the pilot.** The writeup must then say plainly that results characterise *an automated review gate of this configuration*, not commercial review bots, and that a low yield is a lower bound rather than an indictment of the category. A commercial bot, if one becomes available, is a second G3 variant in the main sweep, not a replacement.

### Reviewer configuration to pin

- Model id, and a different vendor from the worker so the two do not share blind spots.
- The prompt, committed and hashed. This is the artifact that makes gate yield attributable.
- Blocking rule, stated as a threshold: for example "block if any comment is tagged severity >= major". Without a threshold the rung has no defined behaviour.
- Explicitly: the reviewer never sees the hidden oracle, and the prompt is written before the pilot, not tuned during it.

---

## 2. The worker, and why model choice is a floor-effect risk

The pilot is 180 runs. If each run is 25-60 model requests, that is roughly **4,500-10,800 requests**, which is the number that has to fit inside a monthly allowance.

Two failure modes, and only one is obvious:

- **Over budget.** Runs fail partway and the harness records infrastructure failures. Annoying, visible, fixable.
- **Floor effect.** A model too weak to solve repository-level tasks completes almost nothing at every rung. Completion is then ~0 everywhere, differences between rungs are unmeasurable, and the pilot looks like a null result when it is really a capability failure. **This is the dangerous one**, because it produces a number that looks like a finding.

So the worker model is chosen by a smoke test, not by reputation.

### Smoke test (before authoring the 12 pilot tasks)

- **On holdout tasks only**, so the 12 pilot tasks stay unseen and the choice does not flatter the model on the tasks it is measured on.
- 3 candidate models x 2 holdout tasks x 4 attempts at G0 = 24 runs.
- Selection rule: take the model with the highest completion; require **at least 2 of 8** on the easiest holdout pair. If no candidate clears it, escalate the plan rather than proceeding.
- Record the choice and disclose it as a limitation: selecting the worker on pilot-adjacent data is mildly optimistic, and using the holdout is the mitigation.

---

## 3. Allowance arithmetic (OpenCode Go)

Plans are monthly dollar allowances, and each model has its own limit and its own monthly request estimate. The 5-hour window is 20% of the monthly allowance, the week 50%. Practical consequence: **180 runs cannot be burst**; they have to be paced across a week or more. That is compatible with the preregistered requirement to interleave rungs rather than batch them, and it should be planned for rather than discovered.

Approximate monthly request capacity by model, Go and Go Plus, from the published estimates:

| Model | Go ($10) | Go Plus ($40) |
| --- | --- | --- |
| MiMo-V2.6-Flash | 150,400 | 300,800 |
| LongCat-2.0 | 57,200 | 228,800 |
| GLM-5.3-Flash | 31,580 | 94,740 |
| Qwen3.8 Flash | 27,000 | 81,000 |
| GPT 6 Luna | 21,130 | 84,520 |
| Claude Haiku 5.5 | 19,230 | 76,920 |
| MiniMax M3 | 16,000 | 48,000 |
| Kimi K2.7 Code | 6,750 | 20,250 |
| GLM-5.2 | 4,300 | 12,900 |
| Kimi K3.1 Pro | 735 | 2,941 |

The flash-tier models have the headroom but are the most likely to hit the floor effect. The coding-stronger mid-tier models only fit comfortably on Go Plus. **Budget one month of Go Plus for the pilot**: about $40 covers the worker runs, the reviewer calls, and the smoke test with margin, and it removes the constraint that would otherwise force a too-weak model.

### Exclusions, for reproducibility rather than cost

- **Exclude Muse Spark 1.2/1.3 Contributor and Iceman Contributor.** Their terms state that prompts and completions are used for training. Running the task suite through them would leak the suite into future training data, which is a contamination vector for replication, not a privacy preference.
- **Do not pin a DeepSeek model as primary without confirming terms.** The published ZDR agreement is listed as valid through 31 October 2026, which is now. A lapse mid-sweep would break reproducibility.
- Prefer models whose retention is 0 days and whose data is not used for training; record the terms in force at the start of the sweep.

---

## 4. Configuration record

Store one file per run under `runs/<run-id>/config.json`:

| Field | Note |
| --- | --- |
| Task id, tier, class | `logic` or `security` |
| Rung | G0-G4 |
| Worker | client name and version, `opencode-go/<model-id>` |
| Reviewer | model id, prompt hash, blocking threshold, suite/severity policy |
| Subject | tag `8.5.0`, commit `8b19813` |
| Image | digest, not tag |
| Timing | dispatch, gate verdict, review session, merge |
| Outcome | gate-green, independent completion, gate escape, adjudication |

Every field here is something a reader would need to reproduce the run. Anything not in this file did not happen.

---

## 5. Open

- [ ] Plan level chosen (Go versus Go Plus)
- [ ] Worker client: `opencode run` headless, or another validated client
- [ ] Reviewer prompt written, hashed, committed before the pilot
- [ ] Smoke test on holdout tasks; worker model recorded
- [ ] Rate-limit pacing plan for 180 runs, including the monthly reset
