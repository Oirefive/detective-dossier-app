from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class CaseSummary(CamelModel):
    id: str
    title: str
    classification: str
    status: str
    updated_at: str
    suspect_count: int
    pinned: bool = False


class CaseDetail(CamelModel):
    id: str
    title: str
    classification: str
    status: str
    summary: str
    updated_at: str
    pinned: bool = False


class CaseCreatePayload(CamelModel):
    title: str
    classification: str
    status: str
    summary: str
    pinned: bool = False


class Person(CamelModel):
    id: str
    full_name: str
    alias_name: str
    birth_date: Optional[str]
    age: Optional[int]
    biography: str
    documents_summary: str
    known_places: str
    habits: str
    photo_path: Optional[str]
    updated_at: str
    pinned: bool = False


class PersonCreatePayload(CamelModel):
    full_name: str
    alias_name: str = ""
    birth_date: Optional[str] = None
    age: Optional[int] = None
    biography: str = ""
    documents_summary: str = ""
    known_places: str = ""
    habits: str = ""
    photo_path: Optional[str] = None
    pinned: bool = False


class CaseParticipant(CamelModel):
    id: str
    case_id: str
    person_id: str
    full_name: str
    alias_name: str
    birth_date: Optional[str]
    age: Optional[int]
    biography: str
    documents_summary: str
    known_places: str
    habits: str
    photo_path: Optional[str]
    role: str
    suspicion_level: int
    status: str
    location: str
    description: str
    notes: str
    updated_at: str
    pinned: bool = False


class CaseAssignmentCreatePayload(CamelModel):
    person_id: str
    role: str = ""
    suspicion_level: int = 0
    status: str = ""
    location: str = ""
    description: str = ""
    notes: str = ""
    pinned: bool = False


class Evidence(CamelModel):
    id: str
    participant_id: str
    title: str
    category: str
    status: str
    details: str


class EvidenceCreatePayload(CamelModel):
    title: str
    category: str = ""
    status: str = ""
    details: str = ""


class EventItem(CamelModel):
    id: str
    participant_id: str
    event_date: str
    title: str
    details: str


class EventCreatePayload(CamelModel):
    event_date: str = ""
    title: str
    details: str = ""


class Relation(CamelModel):
    id: str
    participant_id: str
    target_type: str
    target_label: str
    relation_type: str
    confidence: int


class RelationCreatePayload(CamelModel):
    target_type: str = ""
    target_label: str
    relation_type: str = ""
    confidence: int = 50


class MatrixProfile(CamelModel):
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


class DestinyMatrixRow(CamelModel):
    name: str
    tone: str
    physics: int
    energy: int
    emotion: int


class DestinyMatrixTotals(CamelModel):
    physics: int
    energy: int
    emotion: int


class DestinyMatrixData(CamelModel):
    svg_html: str
    chakra_rows: list[DestinyMatrixRow]
    totals: DestinyMatrixTotals


class Dossier(CamelModel):
    participant: CaseParticipant
    case: CaseDetail
    evidence: list[Evidence]
    events: list[EventItem]
    relations: list[Relation]
    matrix: MatrixProfile | None


class RelationshipHit(CamelModel):
    participant: CaseParticipant
    score: int
    confidence: str
    summary: str
    matched_on: list[str]
    highlights: list[str]
    top_links: list[str]


class RelationshipSearchResponse(CamelModel):
    query: str
    case_id: str
    total: int
    hits: list[RelationshipHit]


class ArchiveSearchResult(CamelModel):
    entity_type: Literal["case", "person", "participant"]
    entity_id: str
    title: str
    subtitle: str
    case_id: str | None = None
    participant_id: str | None = None
    person_id: str | None = None
    status: str = ""
    score: int
    pinned: bool = False
    highlights: list[str]


class ArchiveSearchResponse(CamelModel):
    query: str
    total: int
    results: list[ArchiveSearchResult]


class MatrixComparisonResponse(CamelModel):
    left_person: Person
    right_person: Person
    left_matrix: MatrixProfile | None
    right_matrix: MatrixProfile | None
    compatibility_score: int
    resonance: str
    shared_strengths: list[str]
    tension_points: list[str]
    summary: str


class CaseCompatibilityResponse(CamelModel):
    person: Person
    case: CaseDetail
    matrix: MatrixProfile | None
    compatibility_score: int
    match_reasons: list[str]
    risk_factors: list[str]
    summary: str


class GraphNode(CamelModel):
    id: str
    label: str
    node_type: Literal["person", "participant", "place", "event", "evidence", "relation", "case"]
    status: str = ""
    pinned: bool = False
    meta: dict[str, Any] = {}


class GraphEdge(CamelModel):
    source: str
    target: str
    label: str
    weight: int = 1


class CaseGraphResponse(CamelModel):
    case_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class AutoBriefResponse(CamelModel):
    case_id: str
    headline: str
    summary: str
    key_people: list[str]
    key_places: list[str]
    key_risks: list[str]
    recommendations: list[str]


class CaseExportBundle(CamelModel):
    case: CaseDetail
    participants: list[CaseParticipant]
    people: list[Person]
    evidence: list[Evidence]
    events: list[EventItem]
    relations: list[Relation]


class ImportCaseResponse(CamelModel):
    case: CaseDetail
    imported_people: int
    imported_participants: int
    imported_evidence: int
    imported_events: int
    imported_relations: int


class AISettings(CamelModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    card_prompt: str = (
        "Ты аналитик расследований. По сырому тексту собери аккуратную карточку человека. "
        "Верни только JSON с полями: fullName, aliasName, birthDate, biography, documentsSummary, knownPlaces, habits. "
        "Пиши по-русски. Не выдумывай факты, которых нет в тексте. Если данных нет, верни пустую строку или null для birthDate."
    )
    dossier_prompt: str = (
        "Ты аналитик расследований. По карточке человека и контексту дела подготовь краткое досье. "
        "Верни только JSON с полями: summary, description, notes, status, suspicionLevel, keyFacts, redFlags, recommendations. "
        "Пиши по-русски, структурно, без воды и без выдумки."
    )


class AIPersonCardRequest(CamelModel):
    source_text: str


class AIPersonCardResponse(CamelModel):
    full_name: str = ""
    alias_name: str = ""
    birth_date: Optional[str] = None
    biography: str = ""
    documents_summary: str = ""
    known_places: str = ""
    habits: str = ""


class AIDossierRequest(CamelModel):
    participant: CaseParticipant | None = None
    person: Person | None = None
    case: CaseDetail | None = None


class AIDossierResponse(CamelModel):
    summary: str = ""
    description: str = ""
    notes: str = ""
    status: str = ""
    suspicion_level: int = 0
    key_facts: list[str] = []
    red_flags: list[str] = []
    recommendations: list[str] = []
