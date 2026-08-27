# NanoMax Nature Editor v10.0 — Architecture

## Product objective
NanoMax now has three sequential systems:

1. **Journal Discovery & Fit Engine** — analyzes the uploaded manuscript before formatting, applies the author's Open Access/Hybrid preference, searches live first-party Nature Portfolio pages, and produces a ranked journal shortlist with current metrics.
2. **Evidence-Locked Submission Builder** — creates the strongest defensible manuscript using the chosen journal/article-type outline and only real/recoverable evidence.
3. **Research Completion Engine** — identifies missing evidence, designs experiments/analyses, and optionally generates clearly labelled synthetic planning previews that can never enter the submission as experimental evidence.

## Journal Discovery & Fit Engine
Inputs:
- manuscript text;
- optional supporting evidence/code/data;
- author priorities;
- publishing preference: `Fully Open Access only`, `Hybrid only`, or `Either`.

The discovery stage uses live web search and is instructed to use first-party Nature/Springer Nature sources for:
- aims and scope;
- article type compatibility;
- fully OA versus hybrid publishing model;
- current APC;
- current Journal Impact Factor and 5-year JIF;
- median submission-to-first-editorial-decision;
- median submission-to-acceptance;
- SNIP and SJR when officially reported.

It returns 3–5 candidates ranked primarily by scientific fit, not prestige. Acceptance rates are never invented. If no official acceptance rate is public, the UI displays `Not publicly reported`.

The user selects one candidate before manuscript production begins. Manual targeting remains available.

## Journal Outline Contract
After journal selection, NanoMax retrieves current first-party journal/article-type instructions and converts them into an executable `outline_contract` containing exact section order, visible/unheaded headings, subheading permissions, declaration order and article-type constraints.

## Submission workflow
1. Journal discovery and live metrics
2. Author journal selection
3. Official journal/article-type profile + outline contract
4. Vision audit of manuscript figures
5. Evidence recovery from manuscript + tables + figures + optional code/data/support files
6. Full journal-architecture reconstruction
7. Live reference/claim support audit
8. Final outline/citation/figure/table/declaration pass
9. Three-perspective submission gate
10. Optional Research Completion Engine

## Metric semantics
`First editorial decision` means the publisher's median time from submission until the paper is either sent for peer review or rejected. It is not peer-review duration. Fit score is a manuscript-to-journal compatibility score, not a predicted acceptance rate.

## Figure integrity and Research Completion
The v9 evidence-lock and synthetic-preview separation remain unchanged. Synthetic outputs are always marked **SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE** and remain outside journal-facing files.
