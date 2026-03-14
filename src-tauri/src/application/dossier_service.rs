use anyhow::Result;

use crate::domain::models::{CaseSummary, Dossier, Evidence, EventItem, Relation, Suspect};
use crate::infrastructure::{db::Database, pdf::PdfService};

pub struct DossierService {
    db: Database,
    pdf: PdfService,
}

impl DossierService {
    pub fn new(db: Database) -> Self {
        Self { db, pdf: PdfService::new() }
    }

    pub fn list_cases(&self) -> Result<Vec<CaseSummary>> {
        self.db.list_cases()
    }

    pub fn list_suspects(&self, case_id: &str) -> Result<Vec<Suspect>> {
        self.db.list_suspects(case_id)
    }

    pub fn get_dossier(&self, suspect_id: &str) -> Result<Dossier> {
        self.db.get_dossier(suspect_id)
    }

    pub fn save_suspect(&self, payload: Suspect) -> Result<Suspect> {
        self.db.save_suspect(payload)
    }

    pub fn save_evidence(&self, payload: Evidence) -> Result<Evidence> {
        self.db.save_evidence(payload)
    }

    pub fn save_event(&self, payload: EventItem) -> Result<EventItem> {
        self.db.save_event(payload)
    }

    pub fn save_relation(&self, payload: Relation) -> Result<Relation> {
        self.db.save_relation(payload)
    }

    pub fn seed_demo_data(&self) -> Result<()> {
        self.db.seed_demo_data()
    }

    pub fn generate_suspect_pdf(&self, suspect_id: &str) -> Result<String> {
        let dossier = self.db.get_dossier(suspect_id)?;
        self.pdf.generate(&dossier)
    }
}
