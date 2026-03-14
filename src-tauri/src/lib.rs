mod application;
mod commands;
mod domain;
mod infrastructure;

use std::sync::Mutex;

use application::dossier_service::DossierService;
use commands::handlers;
use infrastructure::db::Database;

pub struct AppState {
    pub service: Mutex<DossierService>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db = Database::new().expect("db init");
    let service = DossierService::new(db);

    tauri::Builder::default()
        .manage(AppState {
            service: Mutex::new(service),
        })
        .invoke_handler(tauri::generate_handler![
            handlers::list_cases,
            handlers::list_suspects,
            handlers::get_dossier,
            handlers::save_suspect,
            handlers::save_evidence,
            handlers::save_event,
            handlers::save_relation,
            handlers::seed_demo_data,
            handlers::generate_suspect_pdf
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
