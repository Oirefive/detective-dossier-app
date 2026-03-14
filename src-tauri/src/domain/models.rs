use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CaseSummary {
    pub id: String,
    pub title: String,
    pub classification: String,
    pub status: String,
    pub updated_at: String,
    pub suspect_count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CaseDetail {
    pub id: String,
    pub title: String,
    pub classification: String,
    pub status: String,
    pub summary: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Suspect {
    pub id: String,
    pub case_id: String,
    pub full_name: String,
    pub alias_name: String,
    pub age: Option<i64>,
    pub role: String,
    pub suspicion_level: i64,
    pub status: String,
    pub location: String,
    pub description: String,
    pub notes: String,
    pub photo_path: Option<String>,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Evidence {
    pub id: String,
    pub suspect_id: String,
    pub title: String,
    pub category: String,
    pub status: String,
    pub details: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EventItem {
    pub id: String,
    pub suspect_id: String,
    pub event_date: String,
    pub title: String,
    pub details: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Relation {
    pub id: String,
    pub suspect_id: String,
    pub target_type: String,
    pub target_label: String,
    pub relation_type: String,
    pub confidence: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Dossier {
    pub suspect: Suspect,
    pub case: CaseDetail,
    pub evidence: Vec<Evidence>,
    pub events: Vec<EventItem>,
    pub relations: Vec<Relation>,
}
