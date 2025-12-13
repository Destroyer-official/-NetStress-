# NetStress 2.0 - Power Trio "Sandwich" Architecture

## Overview

NetStress uses a revolutionary three-layer "Sandwich" architecture where each programming language handles what it does best:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON LAYER (Brain)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  main.py │ ddos.py │ CLI │ GUI │ AI/ML │ Analytics │ Configuration  │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  • User interface (CLI arguments, GUI windows)                       │   │
│  │  • Configuration management (.conf files, JSON)                      │   │
│  │  • AI/ML optimization (genetic algorithms, RL)                       │   │
│  │  • Real-time visualization and reporting                             │   │
│  │  • Distributed coordination                                          │   │
│  │  • High-level attack orchestration                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         RUST LAYER (Engine)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  netstress_engine (PyO3) │ Packet Gen │ Threading │ Lock-Free       │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  • High-speed packet generation (millions PPS)                       │   │
│  │  • Memory-safe buffer management (no segfaults)                      │   │
│  │  • SIMD-accelerated checksums (AVX2/SSE2)                            │   │
│  │  • Nanosecond-precision rate limiting                                │   │
│  │  • Lock-free threading with atomic statistics                        │   │
│  │  • Protocol builders (UDP, TCP, ICMP, HTTP, DNS)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         C LAYER (Metal)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  driver_shim.c │ DPDK │ AF_XDP │ io_uring │ sendmmsg │ Raw Sockets  │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  • Kernel bypass (DPDK, AF_XDP)                                      │   │
│  │  • Async I/O (io_uring)                                              │   │
│  │  • Batch syscalls (sendmmsg)                                         │   │
│  │  • Hardware checksum offload                                         │   │
│  │  • Platform-specific optimizations                                   │   │
│  │  • Direct NIC driver communication                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

### Python Layer (Brain) - "The Manager"

**Why Python?**

- Fastest for writing logic, parsing arguments, displaying graphs
- Rich ecosystem for AI/ML (numpy, scikit-learn, tensorflow)
- Easy to modify and extend
- Great for configuration and reporting

**What it does:**

- `main.py` - Entry point, capability detection
- `ddos.py` - Attack orchestration, protocol selection
- `core/ai/` - AI/ML optimization engines
- `core/analytics/` - Real-time metrics and visualization
- `core/interfaces/` - CLI and GUI interfaces

### Rust Layer (Engine) - "The Workhorse"

**Why Rust?**

- Memory safety guaranteed (no buffer overflows, use-after-free)
- Performance comparable to C
- Excellent concurrency (fearless threading)
- Zero-cost abstractions
- PyO3 provides seamless Python integration

**What it does:**

- `native/rust_engine/src/engine.rs` - High-speed flood engine
- `native/rust_engine/src/packet.rs` - Packet building
- `native/rust_engine/src/simd.rs` - SIMD-accelerated operations
- `native/rust_engine/src/queue.rs` - Lock-free MPMC queues
- `native/rust_engine/src/pool.rs` - Pre-allocated buffer pools

### C Layer (Metal) - "The Hardware Whisperer"

**Why C?**

- Native language of hardware drivers
- DPDK, AF_XDP, io_uring are C libraries
- Direct access to kernel syscalls
- Minimal overhead for critical paths

**What it does:**

- `native/c_driver/driver_shim.c` - Backend implementations
- DPDK integration for kernel bypass
- AF_XDP for zero-copy networking
- io_uring for async batch I/O
- sendmmsg for batch syscalls

## Data Flow

```
User Input (CLI/GUI)
        │
        ▼
┌───────────────────┐
│   Python Layer    │  Configuration, validation, orchestration
│   (main.py)       │
└─────────┬─────────┘
          │ PyO3 FFI
          ▼
┌───────────────────┐
│   Rust Layer      │  Packet generation, threading, rate limiting
│   (netstress_engine)
└─────────┬─────────┘
          │ C FFI
          ▼
┌───────────────────┐
│   C Layer         │  Hardware access, kernel bypass, syscalls
│   (driver_shim)   │
└─────────┬─────────┘
          │
          ▼
    Network Interface
```

## Communication Between Layers

### Python → Rust (PyO3)

```python
# Python code
from core.native_engine import UltimateEngine, EngineConfig

config = EngineConfig(target="192.168.1.1", port=80)
engine = UltimateEngine(config)
engine.start()
stats = engine.get_stats()  # Returns Python dict
```

```rust
// Rust code (lib.rs)
#[pyclass]
pub struct PacketEngine {
    engine: Arc<RwLock<FloodEngine>>,
}

#[pymethods]
impl PacketEngine {
    fn start(&self) -> PyResult<()> {
        self.engine.write().start()
    }

    fn get_stats(&self) -> PyResult<PyObject> {
        // Convert Rust stats to Python dict
    }
}
```

### Rust → C (FFI)

```rust
// Rust code (lib.rs)
#[cfg(feature = "dpdk")]
extern "C" {
    fn dpdk_send_burst(
        port_id: i32,
        packets: *const *const u8,
        lengths: *const u32,
        count: u32,
    ) -> i32;
}
```

```c
// C code (driver_shim.c)
int dpdk_send_burst(int port_id, const uint8_t** packets,
                    const uint32_t* lengths, uint32_t count) {
    // Use DPDK rte_eth_tx_burst
    return rte_eth_tx_burst(port_id, 0, mbufs, count);
}
```

## File Structure

```
NetStress/
├── main.py                    # Python entry point
├── ddos.py                    # Python attack orchestration
│
├── core/                      # Python modules
│   ├── native_engine.py       # Python wrapper for Rust engine
│   ├── ai/                    # AI/ML optimization
│   ├── analytics/             # Real-time analytics
│   ├── interfaces/            # CLI, GUI
│   └── ...
│
├── native/                    # Native code
│   ├── rust_engine/           # Rust packet engine
│   │   ├── src/
│   │   │   ├── lib.rs         # PyO3 module (Python bindings)
│   │   │   ├── engine.rs      # Flood engine
│   │   │   ├── packet.rs      # Packet building
│   │   │   └── ...
│   │   └── Cargo.toml
│   │
│   └── c_driver/              # C hardware interface
│       ├── driver_shim.c      # Backend implementations
│       └── driver_shim.h      # API definitions
│
└── docs/
    └── ARCHITECTURE.md        # This file
```

## Performance Tiers

| Tier | Backend  | PPS      | Bandwidth    | Layer  |
| ---- | -------- | -------- | ------------ | ------ |
| 1    | DPDK     | 100M+    | 100+ Gbps    | C      |
| 2    | AF_XDP   | 10M-50M  | 40-100 Gbps  | C      |
| 3    | io_uring | 1M-10M   | 10-40 Gbps   | C      |
| 4    | sendmmsg | 500K-2M  | 5-20 Gbps    | C      |
| 5    | Rust Raw | 50K-500K | 1-5 Gbps     | Rust   |
| 6    | Python   | 10K-50K  | 0.1-0.5 Gbps | Python |

## Building the Stack

### 1. Python Layer (Always Available)

```bash
pip install -r requirements.txt
```

### 2. Rust Layer (Recommended)

```bash
cd native/rust_engine
pip install maturin
maturin develop --release
```

### 3. C Layer (Advanced)

```bash
# Linux with DPDK
cd native/c_driver
make HAS_DPDK=1

# Linux with AF_XDP
make HAS_AF_XDP=1

# Linux with io_uring
make HAS_IO_URING=1
```

## Automatic Backend Selection

The engine automatically selects the best available backend:

```python
from core.native_engine import get_capabilities

caps = get_capabilities()
# Returns: {
#   'platform': 'Linux',
#   'native_available': True,
#   'has_dpdk': False,
#   'has_af_xdp': True,
#   'has_io_uring': True,
#   'has_sendmmsg': True,
#   'recommended_backend': 'io_uring'
# }
```

Priority order:

1. DPDK (if available and configured)
2. AF_XDP (Linux 4.18+, root required)
3. io_uring (Linux 5.1+)
4. sendmmsg (Linux 3.0+)
5. Raw Socket (always available)
6. Python fallback (when native unavailable)

## Key Design Decisions

### Why Not Pure Python?

Python's GIL (Global Interpreter Lock) limits true parallelism. For network stress testing, we need:

- Millions of packets per second
- Nanosecond-precision timing
- Zero-copy operations

Python alone cannot achieve this.

### Why Not Pure Rust?

Rust is excellent for the engine, but:

- Python has better AI/ML libraries
- Python is easier for configuration and scripting
- Python has better GUI frameworks
- Users can extend Python code easily

### Why Include C?

Many high-performance networking libraries are C:

- DPDK (Data Plane Development Kit)
- AF_XDP (Linux kernel XDP)
- io_uring (Linux async I/O)

While Rust can call these via FFI, a thin C shim simplifies integration.

## Extending the Architecture

### Adding a New Backend (C Layer)

1. Add function declarations to `driver_shim.h`
2. Implement in `driver_shim.c`
3. Add FFI declarations in Rust `lib.rs`
4. Update `backend_selector.rs` for auto-detection

### Adding a New Protocol (Rust Layer)

1. Add protocol enum variant in `packet.rs`
2. Implement builder in `protocol_builder.rs`
3. Add PyO3 wrapper function in `lib.rs`
4. Update Python wrapper in `native_engine.py`

### Adding a New Feature (Python Layer)

1. Create module in `core/`
2. Import in `ddos.py` or `main.py`
3. Add CLI arguments if needed
4. Update documentation

## Conclusion

The "Sandwich" architecture provides:

- **Flexibility**: Python for easy customization
- **Performance**: Rust for safe high-speed operations
- **Hardware Access**: C for kernel bypass and drivers
- **Safety**: Memory safety from Rust, no segfaults
- **Extensibility**: Each layer can be extended independently

This design allows NetStress to achieve professional-grade performance while remaining accessible to users who want to customize or extend it.
