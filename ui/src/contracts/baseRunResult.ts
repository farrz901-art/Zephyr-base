export interface BaseErrorV1 {
  schema_version: number;
  error_code: string;
  category: "input" | "processing" | "dependency" | "filesystem" | "unknown";
  user_message: string;
  technical_detail_safe: string;
  secret_safe: boolean;
}

export interface BaseUsageFactV1 {
  schema_version: number;
  fact_kind: string;
  billing_semantics: boolean;
  input_bytes?: number;
  output_files_count: number;
  bundled_runtime_used?: boolean;
  zephyr_dev_working_tree_required?: boolean;
  installer_runtime_complete?: boolean;
  requires_network?: boolean;
  requires_p45_substrate?: boolean;
}

export interface BaseReceiptViewV1 {
  schema_version: number;
  run_id: string;
  request_id: string;
  status: string;
  delivery_outcome: string;
  output_root: string;
  artifacts: string[];
  created_by: string;
  production_runtime: boolean;
  adapter_runtime: string;
  bundled_runtime_used?: boolean;
  zephyr_dev_working_tree_required?: boolean;
  installer_runtime_complete?: boolean;
  requires_network?: boolean;
  requires_p45_substrate?: boolean;
}

export interface BaseContentEvidenceV1 {
  schema_version?: number;
  evidence_kind: string;
  normalized_text_preview?: string;
  source_kind?: string;
  input_bytes?: number;
  elements_count?: number;
  token_marker_found?: boolean;
  bundled_runtime_used?: boolean;
  zephyr_dev_working_tree_required?: boolean;
  installer_runtime_complete?: boolean;
  requires_network?: boolean;
  requires_p45_substrate?: boolean;
}

export interface BaseRunResultV1 {
  schema_version: number;
  request_id: string;
  status: "success" | "failed";
  normalized_text_preview: string;
  content_evidence_summary: {
    elements_count: number;
    has_normalized_text: boolean;
    evidence_kind: string;
  };
  receipt: BaseReceiptViewV1;
  usage_fact: BaseUsageFactV1;
  output_files: string[];
  error: BaseErrorV1 | null;
  adapter_runtime: string;
  bundled_runtime_used?: boolean;
  zephyr_dev_working_tree_required?: boolean;
  installer_runtime_complete?: boolean;
  requires_network?: boolean;
  requires_p45_substrate?: boolean;
  content_evidence_kind?: string;
  fixture_runner_used?: boolean;
}

export interface RunLocalFilePayload {
  inputPath: string;
  outputDir: string;
}

export interface RunLocalTextPayload {
  inlineText: string;
  outputDir: string;
}

export interface ReadRunResultPayload {
  outputDir: string;
}

export interface OutputFolderPlanPayload {
  outputDir: string;
}

export interface InteractionProofWritePayload {
  outputDir: string;
  proof: InteractionProofV1;
  runResult: BaseRunResultV1;
}

export interface InteractionProofWriteResult {
  output_dir: string;
  proof_path: string;
  run_result_path: string;
  tauri_invoke_used: boolean;
}

export interface LineageSnapshotV1 {
  public_export_lineage: Record<string, unknown>;
  bundle_manifest: Record<string, unknown>;
  uses_current_python_environment: boolean;
  embedded_python_runtime: boolean;
  wheelhouse_bundled: boolean;
  installer_runtime_complete: boolean;
}

export interface RuntimeModeSummary {
  mode: "mock_artifact_mode" | "invoke_ready_not_window_e2e";
  tauri_invoke_ready: boolean;
  tauri_invoke_e2e_verified: boolean;
  uses_bundled_adapter: boolean;
  uses_current_python_environment: boolean;
  embedded_python_runtime: boolean;
  wheelhouse_bundled: boolean;
  installer_runtime_complete: boolean;
}

export interface ResultDisplayModel {
  request_id: string;
  status: "success" | "failed";
  normalized_text_preview: string;
  evidence_kind: string;
  output_root: string;
  billing_semantics: boolean;
  has_error: boolean;
  error_message: string | null;
}

export type RunLifecycleState =
  | "idle"
  | "preparing_request"
  | "invoking_tauri_command"
  | "processing_local_runtime"
  | "reading_result"
  | "success"
  | "failed";

export interface InteractionProofV1 {
  schema_version: number;
  report_id: string;
  proof_kind: "manual_window_click" | "automated_window_click";
  marker: string;
  window_launched: boolean;
  user_clicked_run: boolean;
  ui_mode: "real_tauri_local_text" | "real_tauri_local_file";
  tauri_invoke_used: boolean;
  direct_python_call: boolean;
  network_call: boolean;
  run_result_path: string;
  normalized_preview_visible: boolean;
  evidence_visible: boolean;
  receipt_visible: boolean;
  usage_fact_visible: boolean;
  billing_semantics_displayed_false: boolean;
  output_folder_plan_visible: boolean;
  error_panel_available: boolean;
  screenshot_path: string | null;
  notes: string[];
}
