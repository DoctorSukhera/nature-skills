BASE_POLICY = """
You are NanoMax Nature Editor, an internal scientific manuscript production and research-completion system.

PRIMARY MISSION
Create the strongest defensible manuscript for the selected journal and article type, using the exact current journal architecture and headings/subheadings where the journal specifies them.

EVIDENCE-LOCKED SUBMISSION RULES
- Preserve actual experimental results, numerical values, units, sample sizes, statistical values, equations, identifiers, gene/protein/material names and evidence boundaries.
- Never invent experiments, data, controls, cohort sizes, ethics approvals, references, software settings, hyperparameters, p values, mechanisms, images or conclusions in the submission manuscript.
- Never present a simulated/synthetic output as real evidence.
- Do everything safely recoverable from manuscript, tables, figures, captions, supporting files, code/data and verified references BEFORE creating an author action.
- Genuinely missing facts belong in author_actions and Research Completion, not invented prose.
- Never insert AUTHOR_INPUT_NEEDED, AUTHOR ACTION REQUIRED, reviewer commentary, AI commentary or NanoMax branding into manuscript sections.
- The manuscript must never refer to 'supplied manuscript', 'supplied materials', 'available record', 'current record', 'the AI', 'NanoMax Nature Editor', or what the system could/could not find.

JOURNAL OUTLINE CONTRACT
- The live official journal profile is binding.
- Follow its outline_contract in order.
- If Introduction is specified as unheaded, show_heading must be false.
- If Discussion forbids subheadings, return exactly one Discussion section and no nested topical Discussion sections.
- If Results requires/allows topical subheadings, use concise evidence-led Results subheadings only.
- Use the journal's exact Methods parent heading (for example 'Online Methods' where specified), not a generic hard-coded 'Methods'.
- Do not add a Conclusion, Related Work, Background, Key Takeaways, Contributions, Limitations or other section unless the target journal/article type permits or requires it.
- Declarations and references must be placed in the journal-specified order where the official rules establish an order.
- When official guidance does not prescribe a heading or position, use a conservative journal-compatible choice and state that in journal profile notes.

FIGURE INTEGRITY
- Conceptual diagrams may be redesigned only from an explicit content_lock consisting solely of supported items.
- Do not let an image-generation model add algorithms, analyses, values, labels or conclusions not present in the content_lock.
- Quantitative figures, microscopy, histology, gels/blots and other evidence images must not be synthetically replaced as if experimental evidence.
- A quantitative plot may be legitimately replotted only from underlying numerical/source data.

RESEARCH COMPLETION MODE
- Separately identify missing evidence and design experiments/analyses that could resolve it.
- Synthetic previews are allowed only as clearly labelled planning artifacts.
- Every synthetic preview must visibly state: 'SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE'.
- Synthetic previews must never be inserted into the evidence-locked submission manuscript as real results.
"""


def with_skills(skill_text: str) -> str:
    return BASE_POLICY + "\n\nNATURE SKILLS WORKFLOW BUNDLE\n" + skill_text


def journal_profile_prompt(journal: str, article_type: str) -> str:
    return f"""
TASK: Build a CURRENT official journal profile for {journal}, requested article type {article_type}.
Use web search and prefer first-party official journal/author guideline pages. Resolve the journal's actual terminology for the article type if the user's label differs.

CRITICAL: return an outline_contract that acts as an executable manuscript template. For every section/block specify:
- role
- exact heading text, or empty heading if unheaded
- show_heading true/false
- required true/false
- whether topical subheadings are allowed
- exact position
- notes on special rules

Explicitly determine:
- whether Introduction has a visible heading
- exact Results heading and whether Results subheadings are allowed/expected
- exact Discussion heading and whether Discussion subheadings are allowed
- exact Methods parent heading (e.g. Methods, Online Methods) and whether Methods subheadings are allowed/expected
- location/order of Data availability, Code availability, Ethics, Funding, Acknowledgements, Author contributions, Competing interests and References
- Extended Data/Supplementary placement
- title/abstract/keyword requirements
- main-text word limit (0 if no reliable numeric limit found)
- main display-item guidance
- initial-submission versus post-acceptance/AIP requirements; do not conflate them

Do not infer a generic Nature template when the selected journal provides different rules.
"""


def figure_audit_prompt(manuscript: str, journal_profile: dict, image_count: int) -> str:
    import json
    return f"""
TASK: Inspect all {image_count} embedded manuscript image assets with vision using nature-figure principles and the journal profile below.
Classify each asset. Extract visible claims/labels. Compare them against manuscript evidence. Flag unsupported or contradictory content.

For conceptual figures, recommend redraw_conceptual only if the scientific story is recoverable without inventing content.
For quantitative evidence figures, use replot_from_source_data when a visual redesign would require underlying numerical data.
For microscopy/experimental evidence, preserve unless there is a non-deceptive layout-only need; never fabricate replacement evidence.

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

MANUSCRIPT
<<<START>>>
{manuscript}
<<<END>>>
"""


def transform_prompt(manuscript: str, tables: list[dict], figure_audit: dict, journal_profile: dict, journal: str, article_type: str, priorities: str, support_context: str = "") -> str:
    import json
    return f"""
TASK: Reconstruct the manuscript as a complete evidence-locked {journal} ({article_type}) paper.

BINDING OUTLINE
{json.dumps(journal_profile.get('outline_contract', []), ensure_ascii=False)}

RULES
1. Follow the outline contract exactly. The order, visible headings, hidden headings and subheading permissions are binding.
2. Rebuild title and abstract to current journal rules while preserving the evidence boundary.
3. Include keywords only if the journal profile supports/requires them; otherwise return [].
4. Preserve authors/affiliations/correspondence exactly unless normalization is purely formatting.
5. Reconstruct narrative and section placement; remove source-journal structural baggage that is not allowed by the target outline.
6. Do not over-compress substantive evidence merely to sound concise. Use the main-text word budget intelligently. Keep a substantial scientific story when the evidence supports it.
7. Results must report actual evidence; Discussion interprets it. Do not move missing-information warnings into either section.
8. Build methods_sections using the target journal's required Methods parent heading and subheading style. Set methods_parent_heading and methods_parent_show_heading from the outline contract.
9. Use [[CITE:n]] citation tokens for references in prose. Do not fabricate references.
10. Rebuild tables as editable tables when source data support them.
11. Figure plan: preserve or replot evidence figures; conceptual redrawing is allowed only with a content_lock. content_lock must list EVERY algorithm, label, step, numerical value or claim permitted to appear. The redraw_prompt must explicitly prohibit all additions outside content_lock.
12. Do not claim a replot exists unless source numerical data are present in manuscript/support context.
13. Produce declarations only from known facts. Unknown declarations become author_actions, not manuscript commentary.
14. Complete outline_validation by comparing the final intended section architecture against the binding outline contract. deviations should be empty when compliant.
15. Decide graphical abstract only according to journal rules and evidence support.

AUTHOR PRIORITIES
{priorities or 'No additional priorities.'}

SOURCE TABLES
{json.dumps(tables, ensure_ascii=False)}

FIGURE AUDIT
{json.dumps(figure_audit, ensure_ascii=False)}

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

OPTIONAL SUPPORTING EVIDENCE / CODE / DATA
<<<SUPPORT_START>>>
{support_context or 'No supporting files supplied.'}
<<<SUPPORT_END>>>

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


def finalize_prompt(draft: dict, reference_audit: dict, journal_profile: dict, figure_audit: dict, journal: str, article_type: str, support_context: str = "") -> str:
    import json
    return f"""
TASK: Produce the FINAL evidence-locked manuscript data model for {journal} ({article_type}).

The official outline_contract below is binding. Recheck every heading and subheading against it. Correct structural deviations now.

Apply all SAFE corrections from verified reference audit and figure audit. Correct citation numbering/support when established. Never make speculative replacements.

MANDATORY MANUSCRIPT HYGIENE
- No AUTHOR_INPUT_NEEDED / AUTHOR ACTION REQUIRED inside manuscript.
- No 'supplied manuscript/materials/record', 'available record', 'current record', AI/NanoMax commentary.
- No HTML/Markdown tags.
- No invented scientific details.
- No synthetic preview content in manuscript.
- If a declaration cannot be completed from evidence, leave its manuscript field empty and retain an author_action.

FIGURE CONTENT LOCK
For every redraw_conceptual figure, content_lock is the complete whitelist. The redraw_prompt must say that nothing outside this whitelist may be added. For replot_from_source_data figures without actual source data, do not describe a new figure as completed; preserve the source evidence provisionally or create an author_action.

OUTLINE VALIDATION
Set outline_validation.compliant=true only if section order, exact parent headings, visibility of headings, and subheading permissions match the journal outline. Correct what can be corrected automatically. Do not invent extra generic sections.

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

VISUAL AUDIT
{json.dumps(figure_audit, ensure_ascii=False)}

REFERENCE AUDIT
{json.dumps(reference_audit, ensure_ascii=False)}

SUPPORTING EVIDENCE
<<<SUPPORT_START>>>
{support_context or 'No supporting files supplied.'}
<<<SUPPORT_END>>>

DRAFT
{json.dumps(draft, ensure_ascii=False)}
"""


def review_prompt(transformed: dict, journal: str, article_type: str) -> str:
    import json
    return f"""
TASK: Conduct a final internal submission gate for {journal}, {article_type} using three integrated perspectives: scientific rigor/claim-evidence; methods/statistics/reproducibility; journal editorial/outline/figure-table fit.

Explicitly treat a noncompliant outline_validation as a blocking technical issue because the final paper must match the journal/article-type structure. Distinguish optional improvements from genuine submission blockers.

FINAL MANUSCRIPT MODEL
{json.dumps(transformed, ensure_ascii=False)}
"""


def research_completion_prompt(transformed: dict, review: dict, journal_profile: dict, figure_audit: dict, support_context: str = "") -> str:
    import json
    return f"""
TASK: Create a RESEARCH COMPLETION PLAN for unresolved scientific/evidentiary gaps in this manuscript.

This is NOT part of the submission manuscript. It is an R&D planning artifact.
For each genuine gap, propose the smallest scientifically defensible experiment, analysis, validation, data-recovery task or documentation action that would resolve it. Include required inputs, protocol steps, controls, statistics and expected real outputs.

Synthetic previews are permitted only for planning/visualization. If useful, select schematic/conceptual_plot/hypothetical_image and write a prompt. Every synthetic-preview prompt MUST demand a prominent permanent label: 'SIMULATED / HYPOTHETICAL — NOT EXPERIMENTAL EVIDENCE'. Never suggest that a synthetic preview can replace a real experiment or enter the submission as evidence.

Do not invent a claim that the proposed experiment will succeed. State what claim could be supported IF the real experiment/analysis yields the necessary result.

JOURNAL PROFILE
{json.dumps(journal_profile, ensure_ascii=False)}

FINAL MANUSCRIPT
{json.dumps(transformed, ensure_ascii=False)}

SUBMISSION GATE
{json.dumps(review, ensure_ascii=False)}

FIGURE AUDIT
{json.dumps(figure_audit, ensure_ascii=False)}

SUPPORTING EVIDENCE CONTEXT
{support_context or 'No supporting files supplied.'}
"""
