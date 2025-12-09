# File Inventory

Complete list of project files and their purposes.

---

## Root Directory

### Entry Points

| File          | Purpose                 |
| ------------- | ----------------------- |
| `ddos.py`     | Main attack engine      |
| `main.py`     | Application entry point |
| `launcher.py` | Interactive launcher    |
| `gui_main.py` | GUI application         |

### Configuration

| File                 | Purpose                    |
| -------------------- | -------------------------- |
| `requirements.txt`   | Python dependencies        |
| `setup.py`           | Installation configuration |
| `pyproject.toml`     | Build configuration        |
| `Dockerfile`         | Docker configuration       |
| `docker-compose.yml` | Docker Compose config      |

### Documentation

| File                 | Purpose              |
| -------------------- | -------------------- |
| `README.md`          | Project overview     |
| `CHANGELOG.md`       | Version history      |
| `CONTRIBUTING.md`    | Contribution guide   |
| `SECURITY.md`        | Security policy      |
| `CODE_OF_CONDUCT.md` | Community guidelines |
| `LICENSE`            | MIT License          |

---

## Core Modules (`core/`)

### Safety (`core/safety/`)

| File                       | Purpose                            |
| -------------------------- | ---------------------------------- |
| `protection_mechanisms.py` | Target validation, resource limits |
| `emergency_shutdown.py`    | Emergency stop functionality       |
| `environment_detection.py` | Environment validation             |
| `audit_logging.py`         | Activity logging                   |
| `blocked_targets.txt`      | Target blocklist                   |

### AI (`core/ai/`)

| File                       | Purpose                    |
| -------------------------- | -------------------------- |
| `ml_optimizer.py`          | ML parameter optimization  |
| `adaptive_strategy.py`     | Adaptive attack strategies |
| `performance_predictor.py` | Performance prediction     |

### Analytics (`core/analytics/`)

| File                      | Purpose              |
| ------------------------- | -------------------- |
| `metrics_collector.py`    | Metrics collection   |
| `performance_tracker.py`  | Performance tracking |
| `visualization_engine.py` | Data visualization   |
| `predictive_analytics.py` | Predictive analysis  |

### Autonomous (`core/autonomous/`)

| File                     | Purpose                |
| ------------------------ | ---------------------- |
| `adaptation_system.py`   | Real-time adaptation   |
| `optimization_engine.py` | Parameter optimization |
| `resource_manager.py`    | Resource management    |

### Interfaces (`core/interfaces/`)

| File     | Purpose                |
| -------- | ---------------------- |
| `cli.py` | Command-line interface |
| `gui.py` | GUI interface          |
| `api.py` | REST API               |
| `web.py` | Web interface          |

### Other Modules

| Directory           | Purpose                  |
| ------------------- | ------------------------ |
| `core/networking/`  | Network operations       |
| `core/platform/`    | Cross-platform support   |
| `core/memory/`      | Memory management        |
| `core/performance/` | Performance optimization |
| `core/target/`      | Target intelligence      |
| `core/testing/`     | Test utilities           |
| `core/integration/` | Component coordination   |

---

## Configuration (`config/`)

| File               | Purpose              |
| ------------------ | -------------------- |
| `production.conf`  | Production settings  |
| `development.conf` | Development settings |

---

## Documentation (`docs/`)

| File                        | Purpose                     |
| --------------------------- | --------------------------- |
| `QUICK_START.md`            | 5-minute setup guide        |
| `INSTALLATION.md`           | Complete installation guide |
| `USAGE.md`                  | Usage guide                 |
| `CLI_USAGE.md`              | CLI reference               |
| `API_REFERENCE.md`          | Python API docs             |
| `ARCHITECTURE.md`           | System design               |
| `STRUCTURE.md`              | Project layout              |
| `TROUBLESHOOTING.md`        | Problem solving             |
| `FAQ.md`                    | Common questions            |
| `PERFORMANCE_RESULTS.md`    | Test results                |
| `SAFETY_SYSTEMS_SUMMARY.md` | Safety overview             |
| `AUDIT_SUMMARY.md`          | Audit system                |
| `PROJECT_ANALYSIS.md`       | Technical analysis          |
| `EXECUTIVE_SUMMARY.md`      | Overview                    |
| `GUI_README.md`             | GUI guide                   |
| `QUICK_REFERENCE.md`        | Quick reference             |
| `DOCUMENTATION_INDEX.md`    | Doc navigation              |

---

## Tests (`tests/`)

| File                     | Purpose              |
| ------------------------ | -------------------- |
| `test_safety_systems.py` | Safety system tests  |
| `test_attack_engines.py` | Attack engine tests  |
| `test_integration.py`    | Integration tests    |
| `conftest.py`            | Pytest configuration |

---

## Scripts (`scripts/`)

| File          | Purpose               |
| ------------- | --------------------- |
| `install.sh`  | Linux/macOS installer |
| `install.bat` | Windows installer     |

---

## Generated Directories

| Directory             | Purpose                 |
| --------------------- | ----------------------- |
| `audit_logs/`         | Audit logs and database |
| `compliance_reports/` | Generated reports       |
| `validation_reports/` | Test reports            |
| `__pycache__/`        | Python cache            |

---

## GitHub (`/.github/`)

| File                                | Purpose                  |
| ----------------------------------- | ------------------------ |
| `ISSUE_TEMPLATE/bug_report.md`      | Bug report template      |
| `ISSUE_TEMPLATE/feature_request.md` | Feature request template |
| `PULL_REQUEST_TEMPLATE.md`          | PR template              |
| `FUNDING.yml`                       | Funding configuration    |

---

**Last Updated**: December 2025
