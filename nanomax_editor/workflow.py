from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .api import OpenAIResponsesClient
from .prompts import (
    with_skills, journal_discovery_prompt, journal_profile_prompt, figure_audit_prompt, transform_prompt,
    reference_audit_prompt, finalize_prompt, review_prompt, research_completion_prompt,
)
WORKFLOW_VERSION = "10.1"

from .schemas import (
    JOURNAL_DISCOVERY_SCHEMA, JOURNAL_PROFILE_SCHEMA, FIGURE_AUDIT_SCHEMA, MANUSCRIPT_SCHEMA,
    REFERENCE_AUDIT_SCHEMA, REVIEW_SCHEMA, RESEARCH_COMPLETION_SCHEMA,
)


@dataclass
class WorkflowState:
    journal_discovery: dict[str, Any] | None = None
    journal_profile: dict[str, Any] | None = None
    figure_audit: dict[str, Any] | None = None
    draft: dict[str, Any] | None = None
    reference_audit: dict[str, Any] | None = None
    final_manuscript: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    research_completion: dict[str, Any] | None = None
    usage: list[dict[str, Any]] = field(default_factory=list)


class NatureReadyWorkflow:
    def __init__(self, client: OpenAIResponsesClient, skill_text: str):
        self.client = client
        self.instructions = with_skills(skill_text)

    def _record(self, state: WorkflowState, result):
        state.usage.append({"response_id": result.response_id, **(result.usage or {})})
        return result.parsed or {}

    def recommend_journals(self, *, manuscript: str, publishing_preference: str, support_context: str = "", priorities: str = "", state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=journal_discovery_prompt(manuscript, publishing_preference, support_context, priorities),
            schema_name="nanomax_journal_discovery_v10",
            schema=JOURNAL_DISCOVERY_SCHEMA,
            max_output_tokens=26000,
            web_search=True,
        )
        state.journal_discovery = self._record(state, r)
        return state.journal_discovery

    def journal_profile(self, *, journal: str, article_type: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=journal_profile_prompt(journal, article_type),
            schema_name="nanomax_journal_profile_v10",
            schema=JOURNAL_PROFILE_SCHEMA,
            max_output_tokens=18000,
            web_search=True,
        )
        state.journal_profile = self._record(state, r)
        return state.journal_profile

    def audit_figures(self, *, manuscript: str, images: list[dict], journal_profile: dict, state: WorkflowState) -> dict:
        if not images:
            state.figure_audit = {"summary":"No embedded image assets detected.", "assets":[]}
            return state.figure_audit
        try:
            r = self.client.structured_with_images(
                instructions=self.instructions,
                input_text=figure_audit_prompt(manuscript, journal_profile, len(images)),
                images=images[:16],
                schema_name="nanomax_figure_audit_v10",
                schema=FIGURE_AUDIT_SCHEMA,
                max_output_tokens=30000,
            )
            state.figure_audit = self._record(state, r)
        except Exception as exc:
            state.figure_audit = {
                "summary": f"Automated visual audit unavailable; source evidence will be preserved. Technical note: {exc}",
                "assets": [
                    {"asset_index":i, "detected_role":"other", "content_summary":img.get("name",f"asset {i}"),
                     "scientific_claims_visible":[], "potential_inconsistencies":[], "recommended_action":"author_check",
                     "reason":"Visual audit unavailable; preserve source evidence unless later safe classification is possible.", "suggested_legend":""}
                    for i,img in enumerate(images,1)
                ]
            }
        return state.figure_audit

    def transform(self, *, manuscript: str, tables: list[dict], figure_audit: dict, journal_profile: dict, journal: str, article_type: str, priorities: str, support_context: str = "", state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=transform_prompt(manuscript, tables, figure_audit, journal_profile, journal, article_type, priorities, support_context),
            schema_name="nanomax_manuscript_draft_v10",
            schema=MANUSCRIPT_SCHEMA,
            max_output_tokens=100000,
        )
        state.draft = self._record(state, r)
        return state.draft

    def audit_references(self, *, manuscript: str, references: list[str], journal: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=reference_audit_prompt(manuscript, references, journal),
            schema_name="nanomax_reference_audit_v10",
            schema=REFERENCE_AUDIT_SCHEMA,
            max_output_tokens=34000,
            web_search=True,
        )
        state.reference_audit = self._record(state, r)
        return state.reference_audit

    def finalize(self, *, draft: dict, reference_audit: dict, journal_profile: dict, figure_audit: dict, journal: str, article_type: str, support_context: str = "", state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=finalize_prompt(draft, reference_audit, journal_profile, figure_audit, journal, article_type, support_context),
            schema_name="nanomax_final_manuscript_v10",
            schema=MANUSCRIPT_SCHEMA,
            max_output_tokens=100000,
        )
        state.final_manuscript = self._record(state, r)
        return state.final_manuscript

    def review(self, *, transformed: dict, journal: str, article_type: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=review_prompt(transformed, journal, article_type),
            schema_name="nanomax_submission_gate_v10",
            schema=REVIEW_SCHEMA,
            max_output_tokens=24000,
        )
        state.review = self._record(state, r)
        return state.review

    def research_completion(self, *, transformed: dict, review: dict, journal_profile: dict, figure_audit: dict, support_context: str = "", state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=research_completion_prompt(transformed, review, journal_profile, figure_audit, support_context),
            schema_name="nanomax_research_completion_v10",
            schema=RESEARCH_COMPLETION_SCHEMA,
            max_output_tokens=42000,
        )
        state.research_completion = self._record(state, r)
        return state.research_completion
