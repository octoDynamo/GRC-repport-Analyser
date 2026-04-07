"""Export service — generates PDF and Excel reports from analysis data."""
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analyse import Analyse
from app.models.risque import Risque
from app.models.conformite import ResultatConformite
from app.models.recommandation import Recommandation


async def export_to_excel(db: AsyncSession, analyse_id: uuid.UUID) -> bytes:
    """Generate an Excel report for the analysis."""
    import xlsxwriter

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Styles
    bold = workbook.add_format({"bold": True, "bg_color": "#003366", "font_color": "white"})
    red = workbook.add_format({"bg_color": "#FF4444", "font_color": "white"})
    orange = workbook.add_format({"bg_color": "#FF8800", "font_color": "white"})
    yellow = workbook.add_format({"bg_color": "#FFCC00"})
    green = workbook.add_format({"bg_color": "#44BB44", "font_color": "white"})

    severity_formats = {"CRITIQUE": red, "ELEVE": orange, "MOYEN": yellow, "FAIBLE": green}

    # Fetch data
    analyse_res = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    analyse = analyse_res.scalar_one_or_none()
    if not analyse:
        raise ValueError("Analyse not found")

    risques_res = await db.execute(select(Risque).where(Risque.analyse_id == analyse_id))
    risques = list(risques_res.scalars().all())

    conf_res = await db.execute(select(ResultatConformite).where(ResultatConformite.analyse_id == analyse_id))
    conformites = list(conf_res.scalars().all())

    rec_res = await db.execute(select(Recommandation).where(Recommandation.analyse_id == analyse_id))
    recommandations = list(rec_res.scalars().all())

    # Sheet 1: Summary
    ws_summary = workbook.add_worksheet("Résumé")
    ws_summary.write(0, 0, "Analyse GRC — Résumé Exécutif", bold)
    ws_summary.write(2, 0, "Score de maturité:", bold)
    ws_summary.write(2, 1, f"{analyse.score_maturite or 0:.1f}%")
    ws_summary.write(3, 0, "Résumé:", bold)
    ws_summary.write(3, 1, analyse.resume_executif or "")

    # Sheet 2: Risks
    ws_risks = workbook.add_worksheet("Risques")
    headers = ["Libellé", "Catégorie", "Probabilité", "Impact", "Score", "Sévérité", "Section"]
    for col, h in enumerate(headers):
        ws_risks.write(0, col, h, bold)
    for row, r in enumerate(risques, 1):
        fmt = severity_formats.get(r.severite)
        ws_risks.write(row, 0, r.libelle)
        ws_risks.write(row, 1, r.categorie)
        ws_risks.write(row, 2, r.probabilite)
        ws_risks.write(row, 3, r.impact)
        ws_risks.write(row, 4, r.score_risque)
        ws_risks.write(row, 5, r.severite, fmt)
        ws_risks.write(row, 6, r.section_source or "")

    # Sheet 3: Compliance
    ws_conf = workbook.add_worksheet("Conformité")
    headers = ["Référentiel", "Domaine", "Statut", "Écart", "Taux (%)"]
    for col, h in enumerate(headers):
        ws_conf.write(0, col, h, bold)
    for row, c in enumerate(conformites, 1):
        ws_conf.write(row, 0, c.referentiel)
        ws_conf.write(row, 1, c.domaine or "")
        ws_conf.write(row, 2, c.statut)
        ws_conf.write(row, 3, c.ecart or "")
        ws_conf.write(row, 4, c.taux_conformite)

    # Sheet 4: Recommendations
    ws_rec = workbook.add_worksheet("Recommandations")
    headers = ["Libellé", "Priorité", "Type", "Effort", "Statut"]
    for col, h in enumerate(headers):
        ws_rec.write(0, col, h, bold)
    for row, r in enumerate(recommandations, 1):
        ws_rec.write(row, 0, r.libelle)
        ws_rec.write(row, 1, r.priorite)
        ws_rec.write(row, 2, r.type_action)
        ws_rec.write(row, 3, r.effort_estime)
        ws_rec.write(row, 4, r.statut)

    workbook.close()
    output.seek(0)
    return output.read()


async def export_to_pdf(db: AsyncSession, analyse_id: uuid.UUID) -> bytes:
    """Generate a PDF report for the analysis."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Fetch data
    analyse_res = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    analyse = analyse_res.scalar_one_or_none()
    if not analyse:
        raise ValueError("Analyse not found")

    risques_res = await db.execute(select(Risque).where(Risque.analyse_id == analyse_id))
    risques = list(risques_res.scalars().all())

    conf_res = await db.execute(select(ResultatConformite).where(ResultatConformite.analyse_id == analyse_id))
    conformites = list(conf_res.scalars().all())

    # Title
    story.append(Paragraph("GRC AI Analyzer — Rapport d'Analyse", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Score de maturité: {analyse.score_maturite or 0:.1f}%", styles["Heading2"]))
    story.append(Spacer(1, 6))

    if analyse.resume_executif:
        story.append(Paragraph("Résumé Exécutif", styles["Heading2"]))
        story.append(Paragraph(analyse.resume_executif, styles["Normal"]))
        story.append(Spacer(1, 12))

    # Risks table
    if risques:
        story.append(Paragraph(f"Risques identifiés ({len(risques)})", styles["Heading2"]))
        data = [["Libellé", "Catégorie", "Score", "Sévérité"]]
        for r in risques[:20]:
            data.append([r.libelle[:60], r.categorie, str(r.score_risque), r.severite])

        t = Table(data, colWidths=[250, 80, 50, 70])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Compliance table
    if conformites:
        story.append(Paragraph("Résultats de conformité", styles["Heading2"]))
        data = [["Référentiel", "Domaine", "Statut", "Taux (%)"]]
        for c in conformites:
            data.append([c.referentiel, (c.domaine or "")[:40], c.statut, f"{c.taux_conformite:.0f}%"])

        t = Table(data, colWidths=[80, 200, 90, 70])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)

    doc.build(story)
    output.seek(0)
    return output.read()
