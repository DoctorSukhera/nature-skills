from __future__ import annotations
from pathlib import Path
import streamlit as st
import pandas as pd

from nanomax_editor.api import OpenAIResponsesClient
from nanomax_editor.document_io import parse_upload, count_citations
from nanomax_editor.skill_loader import load_skills, combine_skills
from nanomax_editor.workflow import NatureReadyWorkflow, WorkflowState
from nanomax_editor.exporters import (
    master_manuscript_docx_bytes, cover_letter_docx_bytes, supplementary_docx_bytes,
    report_docx_bytes, package_zip_bytes,
)

ROOT = Path(__file__).resolve().parent
APP_VERSION = "7.0"
SKILLS = [
    "nature-writing","nature-polishing","nature-reviewer","nature-statistics",
    "nature-citation","nature-ref-verifier","nature-academic-search","nature-data","nature-figure"
]

st.set_page_config(page_title="NanoMax Nature Editor", page_icon="🧬", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.2rem}.hero{padding:1.4rem 1.6rem;border:1px solid #e5e7eb;border-radius:22px;background:linear-gradient(135deg,#fbfaff,#f4f0ff);margin-bottom:1rem}.k{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;opacity:.65}.t{font-size:2.35rem;font-weight:800;line-height:1.08}.s{font-size:1.03rem;color:#4b5563;max-width:1050px}.pill{display:inline-block;padding:.25rem .6rem;border:1px solid #ddd6fe;border-radius:999px;margin:.2rem;font-size:.78rem;background:#faf8ff}
</style>
""", unsafe_allow_html=True)


def secret(name, default=""):
    try: return st.secrets.get(name, default)
    except Exception: return default


def reset_result():
    for k in ["result","redrawn","graphical_abstract"]:
        st.session_state.pop(k, None)

if "redrawn" not in st.session_state: st.session_state.redrawn = {}
if "graphical_abstract" not in st.session_state: st.session_state.graphical_abstract = None

password = secret("APP_PASSWORD")
if password:
    if "auth_ok" not in st.session_state: st.session_state.auth_ok = False
    if not st.session_state.auth_ok:
        st.title("NanoMax Nature Editor")
        entered = st.text_input("Private access password", type="password")
        if st.button("Enter"):
            if entered == password: st.session_state.auth_ok=True; st.rerun()
            else: st.error("Incorrect password")
        st.stop()

st.markdown(f"""<div class='hero'><div class='k'>NanoMax Lab • Manuscript Production Intelligence • v{APP_VERSION}</div><div class='t'>NanoMax Nature Editor</div><div class='s'>Converts a working manuscript into one complete journal-structured Word manuscript with integrated tables and figures, verified references, figure-integrity checks, a cover letter, and journal-specific submission extras.</div><div><span class='pill'>One master DOCX</span><span class='pill'>Figures + tables inline</span><span class='pill'>Vision figure audit</span><span class='pill'>Nature Skills router</span><span class='pill'>Cover letter</span><span class='pill'>Submission package</span></div></div>""", unsafe_allow_html=True)

skills = load_skills(ROOT, SKILLS)
missing = [k for k,v in skills.items() if not v]
if missing:
    st.error("Missing required Nature Skills: " + ", ".join(missing) + ". Deploy this app in the ROOT of the nature-skills fork.")
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
    live_refs = st.checkbox("Verify references/citations on the web", True)
    redraw_concepts = st.checkbox("Automatically redraw safe conceptual schematics", True, help="Only conceptual diagrams. Quantitative and experimental evidence images are not fabricated.")
    make_graphical = st.checkbox("Generate a graphical abstract when appropriate", True, help="Generated only from supported manuscript evidence; whether it belongs in the submission depends on the selected journal.")
    st.divider(); st.caption("Nature Skills loaded")
    for n in SKILLS: st.write("✓ " + n)

st.header("1. Upload manuscript")
up = st.file_uploader("DOCX preferred; PDF/TXT/Markdown supported", type=["docx","pdf","txt","md"], on_change=reset_result)
priorities = st.text_area("Author priorities (optional)", placeholder="e.g. preserve all actual results; target a strong Nature Cancer Article; improve graphical abstract; keep figures but redesign conceptual workflows")

if up:
    try:
        bundle = parse_upload(up); st.session_state.bundle = bundle
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Words", len(bundle.text.split())); c2.metric("Tables", len(bundle.tables)); c3.metric("Embedded images", len(bundle.images)); c4.metric("Citation markers", count_citations(bundle.text))
        with st.expander("Source preview"): st.text(bundle.text[:10000])
    except Exception as e:
        st.error(str(e)); st.stop()

st.header("2. Build complete journal-ready manuscript")
if st.button("Run complete Nature transformation", type="primary", disabled=not bool(up), use_container_width=True):
    bundle = st.session_state.bundle
    client = OpenAIResponsesClient(api_key, model, reasoning)
    flow = NatureReadyWorkflow(client, skill_text); state = WorkflowState(); st.session_state.state = state
    st.session_state.redrawn = {}; st.session_state.graphical_abstract = None
    try:
        with st.status("NanoMax Nature Editor is rebuilding the complete paper...", expanded=True) as status:
            st.write("1/6 — Checking current official journal instructions")
            profile = flow.journal_profile(journal=journal, article_type=article_type, state=state)
            st.write("2/6 — Inspecting every embedded figure with vision + nature-figure")
            figuraudit = flow.audit_figures(manuscript=bundle.text, images=bundle.images, journal_profile=profile, state=state)
            st.write("3/6 — Reconstructing title, abstract, paper architecture, tables, figures and declarations")
            draft = flow.transform(manuscript=bundle.text, tables=bundle.tables, figure_audit=figuraudit, journal_profile=profile, journal=journal, article_type=article_type, priorities=priorities, state=state)
            st.write("4/6 — Verifying references and citation support")
            if live_refs:
                refaudit = flow.audit_references(manuscript=bundle.text, references=draft.get("references", []), journal=journal, state=state)
            else:
                refaudit = {"summary":"Skipped by user","verified_count":0,"needs_author_check":[],"citation_support_concerns":[],"recommended_updates":[],"do_not_auto_replace":[],"verified_reference_list":draft.get("references",[]),"citation_corrections":[]}
            st.write("5/6 — Integrating verified citations and removing reviewer-note text from the manuscript")
            final = flow.finalize(draft=draft, reference_audit=refaudit, journal_profile=profile, figure_audit=figuraudit, journal=journal, article_type=article_type, state=state)

            # Automatically redraw only conceptual figures, preserving quantitative/experimental evidence.
            if redraw_concepts and bundle.images:
                conceptual_jobs = []
                for f in final.get("figure_plan",[]):
                    if f.get("action") == "redraw_conceptual":
                        for idx in f.get("source_asset_indices",[]):
                            if 1 <= idx <= len(bundle.images): conceptual_jobs.append((idx,f))
                seen=set()
                for idx,f in conceptual_jobs:
                    if idx in seen: continue
                    seen.add(idx)
                    st.write(f"   • Redrawing conceptual source asset {idx}")
                    try:
                        img=bundle.images[idx-1]
                        blob=client.edit_image(image_bytes=img["bytes"], filename=img["name"], prompt=f.get("redraw_prompt") or "Redesign this conceptual scientific schematic for a high-impact journal. Preserve supported scientific meaning; remove unsupported numerical or methodological claims; do not invent data.", image_model=secret("IMAGE_MODEL","gpt-image-2"))
                        st.session_state.redrawn[idx]=blob
                    except Exception as exc:
                        st.warning(f"Conceptual asset {idx} was preserved because automatic redraw failed: {exc}")

            ga = final.get("graphical_abstract") or {}
            if make_graphical and ga.get("recommended") and ga.get("generation_prompt"):
                st.write("   • Generating evidence-constrained graphical abstract")
                try:
                    st.session_state.graphical_abstract = client.generate_image(prompt=ga["generation_prompt"], image_model=secret("IMAGE_MODEL","gpt-image-2"))
                except Exception as exc:
                    st.warning(f"Graphical abstract generation skipped: {exc}")

            st.write("6/6 — Running final scientific/editorial submission gate")
            review = flow.review(transformed=final, journal=journal, article_type=article_type, state=state)
            status.update(label="Complete manuscript transformation finished", state="complete")
        st.session_state.result={"profile":profile,"figure_audit":figuraudit,"draft":draft,"refaudit":refaudit,"final":final,"review":review}
    except Exception as e:
        st.exception(e)

res = st.session_state.get("result")
if res:
    t=res["final"]; review=res["review"]
    st.header("3. Submission dashboard")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Readiness",f"{review.get('submission_readiness_score',0)}/100"); c2.metric("Blocking issues",len(review.get("blocking_issues",[]))); c3.metric("Author checks",len(t.get("author_actions",[]))); c4.metric("Final figures",len([f for f in t.get("figure_plan",[]) if f.get("action")!='remove_if_redundant']))
    tabs=st.tabs(["Final manuscript","Figures","Tables","References","Journal rules","Submission gate","Export"])
    with tabs[0]:
        st.subheader(t.get("title","")); fm=t.get("front_matter",{}); st.write(fm.get("authors_line","")); st.markdown("**Abstract**"); st.write(t.get("abstract",""))
        if t.get("keywords"): st.write("**Keywords:** "+", ".join(t["keywords"]))
        for sec in t.get("main_sections",[]):
            if sec.get("show_heading"): st.markdown("### "+sec.get("heading",""))
            for p in sec.get("paragraphs",[]): st.write(p)
        if t.get("methods_sections"): st.markdown("## Methods")
        for sec in t.get("methods_sections",[]):
            if sec.get("show_heading"): st.markdown("### "+sec.get("heading",""))
            for p in sec.get("paragraphs",[]): st.write(p)
    with tabs[1]:
        st.write(res["figure_audit"].get("summary",""))
        fp=t.get("figure_plan",[])
        if fp: st.dataframe(pd.DataFrame(fp),use_container_width=True,hide_index=True)
        for i,img in enumerate(st.session_state.bundle.images,1):
            with st.expander(f"Source figure asset {i}: {img['name']}"):
                shown=st.session_state.redrawn.get(i,img["bytes"])
                try: st.image(shown,use_container_width=True)
                except Exception: st.write("Preview unavailable")
                if i in st.session_state.redrawn: st.success("Conceptual figure automatically redrawn")
        if st.session_state.graphical_abstract:
            st.markdown("### Generated graphical abstract"); st.image(st.session_state.graphical_abstract,use_container_width=True)
    with tabs[2]:
        for table in t.get("tables",[]):
            st.markdown(f"### {table.get('number','')} {table.get('title','')}")
            if table.get("columns"): st.dataframe(pd.DataFrame(table.get("rows",[]),columns=table.get("columns",[])),use_container_width=True)
            st.caption(f"Destination: {table.get('destination')} • Placement: {table.get('placement_after')}")
    with tabs[3]:
        st.write(res["refaudit"].get("summary","")); st.metric("References checked",res["refaudit"].get("verified_count",0))
        for k in ["citation_corrections","needs_author_check","citation_support_concerns","recommended_updates"]:
            vals=res["refaudit"].get(k,[]) or []
            if vals:
                st.markdown("#### "+k.replace("_"," ").title())
                for x in vals: st.write("- "+x)
    with tabs[4]: st.json(res["profile"])
    with tabs[5]:
        st.metric("Editorial decision",review.get("editorial_decision",""))
        for k in ["blocking_issues","major_issues","minor_issues","strengths","final_actions"]:
            vals=review.get(k,[]) or []
            if vals:
                st.markdown("#### "+k.replace("_"," ").title())
                for x in vals: st.write("- "+x)
    with tabs[6]:
        master=master_manuscript_docx_bytes(t,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn,graphical_abstract=st.session_state.graphical_abstract)
        cover=cover_letter_docx_bytes(t,journal)
        supp=supplementary_docx_bytes(t,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn)
        report=report_docx_bytes(res["profile"],res["figure_audit"],res["refaudit"],review,t)
        zipb=package_zip_bytes(master_docx=master,cover_letter_docx=cover,report_docx=report,transformed=t,journal_profile=res["profile"],figure_audit=res["figure_audit"],reference_audit=res["refaudit"],review=review,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn,graphical_abstract=st.session_state.graphical_abstract,supplementary_docx=supp)
        st.success("PRIMARY OUTPUT: one complete Word manuscript containing the paper text, editable tables, embedded main figures/Extended Data, legends, references and declarations.")
        st.download_button("Download COMPLETE manuscript DOCX",master,"NanoMax_Nature_Editor_Final_Manuscript.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",type="primary",use_container_width=True)
        st.download_button("Download cover letter DOCX",cover,"Cover_Letter.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        if st.session_state.graphical_abstract: st.download_button("Download graphical abstract PNG",st.session_state.graphical_abstract,"Graphical_Abstract.png","image/png",use_container_width=True)
        if supp: st.download_button("Download Supplementary Information DOCX",supp,"Supplementary_Information.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        st.download_button("Download full submission package ZIP",zipb,"NanoMax_Nature_Editor_Submission_Package.zip","application/zip",use_container_width=True)
        with st.expander("Quality-control audit (secondary output)"):
            st.download_button("Download submission audit DOCX",report,"NanoMax_Submission_Audit.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if review.get("blocking_issues"):
            st.warning("The master manuscript has been fully assembled, but the submission gate still identifies author-verification items. They remain in the separate audit rather than being inserted as reviewer notes inside the manuscript.")
        else:
            st.success("No blocking issue was detected by the internal gate. Authors should still perform a final human verification before submission.")

st.caption("NanoMax Nature Editor is an independent research-group tool and is not affiliated with or endorsed by Nature Portfolio.")
