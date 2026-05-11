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
pub const INTERACTION_PROOF_NAME: &str = "ui_interaction_proof.json";
const LINEAGE_MANIFEST: &str = "manifests/public_export_lineage.json";
const MANAGED_PYTHON_POINTER: &str = ".tmp/base_runtime_python_path.txt";
const DEFAULT_MANAGED_VENV: &str = ".tmp/base_runtime_venv";
const FALLBACK_MANAGED_VENV: &str = ".tmp/base_runtime_venv_managed";
const PACKAGE_WHEELHOUSE: &str = "runtime/wheelhouse";
const REPO_WHEELHOUSE: &str = ".tmp/base_runtime_wheelhouse";
const REQUIREMENTS_FILE: &str = "runtime/python-runtime/base-runtime-requirements.txt";
const PACKAGE_READY_SIGNAL: &str = "Local runtime is ready.";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdapterInvocation {
    pub program: String,
    pub args: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PythonRuntimeSelection {
    pub program: String,
    pub selected_python_path: String,
    pub managed_runtime_available: bool,
    pub managed_python_runtime_used: bool,
    pub uses_current_python_environment: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct BootstrapPythonCandidate {
    program: String,
    args_prefix: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimePrepareResult {
    pub managed_runtime_created: bool,
    pub managed_runtime_available: bool,
    pub managed_python_runtime_used: bool,
    pub uses_current_python_environment: bool,
    pub selected_python_path: String,
    pub wheelhouse_path: String,
    pub requirements_path: String,
    pub uses_no_index: bool,
    pub uses_find_links: bool,
    pub requires_network_for_dependency_install: bool,
    pub requires_network_at_runtime: bool,
    pub pointer_path: String,
    pub package_ready_signal: String,
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

#[cfg(windows)]
fn normalize_path_buf(path: PathBuf) -> PathBuf {
    let rendered = path.display().to_string();
    if let Some(stripped) = rendered.strip_prefix(r"\\?\") {
        return PathBuf::from(stripped);
    }
    path
}

#[cfg(not(windows))]
fn normalize_path_buf(path: PathBuf) -> PathBuf {
    path
}

fn normalized_path_string(path: &Path) -> String {
    normalize_path_buf(path.to_path_buf()).display().to_string()
}

pub fn resolve_app_root_from(start: Option<&Path>) -> Result<PathBuf, BridgeError> {
    let seed = match start {
        Some(path) => path.to_path_buf(),
        None => env::current_dir().map_err(|error| {
            BridgeError::dependency(format!("Could not read current directory: {error}"))
        })?,
    };
    let search_root = if seed.exists() {
        normalize_path_buf(seed.canonicalize().unwrap_or(seed))
    } else {
        seed
    };
    for candidate in search_root.ancestors() {
        if candidate.join(ADAPTER_SCRIPT).exists()
            && candidate.join(BUNDLE_ROOT).join("run_bundle_public_core.py").exists()
            && candidate.join(LINEAGE_MANIFEST).exists()
        {
            return Ok(normalize_path_buf(candidate.to_path_buf()));
        }
    }
    Err(BridgeError::dependency(
        "Could not locate the Zephyr-base app root for the bundled adapter.",
    ))
}

fn managed_python_path_from_root(venv_root: PathBuf) -> PathBuf {
    if cfg!(windows) {
        venv_root.join("Scripts").join("python.exe")
    } else {
        venv_root.join("bin").join("python")
    }
}

fn pointer_path(app_root: &Path) -> PathBuf {
    app_root.join(MANAGED_PYTHON_POINTER)
}

fn read_managed_python_pointer(app_root: &Path) -> Option<PathBuf> {
    let raw = fs::read_to_string(pointer_path(app_root)).ok()?;
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return None;
    }
    Some(PathBuf::from(trimmed))
}

fn managed_python_candidates(app_root: &Path) -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    let mut push_unique = |candidate: PathBuf| {
        if !candidates.iter().any(|existing| existing == &candidate) {
            candidates.push(candidate);
        }
    };
    if let Some(pointer_python) = read_managed_python_pointer(app_root) {
        push_unique(pointer_python);
    }
    push_unique(managed_python_path_from_root(app_root.join(DEFAULT_MANAGED_VENV)));
    push_unique(managed_python_path_from_root(app_root.join(FALLBACK_MANAGED_VENV)));
    candidates
}

pub fn select_python_runtime(app_root: &Path) -> PythonRuntimeSelection {
    let managed_candidates = managed_python_candidates(app_root);
    let managed_runtime_available =
        managed_candidates.iter().any(|candidate| candidate.exists());
    if let Ok(env_python) = env::var("ZEPHYR_BASE_PYTHON") {
        if !env_python.trim().is_empty() {
            let env_path = PathBuf::from(&env_python);
            let managed_python_runtime_used =
                managed_candidates.iter().any(|candidate| candidate == &env_path);
            return PythonRuntimeSelection {
                program: env_python.clone(),
                selected_python_path: env_python,
                managed_runtime_available,
                managed_python_runtime_used,
                uses_current_python_environment: !managed_python_runtime_used,
            };
        }
    }
    if let Some(managed_python) = managed_candidates
        .into_iter()
        .find(|candidate| candidate.exists())
    {
        let program = managed_python.display().to_string();
        return PythonRuntimeSelection {
            program: program.clone(),
            selected_python_path: program,
            managed_runtime_available,
            managed_python_runtime_used: true,
            uses_current_python_environment: false,
        };
    }
    PythonRuntimeSelection {
        program: "python".to_string(),
        selected_python_path: "python".to_string(),
        managed_runtime_available: false,
        managed_python_runtime_used: false,
        uses_current_python_environment: true,
    }
}

pub fn runtime_wheelhouse_path(app_root: &Path) -> Result<PathBuf, BridgeError> {
    let package_wheelhouse = app_root.join(PACKAGE_WHEELHOUSE);
    if package_wheelhouse.exists() {
        return Ok(package_wheelhouse);
    }
    let repo_wheelhouse = app_root.join(REPO_WHEELHOUSE);
    if repo_wheelhouse.exists() {
        return Ok(repo_wheelhouse);
    }
    Err(BridgeError::dependency(
        "Local runtime could not be prepared. The packaged wheelhouse is missing.",
    ))
}

fn runtime_requirements_path(app_root: &Path) -> Result<PathBuf, BridgeError> {
    let requirements = app_root.join(REQUIREMENTS_FILE);
    if requirements.exists() {
        return Ok(requirements);
    }
    Err(BridgeError::dependency(
        "Local runtime could not be prepared. The runtime requirements file is missing.",
    ))
}

fn bootstrap_python_candidates() -> Vec<BootstrapPythonCandidate> {
    let mut candidates = Vec::new();
    if let Ok(env_python) = env::var("ZEPHYR_BASE_PYTHON") {
        if !env_python.trim().is_empty() && PathBuf::from(&env_python).exists() {
            candidates.push(BootstrapPythonCandidate {
                program: env_python,
                args_prefix: Vec::new(),
            });
        }
    }
    candidates.push(BootstrapPythonCandidate {
        program: "python".to_string(),
        args_prefix: Vec::new(),
    });
    if cfg!(windows) {
        candidates.push(BootstrapPythonCandidate {
            program: "py".to_string(),
            args_prefix: vec!["-3.12".to_string()],
        });
        candidates.push(BootstrapPythonCandidate {
            program: "py".to_string(),
            args_prefix: Vec::new(),
        });
    }
    candidates
}

fn run_command(
    app_root: &Path,
    program: &str,
    args: &[String],
) -> Result<std::process::Output, BridgeError> {
    Command::new(program)
        .args(args)
        .current_dir(app_root)
        .output()
        .map_err(|error| {
            BridgeError::dependency(format!(
                "Local runtime could not be prepared. Could not launch {program}: {error}"
            ))
        })
}

fn python_imports_available(program: &str, app_root: &Path) -> bool {
    let args = vec![
        "-c".to_string(),
        "import pydantic, unstructured".to_string(),
    ];
    match run_command(app_root, program, &args) {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}

fn write_managed_python_pointer(app_root: &Path, managed_python: &Path) -> Result<(), BridgeError> {
    let pointer = pointer_path(app_root);
    if let Some(parent) = pointer.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            BridgeError::dependency(format!(
                "Local runtime could not be prepared. Could not create {}: {error}",
                parent.display()
            ))
        })?;
    }
    fs::write(&pointer, normalized_path_string(managed_python)).map_err(|error| {
        BridgeError::dependency(format!(
            "Local runtime could not be prepared. Could not write {}: {error}",
            pointer.display()
        ))
    })
}

fn bootstrap_managed_runtime(
    app_root: &Path,
    wheelhouse_path: &Path,
    requirements_path: &Path,
) -> Result<PathBuf, BridgeError> {
    let venv_root = app_root.join(DEFAULT_MANAGED_VENV);
    if venv_root.exists() {
        fs::remove_dir_all(&venv_root).map_err(|error| {
            BridgeError::dependency(format!(
                "Local runtime could not be prepared. Could not reset {}: {error}",
                venv_root.display()
            ))
        })?;
    }

    let mut created = false;
    let mut last_failure = String::new();
    for candidate in bootstrap_python_candidates() {
        let mut create_args = candidate.args_prefix.clone();
        create_args.push("-m".to_string());
        create_args.push("venv".to_string());
        create_args.push(normalized_path_string(&venv_root));
        let create = match Command::new(&candidate.program)
            .args(&create_args)
            .current_dir(app_root)
            .output()
        {
            Ok(output) => output,
            Err(error) => {
                last_failure = format!(
                    "Could not launch {}: {}",
                    candidate.program, error
                );
                continue;
            }
        };
        if !create.status.success() {
            last_failure = format!(
                "{} {}",
                String::from_utf8_lossy(&create.stdout).trim(),
                String::from_utf8_lossy(&create.stderr).trim()
            )
            .trim()
            .to_string();
            continue;
        }
        created = true;
        break;
    }
    if !created {
        return Err(BridgeError::dependency(format!(
            "Local runtime could not be prepared. No bootstrap Python could create a managed runtime. {last_failure}"
        )));
    }

    let managed_python = managed_python_path_from_root(venv_root.clone());
    let pip_check_args = vec!["-m".to_string(), "pip".to_string(), "--version".to_string()];
    let pip_check = run_command(app_root, &managed_python.display().to_string(), &pip_check_args)?;
    if !pip_check.status.success() {
        let ensurepip_args = vec![
            "-m".to_string(),
            "ensurepip".to_string(),
            "--upgrade".to_string(),
        ];
        let ensurepip =
            run_command(app_root, &managed_python.display().to_string(), &ensurepip_args)?;
        if !ensurepip.status.success() {
            return Err(BridgeError::dependency(format!(
                "Local runtime could not be prepared. ensurepip failed: {}",
                String::from_utf8_lossy(&ensurepip.stderr).trim()
            )));
        }
    }

    let install_args = vec![
        "-m".to_string(),
        "pip".to_string(),
        "install".to_string(),
        "--no-index".to_string(),
        "--find-links".to_string(),
        wheelhouse_path.display().to_string(),
        "-r".to_string(),
        requirements_path.display().to_string(),
    ];
    let install =
        run_command(app_root, &managed_python.display().to_string(), &install_args)?;
    if !install.status.success() {
        return Err(BridgeError::dependency(format!(
            "Local runtime could not be prepared. Offline dependency install failed: {}",
            String::from_utf8_lossy(&install.stderr).trim()
        )));
    }
    if !python_imports_available(&managed_python.display().to_string(), app_root) {
        return Err(BridgeError::dependency(
            "Local runtime could not be prepared. The managed runtime is missing pydantic or unstructured after bootstrap.",
        ));
    }
    write_managed_python_pointer(app_root, &managed_python)?;
    Ok(managed_python)
}

pub fn ensure_local_runtime(app_root: &Path) -> Result<RuntimePrepareResult, BridgeError> {
    let wheelhouse_path = runtime_wheelhouse_path(app_root)?;
    let requirements_path = runtime_requirements_path(app_root)?;
    let mut selection = select_python_runtime(app_root);
    let mut managed_runtime_created = false;

    if !selection.managed_python_runtime_used
        || !python_imports_available(&selection.program, app_root)
    {
        let managed_python =
            bootstrap_managed_runtime(app_root, &wheelhouse_path, &requirements_path)?;
        selection = select_python_runtime(app_root);
        managed_runtime_created = true;
        if selection.selected_python_path != managed_python.display().to_string()
            || !selection.managed_python_runtime_used
        {
            return Err(BridgeError::dependency(
                "Local runtime could not be prepared. The bridge did not select the managed runtime after bootstrap.",
            ));
        }
    }

    Ok(RuntimePrepareResult {
        managed_runtime_created,
        managed_runtime_available: selection.managed_runtime_available,
        managed_python_runtime_used: selection.managed_python_runtime_used,
        uses_current_python_environment: selection.uses_current_python_environment,
        selected_python_path: selection.selected_python_path,
        wheelhouse_path: wheelhouse_path.display().to_string(),
        requirements_path: requirements_path.display().to_string(),
        uses_no_index: true,
        uses_find_links: true,
        requires_network_for_dependency_install: false,
        requires_network_at_runtime: false,
        pointer_path: pointer_path(app_root).display().to_string(),
        package_ready_signal: PACKAGE_READY_SIGNAL.to_string(),
    })
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
    let selection = select_python_runtime(app_root);
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
    AdapterInvocation {
        program: selection.program,
        args,
    }
}

fn write_request_json(output_dir: &Path, request: &Value) -> Result<PathBuf, BridgeError> {
    fs::create_dir_all(output_dir).map_err(|error| {
        BridgeError::processing(format!(
            "Could not create output directory {}: {error}",
            output_dir.display()
        ))
    })?;
    let request_path = output_dir.join("_tauri_bridge_request.json");
    let rendered = serde_json::to_string_pretty(request).map_err(|error| {
        BridgeError::processing(format!("Could not render request JSON: {error}"))
    })?;
    fs::write(&request_path, rendered).map_err(|error| {
        BridgeError::processing(format!(
            "Could not write request payload {}: {error}",
            request_path.display()
        ))
    })?;
    Ok(request_path)
}

fn write_json_file(path: &Path, value: &Value) -> Result<(), BridgeError> {
    let rendered = serde_json::to_string_pretty(value).map_err(|error| {
        BridgeError::processing(format!(
            "Could not render JSON file {}: {error}",
            path.display()
        ))
    })?;
    fs::write(path, rendered).map_err(|error| {
        BridgeError::processing(format!(
            "Could not write JSON file {}: {error}",
            path.display()
        ))
    })
}

fn read_json_file(path: &Path) -> Result<Value, BridgeError> {
    let rendered = fs::read_to_string(path).map_err(|error| {
        BridgeError::processing(format!(
            "Could not read JSON file {}: {error}",
            path.display()
        ))
    })?;
    serde_json::from_str(&rendered).map_err(|error| {
        BridgeError::processing(format!(
            "Could not parse JSON file {}: {error}",
            path.display()
        ))
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
    let runtime = ensure_local_runtime(app_root)?;
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
    let mut run_result = read_run_result_from_path(output_dir)?;
    if let Some(map) = run_result.as_object_mut() {
        map.insert(
            "managed_runtime_available".to_string(),
            json!(runtime.managed_runtime_available),
        );
        map.insert(
            "managed_python_runtime_used".to_string(),
            json!(runtime.managed_python_runtime_used),
        );
        map.insert(
            "uses_current_python_environment".to_string(),
            json!(runtime.uses_current_python_environment),
        );
        map.insert(
            "selected_python_path".to_string(),
            json!(runtime.selected_python_path),
        );
    }
    Ok(run_result)
}

pub fn prepare_local_runtime() -> Result<Value, BridgeError> {
    let app_root = resolve_app_root_from(None)?;
    let runtime = ensure_local_runtime(&app_root)?;
    Ok(json!({
        "managed_runtime_created": runtime.managed_runtime_created,
        "managed_runtime_available": runtime.managed_runtime_available,
        "managed_python_runtime_used": runtime.managed_python_runtime_used,
        "uses_current_python_environment": runtime.uses_current_python_environment,
        "selected_python_path": runtime.selected_python_path,
        "wheelhouse_path": runtime.wheelhouse_path,
        "requirements_path": runtime.requirements_path,
        "uses_no_index": runtime.uses_no_index,
        "uses_find_links": runtime.uses_find_links,
        "requires_network_for_dependency_install": runtime.requires_network_for_dependency_install,
        "requires_network_at_runtime": runtime.requires_network_at_runtime,
        "pointer_path": runtime.pointer_path,
        "package_ready_signal": runtime.package_ready_signal
    }))
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

pub fn write_interaction_proof(
    output_dir: &str,
    proof: &Value,
    run_result: &Value,
) -> Result<Value, BridgeError> {
    if !proof.is_object() {
        return Err(BridgeError::input(
            "Interaction proof payload must be a JSON object.",
        ));
    }
    if !run_result.is_object() {
        return Err(BridgeError::input("Run result payload must be a JSON object."));
    }
    let marker = proof
        .get("marker")
        .and_then(Value::as_str)
        .unwrap_or("")
        .trim()
        .to_string();
    if marker.is_empty() {
        return Err(BridgeError::input("Interaction proof marker must not be empty."));
    }

    let app_root = resolve_app_root_from(None)?;
    let output_root = resolve_relative(&app_root, output_dir);
    fs::create_dir_all(&output_root).map_err(|error| {
        BridgeError::processing(format!(
            "Could not create interaction proof directory {}: {error}",
            output_root.display()
        ))
    })?;

    let run_result_path = output_root.join(RUN_RESULT_NAME);
    let proof_path = output_root.join(INTERACTION_PROOF_NAME);

    write_json_file(&run_result_path, run_result)?;
    write_json_file(&proof_path, proof)?;

    Ok(json!({
        "output_dir": output_root.display().to_string(),
        "proof_path": proof_path.display().to_string(),
        "run_result_path": run_result_path.display().to_string(),
        "tauri_invoke_used": true
    }))
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

    #[test]
    fn write_interaction_proof_requires_marker() {
        let root = unique_temp_dir("proof_root");
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

        env::set_current_dir(&root).expect("set cwd");
        let error = write_interaction_proof(
            ".tmp/proof",
            &json!({"marker": ""}),
            &json!({"request_id": "x"}),
        )
        .expect_err("marker validation");
        assert!(error.to_string().contains("rejected the input"));
    }
}
