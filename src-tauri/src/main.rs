mod bridge;
mod commands;
mod errors;
mod lineage;

use std::process::ExitCode;

use serde_json::Value;

fn print_result(result: Result<Value, String>) -> ExitCode {
    match result {
        Ok(value) => match serde_json::to_string_pretty(&value) {
            Ok(rendered) => {
                println!("{rendered}");
                ExitCode::SUCCESS
            }
            Err(error) => {
                eprintln!("Failed to render JSON result: {error}");
                ExitCode::from(1)
            }
        },
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(1)
        }
    }
}

fn usage() {
    eprintln!(
        "Zephyr Base Tauri command bridge first slice. Commands: run-local-file <input_path> <output_dir>, run-local-text <inline_text> <output_dir>, read-run-result <output_dir>, open-output-folder-plan <output_dir>, read-lineage-snapshot"
    );
}

fn main() -> ExitCode {
    let mut args = std::env::args().skip(1);
    let Some(command) = args.next() else {
        usage();
        return ExitCode::SUCCESS;
    };

    match command.as_str() {
        "run-local-file" => {
            let Some(input_path) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            let Some(output_dir) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            print_result(commands::run_local_file(input_path, output_dir))
        }
        "run-local-text" => {
            let Some(inline_text) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            let Some(output_dir) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            print_result(commands::run_local_text(inline_text, output_dir))
        }
        "read-run-result" => {
            let Some(output_dir) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            print_result(commands::read_run_result(output_dir))
        }
        "open-output-folder-plan" => {
            let Some(output_dir) = args.next() else {
                usage();
                return ExitCode::from(1);
            };
            print_result(commands::open_output_folder_plan(output_dir))
        }
        "read-lineage-snapshot" => print_result(commands::read_lineage_snapshot()),
        _ => {
            usage();
            ExitCode::from(1)
        }
    }
}
