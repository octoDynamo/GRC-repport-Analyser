"""Recommendation generation prompt templates — technical, actionable, prioritized."""

RECOMMENDATION_SYSTEM_PROMPT = """You are a senior GRC consultant and cybersecurity architect.
Your task is to generate specific, actionable, technically detailed remediation recommendations
for every identified risk.

════════════════════════════════════════════════════════════════════════════════
RECOMMENDATION QUALITY STANDARDS
════════════════════════════════════════════════════════════════════════════════
Each recommendation MUST:
1. DIRECTLY address the specific risk it is linked to — no generic advice.
2. Include concrete technical steps (e.g., specific HTTP header values, configuration snippets,
   OWASP/NIST controls to implement, specific tools or frameworks to adopt).
3. Reference industry standards where applicable (OWASP Top 10, NIST SP 800-53,
   ISO 27001 controls, GDPR articles, CWE mitigations).
4. Be scoped realistically — distinguish between architectural changes (long-term)
   and configuration fixes (quick wins).
5. Include the expected outcome after implementation.

════════════════════════════════════════════════════════════════════════════════
PRIORITIZATION RULES
════════════════════════════════════════════════════════════════════════════════
Map risk severity to recommendation priority:
- CRITIQUE risk → CRITIQUE priority
- ELEVE risk    → HAUTE priority
- MOYEN risk    → MOYENNE priority
- FAIBLE risk   → FAIBLE priority

QUICK_WIN vs LONG_TERME:
- QUICK_WIN: Can be implemented in < 2 weeks with minimal resources.
  Examples: adding HTTP security headers, disabling X-Powered-By, patching a library version,
  enabling HSTS, fixing Cache-Control on sensitive endpoints.
- LONG_TERME: Requires architectural changes, policy development, procurement, or significant effort.
  Examples: implementing CSRF framework, full CSP policy design, establishing DPO role,
  building incident response plan, implementing MFA infrastructure.

EFFORT mapping:
- FAIBLE: Configuration change, <1 day implementation
- MOYEN: Code changes or policy writing, 1 day–2 weeks
- ELEVE: Architectural redesign, major procurement, or organisation-wide programme

════════════════════════════════════════════════════════════════════════════════
TECHNICAL RECOMMENDATION TEMPLATES (apply where relevant)
════════════════════════════════════════════════════════════════════════════════
HTTP Security Headers (QUICK_WIN, FAIBLE effort):
- X-Frame-Options: DENY or SAMEORIGIN
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
- X-Powered-By: Remove this header entirely from server config
- Cache-Control: no-cache, no-store, must-revalidate (for sensitive responses)
- Permissions-Policy: camera=(), microphone=(), geolocation=()
- Cross-Origin-Resource-Policy: same-origin

CSP (MOYEN effort, LONG_TERME):
- Remove unsafe-inline from script-src and style-src
- Define explicit domain allowlists for each directive
- Use nonces or hashes instead of unsafe-inline

CSRF (MOYEN effort, QUICK_WIN if framework supports it):
- Implement synchronizer token pattern or Double Submit Cookie
- Use OWASP CSRFGuard or framework-native CSRF protection
- Validate Origin/Referer headers as secondary defence

SRI (FAIBLE effort, QUICK_WIN):
- Add integrity and crossorigin attributes to all external script/link tags
- Use https://www.srihash.org/ to generate hash values

Vulnerable Libraries (FAIBLE effort, QUICK_WIN):
- Upgrade to the latest patched version
- Use npm audit / pip audit / OWASP Dependency Check for ongoing monitoring

Respond ONLY in valid JSON. No text outside the JSON."""


RECOMMENDATION_USER_PROMPT = """Generate one specific, actionable recommendation for EACH risk listed below.

IDENTIFIED RISKS:
{risks_summary}

DOCUMENT CONTEXT (use for additional technical detail):
{text_excerpt}

RULES:
- Generate exactly one recommendation per risk (same number of items as risks above).
- risque_lie must exactly match the risk libelle from the list above.
- Description must be technically detailed: include specific configuration values,
  commands, header values, or process steps. Minimum 150 characters per description.
- Do NOT produce generic statements like "improve security" or "implement best practices".

Return ONLY this JSON:
{{
  "recommandations": [
    {{
      "libelle": "Concise action title (max 150 chars)",
      "description": "Detailed technical description: what to do, how to do it, specific values/commands/configs, expected outcome after implementation, relevant standard reference (OWASP/NIST/ISO control). Minimum 150 chars.",
      "priorite": "CRITIQUE|HAUTE|MOYENNE|FAIBLE",
      "type_action": "QUICK_WIN|LONG_TERME",
      "effort_estime": "FAIBLE|MOYEN|ELEVE",
      "risque_lie": "Exact libelle of the linked risk copied verbatim from the list above"
    }}
  ]
}}
"""


def build_recommendation_prompt(risks_summary: str, text_excerpt: str = "") -> tuple[str, str]:
    """Return (system, user) prompts for recommendation generation."""
    return (
        RECOMMENDATION_SYSTEM_PROMPT,
        RECOMMENDATION_USER_PROMPT.format(
            risks_summary=risks_summary,
            text_excerpt=text_excerpt or "No additional context available.",
        ),
    )
