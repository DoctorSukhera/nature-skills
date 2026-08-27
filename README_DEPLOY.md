# NanoMax Nature Editor v9.0

Journal-contract manuscript production + Research Completion Engine for a `nature-skills` fork.

## What changed in v9
- The selected journal/article type generates a live **binding outline contract**.
- Heading visibility and subheading permissions are enforced (e.g. unheaded Introduction, topical Results, unsubheaded Discussion, exact Methods/Online Methods wording when specified).
- DOCX export no longer hard-codes a generic `Methods` parent heading.
- Conceptual figure redraws use a strict scientific `content_lock` whitelist.
- The **Research Completion Engine** proposes missing experiments/analyses separately from the submission paper.
- Optional synthetic previews are permanently labelled as hypothetical and are excluded from submission files.
- Exports are split into **SUBMIT TO JOURNAL** and **INTERNAL QC + RESEARCH** packages.

## Deploy
Place this overlay at the root of your fork so the repository contains:

```text
skills/
nanomax_editor/
streamlit_app.py
requirements.txt
```

Keep the original `skills/` directory intact.

Streamlit settings:
- Repository: your `nature-skills` fork
- Branch: `main`
- Main file: `streamlit_app.py`

Secrets:

```toml
OPENAI_API_KEY = "YOUR_KEY"
OPENAI_MODEL = "gpt-5.6-terra"
IMAGE_MODEL = "gpt-image-2"
APP_PASSWORD = "YOUR_PRIVATE_PASSWORD"
```

Never commit the real API key.

## Recommended workflow
Upload the manuscript plus any available source data, notebooks/code, Supplementary Information, model configuration, data dictionaries and result tables. Choose the exact target journal/article type and run `Submission + Research Completion`.

The primary manuscript remains evidence locked. Synthetic previews are research-planning artifacts only.
