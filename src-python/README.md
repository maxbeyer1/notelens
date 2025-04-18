# NoteLens Python Backend

The NoteLens Python backend provides the core functionality for semantic search of Apple Notes.

## Architecture

The backend is organized into several modules:

### Core Components

- **Main Module** (`main.py`): Entry point that initializes and coordinates all services
- **Setup Manager** (`core/setup_manager.py`): Handles app initialization and database setup
- **Database Manager** (`core/database.py`): Manages the SQLite database with vector capabilities
- **Message Bus** (`core/message_bus.py`): Internal publish-subscribe system for component communication
- **Watcher** (`core/watcher.py`): Monitors the Apple Notes database for changes

### Notes Processing

- **Notes Service** (`notes/service.py`): Core service for note operations and search
- **Notes Parser** (`notes/parser/parser.py`): Extracts and processes Apple Notes data
- **Notes Tracker** (`notes/tracker.py`): Tracks note changes and updates

### WebSocket Interface

- **WebSocket Server** (`websocket/server.py`): Handles communication with the frontend
- **WebSocket Handlers**: Process specific request types:
  - `setup.py`: Handles setup and initialization requests
  - `search.py`: Processes search queries
  - `ping.py`: Simple health check handler

## Technical Features

1. **Vector Embeddings**:

   - Uses text embeddings via `sqlite-vec` and a custom embedding model
   - Stored in SQLite using vector extensions for efficient similarity search

2. **Asynchronous Processing**:

   - Built with Python's `asyncio` for non-blocking operations
   - Parallel processing of note indexing and search operations

3. **Real-time Updates**:

   - Uses the `watchdog` library to monitor file system changes
   - Automatically updates the search index when notes are modified

4. **WebSocket API**:
   - Provides a WebSocket interface for the frontend to perform searches
   - Sends real-time progress updates during setup and indexing

## Libraries Used

- `sqlite-vec`: Vector extension for SQLite enabling semantic search
- `websockets`: WebSocket server implementation
- `pydantic`: Data validation and settings management
- `watchdog`: File system monitoring
- `tqdm`: Progress reporting
- `numpy`: Numerical operations for vector processing
