from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .chakra_analysis import ChakraAnalysis
from .models import DestinyMatrixData, Dossier, Evidence, EventItem, Relation


class PdfService:
    def __init__(self, export_dir: Path) -> None:
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.font_main = "ArchiveSans"
        self.font_bold = "ArchiveSansBold"
        self.font_mono = "ArchiveMono"
        self._register_fonts()
        self.styles = self._build_styles()

    def generate(
        self,
        dossier: Dossier,
        template: str = "dossier",
        destiny_matrix: DestinyMatrixData | None = None,
        chakra_analysis: ChakraAnalysis | None = None,
    ) -> str:
        suffix = "board" if template == "board" else "dossier"
        filename = f"{self._safe_filename(dossier.participant.full_name)}_{suffix}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        output_path = self.export_dir / filename
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=17 * mm,
            rightMargin=17 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            title=f"Архив расследований - {dossier.participant.full_name}",
        )
        if template == "board":
            story = self._board_story(dossier)
        else:
            story = self._story(dossier, destiny_matrix=destiny_matrix, chakra_analysis=chakra_analysis)
        document.build(story, onFirstPage=self._draw_page, onLaterPages=self._draw_page)
        return str(output_path)

    def _story(
        self,
        dossier: Dossier,
        destiny_matrix: DestinyMatrixData | None = None,
        chakra_analysis: ChakraAnalysis | None = None,
    ) -> list:
        subject_code = dossier.participant.id[:2].upper() if dossier.participant.id else "01"
        story: list = [
            Spacer(1, 6 * mm),
            Paragraph("/SUBJECTS", self.styles["micro"]),
            Spacer(1, 2 * mm),
            Paragraph(dossier.participant.full_name.upper(), self.styles["hero_name"]),
            Paragraph(f"ОБЪЕКТ : {subject_code}", self.styles["hero_code"]),
            Spacer(1, 3 * mm),
            Paragraph(f"СТАТУС: {self._empty(dossier.participant.status).upper()}", self.styles["status"]),
            Spacer(1, 4 * mm),
            self._identity_table(dossier),
            Spacer(1, 5 * mm),
            self._wide_block("НАБЛЮДЕНИЕ", dossier.participant.description or dossier.case.summary),
            Spacer(1, 2.2 * mm),
            self._wide_block("НАСТОРОЖЕННОСТЬ", self._risk_sentence(dossier.participant.suspicion_level)),
            Spacer(1, 2.2 * mm),
            self._wide_block("ПСИХОПОРТРЕТ", dossier.participant.biography or dossier.participant.habits),
            Spacer(1, 2.2 * mm),
            self._wide_block("МОДИФИКАЦИИ", self._modification_line(dossier)),
            Spacer(1, 2.2 * mm),
            self._wide_block("ИТОГОВАЯ ОЦЕНКА", self._assessment_line(dossier)),
            Spacer(1, 5 * mm),
            self._bottom_panels(dossier),
            PageBreak(),
            Paragraph("/MATERIALS", self.styles["micro"]),
            Spacer(1, 2 * mm),
            Paragraph("ПРИЛОЖЕНИЯ И ЖУРНАЛ СОБЫТИЙ", self.styles["section"]),
            Spacer(1, 4 * mm),
        ]
        story.extend(self._material_section("УЛИКИ", dossier.evidence, self._format_evidence))
        story.append(Spacer(1, 4 * mm))
        story.extend(self._material_section("СОБЫТИЯ", dossier.events, self._format_event))
        story.append(Spacer(1, 4 * mm))
        story.extend(self._material_section("СВЯЗИ", dossier.relations, self._format_relation))
        story.append(Spacer(1, 4 * mm))
        story.append(self._material_card("ФИНАЛЬНЫЙ РЕЗУЛЬТАТ", self._assessment_line(dossier)))
        if dossier.matrix:
            story.extend([PageBreak(), Paragraph("/ESOTERIC APPENDIX", self.styles["micro"]), Spacer(1, 2 * mm), Paragraph("МАТРИЦА СУДЬБЫ", self.styles["section"]), Spacer(1, 4 * mm)])
            story.extend(self._matrix_pdf_section(dossier))
        if chakra_analysis:
            story.extend([PageBreak(), Paragraph("/CHAKRA APPENDIX", self.styles["micro"]), Spacer(1, 2 * mm), Paragraph("ЧАКРОАНАЛИЗ", self.styles["section"]), Spacer(1, 4 * mm)])
            story.extend(self._chakra_pdf_section(dossier, destiny_matrix, chakra_analysis))
        return story

    def _board_story(self, dossier: Dossier) -> list:
        story: list = [
            Spacer(1, 8 * mm),
            self._board_header(dossier),
            Spacer(1, 5 * mm),
            self._board_layout(dossier),
            Spacer(1, 4 * mm),
            self._board_matrix_strip(dossier),
            PageBreak(),
            Paragraph("/BOARD NOTES", self.styles["micro"]),
            Spacer(1, 2 * mm),
            Paragraph("ПОЛЕВЫЕ МАТЕРИАЛЫ", self.styles["section"]),
            Spacer(1, 4 * mm),
        ]
        story.extend(self._board_materials(dossier))
        return story

    def _identity_table(self, dossier: Dossier):
        photo = self._photo_block(dossier.participant.photo_path)
        info = Table(
            [
                [Paragraph("ИМЯ:", self.styles["label"]), Paragraph(self._empty(dossier.participant.full_name), self.styles["value"])],
                [Paragraph("ВОЗРАСТ:", self.styles["label"]), Paragraph(str(dossier.participant.age) if dossier.participant.age is not None else "Не указан", self.styles["value"])],
                [Paragraph("ПРОФЕССИЯ:", self.styles["label"]), Paragraph(self._empty(dossier.participant.role), self.styles["value"])],
                [Paragraph("ТЕКУЩИЙ СТАТУС:", self.styles["label"]), Paragraph(self._empty(dossier.participant.status), self.styles["value"])],
                [Paragraph("ЛОКАЦИЯ:", self.styles["label"]), Paragraph(self._empty(dossier.participant.location), self.styles["value"])],
                [Paragraph("ДОКУМЕНТЫ:", self.styles["label"]), Paragraph(self._empty(dossier.participant.documents_summary), self.styles["value"])],
            ],
            colWidths=[38 * mm, 82 * mm],
        )
        info.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        shell = Table([[photo, info]], colWidths=[34 * mm, 126 * mm])
        shell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return shell

    def _board_matrix_strip(self, dossier: Dossier):
        if not dossier.matrix:
            return self._board_note("МАТРИЦА", "Дата рождения не задана, матрица не рассчитана.", width=160 * mm)
        row = Table(
            [[
                self._board_note("ПУТЬ", str(dossier.matrix.life_path), width=30 * mm),
                self._board_note("МИССИЯ", str(dossier.matrix.mission), width=30 * mm),
                self._board_note("ДУХОВНОСТЬ", str(dossier.matrix.spirituality), width=44 * mm),
                self._board_note("ТЕНЬ", dossier.matrix.shadow_pattern, width=48 * mm),
            ]],
            colWidths=[32 * mm, 32 * mm, 46 * mm, 50 * mm],
        )
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return row

    def _board_header(self, dossier: Dossier):
        header = Table(
            [
                [Paragraph("CASE BOARD / ARCHIVE", self.styles["micro"]), Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), self.styles["board_meta_right"])],
                [Paragraph(dossier.case.title.upper(), self.styles["board_title"]), Paragraph(self._risk_word(dossier.participant.suspicion_level), self.styles["board_flag"])],
                [Paragraph(f"ОБЪЕКТ: {dossier.participant.full_name.upper()}", self.styles["board_subtitle"]), Paragraph(self._empty(dossier.participant.status).upper(), self.styles["board_status"])],
            ],
            colWidths=[118 * mm, 42 * mm],
        )
        header.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return header

    def _board_layout(self, dossier: Dossier):
        left = Table(
            [
                [self._board_paper(self._photo_block(dossier.participant.photo_path), "СНИМОК", 50 * mm)],
                [Spacer(1, 2 * mm)],
                [self._board_note("ДОКУМЕНТЫ", dossier.participant.documents_summary or "Следы по документам не оформлены.")],
                [Spacer(1, 2 * mm)],
                [self._board_note("МЕСТА", dossier.participant.known_places or "Локации уточняются.")],
            ],
            colWidths=[54 * mm],
        )
        left.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

        center = Table(
            [
                [self._board_note("ПРОФИЛЬ", dossier.participant.biography or dossier.participant.description, width=62 * mm)],
                [Spacer(1, 2 * mm)],
                [self._board_note("ПОВАДКИ", dossier.participant.habits or "Поведенческий паттерн ещё собирается.", width=62 * mm)],
                [Spacer(1, 2 * mm)],
                [self._board_note("ЗАМЕТКИ", dossier.participant.notes or "Оперативные заметки отсутствуют.", width=62 * mm)],
            ],
            colWidths=[66 * mm],
        )
        center.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

        right = Table(
            [
                [self._board_note("ОЦЕНКА", self._assessment_line(dossier), width=36 * mm)],
                [Spacer(1, 2 * mm)],
                [self._board_note("СТАТУС", self._empty(dossier.participant.status), width=36 * mm)],
                [Spacer(1, 2 * mm)],
                [self._board_note("РИСК", self._risk_sentence(dossier.participant.suspicion_level), width=36 * mm)],
            ],
            colWidths=[40 * mm],
        )
        right.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

        shell = Table([[left, center, right]], colWidths=[54 * mm, 66 * mm, 40 * mm])
        shell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return shell

    def _board_materials(self, dossier: Dossier) -> list:
        blocks: list = []
        for title, items, formatter in (
            ("УЛИКИ", dossier.evidence[:3], self._format_evidence),
            ("СОБЫТИЯ", dossier.events[:3], self._format_event),
            ("СВЯЗИ", dossier.relations[:3], self._format_relation),
        ):
            blocks.append(Paragraph(title, self.styles["section"]))
            if not items:
                blocks.extend([Spacer(1, 2 * mm), self._board_note(title, "Нет данных.", width=160 * mm)])
                continue
            row = []
            for item in items:
                header, text = formatter(item)
                row.append(self._board_note(header, text, width=50 * mm))
            while len(row) < 3:
                row.append(Spacer(1, 1))
            table = Table([row], colWidths=[52 * mm, 52 * mm, 52 * mm])
            table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            blocks.extend([Spacer(1, 2 * mm), table, Spacer(1, 3 * mm)])
        return blocks

    def _board_index(self, dossier: Dossier):
        lines = [
            f"/ {self._risk_word(dossier.participant.suspicion_level)}",
            f"/ {self._empty(dossier.participant.alias_name).upper()}",
            f"/ {self._empty(dossier.participant.location).upper()}",
        ]
        body = "<br/>".join(lines)
        box = Table(
            [
                [Paragraph("/SUBJECTS", self.styles["micro_box"])],
                [Paragraph(body, self.styles["sidebar_list"])],
            ],
            colWidths=[36 * mm],
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eadfcb")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#907456")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return box

    def _board_note(self, title: str, text: str, width: float = 54 * mm):
        box = Table(
            [
                [Paragraph(title, self.styles["panel_title"])],
                [Paragraph(self._empty(text).replace("\n", "<br/>"), self.styles["panel_body"])],
            ],
            colWidths=[width],
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#efe5d4")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8f7354")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return box

    def _board_paper(self, content, caption: str, width: float):
        box = Table(
            [
                [content],
                [Paragraph(caption, self.styles["photo_caption"])],
            ],
            colWidths=[width],
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3eadb")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8f7354")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return box

    def _bottom_panels(self, dossier: Dossier):
        left = self._panel_block(
            "ЛОГИ НАБЛЮДЕНИЯ",
            [
                dossier.participant.notes or "Объект наблюдается фрагментарно.",
                dossier.participant.known_places or "Привязка к местам пока слабая.",
            ],
            105 * mm,
        )
        right = self._panel_block(
            "СЛУЖЕБНАЯ СВОДКА",
            [
                f"Статус: {self._empty(dossier.participant.status)}",
                f"Риск: {self._risk_sentence(dossier.participant.suspicion_level)}",
                f"Псевдоним: {self._empty(dossier.participant.alias_name)}",
            ],
            55 * mm,
        )
        shell = Table([[left, right]], colWidths=[105 * mm, 55 * mm])
        shell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return shell

    def _panel_block(self, title: str, lines: list[str], width: float):
        content = [[Paragraph(title, self.styles["panel_title"])]]
        for line in lines:
            content.append([Paragraph(self._empty(line), self.styles["panel_body"])])
        box = Table(content, colWidths=[width])
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ede3d1")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#907456")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return box

    def _wide_block(self, label: str, text: str):
        table = Table(
            [[Paragraph(f"{label}: ", self.styles["line_label"]), Paragraph(self._empty(text), self.styles["line_text"])]],
            colWidths=[45 * mm, 115 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return table

    def _material_section(self, title: str, items: list, formatter) -> list:
        blocks: list = [Paragraph(title, self.styles["section"])]
        if not items:
            blocks.extend([Spacer(1, 2 * mm), self._material_card("Нет данных", "Раздел пока пуст.")])
            return blocks
        for item in items:
            header, text = formatter(item)
            blocks.extend([Spacer(1, 2 * mm), self._material_card(header, text)])
        return blocks

    def _matrix_pdf_section(self, dossier: Dossier) -> list:
        blocks: list = []
        if not dossier.matrix:
            blocks.extend([Spacer(1, 2 * mm), self._material_card("Матрица не рассчитана", "Укажите дату рождения объекта.")])
            return blocks

        metrics = Table(
            [[
                self._mini_metric("Путь", str(dossier.matrix.life_path)),
                self._mini_metric("Миссия", str(dossier.matrix.mission)),
                self._mini_metric("Цель", str(dossier.matrix.purpose_line)),
                self._mini_metric("Семья", str(dossier.matrix.family_line)),
                self._mini_metric("Устойчивость", str(dossier.matrix.stability_line)),
            ]],
            colWidths=[31 * mm, 31 * mm, 31 * mm, 31 * mm, 31 * mm],
        )
        metrics.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        blocks.extend([Spacer(1, 2 * mm), metrics, Spacer(1, 3 * mm)])

        blocks.append(
            self._material_card(
                "РАЗБОР",
                (
                    f"Сектора: 1={dossier.matrix.character}, 2={dossier.matrix.energy}, 3={dossier.matrix.interests}, "
                    f"4={dossier.matrix.health}, 5={dossier.matrix.logic}, 6={dossier.matrix.labor}, "
                    f"7={dossier.matrix.luck}, 8={dossier.matrix.duty}, 9={dossier.matrix.memory}. "
                    f"Доминирующие числа: {', '.join(map(str, dossier.matrix.dominant_numbers)) or 'нет'}. "
                    f"Пустоты: {', '.join(map(str, dossier.matrix.missing_numbers)) or 'нет'}."
                ),
            )
        )
        blocks.extend(
            [
                Spacer(1, 2 * mm),
                self._material_card("СИЛЬНЫЕ СТОРОНЫ", "; ".join(dossier.matrix.strengths)),
                Spacer(1, 2 * mm),
                self._material_card("РИСКИ", "; ".join(dossier.matrix.risks)),
                Spacer(1, 2 * mm),
                self._material_card(
                    "ВЕКТОР",
                    (
                        f"Стиль отношений: {dossier.matrix.relationship_style}. "
                        f"Социальный вектор: {dossier.matrix.social_vector}. "
                        f"Теневая сторона: {dossier.matrix.shadow_pattern}. "
                        f"{dossier.matrix.warning}"
                    ),
                ),
            ]
        )
        return blocks

    def _chakra_pdf_section(self, dossier: Dossier, destiny_matrix: DestinyMatrixData | None, chakra_analysis: ChakraAnalysis) -> list:
        blocks: list = []
        personal_left = self._panel_block(
            "ЛИЧНОСТНЫЙ КОНТУР",
            [
                f"Типология: {chakra_analysis.typology_number} — {chakra_analysis.typology_name}",
                f"Подтип: {chakra_analysis.subtype}",
                f"Тип личности: {chakra_analysis.personality_type}",
                f"Вибрация: {chakra_analysis.vibration}",
                f"Триада: {chakra_analysis.triad}",
                f"Этап души: {chakra_analysis.soul_stage}",
                f"Код успеха: {chakra_analysis.code_of_success}",
            ],
            103 * mm,
        )
        personal_right = self._panel_block(
            "КОНТУРЫ ЛИЧНОСТИ",
            [
                f"Темперамент: {chakra_analysis.temperament}",
                f"Характер: {chakra_analysis.character}",
                f"Интеллект: {chakra_analysis.intelligence}",
            ],
            57 * mm,
        )
        top_shell = Table([[personal_left, personal_right]], colWidths=[103 * mm, 57 * mm])
        top_shell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        blocks.extend([top_shell, Spacer(1, 3 * mm)])

        metrics_shell = Table(
            [[
                self._panel_block(
                    "СИЛА ЭНЕРГЕТИКИ",
                    [
                        f"Общая энергия: {chakra_analysis.total_energy}%",
                        f"Хочу: {chakra_analysis.want}",
                        f"Могу: {chakra_analysis.can}",
                    ],
                    50 * mm,
                ),
                self._panel_block(
                    "ЖЕНСКОЕ И МУЖСКОЕ НАЧАЛО",
                    [
                        f"Инь: {chakra_analysis.yin}%",
                        f"Ян: {chakra_analysis.yang}%",
                    ],
                    50 * mm,
                ),
                self._panel_block(
                    "ЦЕННОСТИ ЖИЗНИ",
                    [
                        f"Материальное: {chakra_analysis.material}%",
                        f"Духовное: {chakra_analysis.spiritual}%",
                    ],
                    50 * mm,
                ),
            ]],
            colWidths=[52 * mm, 52 * mm, 52 * mm],
        )
        metrics_shell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        blocks.extend([metrics_shell, Spacer(1, 3 * mm)])

        chakra_rows = [[
            Paragraph("Чакроанализ", self.styles["material_header"]),
            Paragraph("Физика", self.styles["material_header"]),
            Paragraph("Энергия", self.styles["material_header"]),
            Paragraph("Эмоция", self.styles["material_header"]),
            Paragraph("Оценка", self.styles["material_header"]),
        ]]
        if destiny_matrix:
            for row, insight in zip(destiny_matrix.chakra_rows, chakra_analysis.insights, strict=True):
                chakra_rows.append([
                    Paragraph(row.name, self.styles["panel_body"]),
                    Paragraph(str(row.physics), self.styles["panel_body"]),
                    Paragraph(str(row.energy), self.styles["panel_body"]),
                    Paragraph(str(row.emotion), self.styles["panel_body"]),
                    Paragraph(f"{insight.percent}% / {insight.label}", self.styles["panel_body"]),
                ])
            chakra_rows.append([
                Paragraph("Итого", self.styles["material_header"]),
                Paragraph(str(destiny_matrix.totals.physics), self.styles["panel_body"]),
                Paragraph(str(destiny_matrix.totals.energy), self.styles["panel_body"]),
                Paragraph(str(destiny_matrix.totals.emotion), self.styles["panel_body"]),
                Paragraph(f"{chakra_analysis.total_energy}%", self.styles["panel_body"]),
            ])
        chakra_table = Table(chakra_rows, colWidths=[46 * mm, 16 * mm, 16 * mm, 16 * mm, 28 * mm])
        chakra_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2d3bc")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#eee5d5")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8f7354")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9b596")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        blocks.extend([chakra_table, Spacer(1, 3 * mm)])

        blocks.append(
            self._material_card(
                "ОБЩИЙ ВЫВОД",
                (
                    f"Доминирует {chakra_analysis.dominant}, слабее выглядит {chakra_analysis.weak_point}. "
                    f"{chakra_analysis.summary}"
                ),
            )
        )
        blocks.append(Spacer(1, 2 * mm))

        for insight in chakra_analysis.insights:
            blocks.extend(
                [
                    self._material_card(
                        f"{insight.name.upper()} / {insight.percent}% / {insight.label.upper()}",
                        insight.summary,
                    ),
                    Spacer(1, 2 * mm),
                ]
            )
        return blocks

    def _mini_metric(self, title: str, value: str):
        box = Table(
            [
                [Paragraph(title.upper(), self.styles["micro_box"])],
                [Paragraph(value, self.styles["board_title"])],
            ],
            colWidths=[29 * mm],
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#efe5d4")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8f7354")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return box

    def _material_card(self, header: str, text: str):
        table = Table(
            [
                [Paragraph(header, self.styles["material_header"])],
                [Paragraph(self._empty(text).replace("\n", "<br/>"), self.styles["panel_body"])],
            ],
            colWidths=[160 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eee5d5")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8f7354")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#c9b596")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return table

    def _photo_block(self, photo_path: str | None):
        resolved = self._resolve_photo_path(photo_path)
        if resolved and resolved.exists():
            try:
                image = Image(str(resolved), width=30 * mm, height=42 * mm)
                image.hAlign = "CENTER"
                shell = Table(
                    [
                        [Spacer(1, 1.5 * mm)],
                        [image],
                        [Paragraph("PHOTO EVIDENCE", self.styles["photo_caption"])],
                    ],
                    colWidths=[32 * mm],
                    rowHeights=[2 * mm, 44 * mm, 6 * mm],
                )
                shell.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4ead8")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8c6f52")),
                            ("LINEABOVE", (0, 0), (-1, 0), 7, colors.HexColor("#d2bf9b")),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                return shell
            except Exception:
                pass

        placeholder = Table(
            [
                [Spacer(1, 1.5 * mm)],
                [Paragraph("ФОТО", self.styles["photo_title"])],
                [Paragraph("добавьте снимок", self.styles["photo_caption"])],
            ],
            colWidths=[32 * mm],
            rowHeights=[2 * mm, 36 * mm, 8 * mm],
        )
        placeholder.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4ead8")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#8c6f52")),
                    ("LINEABOVE", (0, 0), (-1, 0), 7, colors.HexColor("#d2bf9b")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return placeholder

    def _format_evidence(self, item: Evidence) -> tuple[str, str]:
        return (
            f"{item.title.upper()} / {self._empty(item.category).upper()} / {self._empty(item.status).upper()}",
            item.details,
        )

    def _format_event(self, item: EventItem) -> tuple[str, str]:
        return (f"{self._empty(item.event_date).upper()} / {item.title.upper()}", item.details)

    def _format_relation(self, item: Relation) -> tuple[str, str]:
        return (
            f"{item.target_label.upper()} / {self._empty(item.relation_type).upper()} / {item.confidence}%",
            f"Тип цели: {self._empty(item.target_type)}",
        )

    def _draw_page(self, pdf, doc) -> None:
        width, height = A4
        pdf.saveState()
        pdf.setFillColor(colors.HexColor("#ded1be"))
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#e9ddca"))
        pdf.rect(9 * mm, 7 * mm, width - 18 * mm, height - 14 * mm, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#d7c7b0"))
        pdf.rect(13 * mm, height - 16 * mm, 16 * mm, 5 * mm, fill=1, stroke=0)
        pdf.rect(width - 35 * mm, height - 17 * mm, 18 * mm, 5 * mm, fill=1, stroke=0)
        pdf.rect(24 * mm, 13 * mm, 14 * mm, 4.5 * mm, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#cebda4"))
        for x, y, w, h in (
            (13 * mm, height - 46 * mm, 6 * mm, 13 * mm),
            (width - 18 * mm, height - 70 * mm, 4 * mm, 18 * mm),
            (15 * mm, 42 * mm, 6 * mm, 20 * mm),
            (width - 20 * mm, 28 * mm, 5 * mm, 15 * mm),
        ):
            pdf.rect(x, y, w, h, fill=1, stroke=0)

        pdf.setStrokeColor(colors.HexColor("#9a7f60"))
        pdf.setLineWidth(0.9)
        pdf.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm, fill=0, stroke=1)

        pdf.setStrokeColor(colors.HexColor("#b9a287"))
        pdf.setLineWidth(0.4)
        pdf.line(17 * mm, height - 31 * mm, width - 17 * mm, height - 31 * mm)
        pdf.line(17 * mm, 21 * mm, width - 17 * mm, 21 * mm)

        pdf.setFillColor(colors.HexColor("#c0aa8b"))
        pdf.circle(20 * mm, height - 20 * mm, 4.5 * mm, fill=1, stroke=0)
        pdf.circle(width - 22 * mm, height - 19 * mm, 3.2 * mm, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#7f5b47"))
        pdf.setFont(self.font_bold, 26)
        pdf.saveState()
        pdf.translate(width - 53 * mm, height - 19 * mm)
        pdf.rotate(4)
        pdf.drawString(0, 0, "СЕКРЕТНО")
        pdf.setLineWidth(1.2)
        pdf.setStrokeColor(colors.HexColor("#7f5b47"))
        pdf.rect(-4, -7, 44 * mm, 12 * mm, fill=0, stroke=1)
        pdf.restoreState()

        pdf.setStrokeColor(colors.HexColor("#8f6f54"))
        pdf.setLineWidth(0.3)
        pdf.line(16 * mm, height - 14 * mm, 28 * mm, height - 19 * mm)
        pdf.line(width - 35 * mm, height - 15 * mm, width - 20 * mm, height - 20 * mm)
        pdf.line(17 * mm, 18 * mm, 31 * mm, 14 * mm)

        pdf.setFillColor(colors.HexColor("#6e604f"))
        pdf.setFont(self.font_mono, 8)
        pdf.drawString(17 * mm, 10 * mm, "ARCHIVE DOSSIER / INTERNAL USE ONLY")
        pdf.drawRightString(width - 17 * mm, 10 * mm, f"PAGE {doc.page}")
        pdf.restoreState()

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "micro": ParagraphStyle("micro", parent=base["BodyText"], fontName=self.font_mono, fontSize=8.5, leading=10, textColor=colors.HexColor("#5a5148")),
            "micro_box": ParagraphStyle("micro_box", parent=base["BodyText"], fontName=self.font_mono, fontSize=8.5, leading=10, textColor=colors.HexColor("#5a5148")),
            "hero_name": ParagraphStyle("hero_name", parent=base["Heading1"], fontName=self.font_bold, fontSize=22, leading=24, textColor=colors.HexColor("#2d2925")),
            "hero_code": ParagraphStyle("hero_code", parent=base["Heading2"], fontName=self.font_bold, fontSize=19, leading=22, textColor=colors.HexColor("#2d2925")),
            "status": ParagraphStyle("status", parent=base["Heading2"], fontName=self.font_bold, fontSize=20, leading=22, textColor=colors.HexColor("#9a4c41")),
            "label": ParagraphStyle("label", parent=base["BodyText"], fontName=self.font_bold, fontSize=10, leading=12, textColor=colors.HexColor("#5a4c40")),
            "value": ParagraphStyle("value", parent=base["BodyText"], fontName=self.font_main, fontSize=10, leading=12.5, textColor=colors.HexColor("#302a24")),
            "line_label": ParagraphStyle("line_label", parent=base["BodyText"], fontName=self.font_bold, fontSize=10.5, leading=13, textColor=colors.HexColor("#5a4c40")),
            "line_text": ParagraphStyle("line_text", parent=base["BodyText"], fontName=self.font_main, fontSize=10, leading=13, textColor=colors.HexColor("#302a24")),
            "panel_title": ParagraphStyle("panel_title", parent=base["Heading3"], fontName=self.font_bold, fontSize=11, leading=13, textColor=colors.HexColor("#4e453d")),
            "panel_body": ParagraphStyle("panel_body", parent=base["BodyText"], fontName=self.font_main, fontSize=10, leading=13, textColor=colors.HexColor("#322d27")),
            "section": ParagraphStyle("section", parent=base["Heading2"], fontName=self.font_bold, fontSize=15, leading=18, textColor=colors.HexColor("#2b2722")),
            "material_header": ParagraphStyle("material_header", parent=base["Heading3"], fontName=self.font_bold, fontSize=10.5, leading=13, textColor=colors.HexColor("#40372f")),
            "photo_title": ParagraphStyle("photo_title", parent=base["Heading3"], fontName=self.font_bold, fontSize=11, leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#7a6247")),
            "photo_caption": ParagraphStyle("photo_caption", parent=base["BodyText"], fontName=self.font_mono, fontSize=7.5, leading=8.6, alignment=TA_CENTER, textColor=colors.HexColor("#746759")),
            "board_meta_right": ParagraphStyle("board_meta_right", parent=base["BodyText"], fontName=self.font_mono, fontSize=8.2, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#6a5e50")),
            "board_title": ParagraphStyle("board_title", parent=base["Heading1"], fontName=self.font_bold, fontSize=18, leading=20, textColor=colors.HexColor("#2d2925")),
            "board_subtitle": ParagraphStyle("board_subtitle", parent=base["Heading2"], fontName=self.font_bold, fontSize=13, leading=15, textColor=colors.HexColor("#40372f")),
            "board_flag": ParagraphStyle("board_flag", parent=base["Heading3"], fontName=self.font_bold, fontSize=10.5, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#8f5e34")),
            "board_status": ParagraphStyle("board_status", parent=base["Heading3"], fontName=self.font_bold, fontSize=11, leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#9a4c41")),
        }

    def _register_fonts(self) -> None:
        main = Path("C:/Windows/Fonts/trebuc.ttf")
        bold = Path("C:/Windows/Fonts/trebucbd.ttf")
        mono = Path("C:/Windows/Fonts/cour.ttf")
        if main.exists() and self.font_main not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(self.font_main, str(main)))
        if bold.exists() and self.font_bold not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(self.font_bold, str(bold)))
        if mono.exists() and self.font_mono not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(self.font_mono, str(mono)))

    @staticmethod
    def _risk_sentence(level: int) -> str:
        if level >= 80:
            return "Высокая. Поведение системное, повторяющееся, требует жёсткого контроля."
        if level >= 60:
            return "Выше средней. Наблюдаются устойчивые совпадения по местам и действиям."
        if level >= 35:
            return "Средняя. Есть признаки вовлечённости, но контур ещё уточняется."
        return "Базовая. Прямых подтверждений недостаточно."

    @staticmethod
    def _risk_word(level: int) -> str:
        if level >= 80:
            return "AWARE"
        if level >= 60:
            return "TRACE"
        if level >= 35:
            return "WATCH"
        return "LOW"

    def _modification_line(self, dossier: Dossier) -> str:
        parts = [self._empty(dossier.participant.habits), self._empty(dossier.participant.documents_summary)]
        return " / ".join(part for part in parts if part and part != "Не указано")

    def _assessment_line(self, dossier: Dossier) -> str:
        return (
            f"Объект {self._empty(dossier.participant.alias_name).lower()} связан с делом "
            f"«{self._empty(dossier.case.title)}». Текущая оценка: {self._risk_sentence(dossier.participant.suspicion_level)}"
        )

    @staticmethod
    def _empty(value: str) -> str:
        return value if value and value.strip() else "Не указано"

    @staticmethod
    def _resolve_photo_path(photo_path: str | None) -> Path | None:
        if not photo_path:
            return None
        if photo_path.startswith("/uploads/"):
            return Path(__file__).resolve().parent.parent / "app_data" / photo_path.lstrip("/")
        path = Path(photo_path)
        return path if path.exists() else None

    @staticmethod
    def _safe_filename(value: str) -> str:
        cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value.strip())
        cleaned = cleaned.strip("_") or "dossier"
        return cleaned[:80]
