#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}       NoteLens Dev Server${NC}"
echo -e "${GREEN}====================================${NC}"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}tmux is not installed. Please install it to run both services simultaneously.${NC}"
    echo "On macOS: brew install tmux"
    echo "On Linux: sudo apt install tmux (or your distro's package manager)"
    exit 1
fi

# Start a new tmux session
SESSION_NAME="notelens-dev"
tmux new-session -d -s $SESSION_NAME

# Configure the first window for frontend
tmux rename-window -t $SESSION_NAME:0 'Frontend'
tmux send-keys -t $SESSION_NAME:0 'echo -e "${GREEN}Starting Frontend (Tauri)...${NC}"; pnpm tauri dev' C-m

# Create a new window for backend
tmux new-window -t $SESSION_NAME:1 -n 'Backend'
tmux send-keys -t $SESSION_NAME:1 'echo -e "${GREEN}Starting Backend (Python)...${NC}"; cd src-python && poetry run python -m notelens.main' C-m

# Attach to the tmux session
echo -e "${GREEN}Starting services in tmux session. Press Ctrl+B then D to detach.${NC}"
echo -e "${YELLOW}You can reattach later with: tmux attach -t ${SESSION_NAME}${NC}"
tmux attach -t $SESSION_NAME