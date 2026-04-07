"""Recommendation generation prompt templates."""

RECOMMENDATION_SYSTEM_PROMPT = """You are a GRC consultant. Generate actionable recommendations.
Respond ONLY in valid JSON."""

RECOMMENDATION_USER_PROMPT = """Based on these identified risks, generate prioritized recommendations.
{risks_summary}

Return this exact JSON:
{{
  "recommandations": [
    {{
      "libelle": "Action title",
      "description": "Detailed description",
      "priorite": "CRITIQUE|HAUTE|MOYENNE|FAIBLE",
      "type_action": "QUICK_WIN|LONG_TERME",
      "effort_estime": "FAIBLE|MOYEN|ELEVE",
      "risque_lie": "Related risk libelle"
    }}
  ]
}}
"""


def build_recommendation_prompt(risks_summary: str) -> tuple[str, str]:
    """Return (system, user) prompts for recommendation generation."""
    return (
        RECOMMENDATION_SYSTEM_PROMPT,
        RECOMMENDATION_USER_PROMPT.format(risks_summary=risks_summary),
    )
