from __future__ import annotations
from pathlib import Path
import os
import streamlit as st
import pandas as pd

from nanomax_editor.api import OpenAIResponsesClient
from nanomax_editor.document_io import parse_upload, count_citations
from nanomax_editor.skill_loader import load_skills, combine_skills, manifest
from nanomax_editor.workflow import NatureReadyWorkflow, WorkflowState
from nanomax_editor.exporters import submission_docx_bytes, report_docx_bytes, package_zip_bytes

ROOT = Path(__file__).resolve().parent
APP_VERSION = "6.0"
SKILLS = [
    "nature-writing","nature-polishing","nature-reviewer","nature-statistics",
    "nature-citation","nature-ref-verifier","nature-academic-search","nature-data","nature-figure"
]

st.set_page_config(page_title="NanoMax Nature Editor", page_icon="🧬", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.2rem}.hero{padding:1.4rem 1.6rem;border:1px solid #e5e7eb;border-radius:22px;background:linear-gradient(135deg,#fbfaff,#f4f0ff);margin-bottom:1rem}.k{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;opacity:.65}.t{font-size:2.4rem;font-weight:800;line-height:1.08}.s{font-size:1.04rem;color:#4b5563;max-width:1000px}.pill{display:inline-block;padding:.25rem .6rem;border:1px solid #ddd6fe;border-radius:999px;margin:.2rem;font-size:.78rem;background:#faf8ff}div[data-testid="stMetric"]{border:1px solid #e5e7eb;padding:.65rem;border-radius:12px}
</style>""", unsafe_allow_html=True)


def secret(name, default=""):
    try: return str(st.secrets.get(name, default))
    except Exception: return os.getenv(name, default)


def require_access():
    expected = secret("APP_PASSWORD")
    if not expected: return
    if st.session_state.get("auth"): return
    st.title("NanoMax Nature Editor")
    pw = st.text_input("Lab password", type="password")
    if st.button("Enter", type="primary"):
        if pw == expected:
            st.session_state.auth = True; st.rerun()
        st.error("Incorrect password")
    st.stop()

require_access()
st.session_state.setdefault("state", WorkflowState())
st.session_state.setdefault("result", None)
st.session_state.setdefault("bundle", None)
st.session_state.setdefault("redrawn", {})

st.markdown(f"""<div class='hero'><div class='k'>NanoMax Lab • Manuscript-to-Submission Intelligence • v{APP_VERSION}</div><div class='t'>NanoMax Nature Editor</div><div class='s'>Transforms a working scientific manuscript into a journal-aware Nature-style submission package using the complete Nature Skills workflow: writing, polishing, statistics, references, citations, figures, data statements and reviewer gating.</div><div><span class='pill'>Journal-aware</span><span class='pill'>Nature Skills router</span><span class='pill'>Reference web audit</span><span class='pill'>Figure redesign plan</span><span class='pill'>Submission package ZIP</span></div></div>""", unsafe_allow_html=True)

skills = load_skills(ROOT, SKILLS)
missing = [k for k,v in skills.items() if not v]
if missing:
    st.error("Missing required Nature Skills: " + ", ".join(missing) + ". This app must be deployed in the ROOT of your nature-skills fork.")
    st.stop()
skill_text = combine_skills(skills, SKILLS)

api_key = secret("OPENAI_API_KEY")
if not api_key:
    st.error("Add OPENAI_API_KEY in Streamlit → Manage app → Settings → Secrets."); st.stop()

with st.sidebar:
    st.header("Target submission")
    journal = st.selectbox("Journal", ["Nature","Nature Communications","Nature Biomedical Engineering","Nature Machine Intelligence","Nature Nanotechnology","Nature Cancer","npj Digital Medicine","Scientific Reports","Other Nature Portfolio journal"])
    if journal == "Other Nature Portfolio journal": journal = st.text_input("Exact journal name", placeholder="e.g. Nature Medicine")
    article_type = st.selectbox("Article type", ["Article","Research Article","Brief Communication","Methods / Resource","Review","Perspective","Other"])
    model = st.selectbox("Editorial model", ["gpt-5.6-terra","gpt-5.6-sol","gpt-5.6-luna"], index=0)
    reasoning = st.select_slider("Reasoning", options=["medium","high","xhigh"], value="high")
    auto_ref = st.checkbox("Run live reference/citation audit", True)
    auto_fig = st.checkbox("Allow conceptual figure redrawing", False, help="Only conceptual/schematic figures. Experimental evidence images are never regenerated. Data plots require source data.")
    st.divider()
    st.caption("Nature Skills loaded")
    for n in SKILLS: st.write("✓ " + n)

st.header("1. Upload source manuscript")
up = st.file_uploader("DOCX preferred; PDF/TXT/Markdown supported", type=["docx","pdf","txt","md"])
priorities = st.text_area("Author priorities (optional)", placeholder="e.g. target Nature Communications; preserve all numerical results; strengthen novelty framing; reduce length")

if up:
    try:
        bundle = parse_upload(up); st.session_state.bundle = bundle
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Words", len(bundle.text.split()))
        c2.metric("Tables", len(bundle.tables))
        c3.metric("Embedded images", len(bundle.images))
        c4.metric("Citation markers", count_citations(bundle.text))
        with st.expander("Source preview"): st.text(bundle.text[:10000])
    except Exception as e:
        st.error(str(e)); st.stop()

st.header("2. Build Nature-ready package")
if st.button("Run complete Nature transformation", type="primary", disabled=not bool(up), use_container_width=True):
    bundle = st.session_state.bundle
    client = OpenAIResponsesClient(api_key, model, reasoning)
    flow = NatureReadyWorkflow(client, skill_text)
    state = WorkflowState(); st.session_state.state = state
    try:
        with st.status("NanoMax Nature Editor is rebuilding the manuscript...", expanded=True) as status:
            st.write("1/4 — Checking current official journal instructions")
            profile = flow.journal_profile(journal=journal, article_type=article_type, state=state)
            st.write("2/4 — Routing through writing, polishing, statistics, data and figure skills")
            transformed = flow.transform(manuscript=bundle.text, tables=bundle.tables, journal_profile=profile, journal=journal, article_type=article_type, priorities=priorities, state=state)
            st.write("3/4 — Auditing references and citation support")
            refaudit = flow.audit_references(manuscript=bundle.text, references=transformed.get("references", []), journal=journal, state=state) if auto_ref else {"summary":"Skipped by user","verified_count":0,"needs_author_check":[],"citation_support_concerns":[],"recommended_updates":[],"do_not_auto_replace":[]}
            st.write("4/4 — Running final reviewer/submission gate")
            review = flow.review(transformed=transformed, journal=journal, article_type=article_type, state=state)
            status.update(label="Nature transformation complete", state="complete")
        st.session_state.result = {"profile":profile,"transformed":transformed,"refaudit":refaudit,"review":review}
    except Exception as e:
        st.exception(e)

res = st.session_state.result
if res:
    t = res["transformed"]; review=res["review"]
    st.header("3. Submission dashboard")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Readiness", f"{review.get('submission_readiness_score',0)}/100")
    c2.metric("Blocking issues", len(review.get("blocking_issues",[])))
    c3.metric("Author actions", len(t.get("author_actions",[])))
    c4.metric("Figures planned", len(t.get("figure_plan",[])))
    tabs = st.tabs(["Journal rules","Rebuilt manuscript","Tables","Figures","References","Reviewer gate","Export"])
    with tabs[0]: st.json(res["profile"])
    with tabs[1]:
        st.subheader(t.get("title","")); st.markdown("**Abstract**"); st.write(t.get("abstract",""))
        if t.get("keywords"): st.write("**Keywords:** " + ", ".join(t["keywords"]))
        for sec in t.get("main_sections",[]): st.markdown("### "+sec.get("heading","")); st.write(sec.get("text",""))
        if t.get("methods_sections"): st.markdown("## Methods")
        for sec in t.get("methods_sections",[]): st.markdown("### "+sec.get("heading","")); st.write(sec.get("text",""))
    with tabs[2]:
        for table in t.get("tables",[]):
            st.markdown(f"### {table.get('number','')} {table.get('title','')}")
            if table.get("columns"): st.dataframe(pd.DataFrame(table.get("rows",[]), columns=table.get("columns",[])), use_container_width=True)
            st.caption(table.get("footnote",""))
    with tabs[3]:
        st.info("Conceptual diagrams can be redesigned. Data plots should be regenerated only from source data; experimental/microscopy/clinical images are preserved as evidence.")
        fp = t.get("figure_plan",[])
        if fp: st.dataframe(pd.DataFrame(fp), use_container_width=True, hide_index=True)
        bundle = st.session_state.bundle
        if bundle and bundle.images:
            for i,img in enumerate(bundle.images,1):
                with st.expander(f"Source image asset {i}: {img['name']}"):
                    try: st.image(img["bytes"], use_container_width=True)
                    except Exception: st.write("Preview unavailable")
                    plan = fp[i-1] if i-1 < len(fp) else None
                    if auto_fig and plan and plan.get("action") == "redraw_conceptual":
                        if st.button(f"Redraw conceptual asset {i}", key=f"redraw_{i}"):
                            prompt = plan.get("redraw_prompt") or "Redesign this scientific conceptual diagram in a clean, publication-grade Nature-style visual language. Preserve scientific labels and meaning. Do not invent data."
                            try:
                                with st.spinner("Redrawing with GPT Image 2..."):
                                    blob = OpenAIResponsesClient(api_key, model, reasoning).edit_image(image_bytes=img["bytes"], filename=img["name"], prompt=prompt, image_model=secret("IMAGE_MODEL","gpt-image-2"))
                                name=f"FigureAsset_{i}_redrawn.png"; st.session_state.redrawn[name]=blob; st.image(blob, use_container_width=True); st.success("Redrawn conceptual figure created")
                            except Exception as e: st.error(str(e))
    with tabs[4]:
        st.write(res["refaudit"].get("summary",""))
        st.metric("Verified / checked", res["refaudit"].get("verified_count",0))
        for k in ["needs_author_check","citation_support_concerns","recommended_updates","do_not_auto_replace"]:
            if res["refaudit"].get(k):
                st.markdown("#### "+k.replace("_"," ").title())
                for x in res["refaudit"][k]: st.write("- "+x)
    with tabs[5]:
        st.metric("Editorial decision", review.get("editorial_decision",""))
        for k in ["blocking_issues","major_issues","minor_issues","strengths","final_actions"]:
            st.markdown("#### "+k.replace("_"," ").title())
            for x in review.get(k,[]): st.write("- "+x)
    with tabs[6]:
        mdoc = submission_docx_bytes(t)
        rdoc = report_docx_bytes(res["profile"],res["refaudit"],review,t)
        zipb = package_zip_bytes(manuscript_docx=mdoc, report_docx=rdoc, transformed=t, journal_profile=res["profile"], reference_audit=res["refaudit"], review=review, source_images=st.session_state.bundle.images, redrawn_images=st.session_state.redrawn)
        st.download_button("Download rebuilt manuscript DOCX", mdoc, "NanoMax_Nature_Ready_Manuscript.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download submission audit DOCX", rdoc, "NanoMax_Submission_Audit.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Download complete submission package ZIP", zipb, "NanoMax_Nature_Editor_Submission_Package.zip", "application/zip", type="primary")
        if review.get("blocking_issues"):
            st.warning("This package is NOT yet truthfully submission-ready because blocking author actions remain. Resolve those items and run the manuscript again.")
        else:
            st.success("The internal submission gate found no blocking issue. Authors must still verify the complete file before journal submission.")

st.caption("NanoMax Nature Editor is an independent research-group tool and is not affiliated with or endorsed by Nature Portfolio.")
