# Quick Start Guide - Production Structure

## Installation

### Windows
```batch
cd Destroyer-DoS
python -m venv venv
venv\Scripts\activate
pip install -e .
```

### Linux/macOS
```bash
cd Destroyer-DoS
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Basic Usage

### Run CLI Attack
```bash
python bin/ddos.py -i target.com -p 80 -t TCP
```

### Run GUI
```bash
python bin/gui.py
```

### Run Interactive Launcher
```bash
python bin/launcher
```

---

## Configuration

### Select Environment
```bash
export DESTROYER_ENV=production    # Unix/Linux
set DESTROYER_ENV=production       # Windows
```

### Edit Configuration
Edit `config/production.conf` or `config/development.conf`:
```ini
[logging]
level = INFO

[safety]
enable_environment_detection = true

[resources]
max_cpu_percent = 80
max_memory_percent = 70
```

---

## Development

### Install Development Dependencies
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/performance/   # Performance tests only
```

### Code Quality

```bash
# Lint code
python tools/lint.py

# Format code
python tools/format.py

# Build package
python tools/build.py
```

---

## Project Structure Reference

```
Key Directories:
├── bin/                    Entry point scripts
├── src/destroyer_dos/      Main application package
│   └── core/              Core subsystems (12 modules)
├── config/                Configuration files
├── tests/                 Test suite
├── docs/                  Documentation
├── tools/                 Development tools
└── archives/unnecessary/  Deprecated files
```

---

## Common Imports

### In Application Code
```python
from src.destroyer_dos.core.safety import SafetyManager
from src.destroyer_dos.core.networking import ProtocolManager
from src.destroyer_dos.core.analytics import MetricsCollector
```

### In Tests
```python
import pytest
from src.destroyer_dos.core.safety import SafetyManager
```

### In Entry Points
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.destroyer_dos.core.interfaces.cli import CLIInterface
```

---

## Troubleshooting

### Import Errors
```python
# If you get "No module named 'src'"
# Make sure you've run: pip install -e .
```

### Configuration Not Found
```bash
# Set DESTROYER_ENV explicitly
export DESTROYER_ENV=production
# Then run your command
```

### Port Already in Use
```bash
# Change network settings in config/production.conf
[attack]
starting_port = 5000
```

---

## File Locations

| Purpose | Location |
|---------|----------|
| Main Application | `src/destroyer_dos/` |
| CLI Entry Point | `bin/ddos.py` |
| GUI Entry Point | `bin/gui.py` |
| Config (Production) | `config/production.conf` |
| Config (Development) | `config/development.conf` |
| Tests | `tests/` |
| Documentation | `docs/` |
| Old Files | `archives/unnecessary/` |

---

## Next Steps

1. **Installation**: Follow installation steps above
2. **Configuration**: Edit `config/production.conf` if needed
3. **Usage**: Run `python bin/ddos.py --help`
4. **Testing**: Run `pytest` to validate setup
5. **Documentation**: See `docs/` for detailed guides

---

## Support

- **Structure Guide**: See `docs/STRUCTURE.md`
- **Usage Guide**: See `docs/USAGE.md` (when available)
- **API Reference**: See `docs/API.md` (when available)
- **Previous Analysis**: See `PROJECT_ANALYSIS.md`

---

**Version:** 1.0
**Last Updated:** December 7, 2025
