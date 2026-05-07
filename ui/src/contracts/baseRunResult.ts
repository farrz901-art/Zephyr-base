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
}

export interface RunLocalFilePayload {
  input_path: string;
  output_dir: string;
}

export interface RunLocalTextPayload {
  inline_text: string;
  output_dir: string;
}

export interface ReadRunResultPayload {
  output_dir: string;
}

export interface OutputFolderPlanPayload {
  output_dir: string;
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
