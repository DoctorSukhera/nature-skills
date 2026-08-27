# NanoMax Nature Editor v9.0 — Architecture

## Product objective
NanoMax Nature Editor has two strictly separated systems:

1. **Evidence-Locked Submission Builder** — creates the strongest defensible manuscript using only real/recoverable evidence.
2. **Research Completion Engine** — identifies missing evidence, designs experiments/analyses, and optionally generates clearly labelled synthetic planning previews that can never enter the submission as experimental evidence.

## Journal Outline Contract
The first API stage retrieves current first-party journal/article-type instructions and converts them into an executable `outline_contract` containing:
- exact section role and order;
- exact parent heading text;
- whether the heading is visible or unheaded;
- whether topical subheadings are permitted;
- required/optional status;
- declaration/reference order;
- article-type word/display rules.

The manuscript reconstruction and finalization stages are required to conform to this contract. The DOCX exporter uses the contract rather than hard-coding a generic Methods outline.

## Submission workflow
1. Official journal/article-type profile + outline contract
2. Vision audit of manuscript figures
3. Evidence recovery from manuscript + tables + figures + optional code/data/support files
4. Full journal-architecture reconstruction
5. Live reference/claim support audit
6. Final outline/citation/figure/table/declaration pass
7. Three-perspective submission gate
8. Optional Research Completion Engine

## Figure integrity
Conceptual redraws require a `content_lock` whitelist. The image prompt explicitly prohibits additions outside that whitelist. Quantitative and experimental figures are never synthetically replaced as evidence. Replotting requires underlying source data.

## Research Completion Engine
For every unresolved evidence gap, NanoMax can produce:
- why the evidence is needed;
- proposed experiment/analysis;
- required inputs;
- protocol steps;
- controls;
- statistical plan;
- expected real outputs;
- claim that could be supported if real results justify it;
- optional synthetic planning preview.

Synthetic previews are separate from journal-facing files and must display:

**SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE**

## Exports
### Journal-facing
- `Final_Manuscript.docx`
- `Cover_Letter.docx`
- optional `Supplementary_Information.docx`
- optional `Graphical_Abstract.png`
- `NanoMax_SUBMIT_TO_JOURNAL.zip`

### Internal research/QC
- submission audit
- session JSON
- source figures
- conceptual redraws
- Research Completion Plan
- synthetic planning previews
- `NanoMax_INTERNAL_QC_AND_RESEARCH.zip`

The internal QC/research ZIP must never be submitted as a journal package.
