from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from .matrix import calculate_matrix, compute_age
from .models import AISettings, ArchiveSearchResponse, ArchiveSearchResult, CaseAssignmentCreatePayload, CaseCreatePayload, CaseDetail, CaseExportBundle, CaseParticipant, CaseSummary, Dossier, Evidence, EvidenceCreatePayload, EventCreatePayload, EventItem, MatrixProfile, Person, PersonCreatePayload, Relation, RelationCreatePayload, RelationshipHit, RelationshipSearchResponse


class Database:
    def __init__(self, root: Path) -> None:
        self.app_data = root
        self.app_data.mkdir(parents=True, exist_ok=True)
        self.db_path = self.app_data / "detective_dossier.sqlite"
        self._init_db()
        self._bootstrap_examples()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                  id TEXT PRIMARY KEY,title TEXT NOT NULL,classification TEXT NOT NULL,status TEXT NOT NULL,
                  summary TEXT NOT NULL,pinned INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS people (
                  id TEXT PRIMARY KEY,full_name TEXT NOT NULL,alias_name TEXT NOT NULL DEFAULT '',birth_date TEXT,age INTEGER,
                  biography TEXT NOT NULL DEFAULT '',documents_summary TEXT NOT NULL DEFAULT '',known_places TEXT NOT NULL DEFAULT '',
                  habits TEXT NOT NULL DEFAULT '',photo_path TEXT,pinned INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS case_people (
                  id TEXT PRIMARY KEY,case_id TEXT NOT NULL,person_id TEXT NOT NULL,role TEXT NOT NULL DEFAULT '',
                  suspicion_level INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT '',location TEXT NOT NULL DEFAULT '',
                  description TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',pinned INTEGER NOT NULL DEFAULT 0,
                  updated_at TEXT NOT NULL,FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE,
                  FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE,UNIQUE(case_id, person_id)
                );
                CREATE TABLE IF NOT EXISTS evidence (
                  id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,title TEXT NOT NULL,category TEXT NOT NULL,status TEXT NOT NULL,
                  details TEXT NOT NULL,FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,event_date TEXT NOT NULL,title TEXT NOT NULL,
                  details TEXT NOT NULL,FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS relations (
                  id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,target_type TEXT NOT NULL,target_label TEXT NOT NULL,
                  relation_type TEXT NOT NULL,confidence INTEGER NOT NULL DEFAULT 0,
                  FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS settings (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                );
                """
            )
            self._ensure_column(conn, "cases", "pinned", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "people", "birth_date", "TEXT")
            self._ensure_column(conn, "people", "pinned", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "case_people", "pinned", "INTEGER NOT NULL DEFAULT 0")
            self._migrate_legacy_link_table(conn, "evidence", "CREATE TABLE evidence (id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,title TEXT NOT NULL,category TEXT NOT NULL,status TEXT NOT NULL,details TEXT NOT NULL,FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE)", "id, COALESCE(participant_id, suspect_id) AS participant_id, title, category, status, details")
            self._migrate_legacy_link_table(conn, "events", "CREATE TABLE events (id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,event_date TEXT NOT NULL,title TEXT NOT NULL,details TEXT NOT NULL,FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE)", "id, COALESCE(participant_id, suspect_id) AS participant_id, event_date, title, details")
            self._migrate_legacy_link_table(conn, "relations", "CREATE TABLE relations (id TEXT PRIMARY KEY,participant_id TEXT NOT NULL,target_type TEXT NOT NULL,target_label TEXT NOT NULL,relation_type TEXT NOT NULL,confidence INTEGER NOT NULL DEFAULT 0,FOREIGN KEY(participant_id) REFERENCES case_people(id) ON DELETE CASCADE)", "id, COALESCE(participant_id, suspect_id) AS participant_id, target_type, target_label, relation_type, confidence")

    def get_ai_settings(self) -> AISettings:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key='ai_settings'").fetchone()
        if row is None:
            return AISettings()
        try:
            payload = json.loads(row["value"])
        except json.JSONDecodeError:
            return AISettings()
        return AISettings(**payload)

    def save_ai_settings(self, settings: AISettings) -> AISettings:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings(key, value) VALUES ('ai_settings', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (json.dumps(settings.model_dump(by_alias=False), ensure_ascii=False),),
            )
        return self.get_ai_settings()

    def list_cases(self) -> list[CaseSummary]:
        with self.connect() as conn:
            rows = conn.execute("SELECT c.id,c.title,c.classification,c.status,c.updated_at,c.pinned,COUNT(cp.id) AS suspect_count FROM cases c LEFT JOIN case_people cp ON cp.case_id=c.id GROUP BY c.id ORDER BY c.pinned DESC,c.updated_at DESC").fetchall()
        return [CaseSummary(**self._row_bool(dict(row), "pinned")) for row in rows]

    def get_case_detail(self, case_id: str) -> CaseDetail:
        with self.connect() as conn:
            row = conn.execute("SELECT id,title,classification,status,summary,pinned,updated_at FROM cases WHERE id=?", (case_id,)).fetchone()
        if row is None:
            raise ValueError("case not found")
        return CaseDetail(**self._row_bool(dict(row), "pinned"))

    def create_case(self, payload: CaseCreatePayload) -> CaseDetail:
        case_id = str(uuid.uuid4())
        updated_at = self._now()
        with self.connect() as conn:
            conn.execute("INSERT INTO cases(id,title,classification,status,summary,pinned,updated_at) VALUES (?,?,?,?,?,?,?)", (case_id, payload.title, payload.classification, payload.status, payload.summary, int(payload.pinned), updated_at))
        return CaseDetail(id=case_id, title=payload.title, classification=payload.classification, status=payload.status, summary=payload.summary, pinned=payload.pinned, updated_at=updated_at)

    def delete_case(self, case_id: str) -> None:
        with self.connect() as conn:
            result = conn.execute("DELETE FROM cases WHERE id=?", (case_id,))
            if result.rowcount == 0:
                raise ValueError("case not found")

    def set_case_pinned(self, case_id: str, pinned: bool) -> CaseDetail:
        with self.connect() as conn:
            result = conn.execute("UPDATE cases SET pinned=?, updated_at=? WHERE id=?", (int(pinned), self._now(), case_id))
            if result.rowcount == 0:
                raise ValueError("case not found")
        return self.get_case_detail(case_id)

    def list_people(self) -> list[Person]:
        with self.connect() as conn:
            rows = conn.execute("SELECT id,full_name,alias_name,birth_date,age,biography,documents_summary,known_places,habits,photo_path,pinned,updated_at FROM people ORDER BY pinned DESC,updated_at DESC,full_name").fetchall()
        return [Person(**self._row_bool(dict(row), "pinned")) for row in rows]

    def get_person(self, person_id: str) -> Person:
        with self.connect() as conn:
            row = conn.execute("SELECT id,full_name,alias_name,birth_date,age,biography,documents_summary,known_places,habits,photo_path,pinned,updated_at FROM people WHERE id=?", (person_id,)).fetchone()
        if row is None:
            raise ValueError("person not found")
        return Person(**self._row_bool(dict(row), "pinned"))

    def create_person(self, payload: PersonCreatePayload) -> Person:
        person_id = str(uuid.uuid4())
        updated_at = self._now()
        age = compute_age(payload.birth_date) if payload.birth_date else payload.age
        with self.connect() as conn:
            conn.execute("INSERT INTO people(id,full_name,alias_name,birth_date,age,biography,documents_summary,known_places,habits,photo_path,pinned,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (person_id, payload.full_name, payload.alias_name, payload.birth_date, age, payload.biography, payload.documents_summary, payload.known_places, payload.habits, payload.photo_path, int(payload.pinned), updated_at))
        return Person(id=person_id, full_name=payload.full_name, alias_name=payload.alias_name, birth_date=payload.birth_date, age=age, biography=payload.biography, documents_summary=payload.documents_summary, known_places=payload.known_places, habits=payload.habits, photo_path=payload.photo_path, pinned=payload.pinned, updated_at=updated_at)

    def save_person(self, person_id: str, payload: PersonCreatePayload) -> Person:
        updated_at = self._now()
        age = compute_age(payload.birth_date) if payload.birth_date else payload.age
        with self.connect() as conn:
            result = conn.execute("UPDATE people SET full_name=?,alias_name=?,birth_date=?,age=?,biography=?,documents_summary=?,known_places=?,habits=?,photo_path=?,pinned=?,updated_at=? WHERE id=?", (payload.full_name, payload.alias_name, payload.birth_date, age, payload.biography, payload.documents_summary, payload.known_places, payload.habits, payload.photo_path, int(payload.pinned), updated_at, person_id))
            if result.rowcount == 0:
                raise ValueError("person not found")
        return self.get_person(person_id)

    def delete_person(self, person_id: str) -> None:
        with self.connect() as conn:
            result = conn.execute("DELETE FROM people WHERE id=?", (person_id,))
            if result.rowcount == 0:
                raise ValueError("person not found")

    def set_person_pinned(self, person_id: str, pinned: bool) -> Person:
        with self.connect() as conn:
            result = conn.execute("UPDATE people SET pinned=?, updated_at=? WHERE id=?", (int(pinned), self._now(), person_id))
            if result.rowcount == 0:
                raise ValueError("person not found")
        return self.get_person(person_id)

    def list_case_people(self, case_id: str) -> list[CaseParticipant]:
        with self.connect() as conn:
            rows = conn.execute(self._participant_select() + " WHERE cp.case_id=? ORDER BY cp.pinned DESC,cp.suspicion_level DESC,cp.updated_at DESC", (case_id,)).fetchall()
        return [CaseParticipant(**self._row_bool(dict(row), "pinned")) for row in rows]

    def get_participant(self, participant_id: str) -> CaseParticipant:
        with self.connect() as conn:
            row = conn.execute(self._participant_select() + " WHERE cp.id=?", (participant_id,)).fetchone()
        if row is None:
            raise ValueError("participant not found")
        return CaseParticipant(**self._row_bool(dict(row), "pinned"))

    def add_person_to_case(self, case_id: str, payload: CaseAssignmentCreatePayload) -> CaseParticipant:
        participant_id = str(uuid.uuid4())
        updated_at = self._now()
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM case_people WHERE case_id=? AND person_id=?", (case_id, payload.person_id)).fetchone()
            if existing:
                participant_id = existing["id"]
            conn.execute(
                """
                INSERT INTO case_people(id,case_id,person_id,role,suspicion_level,status,location,description,notes,pinned,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(case_id, person_id) DO UPDATE SET
                role=excluded.role,suspicion_level=excluded.suspicion_level,status=excluded.status,location=excluded.location,
                description=excluded.description,notes=excluded.notes,pinned=excluded.pinned,updated_at=excluded.updated_at
                """,
                (participant_id, case_id, payload.person_id, payload.role, payload.suspicion_level, payload.status, payload.location, payload.description, payload.notes, int(payload.pinned), updated_at),
            )
            conn.execute("UPDATE cases SET updated_at=? WHERE id=?", (updated_at, case_id))
        return self._load_participant_by_case_person(case_id, payload.person_id)

    def set_participant_pinned(self, participant_id: str, pinned: bool) -> CaseParticipant:
        with self.connect() as conn:
            result = conn.execute("UPDATE case_people SET pinned=?, updated_at=? WHERE id=?", (int(pinned), self._now(), participant_id))
            if result.rowcount == 0:
                raise ValueError("participant not found")
            self._touch_participant_case(conn, participant_id)
        return self.get_participant(participant_id)

    def get_dossier(self, participant_id: str) -> Dossier:
        participant = self.get_participant(participant_id)
        case = self.get_case_detail(participant.case_id)
        with self.connect() as conn:
            evidence_rows = conn.execute("SELECT id,participant_id,title,category,status,details FROM evidence WHERE participant_id=? ORDER BY title", (participant_id,)).fetchall()
            event_rows = conn.execute("SELECT id,participant_id,event_date,title,details FROM events WHERE participant_id=? ORDER BY event_date DESC", (participant_id,)).fetchall()
            relation_rows = conn.execute("SELECT id,participant_id,target_type,target_label,relation_type,confidence FROM relations WHERE participant_id=? ORDER BY confidence DESC", (participant_id,)).fetchall()
        matrix = calculate_matrix(participant.birth_date)
        return Dossier(participant=participant, case=case, evidence=[Evidence(**dict(row)) for row in evidence_rows], events=[EventItem(**dict(row)) for row in event_rows], relations=[Relation(**dict(row)) for row in relation_rows], matrix=(MatrixProfile(**matrix.__dict__) if matrix else None))

    def save_participant(self, payload: CaseParticipant) -> CaseParticipant:
        updated_at = self._now()
        age = compute_age(payload.birth_date) if payload.birth_date else payload.age
        with self.connect() as conn:
            conn.execute("UPDATE people SET full_name=?,alias_name=?,birth_date=?,age=?,biography=?,documents_summary=?,known_places=?,habits=?,photo_path=?,updated_at=? WHERE id=?", (payload.full_name, payload.alias_name, payload.birth_date, age, payload.biography, payload.documents_summary, payload.known_places, payload.habits, payload.photo_path, updated_at, payload.person_id))
            result = conn.execute("UPDATE case_people SET role=?,suspicion_level=?,status=?,location=?,description=?,notes=?,pinned=?,updated_at=? WHERE id=?", (payload.role, payload.suspicion_level, payload.status, payload.location, payload.description, payload.notes, int(payload.pinned), updated_at, payload.id))
            if result.rowcount == 0:
                raise ValueError("participant not found")
            conn.execute("UPDATE cases SET updated_at=? WHERE id=?", (updated_at, payload.case_id))
        return self.get_dossier(payload.id).participant

    def create_evidence(self, participant_id: str, payload: EvidenceCreatePayload) -> Evidence:
        evidence_id = str(uuid.uuid4())
        with self.connect() as conn:
            self._ensure_participant_exists(conn, participant_id)
            conn.execute("INSERT INTO evidence(id,participant_id,title,category,status,details) VALUES (?,?,?,?,?,?)", (evidence_id, participant_id, payload.title, payload.category, payload.status, payload.details))
            self._touch_participant_case(conn, participant_id)
        return Evidence(id=evidence_id, participant_id=participant_id, title=payload.title, category=payload.category, status=payload.status, details=payload.details)

    def delete_evidence(self, evidence_id: str) -> None:
        with self.connect() as conn:
            row = conn.execute("SELECT participant_id FROM evidence WHERE id=?", (evidence_id,)).fetchone()
            if row is None:
                raise ValueError("evidence not found")
            conn.execute("DELETE FROM evidence WHERE id=?", (evidence_id,))
            self._touch_participant_case(conn, row["participant_id"])

    def create_event(self, participant_id: str, payload: EventCreatePayload) -> EventItem:
        event_id = str(uuid.uuid4())
        event_date = payload.event_date.strip() or self._now()
        with self.connect() as conn:
            self._ensure_participant_exists(conn, participant_id)
            conn.execute("INSERT INTO events(id,participant_id,event_date,title,details) VALUES (?,?,?,?,?)", (event_id, participant_id, event_date, payload.title, payload.details))
            self._touch_participant_case(conn, participant_id)
        return EventItem(id=event_id, participant_id=participant_id, event_date=event_date, title=payload.title, details=payload.details)

    def delete_event(self, event_id: str) -> None:
        with self.connect() as conn:
            row = conn.execute("SELECT participant_id FROM events WHERE id=?", (event_id,)).fetchone()
            if row is None:
                raise ValueError("event not found")
            conn.execute("DELETE FROM events WHERE id=?", (event_id,))
            self._touch_participant_case(conn, row["participant_id"])

    def create_relation(self, participant_id: str, payload: RelationCreatePayload) -> Relation:
        relation_id = str(uuid.uuid4())
        confidence = max(0, min(100, payload.confidence))
        with self.connect() as conn:
            self._ensure_participant_exists(conn, participant_id)
            conn.execute("INSERT INTO relations(id,participant_id,target_type,target_label,relation_type,confidence) VALUES (?,?,?,?,?,?)", (relation_id, participant_id, payload.target_type, payload.target_label, payload.relation_type, confidence))
            self._touch_participant_case(conn, participant_id)
        return Relation(id=relation_id, participant_id=participant_id, target_type=payload.target_type, target_label=payload.target_label, relation_type=payload.relation_type, confidence=confidence)

    def delete_relation(self, relation_id: str) -> None:
        with self.connect() as conn:
            row = conn.execute("SELECT participant_id FROM relations WHERE id=?", (relation_id,)).fetchone()
            if row is None:
                raise ValueError("relation not found")
            conn.execute("DELETE FROM relations WHERE id=?", (relation_id,))
            self._touch_participant_case(conn, row["participant_id"])

    def search_relationships(self, case_id: str, query: str) -> RelationshipSearchResponse:
        tokens = self._tokenize(query)
        participants = self.list_case_people(case_id)
        if not tokens:
            return RelationshipSearchResponse(query=query, case_id=case_id, total=0, hits=[])
        hits: list[RelationshipHit] = []
        with self.connect() as conn:
            for participant in participants:
                evidence = [Evidence(**dict(row)) for row in conn.execute("SELECT id,participant_id,title,category,status,details FROM evidence WHERE participant_id=?", (participant.id,)).fetchall()]
                events = [EventItem(**dict(row)) for row in conn.execute("SELECT id,participant_id,event_date,title,details FROM events WHERE participant_id=?", (participant.id,)).fetchall()]
                relations = [Relation(**dict(row)) for row in conn.execute("SELECT id,participant_id,target_type,target_label,relation_type,confidence FROM relations WHERE participant_id=?", (participant.id,)).fetchall()]
                score, matched_on, highlights, top_links = self._score_participant(tokens, participant, evidence, events, relations)
                if score <= 0:
                    continue
                hits.append(RelationshipHit(participant=participant, score=score, confidence=self._confidence(score), summary=self._summary_for_hit(participant, matched_on, top_links), matched_on=matched_on[:6], highlights=highlights[:5], top_links=top_links[:4]))
        hits.sort(key=lambda item: (-item.score, not item.participant.pinned, -item.participant.suspicion_level, item.participant.full_name))
        return RelationshipSearchResponse(query=query, case_id=case_id, total=len(hits), hits=hits[:12])

    def archive_search(self, query: str) -> ArchiveSearchResponse:
        tokens = self._tokenize(query)
        if not tokens:
            return ArchiveSearchResponse(query=query, total=0, results=[])
        results: list[ArchiveSearchResult] = []
        with self.connect() as conn:
            for row in conn.execute("SELECT id,title,classification,status,summary,pinned FROM cases").fetchall():
                score, highlights = self._score_text(tokens, " ".join([row["title"], row["classification"], row["status"], row["summary"]]), [row["title"], row["summary"]])
                if score:
                    results.append(ArchiveSearchResult(entity_type="case", entity_id=row["id"], title=row["title"], subtitle=f'{row["classification"]} · {row["status"]}', case_id=row["id"], status=row["status"], score=score + (15 if row["pinned"] else 0), pinned=bool(row["pinned"]), highlights=highlights))
            for row in conn.execute("SELECT id,full_name,alias_name,biography,documents_summary,known_places,habits,pinned FROM people").fetchall():
                score, highlights = self._score_text(tokens, " ".join([row["full_name"], row["alias_name"], row["biography"], row["documents_summary"], row["known_places"], row["habits"]]), [row["full_name"], row["alias_name"], row["known_places"]])
                if score:
                    results.append(ArchiveSearchResult(entity_type="person", entity_id=row["id"], title=row["full_name"], subtitle=row["alias_name"] or "Карточка человека", person_id=row["id"], score=score + (15 if row["pinned"] else 0), pinned=bool(row["pinned"]), highlights=highlights))
            for raw in conn.execute(self._participant_select()).fetchall():
                row = self._row_bool(dict(raw), "pinned")
                score, highlights = self._score_text(tokens, " ".join([row["full_name"], row["alias_name"], row["role"], row["status"], row["location"], row["description"], row["notes"], row["known_places"], row["documents_summary"]]), [row["full_name"], row["description"], row["location"]])
                if score:
                    results.append(ArchiveSearchResult(entity_type="participant", entity_id=row["id"], title=row["full_name"], subtitle=f'{row["role"] or "Участник"} · {row["status"] or "Без статуса"}', case_id=row["case_id"], participant_id=row["id"], person_id=row["person_id"], status=row["status"], score=score + (15 if row["pinned"] else 0), pinned=row["pinned"], highlights=highlights))
        results.sort(key=lambda item: (-item.score, not item.pinned, item.title))
        return ArchiveSearchResponse(query=query, total=len(results), results=results[:20])

    def export_case_bundle(self, case_id: str) -> CaseExportBundle:
        case = self.get_case_detail(case_id)
        participants = self.list_case_people(case_id)
        person_ids = [item.person_id for item in participants]
        with self.connect() as conn:
            people_rows = []
            if person_ids:
                placeholders = ",".join("?" for _ in person_ids)
                people_rows = conn.execute(f"SELECT id,full_name,alias_name,birth_date,age,biography,documents_summary,known_places,habits,photo_path,pinned,updated_at FROM people WHERE id IN ({placeholders})", person_ids).fetchall()
            evidence_rows = conn.execute("SELECT id,participant_id,title,category,status,details FROM evidence WHERE participant_id IN (SELECT id FROM case_people WHERE case_id=?) ORDER BY title", (case_id,)).fetchall()
            event_rows = conn.execute("SELECT id,participant_id,event_date,title,details FROM events WHERE participant_id IN (SELECT id FROM case_people WHERE case_id=?) ORDER BY event_date DESC", (case_id,)).fetchall()
            relation_rows = conn.execute("SELECT id,participant_id,target_type,target_label,relation_type,confidence FROM relations WHERE participant_id IN (SELECT id FROM case_people WHERE case_id=?) ORDER BY confidence DESC", (case_id,)).fetchall()
        return CaseExportBundle(case=case, participants=participants, people=[Person(**self._row_bool(dict(row), "pinned")) for row in people_rows], evidence=[Evidence(**dict(row)) for row in evidence_rows], events=[EventItem(**dict(row)) for row in event_rows], relations=[Relation(**dict(row)) for row in relation_rows])

    def import_case_bundle(self, bundle: CaseExportBundle) -> CaseDetail:
        case_id = str(uuid.uuid4())
        now = self._now()
        people_map: dict[str, str] = {}
        participant_map: dict[str, str] = {}
        with self.connect() as conn:
            conn.execute("INSERT INTO cases(id,title,classification,status,summary,pinned,updated_at) VALUES (?,?,?,?,?,?,?)", (case_id, bundle.case.title, bundle.case.classification, bundle.case.status, bundle.case.summary, int(bundle.case.pinned), now))
            for person in bundle.people:
                new_person_id = str(uuid.uuid4())
                people_map[person.id] = new_person_id
                conn.execute("INSERT INTO people(id,full_name,alias_name,birth_date,age,biography,documents_summary,known_places,habits,photo_path,pinned,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (new_person_id, person.full_name, person.alias_name, person.birth_date, compute_age(person.birth_date) if person.birth_date else person.age, person.biography, person.documents_summary, person.known_places, person.habits, person.photo_path, int(person.pinned), now))
            for participant in bundle.participants:
                new_participant_id = str(uuid.uuid4())
                participant_map[participant.id] = new_participant_id
                conn.execute("INSERT INTO case_people(id,case_id,person_id,role,suspicion_level,status,location,description,notes,pinned,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (new_participant_id, case_id, people_map.get(participant.person_id, participant.person_id), participant.role, participant.suspicion_level, participant.status, participant.location, participant.description, participant.notes, int(participant.pinned), now))
            for item in bundle.evidence:
                if item.participant_id in participant_map:
                    conn.execute("INSERT INTO evidence(id,participant_id,title,category,status,details) VALUES (?,?,?,?,?,?)", (str(uuid.uuid4()), participant_map[item.participant_id], item.title, item.category, item.status, item.details))
            for item in bundle.events:
                if item.participant_id in participant_map:
                    conn.execute("INSERT INTO events(id,participant_id,event_date,title,details) VALUES (?,?,?,?,?)", (str(uuid.uuid4()), participant_map[item.participant_id], item.event_date, item.title, item.details))
            for item in bundle.relations:
                if item.participant_id in participant_map:
                    conn.execute("INSERT INTO relations(id,participant_id,target_type,target_label,relation_type,confidence) VALUES (?,?,?,?,?,?)", (str(uuid.uuid4()), participant_map[item.participant_id], item.target_type, item.target_label, item.relation_type, item.confidence))
        return self.get_case_detail(case_id)

    def _score_text(self, tokens: list[str], haystack: str, highlight_sources: list[str]) -> tuple[int, list[str]]:
        score = 0
        for token in tokens:
            if self._matches_token(token, haystack):
                score += 20
        highlights = [source for source in highlight_sources if source and any(self._matches_token(token, source) for token in tokens)]
        return score, highlights[:3]

    def _score_participant(self, tokens: list[str], participant: CaseParticipant, evidence: list[Evidence], events: list[EventItem], relations: list[Relation]) -> tuple[int, list[str], list[str], list[str]]:
        score = 0
        matched_on: list[str] = []
        highlights: list[str] = []
        link_scores: Counter[str] = Counter()
        fields = {"ФИО": participant.full_name, "Псевдоним": participant.alias_name, "Биография": participant.biography, "Документы": participant.documents_summary, "Места": participant.known_places, "Повадки": participant.habits, "Роль": participant.role, "Локация": participant.location, "Описание по делу": participant.description, "Заметки": participant.notes}
        weights = {"ФИО": 40, "Псевдоним": 32, "Биография": 10, "Документы": 18, "Места": 18, "Повадки": 16, "Роль": 14, "Локация": 15, "Описание по делу": 14, "Заметки": 12}
        for token in tokens:
            for label, value in fields.items():
                if self._matches_token(token, value):
                    score += weights[label]
                    matched_on.append(f"{label}: {token}")
                    highlights.append(f"{label}: {value}")
            for item in evidence:
                haystack = f"{item.title} {item.category} {item.status} {item.details}"
                if self._matches_token(token, haystack):
                    score += 20
                    matched_on.append(f"Улика: {token}")
                    highlights.append(f"Улика «{item.title}»: {item.details}")
                    link_scores[f"Улика: {item.title}"] += 20
            for item in events:
                haystack = f"{item.event_date} {item.title} {item.details}"
                if self._matches_token(token, haystack):
                    score += 17
                    matched_on.append(f"Событие: {token}")
                    highlights.append(f"Событие «{item.title}» ({item.event_date})")
                    link_scores[f"Событие: {item.title}"] += 17
            for item in relations:
                haystack = f"{item.target_type} {item.target_label} {item.relation_type}"
                if self._matches_token(token, haystack):
                    boost = 14 + int(item.confidence / 12)
                    score += boost
                    matched_on.append(f"Связь: {token}")
                    highlights.append(f"Связь с «{item.target_label}» ({item.relation_type}, {item.confidence}%)")
                    link_scores[f"{item.target_label} [{item.relation_type}]"] += boost
        unique_tokens = len({item.split(': ', 1)[-1] for item in matched_on})
        if unique_tokens > 1:
            score += unique_tokens * 8
        if evidence and events and relations:
            score += 10
            link_scores["Комплексная связь: есть документы, события и связи"] += 10
        return score, self._dedupe(matched_on), self._dedupe(highlights), [label for label, _ in link_scores.most_common()]

    def _bootstrap_examples(self) -> None:
        with self.connect() as conn:
            existing_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            existing_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
            existing_case_people = conn.execute("SELECT COUNT(*) FROM case_people").fetchone()[0]
            if existing_cases and existing_people and existing_case_people:
                return
        case = self.create_case(CaseCreatePayload(title="Операция «Ночной реестр»", classification="Секретный архив", status="Под наблюдением", summary="Проверка поддельных пропусков, доступа к архиву и передачи документов через терминал 4.", pinned=True))
        broker = self.create_person(PersonCreatePayload(full_name="Марк Вейн", alias_name="Брокер", age=42, biography="Связан с логистическими посредниками и схемами нелегальной передачи документов.", documents_summary="Поддельные пропуска, копии ведомостей на вывоз, схема маршрутов.", known_places="Терминал 4, северный склад, архивный проход.", habits="Не пользуется личным телефоном, приходит заранее, передаёт записки лично.", pinned=True))
        courier = self.create_person(PersonCreatePayload(full_name="Лена Орлова", alias_name="Курьер-9", age=31, biography="Использует арендованные машины и меняет маршруты каждые 48 часов.", documents_summary="Поддельное удостоверение подрядчика, маршрутные листы, квитанции аренды.", known_places="Северная набережная, архивный блок, внешний периметр терминала.", habits="Избегает повторных визитов в одно место, не носит полный пакет документов."))
        broker_participant = self.add_person_to_case(case.id, CaseAssignmentCreatePayload(person_id=broker.id, role="Посредник", suspicion_level=87, status="Активен", location="Складской район, терминал 4", description="Координирует передачу поддельных пропусков и теневые переводы через цепочку посредников.", notes="Предпочитает короткие встречи в порту и бумажные записки.", pinned=True))
        self.add_person_to_case(case.id, CaseAssignmentCreatePayload(person_id=courier.id, role="Курьер", suspicion_level=64, status="Под наблюдением", location="Северная набережная", description="Связана с основным фигурантом через повторяющиеся передачи документов.", notes="Замечена рядом с архивным блоком и периметром терминала."))
        with self.connect() as conn:
            conn.executemany("INSERT INTO evidence(id,participant_id,title,category,status,details) VALUES (?,?,?,?,?,?)", [(str(uuid.uuid4()), broker_participant.id, "Поддельный пропуск", "Документ", "Изъят", "Оформлен на имя сотрудника порта, печати подделаны."), (str(uuid.uuid4()), broker_participant.id, "Флеш-накопитель", "Носитель", "На экспертизе", "Содержит выгрузку журналов и снимки пропускных реестров.")])
            conn.executemany("INSERT INTO events(id,participant_id,event_date,title,details) VALUES (?,?,?,?,?)", [(str(uuid.uuid4()), broker_participant.id, "2026-02-14 21:20", "Передача у терминала", "Зафиксирован обмен конвертом на парковке грузового терминала."), (str(uuid.uuid4()), broker_participant.id, "2026-02-16 08:45", "Доступ в архив", "Прошёл в архивную зону по чужому пропуску.")])
            conn.executemany("INSERT INTO relations(id,participant_id,target_type,target_label,relation_type,confidence) VALUES (?,?,?,?,?,?)", [(str(uuid.uuid4()), broker_participant.id, "человек", "Лена Орлова", "передача документов", 81), (str(uuid.uuid4()), broker_participant.id, "локация", "Терминал 4", "частые встречи", 74), (str(uuid.uuid4()), broker_participant.id, "улика", "Флеш-накопитель", "след владения", 67)])

    def _load_participant_by_case_person(self, case_id: str, person_id: str) -> CaseParticipant:
        with self.connect() as conn:
            row = conn.execute(self._participant_select() + " WHERE cp.case_id=? AND cp.person_id=?", (case_id, person_id)).fetchone()
        if row is None:
            raise ValueError("participant not found")
        return CaseParticipant(**self._row_bool(dict(row), "pinned"))

    @staticmethod
    def _ensure_participant_exists(conn: sqlite3.Connection, participant_id: str) -> None:
        if conn.execute("SELECT case_id FROM case_people WHERE id=?", (participant_id,)).fetchone() is None:
            raise ValueError("participant not found")

    def _touch_participant_case(self, conn: sqlite3.Connection, participant_id: str) -> None:
        row = conn.execute("SELECT case_id FROM case_people WHERE id=?", (participant_id,)).fetchone()
        if row is None:
            raise ValueError("participant not found")
        timestamp = self._now()
        conn.execute("UPDATE case_people SET updated_at=? WHERE id=?", (timestamp, participant_id))
        conn.execute("UPDATE cases SET updated_at=? WHERE id=?", (timestamp, row["case_id"]))

    @staticmethod
    def _participant_select() -> str:
        return "SELECT cp.id,cp.case_id,cp.person_id,p.full_name,p.alias_name,p.birth_date,p.age,p.biography,p.documents_summary,p.known_places,p.habits,p.photo_path,cp.role,cp.suspicion_level,cp.status,cp.location,cp.description,cp.notes,cp.pinned,cp.updated_at FROM case_people cp JOIN people p ON p.id=cp.person_id"

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _normalize(value: str) -> str:
        return (value or "").lower().replace("ё", "е")

    @classmethod
    def _tokenize(cls, query: str) -> list[str]:
        return [token for token in re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", cls._normalize(query)) if len(token) >= 2]

    @classmethod
    def _matches_token(cls, token: str, text: str) -> bool:
        normalized_text = cls._normalize(text)
        if token in normalized_text:
            return True
        if len(token) < 4:
            return False
        for word in re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", normalized_text):
            if abs(len(word) - len(token)) <= 2 and SequenceMatcher(None, token, word).ratio() >= 0.76:
                return True
        return False

    @staticmethod
    def _confidence(score: int) -> str:
        if score >= 95:
            return "высокая"
        if score >= 55:
            return "средняя"
        return "базовая"

    @staticmethod
    def _summary_for_hit(participant: CaseParticipant, matched_on: list[str], top_links: list[str]) -> str:
        reasons = ", ".join(matched_on[:3]).lower() if matched_on else "общий контекст дела"
        anchor = top_links[0] if top_links else "без опорной связи"
        return f"{participant.full_name} попал в выдачу по признакам: {reasons}. Опорная связь: {anchor}."

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    @staticmethod
    def _row_bool(row: dict, *keys: str) -> dict:
        for key in keys:
            if key in row:
                row[key] = bool(row[key])
        return row

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        if any(item["name"] == column for item in conn.execute(f"PRAGMA table_info({table})").fetchall()):
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
        return any(item["name"] == column for item in conn.execute(f"PRAGMA table_info({table})").fetchall())

    def _migrate_legacy_link_table(self, conn: sqlite3.Connection, table: str, create_sql: str, select_sql: str) -> None:
        self._ensure_column(conn, table, "participant_id", "TEXT")
        if not self._table_has_column(conn, table, "suspect_id"):
            return
        temp_table = f"{table}_legacy_backup"
        conn.execute(f"ALTER TABLE {table} RENAME TO {temp_table}")
        conn.execute(create_sql)
        conn.execute(f"INSERT INTO {table} SELECT {select_sql} FROM {temp_table} WHERE COALESCE(participant_id, suspect_id) IS NOT NULL AND COALESCE(participant_id, suspect_id) != ''")
        conn.execute(f"DROP TABLE {temp_table}")
