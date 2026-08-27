BASE_POLICY = """
You are NanoMax Nature Editor, an internal manuscript-to-submission production system for a scientific research group.

MISSION
Convert an uploaded working scientific manuscript into the strongest defensible initial-submission package for the selected journal. The PRIMARY product is a complete journal-structured manuscript, not a reviewer report.

SCIENTIFIC INTEGRITY
- Preserve actual experimental results, numerical values, units, sample sizes, statistical values, equations, identifiers, gene/protein/material names and evidence boundaries.
- Never invent experiments, data, controls, cohort sizes, ethics approvals, references, software settings, hyperparameters, p values, mechanisms or conclusions.
- Never convert association into causation without causal evidence.
- Do everything safely recoverable from the supplied manuscript, tables, figures, captions and verified references BEFORE asking the author.
- Genuinely missing facts belong in author_actions, not as invented prose.
- IMPORTANT: do NOT insert strings such as AUTHOR_INPUT_NEEDED or AUTHOR ACTION REQUIRED into the manuscript body. Keep unresolved checks only in author_actions. Rewrite surrounding manuscript prose conservatively so the manuscript remains readable.
- Experimental, microscopy, pathology and clinical images are evidence and must not be fabricated or semantically altered. Conceptual schematics may be redesigned. Quantitative plots may only be replotted from real source data.
- Detect contradictions between figure text and manuscript evidence. Do not preserve unsupported numbers or workflow claims merely because they appear in a graphic.

MANUSCRIPT OUTPUT RULES
- Rebuild title, abstract, section architecture, narrative, tables, legends, references and declarations according to the CURRENT selected journal profile.
- Preserve author names and affiliations exactly unless the user explicitly asks to change them.
- The manuscript must use a coherent final citation numbering scheme. In prose, write citations using tokens like [[CITE:1]], [[CITE:2,3]], or [[CITE:4-6]]. The exporter will render these as journal-style superscripts.
- Main tables and main figures must be integrated into the manuscript at logical locations, not merely listed as detached assets.
- A complete initial-submission manuscript should contain front matter, article text, Methods if required, figures with legends, tables with titles/footnotes, references and required declarations.
- Produce a cover letter as a separate submission item.
- Produce a graphical-abstract plan only when required, useful, or explicitly requested. Never imply it is required if the journal does not require it.

USE OF NATURE SKILLS
The supplied Nature Skills are governing workflow modules, not decorative examples. Apply them according to their intended role and preserve their safety boundaries.
""".strip()


def with_skills(skill_text: str) -> str:
    return BASE_POLICY + "\n\nLOADED NATURE-SKILLS WORKFLOWS\n" + skill_text


def journal_profile_prompt(journal: str, article_type: str) -> str:
    return f"""Find the CURRENT official author instructions for {journal}, article type {article_type}. Prefer official journal/Nature Portfolio pages. Distinguish initial-submission requirements from post-acceptance/AIP production requirements. Return rules relevant to title, abstract, keywords, section order, references, figures, tables, declarations, initial-submission file composition, cover letter, graphical abstract and supplementary information. If an item is not required, say so. Do not invent rules when the official source is silent."""


def figure_audit_prompt(manuscript: str, journal_profile: dict, image_count: int) -> str:
    import json
    return f"""
TASK: Visually audit the {image_count} uploaded manuscript image assets using the loaded nature-figure and scientific-integrity workflows.

For each asset, identify what it actually shows, whether it is a conceptual schematic or quantitative evidence, visible numerical/methodological claims, and any contradiction with the manuscript. Recommend preserve, redraw_conceptual, replot_from_source_data, move_extended_data, remove_if_redundant or author_check.

Critical rules:
- Do not trust text inside a figure if it conflicts with the manuscript.
- A diagram may be redesigned only if it is conceptual.
- ROC curves, heatmaps, confusion matrices, bar/line plots and other quantitative graphics require the underlying real values for replotting; never visually invent replacement curves or values.
- Experimental or clinical evidence images are preserved.

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def transform_prompt(manuscript: str, tables: list[dict], figure_audit: dict, journal_profile: dict, journal: str, article_type: str, priorities: str) -> str:
    import json
    return f"""
TASK: Reconstruct this manuscript for {journal} ({article_type}) using the complete loaded Nature Skills workflow.

AUTHOR PRIORITIES: {priorities or 'None supplied'}

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

VISUAL FIGURE AUDIT
{json.dumps(figure_audit, ensure_ascii=False)}

SOURCE TABLES
{json.dumps(tables, ensure_ascii=False)}

REQUIRED BEHAVIOR
1. Produce a complete manuscript architecture, not a review memo.
2. Preserve the exact author identity/affiliation information found in the source. Do not invent missing contributions or declarations.
3. Rewrite title and abstract to target-journal style and actual evidence strength.
4. Restructure sections according to the journal. For an unheaded introduction, use heading='Introduction' and show_heading=false.
5. Use paragraphs arrays; write polished manuscript prose only. Never put AUTHOR_INPUT_NEEDED markers in body text.
6. Use [[CITE:n]] citation tokens in body text and legends.
7. Redesign source tables into concise editable tables while preserving factual values. Specify logical placement_after and destination.
8. Build a figure plan that maps final figures to source_asset_indices from the visual audit. Correct or remove unsupported graphical claims. Use redraw_conceptual only for true schematics. Use replot_from_source_data for quantitative plots needing source numerical data.
9. Write complete publication-grade legends based on supplied evidence.
10. Draft Data availability, Code availability, ethics, funding, acknowledgements, author contributions and competing interests only to the extent supported. If facts are missing, use neutral provisional wording where safe and put the unresolved fact in author_actions. Do not put warnings inside the manuscript text.
11. Produce a journal-appropriate cover letter emphasizing novelty, scope fit and evidence without hype.
12. Decide whether a graphical abstract is recommended. If useful, create a generation prompt that represents only supported science and avoids unsupported counts/performance/methods.
13. Move specialist material to Extended Data or Supplementary only when appropriate; the main manuscript must still tell a complete scientific story.
14. Keep all real results available in the source. Do not silently discard figures or tables merely to reduce length; if moved, record their destination.

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def reference_audit_prompt(manuscript: str, references: list[str], journal: str) -> str:
    import json
    return f"""
TASK: Using web search and the loaded citation/reference skills, audit and normalize the manuscript references for {journal}.
Verify bibliographic existence and metadata from DOI, PubMed, Crossref, publisher or other primary bibliographic sources. Check claim-to-citation support and identify wrong citation numbers. Never invent a reference.

Return a verified_reference_list containing the best corrected version of every safely verified supplied reference, in final journal-compatible order where possible. If a supplied reference cannot be safely resolved, preserve it rather than fabricating metadata and flag it in needs_author_check. citation_corrections should state concrete safe renumbering/support corrections.

REFERENCES
{json.dumps(references, ensure_ascii=False)}

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def finalize_prompt(draft: dict, reference_audit: dict, journal_profile: dict, figure_audit: dict, journal: str, article_type: str) -> str:
    import json
    return f"""
TASK: Produce the FINAL manuscript data model for {journal} ({article_type}). This is the version that will be assembled into the master Word file.

Apply all SAFE corrections from the verified reference audit and visual figure audit. Correct citation numbering and support when the audit establishes the right source. Do not make speculative replacements. Remove duplicate reference numbering such as '1. 1.'. Ensure citations in prose use [[CITE:n]] tokens matching the final references array.

Critically, convert reviewer-style warnings into either:
(a) conservative manuscript wording that is supported by existing evidence, or
(b) author_actions outside the manuscript.
Never leave AUTHOR_INPUT_NEEDED or AUTHOR ACTION REQUIRED text inside title, abstract, main_sections, methods_sections, legends, declarations, tables or references.

Maintain a complete paper even when author actions remain. Do not call unsupported work validated, prospective, causal, clinically deployable, externally validated or statistically significant.

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

VISUAL AUDIT
{json.dumps(figure_audit, ensure_ascii=False)}

REFERENCE AUDIT
{json.dumps(reference_audit, ensure_ascii=False)}

DRAFT MANUSCRIPT MODEL
{json.dumps(draft, ensure_ascii=False)}
"""


def review_prompt(transformed: dict, journal: str, article_type: str) -> str:
    import json
    return f"""
TASK: Conduct a final internal submission gate for {journal}, {article_type}. Review the COMPLETE final manuscript model as three integrated perspectives: scientific rigor/claim-evidence, methods-statistics-reproducibility, and journal editorial/figure-table fit.

Do not lower readiness simply because optional enhancements are absent. A blocking issue is a genuinely missing or contradictory item that prevents truthful submission or makes a central result uninterpretable. Distinguish 'could improve' from 'cannot submit'.

FINAL MANUSCRIPT MODEL
{json.dumps(transformed, ensure_ascii=False)}
"""
