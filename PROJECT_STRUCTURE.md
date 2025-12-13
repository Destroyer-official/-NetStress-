# NetStress 2.0 Project Structure

## Version 2.0 - Optimized Architecture

### Key Optimizations Applied (December 2025)

1. **Native Rust Engine (v2.0)**

   - Multiple sockets per thread (4x) for reduced lock contention
   - 32MB socket buffers for high throughput
   - Connected UDP sockets (avoids per-packet address lookup)
   - Batch atomic counter updates (5000 packets)
   - Pre-generated payload variants for cache efficiency
   - TCP connection pooling with keep-alive
   - Peak performance: 400,000+ PPS

2. **Python Fallback Engine (Optimized)**

   - Multiple sockets per thread (4x)
   - Connected UDP sockets
   - Thread-local statistics buffers
   - Batch updates to reduce lock contention
   - Adaptive rate limiting
   - Peak performance: 220,000+ PPS

3. **Advanced Evasion System**

   - Markov chain-based timing patterns
   - Entropy-maximizing payload variations
   - Protocol-aware traffic mimicry
   - Real-time defense detection response
   - Browser behavior simulation

4. **Lock-Free Data Structures**

   - Batch queue for high-throughput scenarios
   - Lock-free statistics aggregator
   - Adaptive rate limiter with feedback

5. **New Attack Vectors**
   - Protocol fuzzer with grammar-based mutations
   - Advanced Slowloris with connection pooling
   - DNS amplification engine with resolver discovery

## Production-Ready Directory Layout

```
-NetStress-/
├── core/                    # Core Python modules
│   ├── analytics/           # Real-time analytics and metrics
│   ├── antidetect/          # Anti-detection and evasion
│   ├── attacks/             # Attack implementations
│   ├── capabilities/        # System capability detection
│   ├── control/             # Rate control and adaptation
│   ├── engines/             # Packet engines
│   ├── evasion/             # Traffic shaping and obfuscation
│   ├── intelligence/        # Traffic intelligence
│   ├── interfaces/          # CLI and API interfaces
│   ├── monitoring/          # Performance monitoring
│   ├── performance/         # Performance optimizations
│   ├── protocols/           # Protocol implementations
│   ├── recon/               # Reconnaissance tools
│   ├── safety/              # Safety mechanisms
│   ├── simulation/          # Network simulation
│   └── native_engine.py     # Native Rust engine integration
│
├── native/                  # Native high-performance engine
│   ├── rust_engine/         # Rust packet engine (PyO3)
│   │   ├── src/             # Rust source code
│   │   ├── Cargo.toml       # Rust dependencies
│   │   └── pyproject.toml   # Python build config
│   └── c_driver/            # C hardware interface
│       ├── driver_shim.c    # Backend implementations
│       └── driver_shim.h    # API definitions
│
├── tests/                   # Test suite
│   ├── test_properties.py   # Property-based tests
│   ├── test_integration_power_trio.py
│   └── ...
│
├── config/                  # Configuration files
├── docs/                    # Documentation
├── examples/                # Usage examples
├── scripts/                 # Build and install scripts
├── tools/                   # Utility tools
├── bin/                     # Compiled binaries
├── models/                  # AI/ML models
│
├── ddos.py                  # Main entry point
├── main.py                  # Alternative entry point
├── netstress_cli.py         # CLI interface
│
├── README.md                # Main documentation
├── CAPABILITIES.md          # Feature capabilities
├── PERFORMANCE_BENCHMARK.md # Benchmark results
├── SECURITY.md              # Security guidelines
├── CONTRIBUTING.md          # Contribution guide
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT License
│
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Python project config
├── setup.py                 # Package setup
├── Makefile                 # Build automation
├── Dockerfile               # Container build
├── docker-compose.yml       # Container orchestration
│
├── .gitignore               # Git ignore rules
├── .github/                 # GitHub workflows
│
└── unnecessary/             # Archived/old files (gitignored)
```

## Key Files

| File                            | Purpose                        |
| ------------------------------- | ------------------------------ |
| `ddos.py`                       | Main attack engine and CLI     |
| `main.py`                       | Alternative entry point        |
| `core/native_engine.py`         | Native Rust engine integration |
| `benchmark_native_vs_python.py` | Performance comparison tool    |

## Building the Native Engine

```bash
# Prerequisites
pip install maturin

# Build and install
cd native/rust_engine
maturin develop --release

# Verify
python -c "from core.native_engine import NATIVE_ENGINE_AVAILABLE; print(f'Native: {NATIVE_ENGINE_AVAILABLE}')"
```

## Quick Start

```bash
# Check system capabilities
python ddos.py --status

# Run benchmark
python benchmark_native_vs_python.py

# Basic UDP flood test
python ddos.py -i 127.0.0.1 -p 9999 -t UDP -d 10
```

## Performance Tiers

| Backend                | PPS      | Platform   |
| ---------------------- | -------- | ---------- |
| Native Rust (IOCP)     | 300K+    | Windows    |
| Native Rust (io_uring) | 1M+      | Linux 5.1+ |
| Native Rust (sendmmsg) | 500K+    | Linux 3.0+ |
| Pure Python            | 50K-200K | All        |
