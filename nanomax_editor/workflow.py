from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .api import OpenAIResponsesClient
from .prompts import with_skills, journal_profile_prompt, transform_prompt, reference_audit_prompt, review_prompt
from .schemas import JOURNAL_PROFILE_SCHEMA, TRANSFORM_SCHEMA, REFERENCE_AUDIT_SCHEMA, REVIEW_SCHEMA


@dataclass
class WorkflowState:
    journal_profile: dict[str, Any] | None = None
    transformed: dict[str, Any] | None = None
    reference_audit: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    usage: list[dict[str, Any]] = field(default_factory=list)


class NatureReadyWorkflow:
    def __init__(self, client: OpenAIResponsesClient, skill_text: str):
        self.client = client
        self.instructions = with_skills(skill_text)

    def _record(self, state: WorkflowState, result):
        state.usage.append({"response_id": result.response_id, **(result.usage or {})})
        return result.parsed or {}

    def journal_profile(self, *, journal: str, article_type: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=journal_profile_prompt(journal, article_type),
            schema_name="nanomax_journal_profile",
            schema=JOURNAL_PROFILE_SCHEMA,
            max_output_tokens=12000,
            web_search=True,
        )
        state.journal_profile = self._record(state, r)
        return state.journal_profile

    def transform(self, *, manuscript: str, tables: list[dict], journal_profile: dict, journal: str, article_type: str, priorities: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=transform_prompt(manuscript, tables, journal_profile, journal, article_type, priorities),
            schema_name="nanomax_nature_transformation",
            schema=TRANSFORM_SCHEMA,
            max_output_tokens=100000,
        )
        state.transformed = self._record(state, r)
        return state.transformed

    def audit_references(self, *, manuscript: str, references: list[str], journal: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=reference_audit_prompt(manuscript, references, journal),
            schema_name="nanomax_reference_audit",
            schema=REFERENCE_AUDIT_SCHEMA,
            max_output_tokens=24000,
            web_search=True,
        )
        state.reference_audit = self._record(state, r)
        return state.reference_audit

    def review(self, *, transformed: dict, journal: str, article_type: str, state: WorkflowState) -> dict:
        r = self.client.structured(
            instructions=self.instructions,
            input_text=review_prompt(transformed, journal, article_type),
            schema_name="nanomax_submission_gate",
            schema=REVIEW_SCHEMA,
            max_output_tokens=22000,
        )
        state.review = self._record(state, r)
        return state.review
