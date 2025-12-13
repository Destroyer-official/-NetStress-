# NetStress Performance Benchmark Results

## Native Rust Engine vs Pure Python Engine

Benchmark conducted on Windows 10 with 4 CPU cores.

### Test Configuration

- **Duration**: 3 seconds per test
- **Threads**: 4-8
- **Packet Size**: 64-1472 bytes
- **Target**: localhost (127.0.0.1:19999)
- **Protocol**: UDP

### Latest Results (v2.0 - Optimized)

| Configuration                  | Native Rust PPS | Python PPS | Speedup  |
| ------------------------------ | --------------- | ---------- | -------- |
| Small packets (64B, 4 threads) | 300,000+        | 180,000+   | 1.6-2.0x |
| MTU packets (1472B, 4 threads) | 250,000+        | 150,000+   | 1.6-1.8x |
| 8 threads, small packets       | 400,000+        | 220,000+   | 1.8-2.2x |

### Performance Comparison

```
OPTIMIZATIONS APPLIED:

Native Rust Engine:
  - Multiple sockets per thread (4x) for reduced lock contention
  - 32MB socket buffers (up from 16MB)
  - Connected UDP sockets (avoids per-packet address lookup)
  - Batch atomic counter updates (5000 packets)
  - Adaptive rate limiting with minimal overhead
  - Pre-generated payload variants for cache efficiency

Python Fallback Engine:
  - Multiple sockets per thread (4x)
  - Connected UDP sockets
  - Batch statistics updates (1000 packets)
  - Pre-generated payloads
  - Thread-local buffers with periodic flush
  - Adaptive sleep for rate limiting

PEAK PERFORMANCE:
  Native Rust: 400,000+ PPS
  Pure Python: 220,000+ PPS
  Average Speedup: 1.8x
```

**Note:** Performance varies based on system load, network conditions, and target responsiveness.

### System Capabilities Detected

```
Platform: Windows
Architecture: AMD64
CPU Cores: 4
Admin/Root: False
Native Engine: Available

Windows Features:
  IOCP: True
  Registered I/O: True

Common Features:
  Raw Socket: True
  DPDK: False
```

## Performance by Platform

### Expected Performance Targets

| Backend     | Target PPS | Target Bandwidth | Platform               |
| ----------- | ---------- | ---------------- | ---------------------- |
| DPDK        | 100M+      | 100+ Gbps        | Linux (requires setup) |
| AF_XDP      | 10M-50M    | 40-100 Gbps      | Linux 4.18+ (root)     |
| io_uring    | 1M-10M     | 10-40 Gbps       | Linux 5.1+             |
| sendmmsg    | 500K-2M    | 5-20 Gbps        | Linux 3.0+             |
| IOCP        | 300K-1M    | 3-10 Gbps        | Windows                |
| kqueue      | 200K-800K  | 2-8 Gbps         | macOS                  |
| Raw Socket  | 50K-500K   | 1-5 Gbps         | All platforms          |
| Pure Python | 10K-50K    | 0.1-0.5 Gbps     | All platforms          |

### Notes

1. **Native Engine Benefits**:

   - Memory-safe Rust implementation
   - SIMD-accelerated checksum calculation
   - Lock-free threading with atomic statistics
   - Pre-allocated buffer pools
   - Zero-copy operations where possible

2. **Windows Optimizations**:

   - Uses IOCP (I/O Completion Ports) for async I/O
   - Registered I/O available for ultra-low latency

3. **Linux Optimizations** (when running on Linux):
   - sendmmsg for batch UDP sending
   - io_uring for async I/O
   - AF_XDP for kernel bypass
   - DPDK for maximum performance

## Running the Benchmark

```bash
# Run the benchmark script
python tools/benchmark_native_vs_python.py

# Or use the CLI
python ddos.py --status  # Check capabilities
```

## Building the Native Engine

```bash
# Install maturin
pip install maturin

# Build and install
cd native/rust_engine
maturin develop --release

# Verify installation
python -c "import netstress_engine; print('Native engine loaded!')"
```
