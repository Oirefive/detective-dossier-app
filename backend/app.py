from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .ai_service import AIService
from .analysis import build_auto_brief, build_case_compatibility, build_case_graph, compare_matrices
from .chakra_analysis import build_chakra_analysis
from .database import Database
from .destiny_matrix_service import fetch_destiny_matrix, fetch_destiny_matrix_safe
from .matrix import calculate_matrix
from .models import AIDossierRequest, AIDossierResponse, AIPersonCardRequest, AIPersonCardResponse, AISettings, ArchiveSearchResponse, AutoBriefResponse, CaseAssignmentCreatePayload, CaseCompatibilityResponse, CaseCreatePayload, CaseDetail, CaseExportBundle, CaseGraphResponse, CaseParticipant, CaseSummary, DestinyMatrixData, Dossier, Evidence, EvidenceCreatePayload, EventCreatePayload, EventItem, ImportCaseResponse, MatrixComparisonResponse, MatrixProfile, Person, PersonCreatePayload, Relation, RelationCreatePayload, RelationshipSearchResponse
from .pdf_service import PdfService


def resolve_bundle_root() -> Path:
    override = os.environ.get("ARCHIVE_BUNDLE_ROOT")
    return Path(override) if override else Path(__file__).resolve().parent.parent


def resolve_data_root(bundle_root: Path) -> Path:
    override = os.environ.get("ARCHIVE_DATA_ROOT")
    return Path(override) if override else bundle_root / "app_data"


BUNDLE_ROOT = resolve_bundle_root()
DATA_ROOT = resolve_data_root(BUNDLE_ROOT)
DIST_DIR = BUNDLE_ROOT / "dist"
UPLOADS_DIR = DATA_ROOT / "uploads"
database = Database(DATA_ROOT)
pdf_service = PdfService(DATA_ROOT / "exports")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Архив расследований")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
app.mount("/exports", StaticFiles(directory=DATA_ROOT / "exports"), name="exports")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    return database.list_cases()


@app.get("/api/settings/ai", response_model=AISettings)
def get_ai_settings() -> AISettings:
    return database.get_ai_settings()


@app.put("/api/settings/ai", response_model=AISettings)
def save_ai_settings(payload: AISettings) -> AISettings:
    return database.save_ai_settings(payload)


@app.post("/api/ai/person-card", response_model=AIPersonCardResponse)
def ai_person_card(payload: AIPersonCardRequest) -> AIPersonCardResponse:
    try:
        return AIService(database.get_ai_settings()).generate_person_card(payload.source_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc


@app.post("/api/ai/dossier", response_model=AIDossierResponse)
def ai_dossier(payload: AIDossierRequest) -> AIDossierResponse:
    try:
        return AIService(database.get_ai_settings()).generate_dossier(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc


@app.post("/api/cases", response_model=CaseDetail)
def create_case(payload: CaseCreatePayload) -> CaseDetail:
    return database.create_case(payload)


@app.delete("/api/cases/{case_id}", status_code=204)
def delete_case(case_id: str) -> Response:
    try:
        database.delete_case(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.put("/api/cases/{case_id}/pin", response_model=CaseDetail)
def pin_case(case_id: str, pinned: bool) -> CaseDetail:
    try:
        return database.set_case_pinned(case_id, pinned)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/people", response_model=list[Person])
def list_people() -> list[Person]:
    return database.list_people()


@app.post("/api/people", response_model=Person)
def create_person(payload: PersonCreatePayload) -> Person:
    return database.create_person(payload)


@app.put("/api/people/{person_id}", response_model=Person)
def save_person(person_id: str, payload: PersonCreatePayload) -> Person:
    try:
        return database.save_person(person_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/people/{person_id}", status_code=204)
def delete_person(person_id: str) -> Response:
    try:
        database.delete_person(person_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.put("/api/people/{person_id}/pin", response_model=Person)
def pin_person(person_id: str, pinned: bool) -> Person:
    try:
        return database.set_person_pinned(person_id, pinned)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/cases/{case_id}/people", response_model=list[CaseParticipant])
def list_case_people(case_id: str) -> list[CaseParticipant]:
    return database.list_case_people(case_id)


@app.post("/api/cases/{case_id}/people", response_model=CaseParticipant)
def add_person_to_case(case_id: str, payload: CaseAssignmentCreatePayload) -> CaseParticipant:
    return database.add_person_to_case(case_id, payload)


@app.get("/api/cases/{case_id}/relationship-search", response_model=RelationshipSearchResponse)
def relationship_search(case_id: str, q: str) -> RelationshipSearchResponse:
    return database.search_relationships(case_id, q)


@app.get("/api/archive-search", response_model=ArchiveSearchResponse)
def archive_search(q: str) -> ArchiveSearchResponse:
    return database.archive_search(q)


@app.get("/api/participants/{participant_id}/dossier", response_model=Dossier)
def get_dossier(participant_id: str) -> Dossier:
    try:
        return database.get_dossier(participant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/destiny-matrix", response_model=DestinyMatrixData)
def get_destiny_matrix(birth_date: str) -> DestinyMatrixData:
    try:
        return fetch_destiny_matrix(birth_date)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"destiny matrix sync failed: {exc}") from exc


@app.put("/api/participants/{participant_id}", response_model=CaseParticipant)
def save_participant(participant_id: str, payload: CaseParticipant) -> CaseParticipant:
    if payload.id != participant_id:
        raise HTTPException(status_code=400, detail="participant id mismatch")
    try:
        return database.save_participant(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/participants/{participant_id}/pin", response_model=CaseParticipant)
def pin_participant(participant_id: str, pinned: bool) -> CaseParticipant:
    try:
        return database.set_participant_pinned(participant_id, pinned)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/participants/{participant_id}/evidence", response_model=Evidence)
def create_evidence(participant_id: str, payload: EvidenceCreatePayload) -> Evidence:
    try:
        return database.create_evidence(participant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/evidence/{evidence_id}", status_code=204)
def delete_evidence(evidence_id: str) -> Response:
    try:
        database.delete_evidence(evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.post("/api/participants/{participant_id}/events", response_model=EventItem)
def create_event(participant_id: str, payload: EventCreatePayload) -> EventItem:
    try:
        return database.create_event(participant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: str) -> Response:
    try:
        database.delete_event(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.post("/api/participants/{participant_id}/relations", response_model=Relation)
def create_relation(participant_id: str, payload: RelationCreatePayload) -> Relation:
    try:
        return database.create_relation(participant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/relations/{relation_id}", status_code=204)
def delete_relation(relation_id: str) -> Response:
    try:
        database.delete_relation(relation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.get("/api/cases/{case_id}/graph", response_model=CaseGraphResponse)
def case_graph(case_id: str) -> CaseGraphResponse:
    try:
        bundle = database.export_case_bundle(case_id)
        return build_case_graph(bundle.case, bundle)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/people/{left_person_id}/matrix-compare/{right_person_id}", response_model=MatrixComparisonResponse)
def matrix_compare(left_person_id: str, right_person_id: str) -> MatrixComparisonResponse:
    try:
        left_person = database.get_person(left_person_id)
        right_person = database.get_person(right_person_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    left_raw = calculate_matrix(left_person.birth_date)
    right_raw = calculate_matrix(right_person.birth_date)
    return compare_matrices(
        left_person,
        right_person,
        MatrixProfile(**left_raw.__dict__) if left_raw else None,
        MatrixProfile(**right_raw.__dict__) if right_raw else None,
    )


@app.get("/api/people/{person_id}/case-compatibility/{case_id}", response_model=CaseCompatibilityResponse)
def case_compatibility(person_id: str, case_id: str) -> CaseCompatibilityResponse:
    try:
        person = database.get_person(person_id)
        case = database.get_case_detail(case_id)
        participants = database.list_case_people(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raw_matrix = calculate_matrix(person.birth_date)
    matrix = MatrixProfile(**raw_matrix.__dict__) if raw_matrix else None
    return build_case_compatibility(person, case, matrix, participants)


@app.get("/api/cases/{case_id}/autobrief", response_model=AutoBriefResponse)
def autobrief(case_id: str) -> AutoBriefResponse:
    try:
        bundle = database.export_case_bundle(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_auto_brief(bundle.case, bundle)


@app.get("/api/cases/{case_id}/export", response_model=CaseExportBundle)
def export_case(case_id: str) -> CaseExportBundle:
    try:
        return database.export_case_bundle(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/cases/import", response_model=ImportCaseResponse)
def import_case(bundle: CaseExportBundle) -> ImportCaseResponse:
    case = database.import_case_bundle(bundle)
    return ImportCaseResponse(case=case, imported_people=len(bundle.people), imported_participants=len(bundle.participants), imported_evidence=len(bundle.evidence), imported_events=len(bundle.events), imported_relations=len(bundle.relations))


@app.post("/api/uploads/photo", response_model=str)
async def upload_photo(file: UploadFile = File(...)) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="unsupported file type")
    file_name = f"{uuid4().hex}{suffix}"
    target = UPLOADS_DIR / file_name
    target.write_bytes(await file.read())
    return f"/uploads/{file_name}"


@app.post("/api/participants/{participant_id}/pdf", response_model=str)
def generate_pdf(participant_id: str, template: str = "dossier") -> str:
    try:
        dossier = database.get_dossier(participant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if template not in {"dossier", "board"}:
        raise HTTPException(status_code=400, detail="unsupported pdf template")
    destiny_matrix = None
    chakra_analysis = None
    if dossier.participant.birth_date:
        destiny_matrix = fetch_destiny_matrix_safe(dossier.participant.birth_date)
        chakra_analysis = build_chakra_analysis(destiny_matrix, dossier.participant.birth_date)
    return pdf_service.generate(dossier, template=template, destiny_matrix=destiny_matrix, chakra_analysis=chakra_analysis)


@app.get("/")
def root():
    index_file = DIST_DIR / "index.html"
    return FileResponse(index_file) if index_file.exists() else {"status": "ok", "message": "Frontend build not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
