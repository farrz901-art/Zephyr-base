use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use serde_json::{json, Value};

use crate::errors::BridgeError;

pub const ADAPTER_SCRIPT: &str = "public-core-bridge/run_public_core_adapter.py";
pub const BUNDLE_ROOT: &str = "runtime/public-core-bundle";
pub const RUN_RESULT_NAME: &str = "run_result.json";
const LINEAGE_MANIFEST: &str = "manifests/public_export_lineage.json";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdapterInvocation {
    pub program: String,
    pub args: Vec<String>,
}

fn request_id(prefix: &str) -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or(0);
    format!("{prefix}-{nanos}")
}

fn resolve_relative(root: &Path, raw: &str) -> PathBuf {
    let path = PathBuf::from(raw);
    if path.is_absolute() {
        path
    } else {
        root.join(path)
    }
}

pub fn resolve_app_root_from(start: Option<&Path>) -> Result<PathBuf, BridgeError> {
    let seed = match start {
        Some(path) => path.to_path_buf(),
        None => env::current_dir().map_err(|error| {
            BridgeError::dependency(format!("Could not read current directory: {error}"))
        })?,
    };
    let search_root = if seed.exists() {
        seed.canonicalize().unwrap_or(seed)
    } else {
        seed
    };
    for candidate in search_root.ancestors() {
        if candidate.join(ADAPTER_SCRIPT).exists()
            && candidate.join(BUNDLE_ROOT).join("run_bundle_public_core.py").exists()
            && candidate.join(LINEAGE_MANIFEST).exists()
        {
            return Ok(candidate.to_path_buf());
        }
    }
    Err(BridgeError::dependency(
        "Could not locate the Zephyr-base app root for the bundled adapter.",
    ))
}

pub fn build_local_file_request(input_path: &Path, output_dir: &Path) -> Value {
    json!({
        "schema_version": 1,
        "request_id": request_id("tauri-local-file"),
        "input_kind": "local_file",
        "input_path": input_path.display().to_string(),
        "output_dir": output_dir.display().to_string(),
        "requested_outputs": [
            "normalized_text",
            "content_evidence",
            "receipt",
            "filesystem_output"
        ]
    })
}

pub fn build_local_text_request(inline_text: &str, output_dir: &Path) -> Value {
    json!({
        "schema_version": 1,
        "request_id": request_id("tauri-local-text"),
        "input_kind": "local_text",
        "inline_text": inline_text,
        "output_dir": output_dir.display().to_string(),
        "requested_outputs": [
            "normalized_text",
            "content_evidence",
            "receipt",
            "filesystem_output"
        ]
    })
}

pub fn bundled_adapter_invocation(
    app_root: &Path,
    request_path: &Path,
    output_dir: &Path,
) -> AdapterInvocation {
    let program = env::var("ZEPHYR_BASE_PYTHON").unwrap_or_else(|_| "python".to_string());
    let args = vec![
        app_root.join(ADAPTER_SCRIPT).display().to_string(),
        "--request".to_string(),
        request_path.display().to_string(),
        "--out-dir".to_string(),
        output_dir.display().to_string(),
        "--bundle-root".to_string(),
        app_root.join(BUNDLE_ROOT).display().to_string(),
        "--json".to_string(),
    ];
    AdapterInvocation { program, args }
}

fn write_request_json(output_dir: &Path, request: &Value) -> Result<PathBuf, BridgeError> {
    fs::create_dir_all(output_dir).map_err(|error| {
        BridgeError::processing(format!(
            "Could not create output directory {}: {error}",
            output_dir.display()
        ))
    })?;
    let request_path = output_dir.join("_tauri_bridge_request.json");
    let rendered = serde_json::to_string_pretty(request)
        .map_err(|error| BridgeError::processing(format!("Could not render request JSON: {error}")))?;
    fs::write(&request_path, rendered).map_err(|error| {
        BridgeError::processing(format!(
            "Could not write request payload {}: {error}",
            request_path.display()
        ))
    })?;
    Ok(request_path)
}

fn read_json_file(path: &Path) -> Result<Value, BridgeError> {
    let rendered = fs::read_to_string(path).map_err(|error| {
        BridgeError::processing(format!("Could not read JSON file {}: {error}", path.display()))
    })?;
    serde_json::from_str(&rendered).map_err(|error| {
        BridgeError::processing(format!("Could not parse JSON file {}: {error}", path.display()))
    })
}

pub fn read_run_result_from_path(output_dir: &Path) -> Result<Value, BridgeError> {
    let run_result_path = output_dir.join(RUN_RESULT_NAME);
    if !run_result_path.exists() {
        return Err(BridgeError::processing(format!(
            "Bundled adapter did not produce {}.",
            run_result_path.display()
        )));
    }
    read_json_file(&run_result_path)
}

fn invoke_request(app_root: &Path, request: &Value, output_dir: &Path) -> Result<Value, BridgeError> {
    let request_path = write_request_json(output_dir, request)?;
    let invocation = bundled_adapter_invocation(app_root, &request_path, output_dir);
    let output = Command::new(&invocation.program)
        .args(&invocation.args)
        .current_dir(app_root)
        .output()
        .map_err(|error| {
            BridgeError::dependency(format!(
                "Could not launch bundled adapter subprocess: {error}"
            ))
        })?;
    let run_result_path = output_dir.join(RUN_RESULT_NAME);
    if !run_result_path.exists() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(BridgeError::processing(format!(
            "Bundled adapter returned {} without run_result.json; stdout={}; stderr={}",
            output.status.code().unwrap_or(-1),
            stdout.trim(),
            stderr.trim()
        )));
    }
    read_run_result_from_path(output_dir)
}

pub fn invoke_local_file(input_path: &str, output_dir: &str) -> Result<Value, BridgeError> {
    let app_root = resolve_app_root_from(None)?;
    let output_root = resolve_relative(&app_root, output_dir);
    let input_root = resolve_relative(&app_root, input_path);
    let request = build_local_file_request(&input_root, &output_root);
    invoke_request(&app_root, &request, &output_root)
}

pub fn invoke_local_text(inline_text: &str, output_dir: &str) -> Result<Value, BridgeError> {
    let app_root = resolve_app_root_from(None)?;
    let output_root = resolve_relative(&app_root, output_dir);
    let request = build_local_text_request(inline_text, &output_root);
    invoke_request(&app_root, &request, &output_root)
}

pub fn read_run_result(output_dir: &str) -> Result<Value, BridgeError> {
    let app_root = resolve_app_root_from(None)?;
    let output_root = resolve_relative(&app_root, output_dir);
    read_run_result_from_path(&output_root)
}

pub fn open_output_folder_plan(output_dir: &str) -> Value {
    json!({
        "action": "open_output_folder_plan",
        "output_dir": output_dir,
        "implemented": false,
        "reason": "S6 returns a safe shell-plan placeholder. Native shell integration lands later.",
        "requires_network": false,
        "requires_p45_substrate": false,
        "commercial_logic_allowed": false
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn unique_temp_dir(label: &str) -> PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_nanos())
            .unwrap_or(0);
        let path = env::temp_dir().join(format!("zephyr_base_{label}_{unique}"));
        fs::create_dir_all(&path).expect("temp dir");
        path
    }

    #[test]
    fn build_local_file_request_has_expected_shape() {
        let request = build_local_file_request(Path::new("C:/input.txt"), Path::new("C:/out"));
        assert_eq!(request["input_kind"], "local_file");
        assert_eq!(request["input_path"], "C:/input.txt");
        assert_eq!(request["output_dir"], "C:/out");
    }

    #[test]
    fn build_local_text_request_has_expected_shape() {
        let request = build_local_text_request("hello", Path::new("C:/out"));
        assert_eq!(request["input_kind"], "local_text");
        assert_eq!(request["inline_text"], "hello");
    }

    #[test]
    fn bundled_adapter_invocation_never_uses_fixture_fallback() {
        let root = Path::new("C:/Zephyr-base");
        let request_path = root.join(".tmp/request.json");
        let output_dir = root.join(".tmp/out");
        let invocation = bundled_adapter_invocation(root, &request_path, &output_dir);
        assert_eq!(invocation.program, "python");
        assert!(invocation
            .args
            .iter()
            .any(|item| item.contains("run_public_core_adapter.py")));
        assert!(invocation
            .args
            .iter()
            .any(|item| item.contains("public-core-bundle")));
        assert!(!invocation
            .args
            .iter()
            .any(|item| item.contains("allow-fixture-fallback")));
    }

    #[test]
    fn resolve_app_root_from_discovers_expected_layout() {
        let root = unique_temp_dir("app_root");
        let nested = root.join("src-tauri/src");
        fs::create_dir_all(&nested).expect("nested dir");
        fs::create_dir_all(root.join("public-core-bridge")).expect("adapter dir");
        fs::create_dir_all(root.join("runtime/public-core-bundle")).expect("bundle dir");
        fs::create_dir_all(root.join("manifests")).expect("manifest dir");
        fs::write(root.join(ADAPTER_SCRIPT), "# adapter").expect("adapter file");
        fs::write(
            root.join(BUNDLE_ROOT).join("run_bundle_public_core.py"),
            "# runner",
        )
        .expect("bundle runner");
        fs::write(root.join(LINEAGE_MANIFEST), "{}").expect("lineage file");

        let resolved = resolve_app_root_from(Some(&nested)).expect("resolve root");
        assert_eq!(resolved, root);
    }
}
