#!/bin/bash
set -e

# Configuration
TARGET_TRIPLE=$(rustc -Vv | grep host | cut -f2 -d' ')
BINARY_NAME="notelens-backend"
BINARY_DIR="src-tauri/binaries"
PYTHON_DIR="src-python"

echo "Building NoteLens for macOS..."
echo "Target triple: $TARGET_TRIPLE"

# Step 1: Install dependencies if needed
echo "Checking dependencies..."
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Please install poetry first."
    echo "You can install it with: pip install poetry"
    exit 1
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    poetry add pyinstaller
fi

# Step 2: Install Python dependencies
echo "Installing Python dependencies..."
cd "$PYTHON_DIR"
poetry install
cd ..

# Step 3: Create Python executable using PyInstaller
echo "Building Python backend with PyInstaller..."
cd "$PYTHON_DIR"

# Create directories that might be needed at runtime
mkdir -p ~/Library/Application\ Support/NoteLens/temp

# Ensure correct permissions on directories
chmod -R 755 ~/Library/Application\ Support/NoteLens

# Explicitly include the rembed0.dylib and vec0.dylib libraries, ensure sqlite_vec is imported
# Also include the ruby parser scripts if they exist
PARSER_PATH="../vendor/apple_cloud_notes_parser"

# Make sure lib directory exists
if [ ! -d "notelens/lib" ]; then
  echo "Creating lib directory"
  mkdir -p "notelens/lib"
fi

# Check if we have the required libraries
if [ ! -f "notelens/lib/rembed0.dylib" ]; then
  echo "ERROR: rembed0.dylib not found in notelens/lib directory"
  exit 1
fi

if [ ! -f "notelens/lib/vec0.dylib" ]; then
  echo "ERROR: vec0.dylib not found in notelens/lib directory"
  exit 1
fi

# Build with or without the parser
if [ -d "$PARSER_PATH" ]; then
  echo "Including Ruby parser from $PARSER_PATH"
  poetry run python -m PyInstaller --onefile --name "$BINARY_NAME" \
    --hidden-import=sqlite_vec \
    --hidden-import=numpy \
    --add-data="notelens/lib/*.dylib:notelens/lib" \
    --add-data="$PARSER_PATH:apple_cloud_notes_parser" \
    notelens/main.py
else
  echo "WARNING: Ruby parser not found at $PARSER_PATH"
  poetry run python -m PyInstaller --onefile --name "$BINARY_NAME" \
    --hidden-import=sqlite_vec \
    --hidden-import=numpy \
    --add-data="notelens/lib/*.dylib:notelens/lib" \
    notelens/main.py
fi

# Step 4: Copy the executable to the Tauri binaries directory
echo "Setting up sidecar binary..."
mkdir -p "../$BINARY_DIR"
cp "dist/$BINARY_NAME" "../$BINARY_DIR/$BINARY_NAME"

# Step 5: Rename with target triple for Tauri
cd "../$BINARY_DIR"
mv "$BINARY_NAME" "$BINARY_NAME-$TARGET_TRIPLE"
echo "Created sidecar binary: $BINARY_NAME-$TARGET_TRIPLE"
cd ../..

# Step 6: Build the Tauri app
echo "Building Tauri application..."
pnpm tauri build

echo "Build complete! Application is in src-tauri/target/release/bundle/"