"""Risk extraction prompt templates."""

RISK_SYSTEM_PROMPT = """You are a GRC expert. Analyze the text and extract ALL risks.
Respond ONLY in valid JSON. No text outside the JSON."""

RISK_USER_PROMPT = """Extract all risks from this GRC report text.
Return this exact JSON structure:
{{
  "risques": [
    {{
      "libelle": "Short risk name",
      "description": "Detailed description",
      "categorie": "CYBER|OPERATIONNEL|LEGAL|FINANCIER|RH",
      "probabilite": 1-5,
      "impact": 1-5,
      "section_source": "Section reference in the document"
    }}
  ]
}}

TEXT: {text}
"""


def build_risk_prompt(text: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for risk extraction."""
    return RISK_SYSTEM_PROMPT, RISK_USER_PROMPT.format(text=text[:8000])
