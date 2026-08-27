JOURNAL_PROFILE_SCHEMA = {
  "type":"object",
  "properties":{
    "journal":{"type":"string"},
    "article_type":{"type":"string"},
    "official_sources":{"type":"array","items":{"type":"string"}},
    "title_rules":{"type":"array","items":{"type":"string"}},
    "abstract_rules":{"type":"array","items":{"type":"string"}},
    "keywords_rule":{"type":"string"},
    "section_order":{"type":"array","items":{"type":"string"}},
    "reference_rules":{"type":"array","items":{"type":"string"}},
    "figure_rules":{"type":"array","items":{"type":"string"}},
    "table_rules":{"type":"array","items":{"type":"string"}},
    "required_declarations":{"type":"array","items":{"type":"string"}},
    "notes":{"type":"array","items":{"type":"string"}}
  },
  "required":["journal","article_type","official_sources","title_rules","abstract_rules","keywords_rule","section_order","reference_rules","figure_rules","table_rules","required_declarations","notes"],
  "additionalProperties":False
}

TRANSFORM_SCHEMA = {
  "type":"object",
  "properties":{
    "title":{"type":"string"},
    "short_title":{"type":"string"},
    "abstract":{"type":"string"},
    "keywords":{"type":"array","items":{"type":"string"}},
    "main_sections":{"type":"array","items":{"type":"object","properties":{"heading":{"type":"string"},"text":{"type":"string"}},"required":["heading","text"],"additionalProperties":False}},
    "methods_sections":{"type":"array","items":{"type":"object","properties":{"heading":{"type":"string"},"text":{"type":"string"}},"required":["heading","text"],"additionalProperties":False}},
    "tables":{"type":"array","items":{"type":"object","properties":{"number":{"type":"string"},"title":{"type":"string"},"columns":{"type":"array","items":{"type":"string"}},"rows":{"type":"array","items":{"type":"array","items":{"type":"string"}}},"footnote":{"type":"string"},"placement":{"type":"string"}},"required":["number","title","columns","rows","footnote","placement"],"additionalProperties":False}},
    "figure_plan":{"type":"array","items":{"type":"object","properties":{"figure":{"type":"string"},"action":{"type":"string","enum":["preserve","redraw_conceptual","replot_from_source_data","move_extended_data","remove_if_redundant","author_action"]},"reason":{"type":"string"},"redraw_prompt":{"type":"string"},"caption":{"type":"string"}},"required":["figure","action","reason","redraw_prompt","caption"],"additionalProperties":False}},
    "references":{"type":"array","items":{"type":"string"}},
    "data_availability":{"type":"string"},
    "code_availability":{"type":"string"},
    "ethics_statement":{"type":"string"},
    "author_contributions":{"type":"string"},
    "competing_interests":{"type":"string"},
    "acknowledgements":{"type":"string"},
    "cover_letter_summary":{"type":"string"},
    "author_actions":{"type":"array","items":{"type":"object","properties":{"severity":{"type":"string"},"location":{"type":"string"},"issue":{"type":"string"},"required_action":{"type":"string"}},"required":["severity","location","issue","required_action"],"additionalProperties":False}},
    "change_summary":{"type":"array","items":{"type":"string"}}
  },
  "required":["title","short_title","abstract","keywords","main_sections","methods_sections","tables","figure_plan","references","data_availability","code_availability","ethics_statement","author_contributions","competing_interests","acknowledgements","cover_letter_summary","author_actions","change_summary"],
  "additionalProperties":False
}

REFERENCE_AUDIT_SCHEMA = {
  "type":"object",
  "properties":{
    "summary":{"type":"string"},
    "verified_count":{"type":"integer"},
    "needs_author_check":{"type":"array","items":{"type":"string"}},
    "citation_support_concerns":{"type":"array","items":{"type":"string"}},
    "recommended_updates":{"type":"array","items":{"type":"string"}},
    "do_not_auto_replace":{"type":"array","items":{"type":"string"}}
  },
  "required":["summary","verified_count","needs_author_check","citation_support_concerns","recommended_updates","do_not_auto_replace"],
  "additionalProperties":False
}

REVIEW_SCHEMA = {
  "type":"object",
  "properties":{
    "editorial_decision":{"type":"string"},
    "submission_readiness_score":{"type":"integer"},
    "blocking_issues":{"type":"array","items":{"type":"string"}},
    "major_issues":{"type":"array","items":{"type":"string"}},
    "minor_issues":{"type":"array","items":{"type":"string"}},
    "strengths":{"type":"array","items":{"type":"string"}},
    "final_actions":{"type":"array","items":{"type":"string"}}
  },
  "required":["editorial_decision","submission_readiness_score","blocking_issues","major_issues","minor_issues","strengths","final_actions"],
  "additionalProperties":False
}
