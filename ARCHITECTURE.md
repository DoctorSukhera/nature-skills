# NanoMax Nature Editor v7.0 Architecture

## Product contract

The primary product is a **complete initial-submission manuscript**, not an editorial memo.

```text
Uploaded manuscript
      ↓
Live target-journal profile
      ↓
Vision audit of every embedded figure
      ↓
Nature Skills manuscript reconstruction
      ↓
Reference + citation web verification
      ↓
Finalization pass (safe corrections applied)
      ↓
Conceptual-figure redesign / optional graphical abstract
      ↓
Final reviewer gate
      ↓
MASTER WORD MANUSCRIPT
+ cover letter
+ optional supplementary information
+ optional graphical abstract
+ secondary QC audit
```

## Nature Skills used

- `nature-writing`: scientific narrative and section reconstruction
- `nature-polishing`: Nature-style scientific language and consistency
- `nature-reviewer`: final internal reviewer gate
- `nature-statistics`: statistical reporting and claim calibration
- `nature-citation`: citation support logic
- `nature-ref-verifier`: bibliographic verification
- `nature-academic-search`: literature/source checks
- `nature-data`: Data Availability / FAIR-oriented checks
- `nature-figure`: figure classification, redesign and publication-quality planning

## Figure integrity model

Each image is visually classified before manuscript transformation.

- Conceptual schematic → may be redrawn.
- ROC/heatmap/bar/line/confusion matrix → preserve unless real source data are available for replotting.
- Microscopy/pathology/clinical/experimental evidence → preserve; never fabricate replacement evidence.
- Unsupported text inside a graphical abstract/workflow is not treated as evidence and should be removed during redesign.

## Document assembly

The DOCX exporter creates one master file and inserts figures/tables according to `placement_after` metadata. Citation tokens `[[CITE:n]]` are converted to superscript citation runs in Word. Duplicate numerical prefixes in references are stripped before final sequential numbering.

## Safety boundary

NanoMax may deeply rewrite and redesign presentation. It may not invent missing scientific facts. Genuinely unavailable details remain in the separate author-action audit rather than appearing as reviewer-note text inside the manuscript.
