use std::fs;
use std::path::Path;

use serde_json::{json, Value};

use crate::bridge::resolve_app_root_from;
use crate::errors::BridgeError;

fn read_json_file(path: &Path) -> Result<Value, BridgeError> {
    let rendered = fs::read_to_string(path).map_err(|error| {
        BridgeError::lineage(format!("Could not read lineage file {}: {error}", path.display()))
    })?;
    serde_json::from_str(&rendered).map_err(|error| {
        BridgeError::lineage(format!("Could not parse lineage file {}: {error}", path.display()))
    })
}

pub fn read_lineage_snapshot() -> Result<Value, BridgeError> {
    let root = resolve_app_root_from(None)?;
    let public_export_lineage = read_json_file(&root.join("manifests/public_export_lineage.json"))?;
    let bundle_manifest = read_json_file(
        &root.join("runtime/public-core-bundle/manifest/public_core_bundle_manifest.json"),
    )?;
    Ok(json!({
        "public_export_lineage": public_export_lineage,
        "bundle_manifest": bundle_manifest,
        "uses_current_python_environment": true,
        "embedded_python_runtime": false,
        "wheelhouse_bundled": false,
        "installer_runtime_complete": false
    }))
}
