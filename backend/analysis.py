from __future__ import annotations

from collections import Counter

from .models import AutoBriefResponse, CaseCompatibilityResponse, CaseDetail, CaseExportBundle, CaseGraphResponse, CaseParticipant, GraphEdge, GraphNode, MatrixComparisonResponse, MatrixProfile, Person


def compare_matrices(left_person: Person, right_person: Person, left_matrix: MatrixProfile | None, right_matrix: MatrixProfile | None) -> MatrixComparisonResponse:
    if not left_matrix or not right_matrix:
        return MatrixComparisonResponse(
            left_person=left_person,
            right_person=right_person,
            left_matrix=left_matrix,
            right_matrix=right_matrix,
            compatibility_score=0,
            resonance="недостаточно данных",
            shared_strengths=[],
            tension_points=["Для сравнения обеим персонам нужна дата рождения."],
            summary="Сравнение не выполнено: у одной из карточек нет даты рождения.",
        )

    same_dominants = sorted(set(left_matrix.dominant_numbers) & set(right_matrix.dominant_numbers))
    shared_gaps = sorted(set(left_matrix.missing_numbers) & set(right_matrix.missing_numbers))
    line_delta = abs(left_matrix.purpose_line - right_matrix.purpose_line) + abs(left_matrix.family_line - right_matrix.family_line) + abs(left_matrix.stability_line - right_matrix.stability_line)
    vector_delta = abs(left_matrix.temperament - right_matrix.temperament) + abs(left_matrix.spirituality - right_matrix.spirituality) + abs(left_matrix.grounding - right_matrix.grounding)
    compatibility_score = max(0, min(100, 62 + len(same_dominants) * 7 - len(shared_gaps) * 4 - line_delta * 2 - vector_delta))

    if compatibility_score >= 80:
        resonance = "сильный резонанс"
    elif compatibility_score >= 60:
        resonance = "рабочая совместимость"
    elif compatibility_score >= 40:
        resonance = "нестабильный союз"
    else:
        resonance = "конфликтный контур"

    shared_strengths: list[str] = []
    if same_dominants:
        shared_strengths.append(f"Совпадают доминирующие числа: {', '.join(map(str, same_dominants))}.")
    if abs(left_matrix.life_path - right_matrix.life_path) <= 1:
        shared_strengths.append("Путь развития идёт в близком темпе, без резкого расхождения ритма.")
    if abs(left_matrix.spirituality - right_matrix.spirituality) <= 1:
        shared_strengths.append("Схожая чувствительность к знакам, символам и повторяющимся паттернам.")
    if abs(left_matrix.grounding - right_matrix.grounding) <= 1:
        shared_strengths.append("Похожий уровень приземлённости: оба либо держатся за фактуру, либо одинаково тонут в хаосе.")

    tension_points: list[str] = []
    if shared_gaps:
        tension_points.append(f"Общие пустоты матрицы: {', '.join(map(str, shared_gaps))}. Эти зоны оба будут недовыполнять.")
    if abs(left_matrix.family_line - right_matrix.family_line) >= 3:
        tension_points.append("Разный режим близости: один тянется к включению, другой держит дистанцию.")
    if abs(left_matrix.purpose_line - right_matrix.purpose_line) >= 3:
        tension_points.append("Линия цели расходится слишком сильно: один давит вперёд, второй этот темп не держит.")
    if abs(left_matrix.temperament - right_matrix.temperament) >= 3:
        tension_points.append("Темперамент сильно расходится, поэтому в стрессе связка будет скрипеть.")

    if not shared_strengths:
        shared_strengths.append("Явного мистического резонанса не видно, но прямого обрушения тоже нет.")
    if not tension_points:
        tension_points.append("Критичных эзотерических противоречий по матрице не выявлено.")

    summary = (
        f"{left_person.full_name} и {right_person.full_name}: {resonance}. "
        f"Совместимость оценена в {compatibility_score} из 100. "
        f"Опора: {shared_strengths[0].lower()} Напряжение: {tension_points[0].lower()}"
    )

    return MatrixComparisonResponse(left_person=left_person, right_person=right_person, left_matrix=left_matrix, right_matrix=right_matrix, compatibility_score=compatibility_score, resonance=resonance, shared_strengths=shared_strengths, tension_points=tension_points, summary=summary)


def build_case_compatibility(person: Person, case: CaseDetail, matrix: MatrixProfile | None, participants: list[CaseParticipant]) -> CaseCompatibilityResponse:
    reasons: list[str] = []
    risks: list[str] = []
    score = 35

    case_text = " ".join([case.title, case.classification, case.status, case.summary]).lower()
    person_text = " ".join([person.full_name, person.alias_name, person.biography, person.documents_summary, person.known_places, person.habits]).lower()

    for keyword in ("архив", "терминал", "порт", "пропуск", "ритуал", "склад", "секта", "ноч"):
        if keyword in case_text and keyword in person_text:
            score += 8
            reasons.append(f"Есть прямое текстовое совпадение по ключу «{keyword}».")

    if matrix:
        if matrix.spirituality >= 4:
            score += 10
            reasons.append("Матрица показывает высокую чувствительность к символическим и аномальным слоям дела.")
        if matrix.purpose_line >= 5:
            score += 7
            reasons.append("Сильная линия цели: человек выдержит длинное и давящее расследование.")
        if len(matrix.missing_numbers) >= 4:
            score -= 6
            risks.append("В матрице много пустот: человек может сорваться или уйти в хаотичный режим.")
        if matrix.family_line <= 2:
            risks.append("Низкая линия семьи: в закрытом деле будет хуже работать через доверительные связи.")
    else:
        risks.append("Нет даты рождения, поэтому эзотерический слой совместимости не рассчитан.")

    if participants:
        avg_risk = sum(item.suspicion_level for item in participants) / len(participants)
        if avg_risk >= 60:
            score += 8
            reasons.append("Само дело тяжёлое, а профиль человека тянет на работу в жёстком контуре.")
        if any(person.full_name.lower() in item.notes.lower() for item in participants):
            score += 6
            reasons.append("Имя человека уже всплывает в заметках по текущему делу.")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("Жёстких пересечений не найдено, но человек вписывается в общий профиль дела по фактуре.")
    if not risks:
        risks.append("Критических факторов несовместимости не выявлено.")

    summary = f"Совместимость человека с делом: {score} из 100. Опора: {reasons[0].lower()} Риск: {risks[0].lower()}"
    return CaseCompatibilityResponse(person=person, case=case, matrix=matrix, compatibility_score=score, match_reasons=reasons, risk_factors=risks, summary=summary)


def build_case_graph(case: CaseDetail, bundle: CaseExportBundle) -> CaseGraphResponse:
    nodes: list[GraphNode] = [GraphNode(id=f"case:{case.id}", label=case.title, node_type="case", status=case.status, pinned=case.pinned, meta={"classification": case.classification})]
    edges: list[GraphEdge] = []
    place_nodes: dict[str, str] = {}
    evidence_nodes: dict[str, str] = {}
    event_nodes: dict[str, str] = {}

    people_by_id = {person.id: person for person in bundle.people}
    for participant in bundle.participants:
      person = people_by_id.get(participant.person_id)
      person_node_id = f"person:{participant.person_id}"
      if person:
          nodes.append(GraphNode(id=person_node_id, label=person.full_name, node_type="person", status=participant.status or person.alias_name, pinned=person.pinned, meta={"alias": person.alias_name}))
      participant_node_id = f"participant:{participant.id}"
      nodes.append(GraphNode(id=participant_node_id, label=participant.alias_name or participant.full_name, node_type="participant", status=participant.status, pinned=participant.pinned, meta={"risk": participant.suspicion_level, "role": participant.role}))
      edges.append(GraphEdge(source=f"case:{case.id}", target=participant_node_id, label="участник", weight=3))
      edges.append(GraphEdge(source=person_node_id, target=participant_node_id, label="роль в деле", weight=2))

      places = [item.strip() for item in (participant.location + "," + participant.known_places).split(",") if item.strip()]
      for place in places[:4]:
          node_id = place_nodes.get(place)
          if node_id is None:
              node_id = f"place:{len(place_nodes) + 1}"
              place_nodes[place] = node_id
              nodes.append(GraphNode(id=node_id, label=place, node_type="place"))
          edges.append(GraphEdge(source=participant_node_id, target=node_id, label="замечен", weight=1))

    for item in bundle.evidence:
        node_id = evidence_nodes.setdefault(item.id, f"evidence:{item.id}")
        nodes.append(GraphNode(id=node_id, label=item.title, node_type="evidence", status=item.status, meta={"category": item.category}))
        edges.append(GraphEdge(source=f"participant:{item.participant_id}", target=node_id, label="улика", weight=2))

    for item in bundle.events:
        node_id = event_nodes.setdefault(item.id, f"event:{item.id}")
        nodes.append(GraphNode(id=node_id, label=item.title, node_type="event", status=item.event_date, meta={"date": item.event_date}))
        edges.append(GraphEdge(source=f"participant:{item.participant_id}", target=node_id, label="событие", weight=2))

    for item in bundle.relations:
        relation_node_id = f"relation:{item.id}"
        nodes.append(GraphNode(id=relation_node_id, label=item.target_label, node_type="relation", status=item.relation_type, meta={"confidence": item.confidence, "targetType": item.target_type}))
        edges.append(GraphEdge(source=f"participant:{item.participant_id}", target=relation_node_id, label="связь", weight=2))

    return CaseGraphResponse(case_id=case.id, nodes=_dedupe_nodes(nodes), edges=edges)


def build_auto_brief(case: CaseDetail, bundle: CaseExportBundle) -> AutoBriefResponse:
    top_people = sorted(bundle.participants, key=lambda item: (-item.suspicion_level, not item.pinned, item.full_name))[:4]
    key_people = [f"{item.full_name} ({item.alias_name or item.role or 'без псевдонима'})" for item in top_people]

    place_counter: Counter[str] = Counter()
    for participant in bundle.participants:
        for place in [item.strip() for item in participant.location.split(",") if item.strip()]:
            place_counter[place] += 2
        for place in [item.strip() for item in participant.known_places.split(",") if item.strip()]:
            place_counter[place] += 1
    key_places = [label for label, _ in place_counter.most_common(5)]

    key_risks: list[str] = []
    if any(item.suspicion_level >= 80 for item in bundle.participants):
        key_risks.append("В деле есть фигуранты с критическим уровнем подозрения.")
    if len(bundle.relations) >= len(bundle.participants):
        key_risks.append("Связей много: сеть уже плотная, а значит и цепочка утечки глубже, чем кажется.")
    if len(bundle.evidence) == 0:
        key_risks.append("Материальной базы пока мало, дело может держаться на косвенных совпадениях.")
    if not key_risks:
        key_risks.append("Риск умеренный, но картина ещё может резко стать хуже после следующей привязки.")

    recommendations = [
        "Сначала добить три главные связи и только потом расширять сеть второстепенных объектов.",
        "Сверить хронологию событий с ключевыми местами и документами, чтобы выбить ложные совпадения.",
        "По топ-фигурантам подготовить отдельные печатные карточки для доски расследования.",
    ]

    headline = f"{case.title}: {len(bundle.participants)} участник(ов), {len(bundle.evidence)} улика(ок), {len(bundle.events)} событие(й)"
    summary = f"Дело «{case.title}» сейчас держится на {len(bundle.participants)} участниках и {len(bundle.relations)} связях. Ядро контура: {', '.join(key_people[:2]) if key_people else 'фигуранты пока не выделены'}. Ключевые точки: {', '.join(key_places[:3]) if key_places else 'локации не зафиксированы'}."

    return AutoBriefResponse(case_id=case.id, headline=headline, summary=summary, key_people=key_people, key_places=key_places, key_risks=key_risks, recommendations=recommendations)


def _dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    seen: dict[str, GraphNode] = {}
    for node in nodes:
        seen.setdefault(node.id, node)
    return list(seen.values())
