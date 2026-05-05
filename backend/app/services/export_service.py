"""Export service — generates PDF and Excel reports from analysis data."""
import io
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analyse import Analyse
from app.models.risque import Risque
from app.models.conformite import ResultatConformite
from app.models.recommandation import Recommandation
from app.models.rapport import Rapport


# ── Colour palette ────────────────────────────────────────────────────────────
_NAVY       = (0x1E / 255, 0x3A / 255, 0x5F / 255)
_BLUE       = (0x2E / 255, 0x86 / 255, 0xC1 / 255)
_LIGHT_BLUE = (0xD6 / 255, 0xEA / 255, 0xF8 / 255)
_WHITE      = (1, 1, 1)
_LIGHT_GREY = (0xF2 / 255, 0xF3 / 255, 0xF4 / 255)
_DARK_GREY  = (0x4A / 255, 0x4A / 255, 0x4A / 255)

_SEV_COLORS = {
    "CRITIQUE": (0xC0 / 255, 0x39 / 255, 0x2B / 255),
    "ELEVE":    (0xE7 / 255, 0x4C / 255, 0x3C / 255),
    "MOYEN":    (0xF3 / 255, 0x9C / 255, 0x12 / 255),
    "FAIBLE":   (0x27 / 255, 0xAE / 255, 0x60 / 255),
}

_PRIO_COLORS = {
    "CRITIQUE": (0xC0 / 255, 0x39 / 255, 0x2B / 255),
    "HAUTE":    (0xE7 / 255, 0x4C / 255, 0x3C / 255),
    "MOYENNE":  (0xF3 / 255, 0x9C / 255, 0x12 / 255),
    "FAIBLE":   (0x27 / 255, 0xAE / 255, 0x60 / 255),
}

_CONFORMITE_COLORS = {
    "CONFORME":         (0x27 / 255, 0xAE / 255, 0x60 / 255),
    "PARTIELLEMENT":    (0xF3 / 255, 0x9C / 255, 0x12 / 255),
    "NON_CONFORME":     (0xC0 / 255, 0x39 / 255, 0x2B / 255),
}

_FRAMEWORK_LABELS = {
    "ISO27001": "ISO 27001",
    "RGPD": "RGPD",
    "LOI0908": "Loi 09-08",
}


def _rgb(*t):
    from reportlab.lib.colors import Color
    return Color(*t)


# ── Page template (header / footer) ───────────────────────────────────────────
def _make_header_footer(rapport_nom: str, generated: str):
    from reportlab.platypus import Frame
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor

    nav = HexColor("#1E3A5F")
    grey = HexColor("#888888")

    def draw(canvas, doc):
        canvas.saveState()
        W, H = A4

        # Header bar
        canvas.setFillColor(nav)
        canvas.rect(0, H - 1.2 * cm, W, 1.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#FFFFFF"))
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(1.5 * cm, H - 0.8 * cm, "GRC AI ANALYZER")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W - 1.5 * cm, H - 0.8 * cm, rapport_nom[:60])

        # Footer line
        canvas.setStrokeColor(HexColor("#CCCCCC"))
        canvas.setLineWidth(0.5)
        canvas.line(1.5 * cm, 1.2 * cm, W - 1.5 * cm, 1.2 * cm)
        canvas.setFillColor(grey)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(1.5 * cm, 0.7 * cm, f"Généré le {generated} — Confidentiel")
        canvas.drawRightString(W - 1.5 * cm, 0.7 * cm, f"Page {doc.page}")

        canvas.restoreState()

    return draw


# ── Helpers ───────────────────────────────────────────────────────────────────
def _section_title(text: str, styles):
    from reportlab.platypus import Paragraph, HRFlowable, Spacer
    from reportlab.lib.colors import HexColor
    items = [
        Spacer(1, 10),
        Paragraph(text, styles["SectionTitle"]),
        HRFlowable(width="100%", thickness=2, color=HexColor("#2E86C1"), spaceAfter=6),
    ]
    return items


def _badge(text: str, color_rgb):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import Color, white
    bg = Color(*color_rgb)
    style = ParagraphStyle(
        "badge",
        fontSize=8,
        textColor=white,
        backColor=bg,
        borderPadding=(2, 4, 2, 4),
        fontName="Helvetica-Bold",
    )
    return Paragraph(f"&nbsp;{text}&nbsp;", style)


def _header_row_style():
    from reportlab.platypus import TableStyle
    from reportlab.lib.colors import HexColor, white
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F2F3F4")]),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


async def _fetch_all(db: AsyncSession, analyse_id: uuid.UUID):
    analyse_res = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    analyse = analyse_res.scalar_one_or_none()
    if not analyse:
        raise ValueError("Analyse not found")

    rapport_res = await db.execute(select(Rapport).where(Rapport.id == analyse.rapport_id))
    rapport = rapport_res.scalar_one_or_none()

    risques_res  = await db.execute(select(Risque).where(Risque.analyse_id == analyse_id).order_by(Risque.score_risque.desc()))
    conformites_res = await db.execute(select(ResultatConformite).where(ResultatConformite.analyse_id == analyse_id))
    recs_res = await db.execute(select(Recommandation).where(Recommandation.analyse_id == analyse_id))

    return (
        analyse,
        rapport,
        list(risques_res.scalars().all()),
        list(conformites_res.scalars().all()),
        list(recs_res.scalars().all()),
    )


# ── PDF export ────────────────────────────────────────────────────────────────
async def export_to_pdf(db: AsyncSession, analyse_id: uuid.UUID) -> bytes:
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame,
        Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    analyse, rapport, risques, conformites, recommandations = await _fetch_all(db, analyse_id)

    rapport_nom = rapport.nom if rapport else "Rapport GRC"
    generated   = datetime.now().strftime("%d/%m/%Y à %H:%M")

    output = io.BytesIO()
    W, H   = A4
    margin = 1.8 * cm

    # ── Doc template with header/footer ───────────────────────────────────────
    doc = BaseDocTemplate(
        output, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=2.2 * cm, bottomMargin=2 * cm,
    )
    frame = Frame(margin, 2 * cm, W - 2 * margin, H - 4.2 * cm, id="normal")
    draw_page = _make_header_footer(rapport_nom, generated)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_page)])

    # ── Custom styles ──────────────────────────────────────────────────────────
    base = getSampleStyleSheet()
    S = dict(
        Title=ParagraphStyle("Title", fontSize=26, fontName="Helvetica-Bold",
                             textColor=HexColor("#1E3A5F"), alignment=TA_CENTER, spaceAfter=6),
        Subtitle=ParagraphStyle("Subtitle", fontSize=13, fontName="Helvetica",
                                textColor=HexColor("#2E86C1"), alignment=TA_CENTER, spaceAfter=4),
        SectionTitle=ParagraphStyle("SectionTitle", fontSize=13, fontName="Helvetica-Bold",
                                    textColor=HexColor("#1E3A5F"), spaceBefore=10, spaceAfter=4),
        Body=ParagraphStyle("Body", fontSize=9, fontName="Helvetica",
                            textColor=HexColor("#333333"), leading=14, spaceAfter=6,
                            alignment=TA_JUSTIFY),
        Small=ParagraphStyle("Small", fontSize=8, fontName="Helvetica",
                             textColor=HexColor("#555555"), leading=12),
        CoverMeta=ParagraphStyle("CoverMeta", fontSize=10, fontName="Helvetica",
                                 textColor=HexColor("#555555"), alignment=TA_CENTER, spaceAfter=3),
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * cm))

    # Blue banner
    banner_data = [[Paragraph(
        '<font color="white"><b>RAPPORT D\'ANALYSE GRC</b></font>',
        ParagraphStyle("banner", fontSize=20, fontName="Helvetica-Bold",
                       alignment=TA_CENTER, textColor=white)
    )]]
    banner = Table(banner_data, colWidths=[W - 2 * margin])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1E3A5F")),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(rapport_nom, S["Subtitle"]))
    story.append(Spacer(1, 1 * cm))

    # Score de maturité badge
    score = analyse.score_maturite or 0
    if score >= 75:
        score_color = "#27AE60"
    elif score >= 50:
        score_color = "#F39C12"
    else:
        score_color = "#E74C3C"

    score_data = [[
        Paragraph(
            f'<font color="{score_color}" size="32"><b>{score:.0f}%</b></font>',
            ParagraphStyle("sc", alignment=TA_CENTER, fontSize=32, fontName="Helvetica-Bold")
        ),
    ], [
        Paragraph("Score de Maturité Global", S["CoverMeta"]),
    ]]
    score_box = Table(score_data, colWidths=[W - 2 * margin])
    score_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F8F9FA")),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_box)
    story.append(Spacer(1, 1.5 * cm))

    # Stats summary
    sev_counts = {s: sum(1 for r in risques if r.severite == s)
                  for s in ("CRITIQUE", "ELEVE", "MOYEN", "FAIBLE")}
    stats_data = [
        [Paragraph("<b>Statistiques</b>", ParagraphStyle("sh", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
         Paragraph("<b>Risques</b>", ParagraphStyle("sh", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
         Paragraph("<b>Conformités</b>", ParagraphStyle("sh", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)),
         Paragraph("<b>Recommandations</b>", ParagraphStyle("sh", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER))],
        [Paragraph("Total identifiés",
                   ParagraphStyle("sv", fontSize=9, alignment=TA_CENTER, textColor=HexColor("#555555"))),
         Paragraph(f"<b>{len(risques)}</b>", ParagraphStyle("sv2", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=HexColor("#1E3A5F"))),
         Paragraph(f"<b>{len(conformites)}</b>", ParagraphStyle("sv2", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=HexColor("#1E3A5F"))),
         Paragraph(f"<b>{len(recommandations)}</b>", ParagraphStyle("sv2", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=HexColor("#1E3A5F")))],
    ]
    stats_box = Table(stats_data, colWidths=[(W - 2 * margin) / 4] * 4)
    stats_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E86C1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FFFFFF")),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CCCCCC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(stats_box)
    story.append(Spacer(1, 1.5 * cm))

    story.append(Paragraph(f"Généré le {generated}", S["CoverMeta"]))
    story.append(Paragraph("Document confidentiel — Usage interne uniquement", S["CoverMeta"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — RÉSUMÉ EXÉCUTIF
    # ══════════════════════════════════════════════════════════════════════════
    story += _section_title("1. Résumé Exécutif", S)

    if analyse.resume_executif:
        for para in analyse.resume_executif.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para.replace("\n", " "), S["Body"]))
                story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Aucun résumé disponible.", S["Body"]))

    story.append(Spacer(1, 0.5 * cm))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — ANALYSE DES RISQUES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section_title("2. Analyse des Risques", S)

    if risques:
        # Severity breakdown table
        sev_rows = [
            [Paragraph("<b>Sévérité</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=white)),
             Paragraph("<b>Nombre</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=white)),
             Paragraph("<b>% du total</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=white))],
        ]
        for sev in ("CRITIQUE", "ELEVE", "MOYEN", "FAIBLE"):
            count = sev_counts[sev]
            pct   = count / len(risques) * 100 if risques else 0
            sev_rows.append([
                _badge(sev, _SEV_COLORS[sev]),
                Paragraph(str(count), ParagraphStyle("c", fontSize=9, alignment=TA_CENTER)),
                Paragraph(f"{pct:.0f}%", ParagraphStyle("c", fontSize=9, alignment=TA_CENTER)),
            ])
        sev_table = Table(sev_rows, colWidths=[5 * cm, 4 * cm, 5 * cm])
        sev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F2F3F4")]),
            ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether([sev_table]))
        story.append(Spacer(1, 0.5 * cm))

        # Full risks table
        story.append(Paragraph("Détail des risques identifiés", S["Small"]))
        story.append(Spacer(1, 4))

        risk_rows = [[
            Paragraph("<b>#</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>ID</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Libellé &amp; Description</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("<b>Cat.</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>P</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>I</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Score</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Sévérité</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
        ]]
        ts = _header_row_style()
        for i, r in enumerate(risques, 1):
            # Build combined libellé + description snippet cell
            desc_snippet = ""
            if r.description:
                desc_snippet = r.description[:160].replace("<", "&lt;").replace(">", "&gt;").strip()
                if len(r.description) > 160:
                    desc_snippet += "…"
            libelle_content = (
                f"<b>{r.libelle[:80]}</b>"
                + (f"<br/><font size='6' color='#666666'>{desc_snippet}</font>" if desc_snippet else "")
            )
            section_id = r.section_source[:10] if r.section_source else "—"
            risk_rows.append([
                Paragraph(str(i), ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(section_id, ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER, fontName="Helvetica-Bold")),
                Paragraph(libelle_content, ParagraphStyle("l", fontSize=7.5, leading=10)),
                Paragraph(r.categorie[:5], ParagraphStyle("n", fontSize=7, alignment=TA_CENTER)),
                Paragraph(str(r.probabilite), ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(str(r.impact), ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(f"{r.score_risque:.0f}", ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                _badge(r.severite, _SEV_COLORS.get(r.severite, (0.5, 0.5, 0.5))),
            ])

        risk_table = Table(risk_rows, colWidths=[0.7 * cm, 1.2 * cm, 7.8 * cm, 1.4 * cm, 0.7 * cm, 0.7 * cm, 1.0 * cm, 1.7 * cm])
        risk_table.setStyle(ts)
        story.append(risk_table)
    else:
        story.append(Paragraph("Aucun risque identifié.", S["Body"]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — CONFORMITÉ
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section_title("3. Résultats de Conformité", S)

    if conformites:
        frameworks = {}
        for c in conformites:
            frameworks.setdefault(c.referentiel, []).append(c)

        for fw, items in frameworks.items():
            fw_label = _FRAMEWORK_LABELS.get(fw, fw)
            avg_rate = sum(c.taux_conformite for c in items) / len(items)
            story.append(Spacer(1, 6))
            fw_header = Table(
                [[Paragraph(f"<b>{fw_label}</b>  —  Taux moyen: <b>{avg_rate:.0f}%</b>",
                            ParagraphStyle("fwh", fontSize=10, fontName="Helvetica-Bold",
                                           textColor=white))]],
                colWidths=[W - 2 * margin]
            )
            fw_header.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#2E86C1")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(fw_header)

            conf_rows = [[
                Paragraph("<b>Domaine</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
                Paragraph("<b>Statut</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
                Paragraph("<b>Taux</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
                Paragraph("<b>Écart</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            ]]
            for c in items:
                conf_rows.append([
                    Paragraph((c.domaine or fw_label)[:60], ParagraphStyle("d", fontSize=8, leading=11)),
                    _badge(c.statut, _CONFORMITE_COLORS.get(c.statut, (0.5, 0.5, 0.5))),
                    Paragraph(f"{c.taux_conformite:.0f}%", ParagraphStyle("t", fontSize=8, alignment=TA_CENTER)),
                    Paragraph((c.ecart or "—")[:80], ParagraphStyle("e", fontSize=7.5, leading=10)),
                ])
            conf_table = Table(conf_rows, colWidths=[4.5 * cm, 2.8 * cm, 1.5 * cm, 6 * cm])
            conf_table.setStyle(_header_row_style())
            story.append(conf_table)
            story.append(Spacer(1, 0.5 * cm))
    else:
        story.append(Paragraph("Aucun résultat de conformité disponible.", S["Body"]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — RECOMMANDATIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story += _section_title("4. Recommandations", S)

    if recommandations:
        recs_sorted = sorted(
            recommandations,
            key=lambda r: ["CRITIQUE", "HAUTE", "MOYENNE", "FAIBLE"].index(r.priorite)
        )
        rec_rows = [[
            Paragraph("<b>#</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Recommandation</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white)),
            Paragraph("<b>Priorité</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Type</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Effort</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
            Paragraph("<b>Statut</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=white, alignment=TA_CENTER)),
        ]]
        for i, r in enumerate(recs_sorted, 1):
            type_label = "Rapide" if r.type_action == "QUICK_WIN" else "Long terme"
            statut_label = {"A_FAIRE": "À faire", "EN_COURS": "En cours", "CLOTURE": "Clôturé"}.get(r.statut, r.statut)
            rec_rows.append([
                Paragraph(str(i), ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(r.libelle[:90], ParagraphStyle("l", fontSize=7.5, leading=10)),
                _badge(r.priorite, _PRIO_COLORS.get(r.priorite, (0.5, 0.5, 0.5))),
                Paragraph(type_label, ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(r.effort_estime, ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
                Paragraph(statut_label, ParagraphStyle("n", fontSize=7.5, alignment=TA_CENTER)),
            ])
        rec_table = Table(rec_rows, colWidths=[0.8 * cm, 7 * cm, 2 * cm, 2 * cm, 1.5 * cm, 1.5 * cm])
        rec_table.setStyle(_header_row_style())
        story.append(rec_table)
    else:
        story.append(Paragraph("Aucune recommandation disponible.", S["Body"]))

    # ── Build ──────────────────────────────────────────────────────────────────
    doc.build(story)
    output.seek(0)
    return output.read()


# ── Excel export ──────────────────────────────────────────────────────────────
async def export_to_excel(db: AsyncSession, analyse_id: uuid.UUID) -> bytes:
    import xlsxwriter

    analyse, rapport, risques, conformites, recommandations = await _fetch_all(db, analyse_id)

    output   = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Formats
    hdr  = workbook.add_format({"bold": True, "bg_color": "#1E3A5F", "font_color": "white",
                                 "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True})
    title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1E3A5F"})
    meta_fmt  = workbook.add_format({"font_color": "#555555", "italic": True})
    even  = workbook.add_format({"bg_color": "#F2F3F4", "border": 1, "valign": "vcenter", "text_wrap": True})
    odd   = workbook.add_format({"bg_color": "#FFFFFF",  "border": 1, "valign": "vcenter", "text_wrap": True})
    center_even = workbook.add_format({"bg_color": "#F2F3F4", "border": 1, "align": "center", "valign": "vcenter"})
    center_odd  = workbook.add_format({"bg_color": "#FFFFFF",  "border": 1, "align": "center", "valign": "vcenter"})

    sev_fmts = {
        "CRITIQUE": workbook.add_format({"bg_color": "#C0392B", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
        "ELEVE":    workbook.add_format({"bg_color": "#E74C3C", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
        "MOYEN":    workbook.add_format({"bg_color": "#F39C12", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
        "FAIBLE":   workbook.add_format({"bg_color": "#27AE60", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
    }
    prio_fmts = {
        "CRITIQUE": sev_fmts["CRITIQUE"],
        "HAUTE":    sev_fmts["ELEVE"],
        "MOYENNE":  sev_fmts["MOYEN"],
        "FAIBLE":   sev_fmts["FAIBLE"],
    }
    conf_fmts = {
        "CONFORME":      workbook.add_format({"bg_color": "#27AE60", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
        "PARTIELLEMENT": workbook.add_format({"bg_color": "#F39C12", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
        "NON_CONFORME":  workbook.add_format({"bg_color": "#C0392B", "font_color": "white", "bold": True, "border": 1, "align": "center"}),
    }

    def row_fmt(i, centered=False):
        if centered:
            return center_even if i % 2 == 0 else center_odd
        return even if i % 2 == 0 else odd

    rapport_nom = rapport.nom if rapport else "Rapport GRC"
    generated   = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── Sheet 1: Résumé ────────────────────────────────────────────────────────
    ws = workbook.add_worksheet("Résumé exécutif")
    ws.set_column(0, 0, 22)
    ws.set_column(1, 1, 65)
    ws.write(0, 0, "GRC AI Analyzer — Rapport d'Analyse", title_fmt)
    ws.write(1, 0, rapport_nom, meta_fmt)
    ws.write(2, 0, f"Généré le {generated}", meta_fmt)
    ws.write(4, 0, "Score de maturité:", hdr)
    ws.write(4, 1, f"{analyse.score_maturite or 0:.1f}%")
    ws.write(5, 0, "Nombre de risques:", hdr)
    ws.write(5, 1, len(risques))
    ws.write(6, 0, "Nombre de recommandations:", hdr)
    ws.write(6, 1, len(recommandations))
    ws.write(8, 0, "Résumé exécutif:", hdr)
    ws.write(8, 1, analyse.resume_executif or "")
    ws.set_row(8, 80)

    # ── Sheet 2: Risques ───────────────────────────────────────────────────────
    ws = workbook.add_worksheet("Risques")
    ws.freeze_panes(1, 0)
    ws.set_column(0, 0, 60)  # libelle
    ws.set_column(1, 1, 30)  # description
    ws.set_column(2, 2, 15)  # categorie
    ws.set_column(3, 5, 12)  # P, I, Score
    ws.set_column(6, 6, 12)  # severite
    ws.set_column(7, 7, 30)  # section
    headers = ["Libellé", "Description", "Catégorie", "Probabilité", "Impact", "Score", "Sévérité", "Section source"]
    for col, h in enumerate(headers):
        ws.write(0, col, h, hdr)
    for i, r in enumerate(risques, 1):
        f = row_fmt(i)
        fc = row_fmt(i, centered=True)
        ws.write(i, 0, r.libelle, f)
        ws.write(i, 1, r.description or "", f)
        ws.write(i, 2, r.categorie, fc)
        ws.write(i, 3, r.probabilite, fc)
        ws.write(i, 4, r.impact, fc)
        ws.write(i, 5, r.score_risque, fc)
        ws.write(i, 6, r.severite, sev_fmts.get(r.severite, fc))
        ws.write(i, 7, r.section_source or "", f)

    # ── Sheet 3: Conformité ────────────────────────────────────────────────────
    ws = workbook.add_worksheet("Conformité")
    ws.freeze_panes(1, 0)
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 40)
    ws.set_column(2, 2, 18)
    ws.set_column(3, 3, 12)
    ws.set_column(4, 4, 50)
    headers = ["Référentiel", "Domaine", "Statut", "Taux (%)", "Écart"]
    for col, h in enumerate(headers):
        ws.write(0, col, h, hdr)
    for i, c in enumerate(conformites, 1):
        f = row_fmt(i)
        fc = row_fmt(i, centered=True)
        ws.write(i, 0, _FRAMEWORK_LABELS.get(c.referentiel, c.referentiel), fc)
        ws.write(i, 1, c.domaine or "", f)
        ws.write(i, 2, c.statut, conf_fmts.get(c.statut, fc))
        ws.write(i, 3, c.taux_conformite, fc)
        ws.write(i, 4, c.ecart or "", f)

    # ── Sheet 4: Recommandations ───────────────────────────────────────────────
    ws = workbook.add_worksheet("Recommandations")
    ws.freeze_panes(1, 0)
    ws.set_column(0, 0, 60)
    ws.set_column(1, 1, 40)
    ws.set_column(2, 2, 12)
    ws.set_column(3, 3, 14)
    ws.set_column(4, 4, 12)
    ws.set_column(5, 5, 12)
    headers = ["Libellé", "Description", "Priorité", "Type d'action", "Effort", "Statut"]
    for col, h in enumerate(headers):
        ws.write(0, col, h, hdr)
    recs_sorted = sorted(recommandations,
                         key=lambda r: ["CRITIQUE", "HAUTE", "MOYENNE", "FAIBLE"].index(r.priorite))
    for i, r in enumerate(recs_sorted, 1):
        f = row_fmt(i)
        fc = row_fmt(i, centered=True)
        ws.write(i, 0, r.libelle, f)
        ws.write(i, 1, r.description or "", f)
        ws.write(i, 2, r.priorite, prio_fmts.get(r.priorite, fc))
        ws.write(i, 3, r.type_action, fc)
        ws.write(i, 4, r.effort_estime, fc)
        ws.write(i, 5, r.statut, fc)

    workbook.close()
    output.seek(0)
    return output.read()
