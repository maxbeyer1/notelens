# NoteLens

Semantic search for your Apple Notes. Built with Tauri, React, and Python.

## Project Structure

- `src` - React frontend
- `src-tauri` - Rust/Tauri app shell
- `src-python` - Python backend for Apple Notes integration

## Building for macOS

NoteLens uses a Python backend to interface with Apple Notes, which is embedded in the Tauri application as a sidecar binary.

### Prerequisites

- Node.js (18+) and pnpm
- Rust and Cargo (latest stable)
- Python 3.12+
- Poetry (Python package manager)
- Xcode command line tools

### Development Setup

1. Install frontend dependencies:
   ```
   pnpm install
   ```

2. Install Python dependencies:
   ```
   cd src-python
   poetry install
   cd ..
   ```

3. Start the development server:
   ```
   pnpm tauri dev
   ```

This will automatically:
- Start the Vite development server for the frontend
- Build and run the Tauri application
- Use a local Python process for backend functionality

### Production Build

To build the production macOS application:

1. Run the build script:
   ```
   ./build-macos-app.sh
   ```

The build script will:
1. Create a standalone executable from the Python backend using PyInstaller
2. Configure the executable as a Tauri sidecar with the correct target triple
3. Build the Tauri application with the embedded Python backend

The final application will be in `src-tauri/target/release/bundle/`.

## Architecture

- **Frontend**: React, TypeScript, and TailwindCSS
- **App Shell**: Tauri (Rust)
- **Backend**: Python for Apple Notes integration

The backend communicates with the frontend via WebSocket, with the Tauri application managing the Python process lifecycle.

## Permissions

The application requires access to your Apple Notes database to provide search functionality. All data is processed locally and never leaves your computer.