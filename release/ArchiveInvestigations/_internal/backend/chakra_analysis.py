from __future__ import annotations

from dataclasses import dataclass

from .models import DestinyMatrixData


@dataclass
class ChakraInsight:
    name: str
    tone: str
    percent: int
    label: str
    summary: str


@dataclass
class ChakraAnalysis:
    total_energy: int
    upper_contour: int
    middle_contour: int
    lower_contour: int
    yin: int
    yang: int
    spiritual: int
    material: int
    dominant: str
    weak_point: str
    summary: str
    typology_number: int
    typology_name: str
    triad: str
    soul_stage: str
    subtype: int
    personality_type: str
    vibration: str
    code_of_success: str
    temperament: str
    character: str
    intelligence: str
    want: int
    can: int
    insights: list[ChakraInsight]


CHAKRA_MEANINGS = {
    "Сахасрара": "связь с идеей, широта психики и ощущение высшего смысла",
    "Аджна": "разум, интуиция, считывание паттернов и образное мышление",
    "Вишудха": "голос, самовыражение и способность доводить мысли до формы",
    "Анахата": "чувства, эмпатия, принятие и эмоциональный контакт",
    "Манипура": "воля, личная сила, контроль, лидерство и импульс к действию",
    "Свадхистана": "близость, удовольствие, семейный контур и телесная мягкость",
    "Муладхара": "выживание, тело, устойчивость, быт и базовая безопасность",
}

TYPOLOGY_NAMES = {
    1: "Инициатор",
    2: "Медиатор",
    3: "Творец",
    4: "Стратег",
    5: "Проводник",
    6: "Хранитель",
    7: "Исследователь",
    8: "Арбитр",
    9: "Внесистемный бунтарь",
    10: "Навигатор цикла",
    11: "Силовой лидер",
    12: "Наблюдатель",
    13: "Трансформатор",
    14: "Балансировщик",
    15: "Искуситель",
    16: "Ломатель старого",
    17: "Идеолог",
    18: "Лунный визионер",
    19: "Солнечный харизматик",
    20: "Пробуждающий",
    21: "Интегратор",
    22: "Свободный странник",
}


def _sum_digits(value: int) -> int:
    return sum(int(char) for char in str(abs(value)))


def _reduce_arcana(value: int) -> int:
    result = abs(value)
    while result > 22:
        result = _sum_digits(result)
    return result or 22


def _percent(value: int) -> int:
    return max(5, min(100, round((value / 22) * 100)))


def _label(percent: int) -> str:
    if percent >= 80:
        return "сильно раскрыта"
    if percent >= 60:
        return "устойчива"
    if percent >= 40:
        return "рабочая"
    if percent >= 25:
        return "нестабильна"
    return "ослаблена"


def _summary(name: str, percent: int) -> str:
    meaning = CHAKRA_MEANINGS[name]
    if percent >= 80:
        return f"{name}: контур выражен ярко, {meaning}. Энергия идёт свободно и задаёт тон остальному профилю."
    if percent >= 60:
        return f"{name}: контур устойчив, {meaning}. Потенциал работает надёжно и не проседает от первого же стресса."
    if percent >= 40:
        return f"{name}: контур в среднем диапазоне, {meaning}. Сфера рабочая, но требует осознанной подпитки."
    if percent >= 25:
        return f"{name}: контур нестабилен, {meaning}. В стрессе зона быстро проседает и даёт перекос в поведении."
    return f"{name}: контур ослаблен, {meaning}. Здесь вероятны блоки, истощение или компенсация через другие центры."


def _avg(values: list[int]) -> int:
    return round(sum(values) / len(values)) if values else 0


def _matrix_points(birth_date: str) -> tuple[int, int, int, int, int]:
    year_text, month_text, day_text = birth_date.split("-")
    day = _reduce_arcana(int(day_text))
    month = _reduce_arcana(int(month_text))
    year = _reduce_arcana(_sum_digits(int(year_text)))
    bottom = _reduce_arcana(day + month + year)
    center = _reduce_arcana(day + month + year + bottom)
    return day, month, year, bottom, center


def _triad(center: int) -> str:
    if center <= 7:
        return "Материалисты"
    if center <= 14:
        return "Прагматики"
    return "Идеалисты"


def _soul_stage(center: int) -> str:
    if center in {1, 4, 8, 11, 19}:
        return "Воин"
    if center in {2, 6, 14, 17, 20}:
        return "Проводник"
    if center in {3, 5, 10, 15, 21}:
        return "Творец"
    if center in {7, 9, 12, 13, 18, 22}:
        return "Искатель"
    return "Наблюдатель"


def _personality_type(center: int) -> str:
    if center in {9, 17, 18}:
        return "Утопист"
    if center in {4, 8, 11, 19}:
        return "Лидер"
    if center in {2, 6, 14, 20}:
        return "Дипломат"
    if center in {5, 7, 12}:
        return "Исследователь"
    return "Преобразователь"


def _temperament(yin: int, yang: int, total_energy: int) -> str:
    if yang - yin >= 10 and total_energy >= 60:
        return "Сангвиник-холерик"
    if yin - yang >= 10:
        return "Флегматик-меланхолик"
    if total_energy >= 60:
        return "Сангвиник"
    return "Сдержанный смешанный"


def _character(material: int, yang: int) -> str:
    if material >= 65 and yang >= 60:
        return "Эгоистичный (лидерский)"
    if material >= 55:
        return "Практичный и волевой"
    if yang < 45:
        return "Мягкий и наблюдательный"
    return "Смешанный, адаптивный"


def _intelligence(spiritual: int, upper: int) -> str:
    if spiritual >= 60 and upper >= 60:
        return "Гармоничный мыслительный"
    if upper >= 60:
        return "Образно-аналитический"
    if spiritual < 45:
        return "Практический"
    return "Смешанный"


def build_chakra_analysis(matrix: DestinyMatrixData, birth_date: str) -> ChakraAnalysis:
    percents = {row.name: _percent(row.energy) for row in matrix.chakra_rows}
    insights = [
        ChakraInsight(
            name=row.name,
            tone=row.tone,
            percent=percents[row.name],
            label=_label(percents[row.name]),
            summary=_summary(row.name, percents[row.name]),
        )
        for row in matrix.chakra_rows
    ]

    upper = _avg([percents["Сахасрара"], percents["Аджна"], percents["Вишудха"]])
    middle = _avg([percents["Анахата"], percents["Манипура"]])
    lower = _avg([percents["Свадхистана"], percents["Муладхара"]])
    yin = _avg([percents["Сахасрара"], percents["Анахата"], percents["Свадхистана"]])
    yang = _avg([percents["Аджна"], percents["Вишудха"], percents["Манипура"], percents["Муладхара"]])
    spiritual = _avg([percents["Сахасрара"], percents["Аджна"], percents["Анахата"]])
    material = _avg([percents["Манипура"], percents["Свадхистана"], percents["Муладхара"]])

    dominant = max(insights, key=lambda item: item.percent).name
    weak_point = min(insights, key=lambda item: item.percent).name
    total_energy = _avg([item.percent for item in insights])

    if upper >= lower + 15:
        summary = "Верхний контур заметно сильнее нижнего: человек живёт через идеи, смысл и внутреннюю настройку, но может выпадать из телесной устойчивости и быта."
    elif lower >= upper + 15:
        summary = "Нижний контур сильнее верхнего: профиль более земной, практичный и телесный, с упором на безопасность, контроль и выживание."
    else:
        summary = "Верхний и нижний контуры относительно сбалансированы: психика не улетает в абстракцию и не застревает только в базовых инстинктах."

    day, month, year, _, center = _matrix_points(birth_date)
    triad = _triad(center)
    soul_stage = _soul_stage(center)
    personality_type = _personality_type(center)
    vibration = "Мужская" if yang >= yin else "Женская"
    code_of_success = f"{day}{month}{year}{center}"
    temperament = _temperament(yin, yang, total_energy)
    character = _character(material, yang)
    intelligence = _intelligence(spiritual, upper)
    want = max(10, round((lower + middle) / 2))
    can = max(10, round((upper + middle + yang) / 3))

    return ChakraAnalysis(
        total_energy=total_energy,
        upper_contour=upper,
        middle_contour=middle,
        lower_contour=lower,
        yin=yin,
        yang=yang,
        spiritual=spiritual,
        material=material,
        dominant=dominant,
        weak_point=weak_point,
        summary=summary,
        typology_number=center,
        typology_name=TYPOLOGY_NAMES.get(center, "Архетип пути"),
        triad=triad,
        soul_stage=soul_stage,
        subtype=day,
        personality_type=personality_type,
        vibration=vibration,
        code_of_success=code_of_success,
        temperament=temperament,
        character=character,
        intelligence=intelligence,
        want=want,
        can=can,
        insights=insights,
    )
