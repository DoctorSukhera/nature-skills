BASE_POLICY = """
You are NanoMax Nature Editor, an internal manuscript-to-submission production system for a scientific research group.

MISSION
Transform a supplied scientific manuscript into the strongest defensible version for the selected Nature Portfolio or other target journal. You may deeply restructure title, abstract, section architecture, prose, tables, captions, declarations, and figure plan, but you must never fabricate science.

SCIENTIFIC INTEGRITY
- Preserve all actual experimental results, numerical values, units, sample sizes, statistical values, equations, gene/protein/material names, identifiers, and evidence boundaries.
- Never invent experiments, data, controls, ethics approvals, references, software settings, sample sizes, p values, mechanisms, or conclusions.
- Never convert association into causation without causal evidence.
- Missing information becomes AUTHOR ACTION REQUIRED, not invented content.
- Experimental/microscopy/clinical images are evidence: do not fabricate or materially alter them. Conceptual schematics may be redesigned. Data plots may be redrawn only from supplied source data.
- A journal-ready result still requires author verification before submission.

USE OF NATURE SKILLS
The supplied Nature Skills are governing workflow modules, not decorative examples. Route the task through them according to their intended role and preserve their safety boundaries.
""".strip()


def with_skills(skill_text: str) -> str:
    return BASE_POLICY + "\n\nLOADED NATURE-SKILLS WORKFLOWS\n" + skill_text


def journal_profile_prompt(journal: str, article_type: str) -> str:
    return f"""Find the CURRENT official author instructions for {journal}, article type {article_type}. Use official journal/Nature Portfolio sources wherever possible. Return only rules relevant to manuscript preparation and submission: title, abstract/summary, keywords, section order, references, figures, tables, declarations. Do not invent a rule if the official source is silent."""


def transform_prompt(manuscript: str, tables: list[dict], journal_profile: dict, journal: str, article_type: str, priorities: str) -> str:
    import json
    return f"""
TASK: Reconstruct this manuscript for {journal} ({article_type}) using the loaded Nature Skills and live journal profile.

AUTHOR PRIORITIES: {priorities or 'None supplied'}

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

REQUIRED BEHAVIOR
1. Rebuild title and abstract/summary to fit the target journal and actual evidence.
2. Rebuild manuscript narrative and section architecture where needed. Do not preserve IEEE-style organization merely because it exists in the source.
3. Generate keywords only if the target profile calls for them; otherwise return an empty list.
4. Redesign tables into concise editable tables while preserving every factual value used.
5. Produce a figure action plan. Conceptual diagrams may be flagged redraw_conceptual. Data plots require source data before replotting. Experimental images must be preserved except for non-deceptive layout/label cleanup.
6. Rewrite all figure captions as publication-grade legends based only on supplied information.
7. Preserve existing references unless a separate verified reference audit supports correction. Do not fabricate a new citation.
8. Draft required declarations only from facts visible in the manuscript; otherwise create an author action.
9. Return a cover-letter summary of novelty/significance without hype.
10. Every missing item that blocks a true ready-to-submit package must be listed under author_actions.

SOURCE TABLES
{json.dumps(tables, ensure_ascii=False)}

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def reference_audit_prompt(manuscript: str, references: list[str], journal: str) -> str:
    import json
    return f"""
TASK: Using web search and the loaded citation/reference skills, audit the manuscript's references and citation support for {journal}.
Verify bibliographic existence and obvious metadata conflicts where possible. Check whether cited references plausibly support the associated claims. Prefer DOI, PubMed, Crossref, publisher, and primary sources. Do not automatically replace a citation merely because a newer paper exists. Never invent a reference.

REFERENCES
{json.dumps(references, ensure_ascii=False)}

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def review_prompt(transformed: dict, journal: str, article_type: str) -> str:
    import json
    return f"""
TASK: Conduct a final internal submission gate for {journal}, {article_type}. Review the transformed manuscript package as three integrated perspectives: scientific rigor/claim-evidence, methods-statistics-reproducibility, and high-impact editorial/figure-table fit. A blocking issue is one that prevents the system from truthfully calling the package ready to submit. Do not demand experiments merely for novelty; identify the exact claim-evidence gap.

TRANSFORMED PACKAGE
{json.dumps(transformed, ensure_ascii=False)}
"""
