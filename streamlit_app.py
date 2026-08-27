from __future__ import annotations
from pathlib import Path
from io import BytesIO
import re
import streamlit as st
import pandas as pd

from nanomax_editor.api import OpenAIResponsesClient
from nanomax_editor.document_io import parse_upload, parse_support_uploads, count_citations
from nanomax_editor.skill_loader import load_skills, combine_skills
from nanomax_editor.workflow import NatureReadyWorkflow, WorkflowState
from nanomax_editor.exporters import (
    master_manuscript_docx_bytes, cover_letter_docx_bytes, supplementary_docx_bytes,
    report_docx_bytes, research_completion_docx_bytes, submission_zip_bytes,
    internal_qc_zip_bytes,
)

ROOT = Path(__file__).resolve().parent
APP_VERSION = "10.0"
SKILLS = [
    "nature-writing","nature-polishing","nature-reviewer","nature-statistics",
    "nature-citation","nature-ref-verifier","nature-academic-search","nature-data","nature-figure"
]

st.set_page_config(page_title="NanoMax Nature Editor", page_icon="🧬", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.2rem}.hero{padding:1.4rem 1.6rem;border:1px solid #e5e7eb;border-radius:22px;background:linear-gradient(135deg,#fbfaff,#f4f0ff);margin-bottom:1rem}.k{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;opacity:.65}.t{font-size:2.35rem;font-weight:800;line-height:1.08}.s{font-size:1.03rem;color:#4b5563;max-width:1100px}.pill{display:inline-block;padding:.25rem .6rem;border:1px solid #ddd6fe;border-radius:999px;margin:.2rem;font-size:.78rem;background:#faf8ff}.warnbox{padding:.8rem 1rem;border-left:4px solid #7c3aed;background:#faf8ff;border-radius:8px}
</style>
""", unsafe_allow_html=True)


def secret(name, default=""):
    try: return st.secrets.get(name, default)
    except Exception: return default


def preview_text(text: str) -> str:
    text = str(text or "").replace("\\<", "<").replace("\\>", ">")
    text = re.sub(r"</?(?:b|strong|i|em|span)[^>]*>", "", text, flags=re.I)
    text = text.replace("**", "")
    return re.sub(r"\[\[CITE:([0-9,\-–\s]+)\]\]", lambda m: "["+m.group(1).replace("–","-")+"]", text)


def reset_result():
    for k in ["result","redrawn","graphical_abstract","synthetic_previews","journal_discovery","selected_journal","selected_article_type"]:
        st.session_state.pop(k, None)


def add_simulated_banner(blob: bytes) -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont
        im=Image.open(BytesIO(blob)).convert("RGB")
        h=max(60, int(im.height*0.085))
        canvas=Image.new("RGB", (im.width, im.height+h), "white")
        canvas.paste(im,(0,h))
        draw=ImageDraw.Draw(canvas)
        text="SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE"
        font=ImageFont.load_default()
        bbox=draw.textbbox((0,0),text,font=font)
        x=max(8,(im.width-(bbox[2]-bbox[0]))//2); y=max(8,(h-(bbox[3]-bbox[1]))//2)
        draw.text((x,y),text,fill="black",font=font)
        out=BytesIO(); canvas.save(out,"PNG"); return out.getvalue()
    except Exception:
        return blob


for k,default in [("redrawn",{}),("graphical_abstract",None),("synthetic_previews",{})]:
    if k not in st.session_state: st.session_state[k]=default

password = secret("APP_PASSWORD")
if password:
    if "auth_ok" not in st.session_state: st.session_state.auth_ok=False
    if not st.session_state.auth_ok:
        st.title("NanoMax Nature Editor")
        entered=st.text_input("Private access password",type="password")
        if st.button("Enter"):
            if entered==password: st.session_state.auth_ok=True; st.rerun()
            else: st.error("Incorrect password")
        st.stop()

st.markdown(f"""<div class='hero'><div class='k'>NanoMax Lab • Journal Discovery + Journal-Contract Production + Research Completion • v{APP_VERSION}</div><div class='t'>NanoMax Nature Editor</div><div class='s'>First ranks suitable Nature Portfolio journals from the uploaded manuscript using live scope, publishing-model and journal-metric data. After the author chooses a target, NanoMax builds an evidence-locked manuscript using that journal's exact live outline and heading/subheading rules. A separate Research Completion Engine designs missing experiments/analyses and clearly labelled synthetic previews for planning only.</div><div><span class='pill'>AI journal finder</span><span class='pill'>OA / Hybrid filter</span><span class='pill'>Live journal metrics</span><span class='pill'>Exact journal outline</span><span class='pill'>One master DOCX</span><span class='pill'>Evidence-locked submission</span><span class='pill'>Nature Skills router</span><span class='pill'>Experiment designer</span><span class='pill'>Synthetic Preview Lab</span></div></div>""",unsafe_allow_html=True)

skills=load_skills(ROOT,SKILLS)
missing=[k for k,v in skills.items() if not v]
if missing:
    st.error("Missing required Nature Skills: "+", ".join(missing)+". Deploy this app in the ROOT of the nature-skills fork.")
    st.stop()
skill_text=combine_skills(skills,SKILLS)

api_key=secret("OPENAI_API_KEY")
if not api_key:
    st.error("Add OPENAI_API_KEY in Streamlit → Manage app → Settings → Secrets."); st.stop()

with st.sidebar:
    st.header("Publishing strategy")
    publishing_preference=st.selectbox(
        "Publishing preference",
        ["Either", "Fully Open Access only", "Hybrid only"],
        help="Fully Open Access = every research article is immediately OA. Hybrid = subscription journal with an optional Gold OA route for eligible primary research."
    )
    manual_journal_mode=st.checkbox("Choose target journal manually",False)
    manual_journal=""; manual_article_type="Article"
    if manual_journal_mode:
        manual_journal=st.selectbox("Manual journal",["Nature","Nature Communications","Nature Biomedical Engineering","Nature Machine Intelligence","Nature Nanotechnology","Nature Cancer","npj Precision Oncology","npj Digital Medicine","Scientific Reports","Other Nature Portfolio journal"])
        if manual_journal=="Other Nature Portfolio journal": manual_journal=st.text_input("Exact journal name",placeholder="e.g. Nature Medicine")
        manual_article_type=st.selectbox("Article type",["Article","Research Article","Brief Communication","Methods / Resource","Review","Perspective","Other"])
    st.divider()
    st.header("Production settings")
    model=st.selectbox("Editorial model",["gpt-5.6-terra","gpt-5.6-sol","gpt-5.6-luna"],index=0)
    reasoning=st.select_slider("Reasoning",options=["medium","high","xhigh"],value="high")
    workflow_mode=st.radio("Workflow",["Submission + Research Completion","Submission only"],index=0)
    live_refs=st.checkbox("Verify references/citations on the web",True)
    redraw_concepts=st.checkbox("Automatically redraw safe conceptual schematics",True,help="Conceptual diagrams only, using a strict evidence content-lock. Quantitative/experimental evidence is not fabricated.")
    make_graphical=st.checkbox("Generate a graphical abstract when appropriate",True)
    st.divider(); st.caption("Nature Skills loaded")
    for n in SKILLS: st.write("✓ "+n)

st.header("1. Upload manuscript and evidence")
up=st.file_uploader("DOCX preferred; PDF/TXT/Markdown supported",type=["docx","pdf","txt","md"],on_change=reset_result)
support_files=st.file_uploader(
    "Supporting evidence (recommended)",
    type=["docx","pdf","txt","md","csv","xlsx","xls","json","py","r","ipynb","yaml","yml"],
    accept_multiple_files=True,
    help="Upload source data, notebooks/code, supplementary information, model settings, data dictionaries, analysis results and methods records. NanoMax searches these before declaring evidence missing.",on_change=reset_result)
priorities=st.text_area("Author priorities (optional)",placeholder="e.g. prioritize realistic journal fit; preserve all valid analyses; minimize APC; improve conceptual figures")

if up:
    try:
        bundle=parse_upload(up); st.session_state.bundle=bundle
        support_context=parse_support_uploads(support_files); st.session_state.support_context=support_context
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Words",len(bundle.text.split())); c2.metric("Tables",len(bundle.tables)); c3.metric("Embedded images",len(bundle.images)); c4.metric("Citation markers",count_citations(bundle.text))
        with st.expander("Source preview"): st.text(bundle.text[:10000])
        if support_files: st.caption(f"Supporting files loaded: {len(support_files)} • evidence context: {len(support_context):,} characters")
    except Exception as e:
        st.error(str(e)); st.stop()

st.header("2. Discover and choose the target Nature Portfolio journal")

journal=""; article_type="Article"
if manual_journal_mode:
    journal=manual_journal; article_type=manual_article_type
    st.info(f"Manual targeting enabled: **{journal} — {article_type}**. NanoMax will still retrieve its live official outline before production.")
else:
    if st.button("Analyze journal fit + live metrics",disabled=not bool(up),use_container_width=True):
        client=OpenAIResponsesClient(api_key,model,reasoning)
        flow=NatureReadyWorkflow(client,skill_text); discovery_state=WorkflowState()
        try:
            with st.status("NanoMax is comparing Nature Portfolio journals...",expanded=True) as ds:
                st.write("• Profiling manuscript topic, design, evidence strength and novelty")
                st.write("• Applying Open Access / Hybrid preference")
                st.write("• Checking official journal scope, article types, Journal Impact Factor, editorial speed and APC")
                discovery=flow.recommend_journals(
                    manuscript=st.session_state.bundle.text,
                    publishing_preference=publishing_preference,
                    support_context=st.session_state.get("support_context",""),
                    priorities=priorities,
                    state=discovery_state,
                )
                st.session_state.journal_discovery=discovery
                if discovery.get("candidates"):
                    top=sorted(discovery["candidates"],key=lambda x:x.get("rank",999))[0]
                    st.session_state.selected_journal=top.get("journal","")
                    st.session_state.selected_article_type=top.get("recommended_article_type","Article")
                ds.update(label="Journal-fit analysis complete",state="complete")
        except Exception as exc:
            st.exception(exc)

    discovery=st.session_state.get("journal_discovery")
    if discovery:
        mp=discovery.get("manuscript_profile",{})
        st.write(discovery.get("recommendation_summary",""))
        st.caption(discovery.get("ranking_note","Fit score is a scope/evidence match score, not an acceptance probability."))
        if mp:
            c1,c2,c3=st.columns(3)
            c1.metric("Primary field",mp.get("primary_field","—")); c2.metric("Study type",mp.get("study_type","—")); c3.metric("Evidence level",mp.get("evidence_level","—"))
        candidates=sorted(discovery.get("candidates",[]),key=lambda x:x.get("rank",999))
        if candidates:
            rows=[]
            for c in candidates:
                rows.append({
                    "Rank":c.get("rank"),"Journal":c.get("journal"),"Fit":f"{c.get('fit_score',0)}/100",
                    "Access":"Fully OA" if c.get("access_model")=="fully_open_access" else ("Hybrid" if c.get("access_model")=="hybrid" else "Unknown"),
                    "Article type":c.get("recommended_article_type"),
                    "JIF":f"{c.get('impact_factor',0):g}" if c.get("impact_factor",0) else "—",
                    "JIF year":c.get("impact_factor_year") or "—",
                    "First editorial decision (median days)":c.get("first_editorial_decision_days") or "—",
                    "Submission → acceptance (median days)":c.get("submission_to_acceptance_days") or "—",
                    "APC":c.get("apc") or "—",
                    "Acceptance rate":c.get("acceptance_rate") or "Not publicly reported",
                })
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            st.caption("‘First editorial decision’ is the publisher median from submission until the paper is either sent for peer review or rejected; it is not peer-review duration. Journal Impact Factor and speed are descriptive metrics, not measures of manuscript quality or acceptance probability.")
            labels=[f"{c['rank']}. {c['journal']} — Fit {c.get('fit_score',0)}/100 — {'Fully OA' if c.get('access_model')=='fully_open_access' else ('Hybrid' if c.get('access_model')=='hybrid' else 'Access unverified')}" for c in candidates]
            current=st.session_state.get("selected_journal",candidates[0].get("journal"))
            idx=next((i for i,c in enumerate(candidates) if c.get("journal")==current),0)
            chosen_label=st.radio("Choose target journal",labels,index=idx)
            chosen=candidates[labels.index(chosen_label)]
            st.session_state.selected_journal=chosen.get("journal","")
            recommended_type=chosen.get("recommended_article_type","Article")
            article_options=[]
            for x in [recommended_type,"Article","Research Article","Brief Communication","Methods / Resource","Review","Perspective","Other"]:
                if x and x not in article_options: article_options.append(x)
            article_type=st.selectbox("Article type for production",article_options,index=0,key="discovery_article_type")
            st.session_state.selected_article_type=article_type
            journal=chosen.get("journal","")
            st.success(f"Selected target: **{journal} — {article_type}**")
            st.write("**Why it fits:** "+chosen.get("fit_rationale",""))
            if chosen.get("main_risk"): st.warning("Main editorial risk: "+chosen.get("main_risk",""))
            with st.expander("Official sources and full journal metrics"):
                st.write("Publishing model: "+chosen.get("publishing_options",""))
                st.write(f"5-year JIF: {chosen.get('five_year_impact_factor',0) or '—'} • SNIP: {chosen.get('snip',0) or '—'} • SJR: {chosen.get('sjr',0) or '—'}")
                st.write("Metrics checked: "+chosen.get("metrics_checked_date",""))
                for url in chosen.get("official_sources",[]): st.write(url)
    else:
        st.info("Upload the manuscript, choose Open Access / Hybrid preference, then run **Analyze journal fit + live metrics**. You can also enable manual journal selection in the sidebar.")

if not journal and not manual_journal_mode:
    journal=st.session_state.get("selected_journal","")
    article_type=st.session_state.get("selected_article_type","Article")

st.header("3. Build journal-contract manuscript")
can_build=bool(up and journal)
if st.button("Run NanoMax full workflow",type="primary",disabled=not can_build,use_container_width=True):
    bundle=st.session_state.bundle
    client=OpenAIResponsesClient(api_key,model,reasoning)
    flow=NatureReadyWorkflow(client,skill_text); state=WorkflowState(); st.session_state.state=state
    st.session_state.redrawn={}; st.session_state.graphical_abstract=None; st.session_state.synthetic_previews={}
    try:
        total=7 if workflow_mode.startswith("Submission +") else 6
        with st.status(f"NanoMax is building the {journal} manuscript...",expanded=True) as status:
            st.write(f"1/{total} — Retrieving current official {journal} / {article_type} rules and exact outline")
            profile=flow.journal_profile(journal=journal,article_type=article_type,state=state)
            st.write(f"2/{total} — Inspecting embedded figures with vision + nature-figure")
            figuraudit=flow.audit_figures(manuscript=bundle.text,images=bundle.images,journal_profile=profile,state=state)
            st.write(f"3/{total} — Recovering evidence and rebuilding paper to the exact journal outline")
            draft=flow.transform(manuscript=bundle.text,tables=bundle.tables,figure_audit=figuraudit,journal_profile=profile,journal=journal,article_type=article_type,priorities=priorities,support_context=st.session_state.get("support_context",""),state=state)
            st.write(f"4/{total} — Verifying references and claim-to-citation support")
            if live_refs:
                refaudit=flow.audit_references(manuscript=bundle.text,references=draft.get("references",[]),journal=journal,state=state)
            else:
                refaudit={"summary":"Skipped by user","verified_count":0,"needs_author_check":[],"citation_support_concerns":[],"recommended_updates":[],"do_not_auto_replace":[],"verified_reference_list":draft.get("references",[]),"citation_corrections":[]}
            st.write(f"5/{total} — Finalizing headings/subheadings, citations, figures, tables and declarations")
            final=flow.finalize(draft=draft,reference_audit=refaudit,journal_profile=profile,figure_audit=figuraudit,journal=journal,article_type=article_type,support_context=st.session_state.get("support_context",""),state=state)

            if redraw_concepts and bundle.images:
                seen=set()
                for f in final.get("figure_plan",[]):
                    if f.get("action")!="redraw_conceptual": continue
                    lock=f.get("content_lock",[]) or []
                    for idx in f.get("source_asset_indices",[]):
                        if idx in seen or not (1<=idx<=len(bundle.images)): continue
                        seen.add(idx); st.write(f"   • Redrawing conceptual source asset {idx} under evidence lock")
                        try:
                            img=bundle.images[idx-1]
                            whitelist="\n".join(f"- {x}" for x in lock) or "- Preserve only content clearly supported by the source manuscript."
                            prompt=(f.get("redraw_prompt") or "Redesign this conceptual scientific schematic for a high-impact journal.")+f"\n\nSTRICT SCIENTIFIC CONTENT WHITELIST:\n{whitelist}\n\nDo not add any algorithm, analysis, sample number, numerical result, method, label or claim outside this whitelist. If uncertain, omit it. This is a scientific layout redesign, not a content-generation task."
                            st.session_state.redrawn[idx]=client.edit_image(image_bytes=img["bytes"],filename=img["name"],prompt=prompt,image_model=secret("IMAGE_MODEL","gpt-image-2"))
                        except Exception as exc:
                            st.warning(f"Conceptual asset {idx} preserved because redraw failed: {exc}")

            ga=final.get("graphical_abstract") or {}
            if make_graphical and ga.get("recommended") and ga.get("generation_prompt"):
                st.write("   • Generating evidence-constrained graphical abstract")
                try:
                    st.session_state.graphical_abstract=client.generate_image(prompt=ga["generation_prompt"]+"\nDo not invent numerical results, sample counts, analyses or methods not explicitly supported by the manuscript.",image_model=secret("IMAGE_MODEL","gpt-image-2"))
                except Exception as exc: st.warning(f"Graphical abstract generation skipped: {exc}")

            st.write(f"6/{total} — Running scientific/editorial/outline submission gate")
            review=flow.review(transformed=final,journal=journal,article_type=article_type,state=state)
            research=None
            if total==7:
                st.write("7/7 — Designing missing experiments/analyses in a separate Research Completion Engine")
                research=flow.research_completion(transformed=final,review=review,journal_profile=profile,figure_audit=figuraudit,support_context=st.session_state.get("support_context",""),state=state)
            status.update(label="NanoMax workflow finished",state="complete")
        st.session_state.result={"journal":journal,"article_type":article_type,"journal_discovery":st.session_state.get("journal_discovery"),"profile":profile,"figure_audit":figuraudit,"draft":draft,"refaudit":refaudit,"final":final,"review":review,"research":research}
    except Exception as e:
        st.exception(e)

res=st.session_state.get("result")
if res:
    t=res["final"]; review=res["review"]; research=res.get("research")
    journal=res.get("journal",journal); article_type=res.get("article_type",article_type)
    st.header("4. Submission dashboard")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Readiness",f"{review.get('submission_readiness_score',0)}/100")
    c2.metric("Blocking issues",len(review.get("blocking_issues",[])))
    c3.metric("Author checks",len(t.get("author_actions",[])))
    c4.metric("Outline", "PASS" if (t.get("outline_validation") or {}).get("compliant") else "CHECK")
    tabs=st.tabs(["Final manuscript","Journal outline","Figures","Tables","References","Submission gate","Research completion","Export"])

    with tabs[0]:
        st.subheader(preview_text(t.get("title",""))); fm=t.get("front_matter",{}); st.write(preview_text(fm.get("authors_line","")))
        st.markdown("**Abstract**"); st.write(preview_text(t.get("abstract","")))
        if t.get("keywords"): st.write("**Keywords:** "+", ".join(preview_text(x) for x in t["keywords"]))
        for sec in t.get("main_sections",[]):
            if sec.get("show_heading") and sec.get("heading"): st.markdown("#"*max(2,min(4,int(sec.get("heading_level",1))+1))+" "+preview_text(sec.get("heading","")))
            for p in sec.get("paragraphs",[]): st.write(preview_text(p))
        if t.get("methods_sections"):
            if t.get("methods_parent_show_heading",True) and t.get("methods_parent_heading"): st.markdown("## "+preview_text(t.get("methods_parent_heading")))
            for sec in t.get("methods_sections",[]):
                if sec.get("show_heading") and sec.get("heading"): st.markdown("### "+preview_text(sec.get("heading","")))
                for p in sec.get("paragraphs",[]): st.write(preview_text(p))

    with tabs[1]:
        st.markdown("### Binding journal outline contract")
        outline=res["profile"].get("outline_contract",[])
        if outline: st.dataframe(pd.DataFrame(outline).sort_values("position"),use_container_width=True,hide_index=True)
        ov=t.get("outline_validation") or {}; st.metric("Outline compliance","PASS" if ov.get("compliant") else "CHECK")
        if ov.get("deviations"):
            for x in ov["deviations"]: st.warning(x)
        st.caption("The exporter uses the journal's Methods parent heading and declaration order rather than a hard-coded generic outline.")

    with tabs[2]:
        st.write(res["figure_audit"].get("summary",""))
        fp=t.get("figure_plan",[])
        if fp: st.dataframe(pd.DataFrame(fp),use_container_width=True,hide_index=True)
        for i,img in enumerate(st.session_state.bundle.images,1):
            with st.expander(f"Source figure asset {i}: {img['name']}"):
                shown=st.session_state.redrawn.get(i,img["bytes"])
                try: st.image(shown,use_container_width=True)
                except Exception: st.write("Preview unavailable")
                if i in st.session_state.redrawn: st.success("Conceptual figure redrawn under evidence content-lock")
        if st.session_state.graphical_abstract:
            st.markdown("### Generated graphical abstract"); st.image(st.session_state.graphical_abstract,use_container_width=True)

    with tabs[3]:
        for table in t.get("tables",[]):
            st.markdown(f"### {table.get('number','')} {table.get('title','')}")
            if table.get("columns"): st.dataframe(pd.DataFrame(table.get("rows",[]),columns=table.get("columns",[])),use_container_width=True)
            st.caption(f"Destination: {table.get('destination')} • Placement: {table.get('placement_after')}")

    with tabs[4]:
        st.write(res["refaudit"].get("summary","")); st.metric("References checked",res["refaudit"].get("verified_count",0))
        for k in ["citation_corrections","needs_author_check","citation_support_concerns","recommended_updates"]:
            vals=res["refaudit"].get(k,[]) or []
            if vals:
                st.markdown("#### "+k.replace("_"," ").title())
                for x in vals: st.write("- "+x)

    with tabs[5]:
        st.metric("Editorial decision",review.get("editorial_decision",""))
        for k in ["blocking_issues","major_issues","minor_issues","strengths","final_actions"]:
            vals=review.get(k,[]) or []
            if vals:
                st.markdown("#### "+k.replace("_"," ").title())
                for x in vals: st.write("- "+x)

    with tabs[6]:
        if not research:
            st.info("Research Completion Engine was not run. Select 'Submission + Research Completion' in the sidebar and rerun if desired.")
        else:
            st.markdown("<div class='warnbox'><b>Research Completion outputs are planning artifacts. Synthetic previews are never experimental evidence and are never inserted into the submission manuscript.</b></div>",unsafe_allow_html=True)
            st.write(research.get("summary",""))
            gaps=research.get("gaps",[]) or []
            for g in gaps:
                with st.expander(f"{g.get('gap_id')} — {g.get('priority','').upper()} — {g.get('missing_evidence','')[:100]}"):
                    st.write("**Why needed:**",g.get("why_needed","")); st.write("**Proposed experiment/analysis:**",g.get("proposed_experiment_or_analysis",""))
                    for label,key in [("Required inputs","required_inputs"),("Protocol","protocol_steps"),("Controls","controls"),("Statistical plan","statistical_plan"),("Expected real outputs","real_output_expected")]:
                        vals=g.get(key,[]) or []
                        if vals: st.write("**"+label+":**"); [st.write("- "+x) for x in vals]
                    st.write("**Claim potentially supported if real evidence succeeds:**",g.get("claim_unlocked_if_real",""))
                    st.caption("Synthetic preview type: "+g.get("synthetic_preview_type","none"))
            previewable=[g for g in gaps if g.get("synthetic_preview_type")!="none" and g.get("synthetic_preview_prompt")]
            if previewable and st.button("Generate up to 3 clearly-labelled synthetic previews",use_container_width=True):
                client=OpenAIResponsesClient(api_key,model,reasoning); created={}
                for g in previewable[:3]:
                    try:
                        prompt=g["synthetic_preview_prompt"]+"\nThis is a planning visualization only. Include a prominent header: SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE. Do not imitate a real patient-specific or experiment-specific record."
                        blob=client.generate_image(prompt=prompt,image_model=secret("IMAGE_MODEL","gpt-image-2"))
                        created[g["gap_id"]]=add_simulated_banner(blob)
                    except Exception as exc: st.warning(f"Preview {g.get('gap_id')} failed: {exc}")
                st.session_state.synthetic_previews.update(created); st.rerun()
            for key,blob in st.session_state.synthetic_previews.items():
                st.markdown(f"#### Synthetic preview — {key}"); st.image(blob,use_container_width=True); st.warning("SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE")

    with tabs[7]:
        master=master_manuscript_docx_bytes(t,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn,graphical_abstract=st.session_state.graphical_abstract,journal_profile=res["profile"])
        cover=cover_letter_docx_bytes(t,journal)
        supp=supplementary_docx_bytes(t,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn)
        report=report_docx_bytes(res["profile"],res["figure_audit"],res["refaudit"],review,t)
        research_doc=research_completion_docx_bytes(research) if research else None
        submit_zip=submission_zip_bytes(master_docx=master,cover_letter_docx=cover,supplementary_docx=supp,graphical_abstract=st.session_state.graphical_abstract)
        qc_zip=internal_qc_zip_bytes(report_docx=report,transformed=t,journal_profile=res["profile"],figure_audit=res["figure_audit"],reference_audit=res["refaudit"],review=review,source_images=st.session_state.bundle.images,redrawn_images=st.session_state.redrawn,research_plan_docx=research_doc,research_plan=research,synthetic_previews=st.session_state.synthetic_previews)
        if review.get("blocking_issues"):
            st.info("The manuscript is fully assembled to the journal outline, but unresolved scientific facts remain. NanoMax keeps those issues outside the manuscript and provides a Research Completion Plan when enabled.")
        else: st.success("No blocking issue was detected by the internal gate. Authors should still perform a final human verification before submission.")
        st.download_button("Download COMPLETE manuscript DOCX",master,"NanoMax_Nature_Editor_Final_Manuscript.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",type="primary",use_container_width=True)
        st.download_button("Download JOURNAL-SUBMISSION files ZIP",submit_zip,"NanoMax_SUBMIT_TO_JOURNAL.zip","application/zip",use_container_width=True)
        st.download_button("Download cover letter DOCX",cover,"Cover_Letter.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        if supp: st.download_button("Download Supplementary Information DOCX",supp,"Supplementary_Information.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        if research_doc: st.download_button("Download Research Completion Plan DOCX",research_doc,"NanoMax_Research_Completion_Plan.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
        st.download_button("Download INTERNAL QC + Research package ZIP",qc_zip,"NanoMax_INTERNAL_QC_AND_RESEARCH.zip","application/zip",use_container_width=True)

st.caption("NanoMax Nature Editor is an independent research-group tool. Synthetic Research Completion outputs are explicitly separated from evidence-locked submission files.")
