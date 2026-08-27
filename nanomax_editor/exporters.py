from __future__ import annotations
from io import BytesIO
from pathlib import Path
import json
import zipfile
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt


def _style_doc(doc: Document):
    sec = doc.sections[0]
    sec.top_margin = Inches(0.8)
    sec.bottom_margin = Inches(0.8)
    sec.left_margin = Inches(0.9)
    sec.right_margin = Inches(0.9)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)


def submission_docx_bytes(pkg: dict) -> bytes:
    doc = Document(); _style_doc(doc)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(pkg.get("title", "")); r.bold = True; r.font.size = Pt(16)
    if pkg.get("abstract"):
        doc.add_heading("Abstract", level=1); doc.add_paragraph(pkg["abstract"])
    kws = pkg.get("keywords") or []
    if kws:
        p = doc.add_paragraph(); p.add_run("Keywords: ").bold = True; p.add_run(", ".join(kws))
    for sec in pkg.get("main_sections", []):
        if sec.get("heading"): doc.add_heading(sec["heading"], level=1)
        doc.add_paragraph(sec.get("text", ""))
    if pkg.get("methods_sections"):
        doc.add_heading("Methods", level=1)
        for sec in pkg.get("methods_sections", []):
            if sec.get("heading"): doc.add_heading(sec["heading"], level=2)
            doc.add_paragraph(sec.get("text", ""))
    for label, key in [
        ("Data availability", "data_availability"), ("Code availability", "code_availability"),
        ("Ethics", "ethics_statement"), ("Acknowledgements", "acknowledgements"),
        ("Author contributions", "author_contributions"), ("Competing interests", "competing_interests")]:
        val = pkg.get(key, "")
        if val:
            doc.add_heading(label, level=1); doc.add_paragraph(val)
    refs = pkg.get("references") or []
    if refs:
        doc.add_heading("References", level=1)
        for i, ref in enumerate(refs, 1):
            doc.add_paragraph(f"{i}. {ref}")
    tables = pkg.get("tables") or []
    if tables:
        doc.add_heading("Tables", level=1)
        for t in tables:
            doc.add_paragraph(f"{t.get('number','')} {t.get('title','')}").runs[0].bold = True
            cols = t.get("columns") or []
            rows = t.get("rows") or []
            if cols:
                table = doc.add_table(rows=1, cols=len(cols)); table.style = "Table Grid"; table.alignment = WD_TABLE_ALIGNMENT.CENTER
                for j,c in enumerate(cols): table.rows[0].cells[j].text = c
                for row in rows:
                    cells = table.add_row().cells
                    for j in range(len(cols)):
                        cells[j].text = str(row[j]) if j < len(row) else ""
            if t.get("footnote"): doc.add_paragraph(t["footnote"])
    if pkg.get("figure_plan"):
        doc.add_heading("Figure legends", level=1)
        for f in pkg["figure_plan"]:
            doc.add_paragraph(f"{f.get('figure','')}. {f.get('caption','')}")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()


def report_docx_bytes(journal_profile: dict, reference_audit: dict, review: dict, pkg: dict) -> bytes:
    doc = Document(); _style_doc(doc)
    doc.add_heading("NanoMax Nature Editor — Submission Audit", level=0)
    doc.add_heading("Journal profile", level=1)
    doc.add_paragraph(json.dumps(journal_profile, ensure_ascii=False, indent=2))
    doc.add_heading("Reference audit", level=1)
    doc.add_paragraph(reference_audit.get("summary", ""))
    for x in reference_audit.get("needs_author_check", []): doc.add_paragraph(x, style="List Bullet")
    doc.add_heading("Final submission gate", level=1)
    doc.add_paragraph(f"Decision: {review.get('editorial_decision','')} | Readiness: {review.get('submission_readiness_score',0)}/100")
    for label, key in [("Blocking issues","blocking_issues"),("Major issues","major_issues"),("Minor issues","minor_issues"),("Final actions","final_actions")]:
        doc.add_heading(label, level=2)
        for x in review.get(key, []): doc.add_paragraph(x, style="List Bullet")
    doc.add_heading("Author actions generated during transformation", level=1)
    for x in pkg.get("author_actions", []):
        doc.add_paragraph(f"[{x.get('severity','')}] {x.get('location','')}: {x.get('issue','')} — {x.get('required_action','')}", style="List Bullet")
    bio = BytesIO(); doc.save(bio); return bio.getvalue()


def package_zip_bytes(*, manuscript_docx: bytes, report_docx: bytes, transformed: dict, journal_profile: dict, reference_audit: dict, review: dict, source_images: list[dict], redrawn_images: dict[str, bytes] | None = None) -> bytes:
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("01_Manuscript/NanoMax_Nature_Ready_Manuscript.docx", manuscript_docx)
        z.writestr("05_Quality_Control/NanoMax_Submission_Audit.docx", report_docx)
        z.writestr("05_Quality_Control/session.json", json.dumps({"journal_profile":journal_profile,"reference_audit":reference_audit,"review":review,"transformed":transformed}, ensure_ascii=False, indent=2))
        for i,img in enumerate(source_images, 1):
            z.writestr(f"02_Figures/source/FigureAsset_{i}.{img.get('ext','png')}", img["bytes"])
        for name,blob in (redrawn_images or {}).items():
            z.writestr(f"02_Figures/redrawn/{name}", blob)
    return out.getvalue()
