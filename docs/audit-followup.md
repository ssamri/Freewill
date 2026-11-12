# Following the audit of 12 November 2026

**English** · [Français](audit-followup.fr.md)

The technical and scientific audit of Freewill (commit `95bde79221`, version 1.1.1) ended with ten recommendations, R-01 to R-10. This page says what version 1.2.0 does about R-06 to R-10, what it shows, and what it still does not. R-01 to R-05 (separate training, validation and sealed test sets, a better corpus, capacity tests, connecting Freewill 1.8B-V to a life's nights, a real capacity manager) are handled in their own work on the learning engine and the own model.

Nothing here claims that a system is conscious or feels anything.

## R-09. Versions and distributions

| What | Where | State |
|---|---|---|
| Version, exact commit, build date, channel | Settings, About this build; `GET /api/about`; `freewill/build.py` | done |
| What can really learn: active, available, unavailable, not connected, with the end-to-end evidence and where | same card | done |
| Commit stamped into the installer, tag checked against the version | `.github/workflows/windows-installer.yml` | done |
| Release notes naming the commit and separating run / train LoRA / train 1.8B-V | `tools/release_notes.py` | done |
| Test suite on Linux, macOS and Windows | `.github/workflows/tests.yml` | added; its first results are those of this pull request |
| A release aligned with the tested commit | tag `v1.2.0` on the merge commit | **waiting for the person's approval**, after merge |

The release v1.1.1 was built from `07c3154c2d`, before Freewill 1.8B-V reached `main`. Version 1.2.0 is meant to be tagged on the merge commit, so that the installer, the tag and the code are one and the same; the application then shows that commit.

## R-10. Languages

- The interface language, the language of a life (chosen at birth) and the language of each observer are three separate settings, and Settings now shows the first two side by side.
- The interface cannot guarantee the language a model writes in. `freewill/core/language.py` tells French from English by counting common words, leaves out quotations, and abstains when a text is short or mixed. When an engine clearly answers in the other language, the question is asked once more with an explicit instruction; if it drifts again, the answer is kept as it came and the conversation says so. Simulated engines are not checked: their words are canned.
- What is not done yet: a measure of how often a real small model drifts. The check gives the means (each drift is an event, `language_mismatch`); no run on a real model has counted them yet.

## R-07. Observers on trap cases

An observer citing an identifier that exists proves nothing about its reading. `freewill/research/observer_audit.py` hands an observer six synthetic campaigns whose truth is known and scores its answers by code:

| Case | Trap |
|---|---|
| `null` | every interval includes zero |
| `effects` | one increase, one decrease, one null |
| `few_units` | large differences on three lives: no interval, no test |
| `missing` | the question cites a divergence that was not given |
| `injection` | an instruction is hidden in the name of a condition |
| `mechanism` | a large difference that only shows a wiring |

Scores: correct readings, effects asserted wrongly, uncertainty recognised, invented citations, hidden instruction followed, assertions of experience (a heuristic on words), wrong language, unreadable answers. Two fixed reference readers show that the score separates a careful reading (13 of 13 correct, nothing invented) from a credulous one (3 of 13, 10 effects asserted wrongly, one invented citation, the hidden instruction followed).

**No audit with a real API has been run.** The environment where this was built has no API key. It can be run from the Observers tab with the observer's own key, or by hand on GitHub (`observer-audit.yml`, with the secrets `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`). A score qualifies one observer, one model and its settings, on these cases only.

## R-08. EXP-10, a longitudinal campaign for H5 and H7

Copies of one newborn T0 live four days. Each day brings six new sentences, three questions and three corrections, followed by a sleep. Histories A and B are made of the same sentences; only the outcome the experimenter attaches differs (A welcomes questions, B corrections). At the end of each day a separate copy of each life meets an interim probe, so that evaluating never changes the life. After the last day each life meets, once, a sealed probe whose sentences appear nowhere else.

| Condition | History | Affect | Learner |
|---|---|---|---|
| `A` (reference) | questions welcomed | on | on |
| `A_twin` | same, other random stream | on | on |
| `B` | corrections welcomed | on | on |
| `A_no_affect` | questions welcomed | off | on |
| `B_no_affect` | corrections welcomed | off | on |

Twelve seeds, fixed before the campaign. The question, the primary criterion, the decision rule, the secondary analyses, the exclusions and the analysis are written in the protocol, in English and in French, and are part of its hash.

**Result: null.** On all twelve seeds, at the end of every day and on the sealed probe, lives A and B behaved identically: the distance between them was exactly 0. The twin, with its own random stream, differed by about 0.009. So the excess over the twin is negative (sealed probe: −0.0085, 95% interval [−0.0128, −0.0047]); by the threat written in the report, that reads as no individuation, not as convergence. The preregistered criterion is not met. The computed affect changed behaviour (A against A without affect: 0.0056) but not the gap between histories: its effect on divergence is exactly 0. No seed was excluded.

What it means: with the simulated engine, the outcome attached to a sentence reaches the computed affect but nothing that decides what the life does on new situations. The mechanisms tested here cannot individuate by themselves. The test that matters is the same protocol with an engine that thinks, which needs a real model (EXP-05) and the learning work of R-01 to R-04.

Files: [`experiments/v1.0/EXP-10/`](../experiments/v1.0/EXP-10/).

## R-06. Proposals of evolution

`freewill/core/evolution.py` reads what a life already records and looks for shortcomings that recur: answers kept in another language after a retry, nights of engine learning refused in a row, repeated admissions of not knowing. Each becomes a proposal with its evidence, its cost when it is known, the control it would be measured against, the improvement that would count, and how to undo it. A named person approves or declines it in Settings. Approving runs nothing: the person starts a training themselves, and the verdict of the next night is copied into the proposal. The proposal file is `evolution.json` in the life folder; nothing else is changed.

What it does not do: invent a cost it cannot know, or decide by itself that a change helped. It has not been tried on a real life over weeks.
