# NetStress 2.0 Power Trio - Project Structure

## Overview

NetStress 2.0 uses a clean, production-ready project structure following Python best practices and the Power Trio architecture (Python/Rust/C).

## Directory Structure

```
NetStress/
├── core/                      # Core Python modules
│   ├── ai/                    # AI/ML optimization
│   │   ├── attack_optimizer.py
│   │   ├── reinforcement_learning.py
│   │   ├── defense_evasion.py
│   │   └── ...
│   ├── analytics/             # Real-time analytics
│   │   ├── metrics_collector.py
│   │   ├── predictive_analytics.py
│   │   └── ...
│   ├── antidetect/            # Anti-detection capabilities
│   ├── attacks/               # Attack implementations
│   ├── autonomous/            # Autonomous adaptation
│   ├── capabilities/          # Capability reporting
│   ├── config/                # Configuration management
│   ├── control/               # Rate control
│   ├── distributed/           # Distributed coordination
│   ├── engines/               # Packet engines
│   ├── evasion/               # Evasion techniques
│   ├── health/                # Health monitoring
│   ├── integration/           # System integration
│   ├── intelligence/          # Traffic intelligence
│   ├── interfaces/            # CLI, API, GUI
│   ├── memory/                # Memory management
│   ├── monitoring/            # Performance monitoring
│   ├── networking/            # Network operations
│   ├── orchestration/         # Attack orchestration
│   ├── performance/           # Performance optimization
│   ├── platform/              # Platform abstraction
│   ├── plugins/               # Plugin system
│   ├── protocols/             # Protocol implementations
│   ├── recon/                 # Reconnaissance
│   ├── reporting/             # Report generation
│   ├── safety/                # Safety controls
│   ├── simulation/            # Network simulation
│   ├── target/                # Target analysis
│   ├── testing/               # Testing utilities
│   └── native_engine.py       # Native engine wrapper
│
├── native/                    # Native Rust/C code
│   ├── rust_engine/           # Rust packet engine
│   │   ├── src/
│   │   │   ├── lib.rs         # PyO3 module
│   │   │   ├── engine.rs      # Flood engine
│   │   │   ├── packet.rs      # Packet building
│   │   │   ├── stats.rs       # Statistics
│   │   │   ├── pool.rs        # Buffer pools
│   │   │   ├── simd.rs        # SIMD operations
│   │   │   ├── queue.rs       # Lock-free queues
│   │   │   ├── backend.rs     # Backend abstraction
│   │   │   ├── safety.rs      # Safety controls
│   │   │   └── ...
│   │   └── Cargo.toml
│   └── c_driver/              # C hardware drivers
│       ├── driver_shim.c
│       └── driver_shim.h
│
├── tests/                     # Test suite
│   ├── test_properties.py     # Property-based tests
│   ├── test_*.py              # Unit/integration tests
│   └── unit/                  # Unit tests
│
├── docs/                      # Documentation
│   ├── API_REFERENCE.md       # API documentation
│   ├── ARCHITECTURE.md        # Architecture guide
│   ├── BUILD_INSTRUCTIONS.md  # Build guide
│   ├── CLI_USAGE.md           # CLI documentation
│   ├── QUICK_START.md         # Quick start guide
│   ├── USAGE.md               # Usage guide
│   └── ...
│
├── config/                    # Configuration files
│   ├── development.conf
│   └── production.conf
│
├── scripts/                   # Utility scripts
│   ├── install.sh             # Linux/macOS installer
│   ├── install.ps1            # Windows installer
│   ├── benchmark.py           # Benchmarking
│   └── deploy.py              # Deployment
│
├── examples/                  # Example code
│   ├── native_stats_bridge_demo.py
│   └── tls_mutual_auth_example.py
│
├── .github/                   # GitHub workflows
│
├── unnecessary/               # Archived/old files (gitignored)
│
├── ddos.py                    # Main attack engine
├── main.py                    # Entry point
├── netstress_cli.py           # CLI interface
├── benchmark_comparison.py    # Performance benchmark
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
├── setup.py                   # Package setup
├── Makefile                   # Build automation
├── Dockerfile                 # Docker image
├── docker-compose.yml         # Docker compose
├── README.md                  # Main documentation
├── LICENSE                    # MIT License
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guide
├── SECURITY.md                # Security policy
└── CODE_OF_CONDUCT.md         # Code of conduct
```

## Key Files

### Entry Points

- `main.py` - Main entry point
- `ddos.py` - Core attack engine
- `netstress_cli.py` - Command-line interface

### Configuration

- `config/development.conf` - Development settings
- `config/production.conf` - Production settings
- `netstress.json` - Runtime configuration

### Native Engine

- `native/rust_engine/` - Rust packet engine (PyO3)
- `native/c_driver/` - C hardware drivers

### Core Modules

- `core/native_engine.py` - Native engine Python wrapper
- `core/ai/` - AI/ML optimization
- `core/analytics/` - Real-time analytics
- `core/attacks/` - Attack implementations
- `core/safety/` - Safety controls

## Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Build native engine
cd native/rust_engine
maturin develop --release

# Run tests
pytest tests/ -v

# Run benchmark
python benchmark_comparison.py
```

## Module Dependencies

```
main.py
  └── ddos.py
        ├── core/native_engine.py
        │     └── native/rust_engine (PyO3)
        │           └── native/c_driver (FFI)
        ├── core/ai/
        ├── core/analytics/
        ├── core/attacks/
        ├── core/safety/
        └── core/...
```

## Performance Tiers

| Tier | Backend    | PPS      | Use Case              |
| ---- | ---------- | -------- | --------------------- |
| 1    | DPDK       | 100M+    | Production, high-end  |
| 2    | AF_XDP     | 10M-50M  | Linux, kernel bypass  |
| 3    | io_uring   | 1M-10M   | Linux 5.1+, async     |
| 4    | sendmmsg   | 500K-2M  | Linux, batch syscalls |
| 5    | Raw Socket | 50K-500K | Cross-platform        |
| 6    | Python     | 50K-200K | Fallback              |

## Cleanup Guidelines

Files that should be in `unnecessary/`:

- Old test files not in `tests/`
- Benchmark results and reports
- Temporary logs
- Old code versions
- Generated reports

Files that should NOT be committed:

- `*.log` files
- `models/*.pkl` (large binary files)
- `__pycache__/`
- `*.pyc`
- Build artifacts
