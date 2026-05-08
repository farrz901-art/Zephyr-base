#![cfg_attr(all(not(debug_assertions), target_os = "windows"), windows_subsystem = "windows")]

mod bridge;
mod commands;
mod errors;
mod lineage;

use std::process;

use serde_json::Value;

fn print_result(result: Result<Value, String>) -> i32 {
    match result {
        Ok(value) => match serde_json::to_string_pretty(&value) {
            Ok(rendered) => {
                println!("{rendered}");
                0
            }
            Err(error) => {
                eprintln!("Failed to render JSON result: {error}");
                1
            }
        },
        Err(error) => {
            eprintln!("{error}");
            1
        }
    }
}

fn usage() {
    eprintln!(
        "Zephyr Base Tauri app path. Commands: run-local-file <input_path> <output_dir>, run-local-text <inline_text> <output_dir>, read-run-result <output_dir>, open-output-folder-plan <output_dir>, read-lineage-snapshot"
    );
}

fn maybe_run_cli() -> Option<i32> {
    let mut args = std::env::args().skip(1);
    let Some(command) = args.next() else {
        return None;
    };

    let exit_code = match command.as_str() {
        "run-local-file" => {
            let Some(input_path) = args.next() else {
                usage();
                return Some(1);
            };
            let Some(output_dir) = args.next() else {
                usage();
                return Some(1);
            };
            print_result(commands::run_local_file(input_path, output_dir))
        }
        "run-local-text" => {
            let Some(inline_text) = args.next() else {
                usage();
                return Some(1);
            };
            let Some(output_dir) = args.next() else {
                usage();
                return Some(1);
            };
            print_result(commands::run_local_text(inline_text, output_dir))
        }
        "read-run-result" => {
            let Some(output_dir) = args.next() else {
                usage();
                return Some(1);
            };
            print_result(commands::read_run_result(output_dir))
        }
        "open-output-folder-plan" => {
            let Some(output_dir) = args.next() else {
                usage();
                return Some(1);
            };
            print_result(commands::open_output_folder_plan(output_dir))
        }
        "read-lineage-snapshot" => print_result(commands::read_lineage_snapshot()),
        _ => {
            usage();
            1
        }
    };
    Some(exit_code)
}

fn main() {
    if let Some(exit_code) = maybe_run_cli() {
        process::exit(exit_code);
    }

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::run_local_file,
            commands::run_local_text,
            commands::read_run_result,
            commands::open_output_folder_plan,
            commands::read_lineage_snapshot,
            commands::write_interaction_proof,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Zephyr Base Tauri app path");
}
