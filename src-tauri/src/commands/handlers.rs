use tauri::State;

use crate::{domain::models::{Dossier, Evidence, EventItem, Relation, Suspect, CaseSummary}, AppState};

#[tauri::command]
pub fn list_cases(state: State<'_, AppState>) -> Result<Vec<CaseSummary>, String> {
    state.service.lock().map_err(|e| e.to_string())?.list_cases().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_suspects(case_id: String, state: State<'_, AppState>) -> Result<Vec<Suspect>, String> {
    state.service.lock().map_err(|e| e.to_string())?.list_suspects(&case_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_dossier(suspect_id: String, state: State<'_, AppState>) -> Result<Dossier, String> {
    state.service.lock().map_err(|e| e.to_string())?.get_dossier(&suspect_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_suspect(payload: Suspect, state: State<'_, AppState>) -> Result<Suspect, String> {
    state.service.lock().map_err(|e| e.to_string())?.save_suspect(payload).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_evidence(payload: Evidence, state: State<'_, AppState>) -> Result<Evidence, String> {
    state.service.lock().map_err(|e| e.to_string())?.save_evidence(payload).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_event(payload: EventItem, state: State<'_, AppState>) -> Result<EventItem, String> {
    state.service.lock().map_err(|e| e.to_string())?.save_event(payload).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_relation(payload: Relation, state: State<'_, AppState>) -> Result<Relation, String> {
    state.service.lock().map_err(|e| e.to_string())?.save_relation(payload).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn seed_demo_data(state: State<'_, AppState>) -> Result<(), String> {
    state.service.lock().map_err(|e| e.to_string())?.seed_demo_data().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn generate_suspect_pdf(suspect_id: String, state: State<'_, AppState>) -> Result<String, String> {
    state.service.lock().map_err(|e| e.to_string())?.generate_suspect_pdf(&suspect_id).map_err(|e| e.to_string())
}
