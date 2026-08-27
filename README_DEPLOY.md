# NanoMax Nature Editor v7.0 — Deployment

NanoMax Nature Editor v7 is a Streamlit overlay for the `nature-skills` repository. It turns a working manuscript into a **single master Word manuscript** with integrated figures and editable tables, plus journal-specific submission extras.

## What changed from v6

- Primary output is `NanoMax_Nature_Editor_Final_Manuscript.docx`.
- Main figures and Extended Data are embedded in the manuscript instead of exported only as loose assets.
- Tables are rebuilt as editable Word tables and placed near their target sections.
- Embedded figures are inspected with multimodal vision before restructuring.
- Conceptual diagrams can be automatically redrawn with GPT Image 2 when enabled.
- Quantitative figures are preserved as evidence unless source data are available for legitimate replotting; they are never visually invented.
- Reference verification is fed back into a finalization pass before Word export.
- Reviewer/audit warnings are kept in the audit rather than injected as `AUTHOR_INPUT_NEEDED` text into the manuscript.
- Cover letter is generated as a separate DOCX.
- Graphical abstract can be generated when appropriate/requested.
- Supplementary Information is generated when the journal-aware manuscript model moves material there.

## Required repository structure

Place these files in the ROOT of your fork:

```text
nature-skills/
├── skills/                     # keep the upstream Nature Skills intact
├── nanomax_editor/
├── streamlit_app.py
├── requirements.txt
├── README_DEPLOY.md
├── ARCHITECTURE.md
└── secrets.toml.example
```

Do not flatten `nanomax_editor/` into the root.

## Streamlit Secrets

In Streamlit Community Cloud → Manage app → Settings → Secrets:

```toml
OPENAI_API_KEY = "YOUR_REAL_API_KEY"
OPENAI_MODEL = "gpt-5.6-terra"
IMAGE_MODEL = "gpt-image-2"
APP_PASSWORD = "YOUR_PRIVATE_PASSWORD"
```

Never commit a real API key to GitHub.

## Streamlit deployment

- Repository: `DoctorSukhera/nature-skills`
- Branch: `main`
- Main file: `streamlit_app.py`

After uploading v7, reboot the app.

## Expected workflow

1. Check current official journal rules.
2. Visually inspect all embedded manuscript figures.
3. Reconstruct the manuscript through Nature Skills.
4. Verify references/citations on the web.
5. Integrate safe reference corrections and produce the final manuscript model.
6. Optionally redraw conceptual diagrams / generate graphical abstract.
7. Run the final submission gate.
8. Export one master manuscript DOCX plus cover letter and optional extras.

## Primary output

`NanoMax_Nature_Editor_Final_Manuscript.docx` should contain:

- title and authors
- affiliations and correspondence
- abstract/summary
- journal-specific article structure
- complete main text
- editable tables
- embedded main figures
- figure legends
- Methods
- Data/Code Availability
- ethics/governance statement when supported
- funding/acknowledgements
- author contributions / competing interests when supported
- references
- Extended Data in the same initial-submission Word file when appropriate

Missing author-only facts remain in the separate QC audit; the app must not fabricate them.
