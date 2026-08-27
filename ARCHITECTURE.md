# NanoMax Nature Editor v6.0

Pipeline:

1. Parse manuscript, editable tables, and embedded figure assets.
2. Retrieve current official target-journal instructions with web search.
3. Load nine Nature Skills from the fork.
4. Deep manuscript reconstruction using `nature-writing` + `nature-polishing`.
5. Statistical and reporting constraints from `nature-statistics` + `nature-data`.
6. Table reconstruction and figure action plan using `nature-figure`.
7. Live reference/citation audit using `nature-citation`, `nature-ref-verifier`, and `nature-academic-search`.
8. Internal final gate using `nature-reviewer`.
9. Export rebuilt DOCX + audit + source/redrawn figure assets + session JSON in a ZIP package.

The system may make major editorial changes but must not fabricate science.
