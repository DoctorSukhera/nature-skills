# NanoMax Nature Editor v6.0 — Deployment

This overlay is designed to be placed in the ROOT of your fork of `Yuan1z0825/nature-skills`.

## Required root structure

```text
nature-skills/
├── skills/
│   ├── nature-writing/
│   ├── nature-polishing/
│   ├── nature-reviewer/
│   ├── nature-statistics/
│   ├── nature-citation/
│   ├── nature-ref-verifier/
│   ├── nature-academic-search/
│   ├── nature-data/
│   └── nature-figure/
├── nanomax_editor/
├── .streamlit/
├── streamlit_app.py
├── requirements.txt
└── ...
```

## Streamlit secrets

```toml
OPENAI_API_KEY = "sk-proj-..."
OPENAI_MODEL = "gpt-5.6-terra"
IMAGE_MODEL = "gpt-image-2"
APP_PASSWORD = "your-private-lab-password"
```

Never commit the real `secrets.toml` file or API key to GitHub.

## Update an existing Streamlit deployment

If the existing app already deploys `DoctorSukhera/nature-skills`, do NOT create a second app. Replace the NanoMax overlay files in the same GitHub repository, commit to `main`, then use Streamlit `Manage app -> Reboot app` if it does not restart automatically.

## Important scientific limitation

The figure engine may redesign conceptual/schematic graphics. It must not fabricate or materially alter microscopy, clinical imaging, gels, blots, histology, or other experimental evidence. Data plots should be regenerated only when source data are supplied. The submission gate will flag missing source data or scientific metadata rather than fabricate them.
