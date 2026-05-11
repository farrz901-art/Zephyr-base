use serde_json::Value;

use crate::bridge;
use crate::errors::to_user_safe_string;
use crate::lineage;

#[tauri::command]
pub fn prepare_local_runtime() -> Result<Value, String> {
    bridge::prepare_local_runtime().map_err(to_user_safe_string)
}

#[tauri::command]
pub fn run_local_file(input_path: String, output_dir: String) -> Result<Value, String> {
    bridge::invoke_local_file(&input_path, &output_dir).map_err(to_user_safe_string)
}

#[tauri::command]
pub fn run_local_text(inline_text: String, output_dir: String) -> Result<Value, String> {
    bridge::invoke_local_text(&inline_text, &output_dir).map_err(to_user_safe_string)
}

#[tauri::command]
pub fn read_run_result(output_dir: String) -> Result<Value, String> {
    bridge::read_run_result(&output_dir).map_err(to_user_safe_string)
}

#[tauri::command]
pub fn open_output_folder_plan(output_dir: String) -> Result<Value, String> {
    Ok(bridge::open_output_folder_plan(&output_dir))
}

#[tauri::command]
pub fn read_lineage_snapshot() -> Result<Value, String> {
    lineage::read_lineage_snapshot().map_err(to_user_safe_string)
}

#[tauri::command]
pub fn write_interaction_proof(
    output_dir: String,
    proof: Value,
    run_result: Value,
) -> Result<Value, String> {
    bridge::write_interaction_proof(&output_dir, &proof, &run_result)
        .map_err(to_user_safe_string)
}
