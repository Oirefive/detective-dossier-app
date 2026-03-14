use std::{fs, path::PathBuf};

use anyhow::{anyhow, Result};
use chrono::Utc;
use rusqlite::{params, Connection, OptionalExtension};
use uuid::Uuid;

use crate::domain::models::{CaseDetail, CaseSummary, Dossier, Evidence, EventItem, Relation, Suspect};

#[derive(Clone)]
pub struct Database {
    db_path: PathBuf,
}

impl Database {
    pub fn new() -> Result<Self> {
        let base = std::env::current_dir()?.join("app_data");
        fs::create_dir_all(&base)?;
        let db_path = base.join("detective_dossier.sqlite");
        let db = Self { db_path };
        db.init()?;
        Ok(db)
    }

    fn connect(&self) -> Result<Connection> {
        Ok(Connection::open(&self.db_path)?)
    }

    fn init(&self) -> Result<()> {
        let conn = self.connect()?;
        conn.execute_batch(
            r#"
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS cases (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              classification TEXT NOT NULL,
              status TEXT NOT NULL,
              summary TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suspects (
              id TEXT PRIMARY KEY,
              case_id TEXT NOT NULL,
              full_name TEXT NOT NULL,
              alias_name TEXT NOT NULL DEFAULT '',
              age INTEGER,
              role TEXT NOT NULL DEFAULT '',
              suspicion_level INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT '',
              location TEXT NOT NULL DEFAULT '',
              description TEXT NOT NULL DEFAULT '',
              notes TEXT NOT NULL DEFAULT '',
              photo_path TEXT,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS evidence (
              id TEXT PRIMARY KEY,
              suspect_id TEXT NOT NULL,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              status TEXT NOT NULL,
              details TEXT NOT NULL,
              FOREIGN KEY(suspect_id) REFERENCES suspects(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              suspect_id TEXT NOT NULL,
              event_date TEXT NOT NULL,
              title TEXT NOT NULL,
              details TEXT NOT NULL,
              FOREIGN KEY(suspect_id) REFERENCES suspects(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS relations (
              id TEXT PRIMARY KEY,
              suspect_id TEXT NOT NULL,
              target_type TEXT NOT NULL,
              target_label TEXT NOT NULL,
              relation_type TEXT NOT NULL,
              confidence INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(suspect_id) REFERENCES suspects(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_suspects_case_id ON suspects(case_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_suspect_id ON evidence(suspect_id);
            CREATE INDEX IF NOT EXISTS idx_events_suspect_id ON events(suspect_id);
            CREATE INDEX IF NOT EXISTS idx_relations_suspect_id ON relations(suspect_id);
            "#,
        )?;
        Ok(())
    }

    pub fn list_cases(&self) -> Result<Vec<CaseSummary>> {
        let conn = self.connect()?;
        let mut stmt = conn.prepare(
            r#"
            SELECT c.id, c.title, c.classification, c.status, c.updated_at,
                   COUNT(s.id) AS suspect_count
            FROM cases c
            LEFT JOIN suspects s ON s.case_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            "#,
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(CaseSummary {
                id: row.get(0)?,
                title: row.get(1)?,
                classification: row.get(2)?,
                status: row.get(3)?,
                updated_at: row.get(4)?,
                suspect_count: row.get(5)?,
            })
        })?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }

    pub fn list_suspects(&self, case_id: &str) -> Result<Vec<Suspect>> {
        let conn = self.connect()?;
        let mut stmt = conn.prepare(
            "SELECT id, case_id, full_name, alias_name, age, role, suspicion_level, status, location, description, notes, photo_path, updated_at FROM suspects WHERE case_id = ? ORDER BY suspicion_level DESC, updated_at DESC",
        )?;
        let rows = stmt.query_map([case_id], map_suspect)?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }

    pub fn get_dossier(&self, suspect_id: &str) -> Result<Dossier> {
        let conn = self.connect()?;
        let suspect = conn
            .query_row(
                "SELECT id, case_id, full_name, alias_name, age, role, suspicion_level, status, location, description, notes, photo_path, updated_at FROM suspects WHERE id = ?",
                [suspect_id],
                map_suspect,
            )
            .optional()?
            .ok_or_else(|| anyhow!("suspect not found"))?;

        let case = conn.query_row(
            "SELECT id, title, classification, status, summary, updated_at FROM cases WHERE id = ?",
            [suspect.case_id.clone()],
            |row| {
                Ok(CaseDetail {
                    id: row.get(0)?,
                    title: row.get(1)?,
                    classification: row.get(2)?,
                    status: row.get(3)?,
                    summary: row.get(4)?,
                    updated_at: row.get(5)?,
                })
            },
        )?;

        let evidence = self.load_evidence(&conn, suspect_id)?;
        let events = self.load_events(&conn, suspect_id)?;
        let relations = self.load_relations(&conn, suspect_id)?;

        Ok(Dossier { suspect, case, evidence, events, relations })
    }

    pub fn save_suspect(&self, mut payload: Suspect) -> Result<Suspect> {
        let conn = self.connect()?;
        if payload.id.is_empty() {
            payload.id = Uuid::new_v4().to_string();
        }
        payload.updated_at = now_iso();
        conn.execute(
            r#"
            INSERT INTO suspects(id, case_id, full_name, alias_name, age, role, suspicion_level, status, location, description, notes, photo_path, updated_at)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)
            ON CONFLICT(id) DO UPDATE SET
              case_id=excluded.case_id,
              full_name=excluded.full_name,
              alias_name=excluded.alias_name,
              age=excluded.age,
              role=excluded.role,
              suspicion_level=excluded.suspicion_level,
              status=excluded.status,
              location=excluded.location,
              description=excluded.description,
              notes=excluded.notes,
              photo_path=excluded.photo_path,
              updated_at=excluded.updated_at
            "#,
            params![
                payload.id,
                payload.case_id,
                payload.full_name,
                payload.alias_name,
                payload.age,
                payload.role,
                payload.suspicion_level,
                payload.status,
                payload.location,
                payload.description,
                payload.notes,
                payload.photo_path,
                payload.updated_at,
            ],
        )?;
        conn.execute(
            "UPDATE cases SET updated_at = ?1 WHERE id = ?2",
            params![now_iso(), payload.case_id],
        )?;
        Ok(payload)
    }

    pub fn save_evidence(&self, mut payload: Evidence) -> Result<Evidence> {
        let conn = self.connect()?;
        if payload.id.is_empty() { payload.id = Uuid::new_v4().to_string(); }
        conn.execute(
            "INSERT INTO evidence(id, suspect_id, title, category, status, details) VALUES (?1, ?2, ?3, ?4, ?5, ?6) ON CONFLICT(id) DO UPDATE SET suspect_id=excluded.suspect_id, title=excluded.title, category=excluded.category, status=excluded.status, details=excluded.details",
            params![payload.id, payload.suspect_id, payload.title, payload.category, payload.status, payload.details],
        )?;
        Ok(payload)
    }

    pub fn save_event(&self, mut payload: EventItem) -> Result<EventItem> {
        let conn = self.connect()?;
        if payload.id.is_empty() { payload.id = Uuid::new_v4().to_string(); }
        conn.execute(
            "INSERT INTO events(id, suspect_id, event_date, title, details) VALUES (?1, ?2, ?3, ?4, ?5) ON CONFLICT(id) DO UPDATE SET suspect_id=excluded.suspect_id, event_date=excluded.event_date, title=excluded.title, details=excluded.details",
            params![payload.id, payload.suspect_id, payload.event_date, payload.title, payload.details],
        )?;
        Ok(payload)
    }

    pub fn save_relation(&self, mut payload: Relation) -> Result<Relation> {
        let conn = self.connect()?;
        if payload.id.is_empty() { payload.id = Uuid::new_v4().to_string(); }
        conn.execute(
            "INSERT INTO relations(id, suspect_id, target_type, target_label, relation_type, confidence) VALUES (?1, ?2, ?3, ?4, ?5, ?6) ON CONFLICT(id) DO UPDATE SET suspect_id=excluded.suspect_id, target_type=excluded.target_type, target_label=excluded.target_label, relation_type=excluded.relation_type, confidence=excluded.confidence",
            params![payload.id, payload.suspect_id, payload.target_type, payload.target_label, payload.relation_type, payload.confidence],
        )?;
        Ok(payload)
    }

    pub fn seed_demo_data(&self) -> Result<()> {
        let conn = self.connect()?;
        conn.execute("DELETE FROM relations", [])?;
        conn.execute("DELETE FROM events", [])?;
        conn.execute("DELETE FROM evidence", [])?;
        conn.execute("DELETE FROM suspects", [])?;
        conn.execute("DELETE FROM cases", [])?;

        let case_id = Uuid::new_v4().to_string();
        let suspect_id = Uuid::new_v4().to_string();
        let second_id = Uuid::new_v4().to_string();
        let now = now_iso();

        conn.execute(
            "INSERT INTO cases(id, title, classification, status, summary, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                case_id,
                "Операция Night Ledger",
                "SECURE ARCHIVE",
                "Под наблюдением",
                "Дело о серии финансовых утечек, поддельных пропусков и контактов через портовую логистику.",
                now
            ],
        )?;

        conn.execute(
            "INSERT INTO suspects(id, case_id, full_name, alias_name, age, role, suspicion_level, status, location, description, notes, photo_path, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, NULL, ?12)",
            params![
                suspect_id,
                case_id,
                "Маркус Вейн",
                "The Broker",
                42,
                "Посредник",
                87,
                "Активен",
                "Складской район, терминал 4",
                "Фигурант координирует передачу поддельных пропусков и перевод средств через цепочку посредников.",
                "Избегает цифровых следов, общается через бумажные записки и короткие встречи в порту.",
                now
            ],
        )?;
        conn.execute(
            "INSERT INTO suspects(id, case_id, full_name, alias_name, age, role, suspicion_level, status, location, description, notes, photo_path, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, NULL, ?12)",
            params![
                second_id,
                case_id,
                "Лена Орлова",
                "Courier-9",
                31,
                "Курьер",
                64,
                "Наблюдение",
                "Северная набережная",
                "Использует арендованные машины и меняет маршруты каждые 48 часов.",
                "Связана с подозреваемым через ручную передачу документов.",
                now
            ],
        )?;

        for item in [
            (Uuid::new_v4().to_string(), suspect_id.clone(), "Поддельный пропуск", "Документ", "Изъят", "Выдан на имя сотрудника порта, печати подделаны."),
            (Uuid::new_v4().to_string(), suspect_id.clone(), "Флеш-накопитель", "Носитель", "На экспертизе", "Содержит экспорт ведомостей и снимки пропускных журналов."),
        ] {
            conn.execute("INSERT INTO evidence(id, suspect_id, title, category, status, details) VALUES (?1, ?2, ?3, ?4, ?5, ?6)", params![item.0, item.1, item.2, item.3, item.4, item.5])?;
        }

        for item in [
            (Uuid::new_v4().to_string(), suspect_id.clone(), "2026-02-14 21:20", "Встреча у терминала", "Обменял конверт на парковке грузового терминала."),
            (Uuid::new_v4().to_string(), suspect_id.clone(), "2026-02-16 08:45", "Переход в архив", "Зафиксирован вход в зону доступа архива по чужому пропуску."),
        ] {
            conn.execute("INSERT INTO events(id, suspect_id, event_date, title, details) VALUES (?1, ?2, ?3, ?4, ?5)", params![item.0, item.1, item.2, item.3, item.4])?;
        }

        for item in [
            (Uuid::new_v4().to_string(), suspect_id.clone(), "person", "Лена Орлова", "передача документов", 81),
            (Uuid::new_v4().to_string(), suspect_id.clone(), "location", "Терминал 4", "частые встречи", 74),
            (Uuid::new_v4().to_string(), suspect_id.clone(), "evidence", "Флеш-накопитель", "следы владения", 67),
        ] {
            conn.execute("INSERT INTO relations(id, suspect_id, target_type, target_label, relation_type, confidence) VALUES (?1, ?2, ?3, ?4, ?5, ?6)", params![item.0, item.1, item.2, item.3, item.4, item.5])?;
        }
        Ok(())
    }

    fn load_evidence(&self, conn: &Connection, suspect_id: &str) -> Result<Vec<Evidence>> {
        let mut stmt = conn.prepare("SELECT id, suspect_id, title, category, status, details FROM evidence WHERE suspect_id = ? ORDER BY title")?;
        let rows = stmt.query_map([suspect_id], |row| {
            Ok(Evidence {
                id: row.get(0)?,
                suspect_id: row.get(1)?,
                title: row.get(2)?,
                category: row.get(3)?,
                status: row.get(4)?,
                details: row.get(5)?,
            })
        })?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }

    fn load_events(&self, conn: &Connection, suspect_id: &str) -> Result<Vec<EventItem>> {
        let mut stmt = conn.prepare("SELECT id, suspect_id, event_date, title, details FROM events WHERE suspect_id = ? ORDER BY event_date DESC")?;
        let rows = stmt.query_map([suspect_id], |row| {
            Ok(EventItem {
                id: row.get(0)?,
                suspect_id: row.get(1)?,
                event_date: row.get(2)?,
                title: row.get(3)?,
                details: row.get(4)?,
            })
        })?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }

    fn load_relations(&self, conn: &Connection, suspect_id: &str) -> Result<Vec<Relation>> {
        let mut stmt = conn.prepare("SELECT id, suspect_id, target_type, target_label, relation_type, confidence FROM relations WHERE suspect_id = ? ORDER BY confidence DESC")?;
        let rows = stmt.query_map([suspect_id], |row| {
            Ok(Relation {
                id: row.get(0)?,
                suspect_id: row.get(1)?,
                target_type: row.get(2)?,
                target_label: row.get(3)?,
                relation_type: row.get(4)?,
                confidence: row.get(5)?,
            })
        })?;
        Ok(rows.collect::<rusqlite::Result<Vec<_>>>()?)
    }
}

fn map_suspect(row: &rusqlite::Row<'_>) -> rusqlite::Result<Suspect> {
    Ok(Suspect {
        id: row.get(0)?,
        case_id: row.get(1)?,
        full_name: row.get(2)?,
        alias_name: row.get(3)?,
        age: row.get(4)?,
        role: row.get(5)?,
        suspicion_level: row.get(6)?,
        status: row.get(7)?,
        location: row.get(8)?,
        description: row.get(9)?,
        notes: row.get(10)?,
        photo_path: row.get(11)?,
        updated_at: row.get(12)?,
    })
}

fn now_iso() -> String {
    Utc::now().format("%Y-%m-%d %H:%M:%S").to_string()
}
