# GitHub Copilot Instructions for Mijia Monitor

This document provides context and guidelines for AI agents working on the `mijia-monitor` codebase.

## 🏗 Project Overview

`mijia-monitor` is a Windows desktop application for real-time monitoring of Xiaomi (Mijia) smart home devices.
- **Framework**: Python 3.9+ with **PySide6** (Qt) for the GUI.
- **Core Logic**: Multi-threaded device polling and data collection.
- **Data Storage**: SQLite database for historical data and logs.
- **External API**: Integrates with `mijia-api` (local submodule) for device communication.

## 🏛 Architecture & Key Components

### 1. Directory Structure
- `src/ui/`: PySide6 widgets and windows. `MainWindow` is the entry point for UI.
- `src/core/`: Business logic.
  - `monitor.py`: `DeviceMonitor` class manages polling threads and API interaction.
  - `database.py`: `DatabaseManager` handles SQLite operations.
- `mijia-api/`: Local package for Mijia cloud interaction. **Note**: Added to `sys.path` dynamically in `monitor.py`.
- `config/`: Configuration files (`config.yaml`, `mijia_auth.json`).

### 2. Data Flow
1. **Polling**: `DeviceMonitor` runs a scheduler and worker threads to fetch device properties via `mijiaAPI`.
2. **Storage**: Data is saved to SQLite via `DatabaseManager`.
3. **UI Updates**: `DeviceMonitor` triggers callbacks. **Crucial**: UI updates must be marshaled to the main Qt thread (e.g., using Signals/Slots).

## 🛠 Development Workflows

### Running the Application
- **Windows (Dev)**: Use `scripts/run_dev.bat` to set up venv and run.
- **Manual**:
  ```bash
  # Activate venv
  python -m src.main
  ```

### Building
- Uses **PyInstaller**.
- Command: `pyinstaller mi-monitor.spec`

### Dependencies
- Managed in `requirements.txt`.
- Key libs: `PySide6`, `mijiaAPI`, `requests`, `pandas`, `pyqtgraph`.

## 📏 Conventions & Patterns

### Imports
- Use **absolute imports** rooted at `src`.
  - ✅ `from src.utils.logger import get_logger`
  - ❌ `from ..utils.logger import get_logger` (avoid relative imports in `src` root)

### Logging
- Always use the project's logger:
  ```python
  from src.utils.logger import get_logger
  logger = get_logger(__name__)
  logger.info("Message")
  ```

### Threading & Concurrency
- `DeviceMonitor` uses `threading.Thread` and `queue.Queue`.
- **Do not** block the main thread with API calls.
- Ensure thread safety when accessing shared resources (use `self.lock` in `DeviceMonitor`).

### Mijia API Integration
- The `mijiaAPI` is imported dynamically.
- Device properties are fetched using `get_devices_prop` with `did` and property methods.
- See `src/core/monitor.py` for the canonical usage pattern.

### Configuration
- Use `ConfigLoader` to access settings.
  ```python
  from src.utils.config_loader import ConfigLoader
  config = ConfigLoader()
  val = config.get('section.key', default_value)
  ```

## ⚠️ Common Pitfalls
- **PyQt vs PySide**: The project uses **PySide6**. Do not import from `PyQt6` or `PyQt5`.
- **Path Handling**: Use `src.utils.path_utils.get_app_path()` or `get_resource_path()` to ensure paths work in both dev and frozen (exe) modes.
- **Signal Handling**: Python signal handlers (Ctrl+C) require a QTimer to wake the interpreter in the Qt event loop (see `src/main.py`).
