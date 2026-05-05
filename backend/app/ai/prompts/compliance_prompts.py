"""Compliance check prompt templates — evidence-based, inference-aware evaluation."""

COMPLIANCE_SYSTEM_PROMPT = """You are a {framework} compliance expert and certified auditor.
Your task is to evaluate a document's compliance posture for {framework}.

════════════════════════════════════════════════════════════════════════════════
EVALUATION PHILOSOPHY
════════════════════════════════════════════════════════════════════════════════
Compliance evidence comes in two forms — evaluate BOTH:

1. EXPLICIT evidence: The domain is directly discussed, policies are mentioned,
   controls are described, or the document explicitly addresses the requirement.

2. IMPLICIT evidence: The document's nature or findings reveal the compliance state
   even without explicit mention. Examples:
   - A vulnerability scan showing missing HSTS headers → A.13 Communications Security is weak
   - A scan showing no data encryption issues → cryptography controls may be partially in place
   - An audit finding CSRF vulnerabilities → access control and application security gaps
   - An incident report describing a breach → incident management, business continuity risks

For domains NOT mentioned in the document:
- If the document TYPE logically addresses this domain and it is absent, mark NON_CONFORME.
- If the document type simply does not cover this domain (e.g., a web scan doesn't address HR),
  mark NON_CONFORME with ecart explaining the domain is out of scope for this document type.

════════════════════════════════════════════════════════════════════════════════
SCORING GUIDE
════════════════════════════════════════════════════════════════════════════════
- CONFORME (taux 75-100%): Domain is explicitly addressed with clear evidence of implementation.
- PARTIEL (taux 10-74%): Some evidence of partial implementation, or implicit evidence exists.
- NON_CONFORME (taux 0-9%): No evidence, or explicit evidence of failure/absence.

taux_global = weighted average of all domain scores (round to nearest integer).

Respond ONLY in valid JSON. No text outside the JSON."""


ISO27001_DOMAINS = """
ISO 27001:2013 ANNEX A CONTROL DOMAINS TO EVALUATE:
A.5  Information Security Policies — existence and review of security policies
A.6  Organisation of Information Security — roles, responsibilities, segregation of duties
A.7  Human Resource Security — screening, training, termination procedures
A.8  Asset Management — asset inventory, ownership, acceptable use, classification
A.9  Access Control — user access provisioning, privilege management, authentication
A.10 Cryptography — encryption policies, key management
A.11 Physical and Environmental Security — physical access controls, equipment protection
A.12 Operational Security — vulnerability management, logging, monitoring, patch management
A.13 Communications Security — network controls, HTTP security headers, secure transfer
A.14 System Acquisition, Development and Maintenance — security in SDLC, code reviews
A.15 Supplier Relationships — supplier contracts, third-party risk management
A.16 Information Security Incident Management — incident response, breach procedures
A.17 Business Continuity Management — BCP, DRP, recovery time objectives
A.18 Compliance — legal and regulatory compliance, audits, IP protection
"""

RGPD_DOMAINS = """
RGPD (GDPR) DOMAINS TO EVALUATE:
1. Licéité du traitement (Art.6) — lawful basis for each processing activity
2. Droits des personnes concernées (Art.12-23) — access, rectification, erasure, portability
3. Consentement (Art.7-8) — freely given, specific, informed, unambiguous consent
4. Protection des données dès la conception (Art.25) — privacy by design and by default
5. Responsabilités du responsable de traitement (Art.24-26) — DPA accountability, processor contracts
6. Registre des activités de traitement (Art.30) — records of processing activities (ROPA)
7. Sécurité du traitement (Art.32) — technical and organisational security measures
8. Notification des violations de données (Art.33-34) — 72h breach notification to CNIL/DPA
9. Analyse d'impact (AIPD/DPIA) (Art.35) — risk assessment for high-risk processing
10. Délégué à la protection des données (DPO) (Art.37-39) — DPO designation and role
11. Transferts de données hors UE (Art.44-49) — adequacy decisions, SCCs, BCRs
12. Information des personnes (Art.13-14) — privacy notices, transparency
"""

LOI0908_DOMAINS = """
LOI 09-08 (MAROC) DOMAINS TO EVALUATE:
1. Droit à l'information (Art.4-6) — informing data subjects before collection
2. Consentement (Art.4) — prior, free, specific, and informed consent
3. Droits des personnes concernées (Art.7-11) — access, rectification, opposition, deletion
4. Sécurité des données personnelles (Art.23) — technical and organisational security measures
5. Notification des violations de données (Art.23) — breach notification procedures
6. Délégué à la protection des données (Art.24) — DPO or responsible person designation
7. Analyse d'impact relative à la vie privée (PIA) — privacy impact assessment
8. Registre des traitements (Art.17-22) — declaration/authorisation with CNDP
9. Transfert international de données (Art.43-44) — restrictions on cross-border transfers
10. Sensibilisation et formation — staff awareness and training on data protection
11. Gestion des sous-traitants (Art.13) — processor agreements and accountability
"""

COMPLIANCE_USER_PROMPT = """Evaluate this document's compliance with {framework_display}.

{domains}

DOCUMENT ANALYSIS INSTRUCTIONS:
1. Read the document to determine its type (vulnerability scan, audit, policy, incident report, etc.).
2. For each domain above, assess compliance based on:
   a) What is explicitly stated in the document
   b) What the document's findings IMPLY about the organisation's security/privacy posture
   c) What is conspicuously absent but should be present for this document type
3. Assign a realistic taux score — do not default everything to 0% unless truly warranted.
4. Provide specific, actionable ecart descriptions that reference actual document content.

Return ONLY this JSON (no text outside):
{{
  "referentiel": "{framework}",
  "taux_global": 0,
  "domaines": [
    {{
      "nom": "Domain name as listed above",
      "statut": "CONFORME|NON_CONFORME|PARTIEL",
      "taux": 0,
      "ecart": "Specific description of the gap, what is missing, or what evidence exists. Reference actual document content. For compliant domains, describe what evidence was found.",
      "evidence": "Direct quote or specific reference from the document supporting this rating (empty string if none)"
    }}
  ]
}}

IMPORTANT: List ALL domains. Do not skip any.
taux_global must equal the rounded average of all domain taux values.

DOCUMENT TEXT:
{text}
"""

FRAMEWORKS = ["ISO27001", "RGPD", "LOI0908"]

FRAMEWORK_DISPLAY = {
    "ISO27001": "ISO 27001:2013 (Système de Management de la Sécurité de l'Information)",
    "RGPD": "RGPD — Règlement Général sur la Protection des Données (EU 2016/679)",
    "LOI0908": "Loi 09-08 — Protection des Données Personnelles au Maroc",
}

FRAMEWORK_DOMAINS = {
    "ISO27001": ISO27001_DOMAINS,
    "RGPD": RGPD_DOMAINS,
    "LOI0908": LOI0908_DOMAINS,
}


def build_compliance_prompt(text: str, framework: str) -> tuple[str, str]:
    """Return (system, user) prompts for a given framework compliance check."""
    display_name = FRAMEWORK_DISPLAY.get(framework, framework)
    domains = FRAMEWORK_DOMAINS.get(framework, "")
    system = COMPLIANCE_SYSTEM_PROMPT.format(framework=display_name)
    user = COMPLIANCE_USER_PROMPT.format(
        framework=framework,
        framework_display=display_name,
        domains=domains,
        text=text,
    )
    return system, user
