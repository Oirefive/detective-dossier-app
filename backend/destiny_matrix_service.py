from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache

import httpx

from .models import DestinyMatrixData, DestinyMatrixRow, DestinyMatrixTotals

REMOTE_URL = "https://matrica-sudby.ru/lk/matrix/get"

CHAKRA_META = [
    ("Сахасрара", "#8a63ff", "A", "B"),
    ("Аджна", "#4a85ff", "O", "P"),
    ("Вишудха", "#2db6ff", "J", "K"),
    ("Анахата", "#7fd84a", "S", "T"),
    ("Манипура", "#ffd23c", "E", "E"),
    ("Свадхистана", "#ff9b38", "Q", "N"),
    ("Муладхара", "#ff584f", "C", "D"),
]


@dataclass
class LocalNode:
    physics: int
    energy: int
    emotion: int


def _sum_digits(value: int) -> int:
    return sum(int(char) for char in str(abs(value)))


def _reduce_arcana(value: int) -> int:
    result = abs(value)
    while result > 22:
        result = _sum_digits(result)
    return result or 22


def _build_local_destiny_matrix(birth_date: str) -> DestinyMatrixData:
    year_text, month_text, day_text = birth_date.split("-")

    day = _reduce_arcana(int(day_text))
    month = _reduce_arcana(int(month_text))
    year = _reduce_arcana(_sum_digits(int(year_text)))
    bottom = _reduce_arcana(day + month + year)
    center = _reduce_arcana(day + month + year + bottom)

    top_left = _reduce_arcana(day + month)
    top_center = _reduce_arcana(month + center)
    top_green = _reduce_arcana(month + bottom)
    left_outer = _reduce_arcana(day + year + center)
    left_inner = _reduce_arcana(day + center)
    right_outer = _reduce_arcana(day + year + center)
    bottom_inner = _reduce_arcana(center + bottom)
    bridge = _reduce_arcana(top_left + _reduce_arcana(year + bottom))

    local_rows = [
        LocalNode(day, month, _reduce_arcana(day + month)),
        LocalNode(left_outer, bridge, _reduce_arcana(left_outer + bridge)),
        LocalNode(left_inner, top_center, _reduce_arcana(left_inner + top_center)),
        LocalNode(day, top_green, _reduce_arcana(day + top_green)),
        LocalNode(center, center, _reduce_arcana(center + center)),
        LocalNode(right_outer, bottom_inner, _reduce_arcana(right_outer + bottom_inner)),
        LocalNode(year, bottom, _reduce_arcana(year + bottom)),
    ]

    rows = [
        DestinyMatrixRow(
            name=name,
            tone=tone,
            physics=node.physics,
            energy=node.energy,
            emotion=node.emotion,
        )
        for (name, tone, *_), node in zip(CHAKRA_META, local_rows, strict=True)
    ]

    totals = DestinyMatrixTotals(
        physics=_reduce_arcana(sum(item.physics for item in local_rows)),
        energy=_reduce_arcana(sum(item.energy for item in local_rows)),
        emotion=_reduce_arcana(sum(item.emotion for item in local_rows)),
    )
    return DestinyMatrixData(svg_html="", chakra_rows=rows, totals=totals)


@lru_cache(maxsize=256)
def fetch_destiny_matrix(birth_date: str) -> DestinyMatrixData:
    year_text, month_text, day_text = birth_date.split("-")
    payload = {
        "day": int(day_text),
        "month": int(month_text),
        "year": int(year_text),
        "name": "Человек",
        "gender": "MALE",
        "dontMakeFull": "1",
    }

    with httpx.Client(
        timeout=20.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        },
    ) as client:
        response = client.post(REMOTE_URL, data=payload)
        response.raise_for_status()
        raw = response.json()

    values: dict[str, int] = raw["values"]
    svg_html = base64.b64decode(raw["svg"]).decode("utf-8")

    rows = [
        DestinyMatrixRow(
            name=name,
            tone=tone,
            physics=values[physics_key],
            energy=values[energy_key],
            emotion=_reduce_arcana(values[physics_key] + values[energy_key]),
        )
        for name, tone, physics_key, energy_key in CHAKRA_META
    ]

    totals = DestinyMatrixTotals(
        physics=values["YOURF_1"],
        energy=values["YOURF_2"],
        emotion=values["YOURF_3"],
    )

    return DestinyMatrixData(svg_html=svg_html, chakra_rows=rows, totals=totals)


def fetch_destiny_matrix_safe(birth_date: str) -> DestinyMatrixData:
    try:
        return fetch_destiny_matrix(birth_date)
    except Exception:
        return _build_local_destiny_matrix(birth_date)
