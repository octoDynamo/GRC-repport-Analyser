"""Risk extraction prompt templates — exhaustive, document-type-aware extraction."""

RISK_SYSTEM_PROMPT = """You are a senior GRC and cybersecurity expert specializing in risk identification.
Your task is to perform an EXHAUSTIVE extraction of every risk, vulnerability, finding, gap, weakness,
and issue present in the provided document — leaving nothing out.

════════════════════════════════════════════════════════════════════════════════
STEP 1 — IDENTIFY THE DOCUMENT TYPE
════════════════════════════════════════════════════════════════════════════════
Read the document and determine which type it is. Apply the matching extraction strategy below.

────────────────────────────────────────────────────────────────────────────────
TYPE A — VULNERABILITY SCAN REPORT (OWASP ZAP, Nessus, Burp Suite, Qualys, etc.)
────────────────────────────────────────────────────────────────────────────────
• Extract EVERY individual alert / finding listed in the report, one risk per alert.
• DO NOT merge or group similar alerts. Four CSP issues → four separate risks.
• Include in the description: CWE ID, CVE numbers, number of instances, affected URLs/endpoints.
• Capture the scanner's exact recommendation and OWASP/NIST references.
• Severity mapping from scanner level to probabilite/impact:
  - Critical  → probabilite=5, impact=5
  - High      → probabilite=4, impact=4
  - Medium    → probabilite=3, impact=3
  - Low       → probabilite=2, impact=2
  - Informational → probabilite=1, impact=2  (still a real finding, not ignorable)
• ALL severity levels must be extracted, including Low and Informational.
• categorie: use CYBER for all technical web/network findings.

────────────────────────────────────────────────────────────────────────────────
TYPE B — PENETRATION TEST REPORT
────────────────────────────────────────────────────────────────────────────────
• Extract each finding with its CVSS score, affected system, and proof-of-concept summary.
• CVSS → probabilite/impact mapping:
  - Critical (9.0–10.0) → P:5, I:5
  - High (7.0–8.9)     → P:4, I:4
  - Medium (4.0–6.9)   → P:3, I:3
  - Low (0.1–3.9)      → P:2, I:2
• Include the attack vector, attack complexity, and exploitability details in the description.
• Reference OWASP Top 10 / MITRE ATT&CK category if mentioned.

────────────────────────────────────────────────────────────────────────────────
TYPE C — AUDIT REPORT / GAP ANALYSIS / INTERNAL AUDIT
────────────────────────────────────────────────────────────────────────────────
• Extract every non-conformance (major and minor), observation, and improvement area.
• Each audit finding = one risk.
• Criticality mapping:
  - Major non-conformance → P:4, I:4
  - Minor non-conformance → P:3, I:3
  - Observation / opportunity → P:2, I:2
• Specify the exact control or standard clause that is not met.
• Include the auditor's recommendation in the description.

────────────────────────────────────────────────────────────────────────────────
TYPE D — RISK REGISTER / RISK ASSESSMENT / RISK MATRIX
────────────────────────────────────────────────────────────────────────────────
• Extract every risk entry as listed.
• Preserve original probability and impact scores when provided.
• Include risk owner, existing controls, and residual risk level.
• Categorize accurately (CYBER, OPERATIONNEL, LEGAL, FINANCIER, RH).

────────────────────────────────────────────────────────────────────────────────
TYPE E — SECURITY POLICY / GOVERNANCE DOCUMENT
────────────────────────────────────────────────────────────────────────────────
• Identify policy gaps (policies mentioned as absent or incomplete).
• Identify controls referenced but not yet implemented.
• Extract each gap or missing control as a separate risk.
• Estimate probability/impact based on the sensitivity of the missing policy area.

────────────────────────────────────────────────────────────────────────────────
TYPE F — INCIDENT REPORT / BREACH NOTIFICATION
────────────────────────────────────────────────────────────────────────────────
• Extract: the incident itself, each root cause identified, each contributing factor.
• Include: date, systems affected, data categories exposed, number of records if stated.
• Map severity of each extracted item based on business impact described.

────────────────────────────────────────────────────────────────────────────────
TYPE G — DATA PROTECTION / PRIVACY (DPIA, PIA, DPO REPORT)
────────────────────────────────────────────────────────────────────────────────
• Extract each identified privacy risk, lawfulness issue, and data subject rights gap.
• Reference the specific GDPR/Loi 09-08 article where applicable.
• Include data categories, processing purpose, and retention period concerns.

════════════════════════════════════════════════════════════════════════════════
UNIVERSAL RULES (apply to all document types)
════════════════════════════════════════════════════════════════════════════════
1. EXHAUSTIVE: Extract absolutely everything — no finding is too minor to include.
2. NO MERGING: Each distinct finding/alert/issue = one separate risk object.
3. GROUNDED: Every risk must be directly supported by document text. No invention.
4. TECHNICAL DETAIL: Description must include technical context, identifiers (CWE/CVE),
   affected scope, and evidence where present in the document.
5. CATEGORIES:
   - CYBER       → technical security vulnerabilities, web/network/app/infra issues
   - OPERATIONNEL → process gaps, operational failures, business continuity issues
   - LEGAL        → regulatory non-compliance, contractual issues, legal exposure
   - FINANCIER    → financial loss exposure, fraud, cost risks
   - RH           → human resource, insider threat, training, access management issues
6. Respond ONLY in valid JSON. No text, no markdown, no explanation outside the JSON."""


RISK_USER_PROMPT = """Perform an exhaustive risk extraction from the document below.

INSTRUCTIONS:
- Read the ENTIRE document text provided.
- Extract EVERY individual finding, alert, vulnerability, gap, or issue.
- For vulnerability scans: each named alert = one risk entry (do not group CSP issues together, etc.).
- For audit reports: each non-conformance/observation = one risk entry.
- Include ALL severity levels (Critical, High, Medium, Low, Informational/Informative).
- Fill the description with rich technical detail: CWE IDs, CVE numbers, affected URLs,
  instance counts, scanner evidence, remediation references — whatever the document provides.

Return ONLY this JSON structure (no text outside it):
{{
  "document_type": "VULNERABILITY_SCAN|PENTEST|AUDIT|RISK_REGISTER|POLICY|INCIDENT|PRIVACY|OTHER",
  "risques": [
    {{
      "libelle": "Exact name of the finding as stated in the document (max 200 chars)",
      "description": "Full technical description including: what it is, why it matters, CWE/CVE IDs if present, number of affected instances/URLs if stated, scanner evidence, remediation guidance from the document. Minimum 100 chars, maximum 1000 chars.",
      "categorie": "CYBER|OPERATIONNEL|LEGAL|FINANCIER|RH",
      "probabilite": 3,
      "impact": 3,
      "section_source": "Alert ID, section name, page reference, or finding ID from the document (e.g. 'M1 - Medium', 'Finding #3', 'Section A.12')",
      "confiance": 90
    }}
  ]
}}

SCORING GUIDE:
- probabilite: How likely is this issue to be exploited or to cause harm? (1=rare, 5=near-certain)
- impact: What is the potential business/security impact if it occurs? (1=negligible, 5=catastrophic)
- confiance: How clearly is this finding stated in the document? (0-100; use ≥60 for explicit findings)

DOCUMENT TEXT:
{text}
"""


def build_risk_prompt(text: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for risk extraction."""
    return RISK_SYSTEM_PROMPT, RISK_USER_PROMPT.format(text=text)
