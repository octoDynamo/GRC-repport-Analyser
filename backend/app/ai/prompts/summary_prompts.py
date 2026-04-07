"""Executive summary prompt templates."""

SUMMARY_SYSTEM_PROMPT = """You are a GRC consultant writing for a CISO audience.
Be concise, structured, and professional. Respond in French."""

SUMMARY_USER_PROMPT = """Write a 300-word executive summary of this GRC analysis.
Structure: 1) Key findings 2) Top 3 risks 3) Compliance status 4) Priority actions

Risks found: {risks_count} risks
ISO 27001 compliance: {iso_score}%
RGPD compliance: {rgpd_score}%
Loi 09-08 compliance: {loi_score}%

Report text excerpt: {text_excerpt}
"""


def build_summary_prompt(
    text: str,
    risks_count: int,
    iso_score: float,
    rgpd_score: float,
    loi_score: float,
) -> tuple[str, str]:
    """Return (system, user) prompts for executive summary generation."""
    return (
        SUMMARY_SYSTEM_PROMPT,
        SUMMARY_USER_PROMPT.format(
            risks_count=risks_count,
            iso_score=round(iso_score, 1),
            rgpd_score=round(rgpd_score, 1),
            loi_score=round(loi_score, 1),
            text_excerpt=text[:3000],
        ),
    )
