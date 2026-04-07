"""Compliance check prompt templates for ISO 27001, RGPD, and Loi 09-08."""

COMPLIANCE_SYSTEM_PROMPT = """You are a {framework} compliance expert.
Respond ONLY in valid JSON."""

COMPLIANCE_USER_PROMPT = """Evaluate this document's compliance with {framework}.
Return this exact JSON:
{{
  "referentiel": "{framework}",
  "taux_global": 0-100,
  "domaines": [
    {{
      "nom": "Domain name",
      "statut": "CONFORME|NON_CONFORME|PARTIEL",
      "ecart": "Description of the gap if any",
      "taux": 0-100
    }}
  ]
}}

TEXT: {text}
"""

FRAMEWORKS = ["ISO27001", "RGPD", "LOI0908"]

FRAMEWORK_DISPLAY = {
    "ISO27001": "ISO 27001 (Information Security Management)",
    "RGPD": "RGPD (Règlement Général sur la Protection des Données)",
    "LOI0908": "Loi 09-08 (Protection des Données Personnelles au Maroc)",
}


def build_compliance_prompt(text: str, framework: str) -> tuple[str, str]:
    """Return (system, user) prompts for a given framework compliance check."""
    display_name = FRAMEWORK_DISPLAY.get(framework, framework)
    system = COMPLIANCE_SYSTEM_PROMPT.format(framework=display_name)
    user = COMPLIANCE_USER_PROMPT.format(framework=framework, text=text[:8000])
    return system, user
