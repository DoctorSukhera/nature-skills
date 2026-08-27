# NanoMax Nature Editor v10.0

Journal Discovery + Journal-Contract manuscript production + Research Completion Engine for a `nature-skills` fork.

## What changed in v10
- **Journal Discovery & Fit Engine** runs immediately after manuscript upload.
- Authors choose a publishing preference before final targeting: **Fully Open Access only**, **Hybrid only**, or **Either**.
- NanoMax ranks 3–5 Nature Portfolio journals by manuscript scope fit, study design, evidence strength, novelty and article-type compatibility.
- Journal ranking uses live first-party Nature/Springer Nature pages rather than hard-coded metrics.
- Candidate cards show current **Journal Impact Factor (JIF)**, 5-year JIF, **median submission-to-first-editorial-decision**, median submission-to-acceptance, SNIP, SJR, publishing model, APC, recommended article type and major editorial risk when those metrics are officially available.
- Acceptance rate is shown only if officially published; otherwise NanoMax reports **Not publicly reported**.
- Fit score is explicitly a scope/evidence match score, **not an acceptance probability**.
- After the author chooses a journal, the existing v9 journal-outline contract, evidence-locked manuscript builder and Research Completion Engine run as before.

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
1. Upload manuscript and optional source data/code/support files.
2. Choose **Fully Open Access only**, **Hybrid only**, or **Either**.
3. Click **Analyze journal fit + live metrics**.
4. Compare the ranked Nature Portfolio shortlist and choose the target journal/article type.
5. Run the full NanoMax journal-contract manuscript workflow.
6. Download the journal-facing package separately from internal QC/Research Completion outputs.

### Metric interpretation
`Submission to first editorial decision` is the publisher median from submission until the manuscript is either sent for peer review or rejected. It is not the duration of peer review. Journal metrics are descriptive and should not be treated as acceptance probabilities or direct measures of journal quality.
