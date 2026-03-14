from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class MatrixProfileData:
    life_path: int
    mission: int
    dominant_numbers: list[int]
    missing_numbers: list[int]
    matrix_rows: list[list[int]]
    character: int
    energy: int
    interests: int
    health: int
    logic: int
    labor: int
    luck: int
    duty: int
    memory: int
    purpose_line: int
    family_line: int
    stability_line: int
    temperament: int
    spirituality: int
    grounding: int
    strengths: list[str]
    risks: list[str]
    relationship_style: str
    social_vector: str
    shadow_pattern: str
    interpretation: str
    warning: str


def compute_age(birth_date: str | None) -> int | None:
    if not birth_date:
        return None
    try:
        born = datetime.strptime(birth_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age if age >= 0 else None


def _reduce_number(value: int) -> int:
    while value > 9 and value not in {11, 22}:
        value = sum(int(char) for char in str(value))
    return value


def _sum_digits(text: str) -> int:
    return sum(int(char) for char in text if char.isdigit())


def _repeat_digit(digit: int, count: int) -> str:
    return str(digit) * count if count > 0 else "-"


def calculate_matrix(birth_date: str | None) -> MatrixProfileData | None:
    if not birth_date:
        return None
    try:
        parsed = datetime.strptime(birth_date.strip(), "%Y-%m-%d")
    except ValueError:
        return None

    date_digits_text = parsed.strftime("%d%m%Y")
    day = parsed.day

    first_work = _sum_digits(date_digits_text)
    second_work = _sum_digits(str(first_work))
    first_day_digit = int(str(day).zfill(2)[0])
    third_work = first_work - (2 * first_day_digit)
    fourth_work = _sum_digits(str(abs(third_work)))

    all_digits_text = f"{date_digits_text}{first_work}{second_work}{abs(third_work)}{fourth_work}"
    digits = [int(char) for char in all_digits_text if char.isdigit() and char != "0"]
    counts = {digit: digits.count(digit) for digit in range(1, 10)}

    life_path = _reduce_number(first_work)
    mission = _reduce_number(second_work + fourth_work)
    dominant = [digit for digit, count in counts.items() if count >= 3]
    missing = [digit for digit, count in counts.items() if count == 0]

    matrix_rows = [
      [counts[1], counts[4], counts[7]],
      [counts[2], counts[5], counts[8]],
      [counts[3], counts[6], counts[9]],
    ]

    purpose_line = counts[1] + counts[4] + counts[7]
    family_line = counts[2] + counts[5] + counts[8]
    stability_line = counts[3] + counts[6] + counts[9]
    temperament = counts[1] + counts[5] + counts[9]
    spirituality = counts[3] + counts[5] + counts[7]
    grounding = counts[4] + counts[5] + counts[6]

    strengths: list[str] = []
    risks: list[str] = []

    if counts[1] >= 3:
        strengths.append("Выраженная воля и желание навязывать собственный ритм.")
    elif counts[1] == 2:
        strengths.append("Устойчивая воля без лишней демонстративности.")
    if counts[2] >= 3:
        strengths.append("Сильная энергетика и заметное влияние на окружающих.")
    if counts[5] >= 2:
        strengths.append("Трезвая логика и способность держать хаос под контролем.")
    if counts[7] >= 2:
        strengths.append("Хорошее чувство удачного момента и редкая выживаемость в жёстких сценариях.")
    if counts[9] >= 2:
        strengths.append("Цепкая память и умение удерживать сложные смысловые конструкции.")
    if spirituality >= 4:
        strengths.append("Повышенная чувствительность к знакам, совпадениям и скрытым паттернам.")

    if counts[1] == 0:
        risks.append("Слабая воля: человек легче попадает под чужое влияние.")
    if counts[2] == 0:
        risks.append("Провалы по энергии: быстро выгорает и закрывается.")
    if counts[4] == 0:
        risks.append("Слабая опора на тело и рутину: трудно держать стабильный режим.")
    if counts[8] == 0:
        risks.append("Сопротивление правилам и долгим обязательствам.")
    if counts[9] == 0:
        risks.append("Разрывы в памяти и логике, сложнее удерживать схему целиком.")
    if len(missing) >= 4:
        risks.append("В матрице много пустот, поэтому поведение может быть нелинейным.")

    relationship_style = (
        "Тянется к эмоциональной сцепке и быстро считывает чужое состояние."
        if family_line >= 5
        else "Держит дистанцию и раскрывается только в контролируемой среде."
        if family_line <= 2
        else "Контактирует выборочно и держит отношения в собственных рамках."
    )
    social_vector = (
        "Идёт через цель, давление и личное пробивание дороги."
        if purpose_line >= family_line and purpose_line >= stability_line
        else "Идёт через связи, влияние и эмоциональные узлы."
        if family_line >= stability_line
        else "Идёт через порядок, труд и повторяемые механики."
    )
    shadow_pattern = (
        "В кризисе становится жёстче, холоднее и усиливает контроль."
        if counts[1] + counts[8] >= 4
        else "В кризисе уходит в хаос, исчезает с радаров и рвёт привычный маршрут."
        if counts[4] == 0 or counts[6] == 0
        else "В кризисе маскирует тревогу под рациональность и отстранённость."
    )

    interpretation = (
        f"Психоматрица собрана по классической схеме Пифагора. "
        f"Рабочие числа: {first_work}, {second_work}, {third_work}, {fourth_work}. "
        f"Число пути: {life_path}, миссия: {mission}. "
        f"Ячейки: 1={_repeat_digit(1, counts[1])}, 2={_repeat_digit(2, counts[2])}, 3={_repeat_digit(3, counts[3])}, "
        f"4={_repeat_digit(4, counts[4])}, 5={_repeat_digit(5, counts[5])}, 6={_repeat_digit(6, counts[6])}, "
        f"7={_repeat_digit(7, counts[7])}, 8={_repeat_digit(8, counts[8])}, 9={_repeat_digit(9, counts[9])}."
    )
    warning = (
        "Матрица показывает сильную чувствительность к повторяющимся знакам и символическим узорам."
        if spirituality >= 4 or counts[7] >= 2
        else "Матрица выглядит более приземлённой: упор идёт на волю, быт, логику и поведенческие циклы."
    )

    return MatrixProfileData(
        life_path=life_path,
        mission=mission,
        dominant_numbers=dominant,
        missing_numbers=missing,
        matrix_rows=matrix_rows,
        character=counts[1],
        energy=counts[2],
        interests=counts[3],
        health=counts[4],
        logic=counts[5],
        labor=counts[6],
        luck=counts[7],
        duty=counts[8],
        memory=counts[9],
        purpose_line=purpose_line,
        family_line=family_line,
        stability_line=stability_line,
        temperament=temperament,
        spirituality=spirituality,
        grounding=grounding,
        strengths=strengths or ["Явных доминант не видно, профиль относительно ровный."],
        risks=risks or ["Критических провалов по матрице не выявлено."],
        relationship_style=relationship_style,
        social_vector=social_vector,
        shadow_pattern=shadow_pattern,
        interpretation=interpretation,
        warning=warning,
    )
