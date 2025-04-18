use tauri::{TitleBarStyle, WebviewUrl, WebviewWindowBuilder, Manager, AppHandle, Emitter};
use tauri_plugin_shell::{ShellExt, process::CommandEvent};
use tauri::async_runtime::JoinHandle;
use std::sync::{Mutex, Arc};

struct BackendState {
    process: Option<JoinHandle<()>>,
}

#[tauri::command]
async fn start_backend(app: AppHandle) -> Result<String, String> {
    let app_clone = app.clone();
    let backend_state = app.state::<Arc<Mutex<BackendState>>>();
    
    let mut state = backend_state.lock().map_err(|e| e.to_string())?;
    if state.process.is_some() {
        return Ok("Backend already running".to_string());
    }

    match app.shell().sidecar("notelens-backend") {
        Ok(command) => {
            let (mut rx, child) = command
                .spawn()
                .map_err(|e| format!("Failed to spawn backend process: {}", e))?;
            
            let handle = tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line = String::from_utf8_lossy(&line);
                            println!("Backend stdout: {}", line);
                        }
                        CommandEvent::Stderr(line) => {
                            let line = String::from_utf8_lossy(&line);
                            println!("Backend stderr: {}", line);
                        }
                        CommandEvent::Error(err) => {
                            println!("Backend error: {}", err);
                            app_clone.emit("backend-error", err).ok();
                        }
                        CommandEvent::Terminated(status) => {
                            println!("Backend terminated with status: {:?}", status);
                            app_clone.emit("backend-terminated", status).ok();
                            break;
                        }
                        _ => {}
                    }
                }
            });
            
            state.process = Some(handle);
            Ok("Backend started successfully".to_string())
        }
        Err(e) => Err(format!("Failed to create backend command: {}", e)),
    }
}

#[tauri::command]
async fn stop_backend(app: AppHandle) -> Result<String, String> {
    let backend_state = app.state::<Arc<Mutex<BackendState>>>();
    
    let mut state = backend_state.lock().map_err(|e| e.to_string())?;
    if let Some(handle) = state.process.take() {
        handle.abort();
        Ok("Backend stopped".to_string())
    } else {
        Ok("Backend not running".to_string())
    }
}

pub fn run() {
    let backend_state = Arc::new(Mutex::new(BackendState {
        process: None,
    }));

    tauri::Builder::default()
        .plugin(tauri_plugin_websocket::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .manage(backend_state)
        .invoke_handler(tauri::generate_handler![start_backend, stop_backend])
        .setup(|app| {
            let win_builder = WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title("Transparent Titlebar Window")
                .inner_size(800.0, 600.0);

            // set transparent title bar only when building for macOS
            #[cfg(target_os = "macos")]
            let win_builder = win_builder.title_bar_style(TitleBarStyle::Transparent);

            let window = win_builder.build().unwrap();

            // set background color only when building for macOS
            #[cfg(target_os = "macos")]
            {
                use cocoa::appkit::{NSColor, NSWindow};
                use cocoa::base::{id, nil};

                let ns_window = window.ns_window().unwrap() as id;
                unsafe {
                    let bg_color = NSColor::colorWithRed_green_blue_alpha_(
                        nil,
                        255.0 / 255.0,
                        255.0 / 255.0,
                        255.0 / 255.0,
                        1.0,
                    );
                    ns_window.setBackgroundColor_(bg_color);
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// #[cfg_attr(mobile, tauri::mobile_entry_point)]
// pub fn run() {
//   tauri::Builder::default()
//     .setup(|app| {
//       if cfg!(debug_assertions) {
//         app.handle().plugin(
//           tauri_plugin_log::Builder::default()
//             .level(log::LevelFilter::Info)
//             .build(),
//         )?;
//       }
//       Ok(())
//     })
//     .run(tauri::generate_context!())
//     .expect("error while running tauri application");
// }
