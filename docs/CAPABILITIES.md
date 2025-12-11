# NetStress Capabilities - Honest Assessment

This document provides a truthful assessment of what NetStress can and cannot do.

## What This Tool IS

NetStress is a **Python-based network stress testing tool** that uses standard operating system networking APIs. It is suitable for:

- Educational purposes and learning about network protocols
- Basic stress testing of your own systems
- Security research in controlled environments
- Testing network resilience at moderate traffic levels

## What This Tool is NOT

NetStress is **NOT**:

- A kernel bypass tool (no DPDK, no XDP)
- A 10+ Gbps traffic generator
- A replacement for professional tools like iperf3, hping3, or DPDK-based generators
- Capable of true zero-copy networking (despite having code that attempts it)

## Honest Performance Expectations

### Linux (Best Performance)

| Metric              | Without Root      | With Root + sendmmsg |
| ------------------- | ----------------- | -------------------- |
| UDP PPS             | 100K-500K         | 500K-2M              |
| TCP Connections/sec | 5K-20K            | 10K-50K              |
| Bandwidth           | 500 Mbps - 5 Gbps | 1-10 Gbps            |

### Windows

| Metric              | Expected Range    |
| ------------------- | ----------------- |
| UDP PPS             | 50K-200K          |
| TCP Connections/sec | 2K-10K            |
| Bandwidth           | 100 Mbps - 2 Gbps |

### macOS

| Metric              | Expected Range    |
| ------------------- | ----------------- |
| UDP PPS             | 100K-300K         |
| TCP Connections/sec | 5K-15K            |
| Bandwidth           | 500 Mbps - 3 Gbps |

**Note**: These are realistic ranges based on typical hardware. Your results may vary based on:

- CPU speed and core count
- Network interface card (NIC) capabilities
- Target system responsiveness
- Network path characteristics

## Features That ARE Implemented

### ✓ Real Packet Generation

- UDP flood using `socket.sendto()`
- TCP connection flood using `asyncio`
- HTTP/HTTPS request flood using `aiohttp`
- DNS query generation

### ✓ Socket Optimizations

- `SO_SNDBUF` / `SO_RCVBUF` buffer tuning
- `TCP_NODELAY` for low latency
- `SO_REUSEADDR` / `SO_REUSEPORT`
- Non-blocking I/O with asyncio

### ✓ Linux-Specific Optimizations (with root)

- `sendmmsg()` for batch UDP sending
- `sysctl` network tuning
- `MSG_ZEROCOPY` on kernel 4.14+
- `sendfile()` for file transfers

### ✓ Safety Features

- Target validation (blocks production domains)
- Resource monitoring
- Duration limits
- Audit logging

## Features That are NOT Implemented

### ✗ XDP (eXpress Data Path)

The codebase contains XDP-related code, but it is **simulation only**. No actual BPF bytecode is compiled or loaded.

**For real XDP**, use:

- [xdp-tools](https://github.com/xdp-project/xdp-tools)
- [libbpf](https://github.com/libbpf/libbpf)

### ✗ eBPF

The codebase references eBPF, but no actual eBPF programs are loaded.

**For real eBPF**, use:

- [bcc](https://github.com/iovisor/bcc)
- [libbpf](https://github.com/libbpf/libbpf)

### ✗ DPDK (Data Plane Development Kit)

The codebase mentions DPDK, but no actual DPDK integration exists.

**For real DPDK**, see:

- [DPDK.org](https://www.dpdk.org/)
- [DPDK Getting Started Guide](https://doc.dpdk.org/guides/linux_gsg/)

### ✗ Kernel Bypass

This tool uses the standard OS network stack. It does not bypass the kernel.

**For kernel bypass**, use:

- DPDK
- PF_RING
- Netmap

### ✗ True Zero-Copy

While the code attempts to use `MSG_ZEROCOPY` and `sendfile()`, Python's memory management means data is still copied in many cases.

**For true zero-copy**, you need:

- C/Rust code with direct buffer management
- DPDK or similar frameworks

## Why These Limitations Exist

### Python's Global Interpreter Lock (GIL)

Python can only execute one thread at a time for CPU-bound operations. This limits parallelism.

### OS Network Stack Overhead

Every packet goes through:

1. Python runtime
2. System call interface
3. Kernel network stack
4. Device driver
5. NIC

Each layer adds latency and CPU overhead.

### Memory Copies

Python's memory management requires copying data between buffers, even when using "zero-copy" APIs.

## Recommendations for Higher Performance

If you need more than what NetStress provides:

### For 10+ Gbps Traffic Generation

Use DPDK-based tools:

- [TRex](https://trex-tgn.cisco.com/) - Cisco's traffic generator
- [MoonGen](https://github.com/emmericp/MoonGen) - Scriptable packet generator
- [pktgen-dpdk](https://github.com/pktgen/Pktgen-DPDK) - DPDK packet generator

### For Kernel-Level Packet Processing

Use XDP/eBPF:

- [xdp-tutorial](https://github.com/xdp-project/xdp-tutorial)
- [Cilium](https://cilium.io/) - eBPF-based networking

### For Professional Stress Testing

Use established tools:

- [iperf3](https://iperf.fr/) - Network bandwidth testing
- [hping3](http://www.hping.org/) - Packet crafting
- [wrk](https://github.com/wg/wrk) - HTTP benchmarking
- [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) - Apache Bench

## Platform-Specific Requirements

### Linux

**Minimum Requirements:**

- Python 3.8+
- Standard user privileges for basic functionality

**Enhanced Performance (requires root):**

- `sendmmsg()` system call (kernel 3.0+)
- `MSG_ZEROCOPY` support (kernel 4.14+)
- `sysctl` network tuning access
- Raw socket creation for ICMP/TCP-SYN

**Commands to check capabilities:**

```bash
# Check kernel version for MSG_ZEROCOPY
uname -r  # Need 4.14+

# Check if running as root
id -u  # Should return 0 for root

# Test sendmmsg availability
python3 -c "import ctypes; print('sendmmsg available' if hasattr(ctypes.CDLL('libc.so.6'), 'sendmmsg') else 'sendmmsg not available')"
```

### Windows

**Requirements:**

- Python 3.8+
- Windows 10/11 or Windows Server 2019+
- Administrator privileges for raw sockets

**Limitations:**

- No `sendmmsg()` equivalent
- Limited raw socket support
- IOCP performance varies by Python version

**Commands to check capabilities:**

```powershell
# Check if running as Administrator
net session 2>nul && echo "Administrator" || echo "Standard User"

# Check Python version
python --version
```

### macOS

**Requirements:**

- Python 3.8+
- macOS 10.15+ (Catalina)
- `sudo` access for raw sockets

**Limitations:**

- BSD socket semantics (different from Linux)
- No `sendmmsg()` support
- Limited `sysctl` tuning options

**Commands to check capabilities:**

```bash
# Check macOS version
sw_vers

# Check if SIP allows network modifications
csrutil status
```

## Running Capability Check

To see what capabilities are available on your system:

```bash
# Basic capability check
python ddos.py --status

# Detailed capability report
python -c "
from core.capabilities.capability_report import CapabilityReport
report = CapabilityReport()
print(report.get_full_report())
"

# Check specific features
python -c "
import platform, os, socket
print(f'Platform: {platform.system()}')
print(f'Root/Admin: {os.geteuid() == 0 if hasattr(os, \"geteuid\") else \"Unknown\"}')
print(f'Raw sockets: {hasattr(socket, \"IPPROTO_RAW\")}')
print(f'sendfile: {hasattr(os, \"sendfile\")}')
"
```

## Conclusion

NetStress is a useful tool for learning and basic testing, but it has real limitations. This document aims to set honest expectations so you can choose the right tool for your needs.

For high-performance network testing, consider the professional tools mentioned above.
