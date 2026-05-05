"""Executive summary prompt templates — plain text, structured, CISO-grade."""

SUMMARY_SYSTEM_PROMPT = """You are a GRC consultant writing a concise executive summary for a CISO audience.

CRITICAL FORMAT RULES — READ CAREFULLY:
1. Write ONLY plain text. No Markdown syntax whatsoever.
   - Do NOT use #, ##, ### for headings.
   - Do NOT use **, __, or * for bold or italic.
   - Do NOT use bullet points with *, -, or +.
   - Do NOT use backticks or code blocks.
   - Use numbered sections: "1. KEY FINDINGS", "2. TOP RISKS", etc.
   - Use plain dashes for lists: "- Item" is acceptable only as a plain text dash, not Markdown.
2. Write in French. Professional, direct, executive-level language.
3. Be factual and grounded — only reference data provided to you.
4. Length: 350-450 words total.

STRUCTURE TO FOLLOW:
1. CONTEXTE ET OBJET DU DOCUMENT (2-3 sentences)
   State what type of document was analysed, who produced it, and when.

2. PRINCIPALES CONCLUSIONS (4-6 bullet points as plain numbered list)
   The most important findings: total risks by severity, compliance scores, critical gaps.

3. RISQUES PRIORITAIRES (top 3-5 most severe risks)
   Name each risk, its severity, and one-sentence impact statement.

4. ETAT DE CONFORMITE
   ISO 27001: X% | RGPD: X% | Loi 09-08: X%
   One sentence interpreting the overall compliance posture.

5. ACTIONS IMMEDIATES RECOMMANDEES (top 3 actions, numbered)
   Specific, actionable items the organisation must address first.

6. CONCLUSION
   One paragraph summarising the overall risk level and urgency."""


SUMMARY_USER_PROMPT = """Write the executive summary using the data below. Follow all format rules strictly.

ANALYSIS DATA:
- Document excerpt for context: see below
- Total risks identified: {risks_count}
- Risks by severity: {risks_by_severity}
- Top risks (most critical): {top_risks}
- ISO 27001 compliance score: {iso_score}%
- RGPD compliance score: {rgpd_score}%
- Loi 09-08 compliance score: {loi_score}%
- Overall maturity score: {maturity_score}%
- Recommendations generated: {recs_count} (one per identified risk, being processed in parallel)

DOCUMENT EXCERPT (first 4000 chars):
{text_excerpt}

IMPORTANT: The recommendations count above is the expected total — do NOT state that no recommendations were generated.
Remember: plain text only, no Markdown, write in French, 350-450 words.
"""


def build_summary_prompt(
    text: str,
    risks_count: int,
    iso_score: float,
    rgpd_score: float,
    loi_score: float,
    risks_by_severity: dict | None = None,
    top_risks: list | None = None,
    recs_count: int = 0,
) -> tuple[str, str]:
    """Return (system, user) prompts for executive summary generation."""
    maturity = round((iso_score + rgpd_score + loi_score) / 3, 1)

    severity_text = "Non disponible"
    if risks_by_severity:
        parts = []
        for sev in ("CRITIQUE", "ELEVE", "MOYEN", "FAIBLE"):
            count = risks_by_severity.get(sev, 0)
            if count > 0:
                parts.append(f"{count} {sev.lower()}")
        severity_text = ", ".join(parts) if parts else "aucun"

    top_risks_text = "Non disponible"
    if top_risks:
        top_risks_text = "; ".join(
            [f"{r['libelle']} (sévérité: {r['severite']}, score: {r['score']})" for r in top_risks[:5]]
        )

    return (
        SUMMARY_SYSTEM_PROMPT,
        SUMMARY_USER_PROMPT.format(
            risks_count=risks_count,
            risks_by_severity=severity_text,
            top_risks=top_risks_text,
            iso_score=round(iso_score, 1),
            rgpd_score=round(rgpd_score, 1),
            loi_score=round(loi_score, 1),
            maturity_score=maturity,
            recs_count=recs_count,
            text_excerpt=text[:4000],
        ),
    )
