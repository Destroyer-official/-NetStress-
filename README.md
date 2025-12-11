# NetStress

A Python-based network stress testing tool for authorized security research and performance testing.

## Legal Notice

**⚠️ AUTHORIZED USE ONLY ⚠️**

This tool is for authorized security testing and performance evaluation only. You must have explicit written permission to test any target system. Unauthorized use against systems you do not own or have permission to test is illegal and may violate:

- Computer Fraud and Abuse Act (CFAA)
- Local cybersecurity laws
- Terms of service agreements

**Use responsibly. The authors assume no liability for misuse.**

## What This Tool Actually Does

NetStress is a Python-based network stress testing framework that generates various types of network traffic to evaluate system performance and resilience. It uses standard operating system networking APIs and socket operations - no kernel bypass or specialized hardware acceleration.

## Honest Capabilities Assessment

### What This Tool ACTUALLY Does:

- ✅ Sends real UDP/TCP/HTTP packets using standard OS sockets
- ✅ Uses `sendfile()` and `MSG_ZEROCOPY` on Linux when available
- ✅ Uses `sendmmsg()` for batch UDP sending on Linux (with root)
- ✅ Applies real socket optimizations (SO_SNDBUF, TCP_NODELAY)
- ✅ Provides honest performance metrics from OS counters

### What This Tool Does NOT Do:

- ❌ **XDP/eBPF**: No kernel-level packet processing (use [xdp-tools](https://github.com/xdp-project/xdp-tools))
- ❌ **DPDK**: No kernel bypass networking (use [DPDK](https://www.dpdk.org/))
- ❌ **Hardware acceleration**: No specialized NIC features or SR-IOV
- ❌ **Multi-gigabit performance**: Limited by Python interpreter and OS network stack
- ❌ **Raw packet crafting**: Limited raw socket support (requires root/admin)
- ❌ **Advanced evasion**: No sophisticated traffic shaping or protocol obfuscation
- ❌ **Distributed attacks**: Single-machine only, no botnet coordination
- ❌ **Real-time guarantees**: Subject to Python GIL and OS scheduling

### Realistic Performance Expectations:

| Platform     | UDP PPS   | TCP Conn/sec | Bandwidth |
| ------------ | --------- | ------------ | --------- |
| Linux (root) | 500K-2M   | 10K-50K      | 1-10 Gbps |
| Linux (user) | 100K-500K | 5K-20K       | 500M-5G   |
| Windows      | 50K-200K  | 2K-10K       | 100M-2G   |
| macOS        | 100K-300K | 5K-15K       | 500M-3G   |

**Note:** These are realistic ranges. Localhost tests don't reflect real network performance.

For detailed capabilities, run: `python ddos.py --status`

## Features

- 15 attack protocols (TCP, UDP, HTTP, HTTPS, DNS, ICMP, etc.)
- Cross-platform support (Windows, Linux, macOS)
- Built-in safety controls
- Configurable parameters

## Quick Start

```bash
git clone https://github.com/Destroyer-official/-NetStress-.git
cd -NetStress-
pip install -r requirements.txt
python ddos.py --help
```

## Supported Protocols

| Protocol     | Type          | Description              |
| ------------ | ------------- | ------------------------ |
| TCP          | Flood         | TCP connection flood     |
| UDP          | Flood         | UDP packet flood         |
| HTTP         | Layer 7       | HTTP request flood       |
| HTTPS        | Layer 7       | HTTPS request flood      |
| DNS          | Query         | DNS query flood          |
| ICMP         | Echo          | ICMP echo flood          |
| SLOW         | Slowloris     | Slow HTTP attack         |
| TCP-SYN      | Raw packet    | SYN flag flood           |
| TCP-ACK      | Raw packet    | ACK flag flood           |
| PUSH-ACK     | Raw packet    | PUSH-ACK flood           |
| SYN-SPOOF    | Spoofed       | Spoofed SYN flood        |
| NTP          | Amplification | NTP reflection           |
| MEMCACHED    | Amplification | Memcached reflection     |
| WS-DISCOVERY | Amplification | WS-Discovery reflection  |
| QUANTUM      | Mixed         | Randomized payload flood |

## Usage

```bash
python ddos.py -i TARGET -p PORT -t PROTOCOL [OPTIONS]

Required:
  -i, --ip      Target IP or hostname
  -p, --port    Target port
  -t, --type    Protocol (TCP, UDP, HTTP, etc.)

Optional:
  -d, --duration    Duration in seconds (default: 60)
  -x, --threads     Worker threads (default: 4)
  -s, --size        Packet size in bytes (default: 1472)
  --status          Show system status
```

## Examples

```bash
# UDP flood
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 60

# HTTP flood
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -x 8 -d 60

# Check status
python ddos.py --status
```

## Requirements

- Python 3.8+
- Dependencies: `pip install -r requirements.txt`
- Admin/root for raw packet protocols (TCP-SYN, ICMP, etc.)

## Important Limitations

### Performance Constraints

- **Python Interpreter Overhead**: ~10-100x slower than equivalent C/C++ tools
- **Global Interpreter Lock (GIL)**: Limits CPU-bound parallelism to single core
- **Memory Management**: Garbage collection can cause periodic latency spikes
- **Standard Network Stack**: Uses OS sockets, not kernel bypass (DPDK/XDP)

### Testing Limitations

- **Localhost Deception**: Tests against 127.0.0.1 measure memory copy speed, not network performance
- **Single Machine**: Cannot simulate distributed attacks or realistic traffic patterns
- **Resource Bounded**: Limited by your machine's CPU, memory, and network interface
- **OS Dependent**: Performance varies significantly between Windows, Linux, and macOS

### Realistic Use Cases

✅ **Good for:**

- Educational purposes and learning network protocols
- Basic load testing of development servers
- Proof-of-concept security demonstrations
- Understanding network behavior under stress

❌ **Not suitable for:**

- Production-grade performance testing (use iperf3, wrk, or commercial tools)
- Realistic DDoS simulation (use distributed testing frameworks)
- High-throughput benchmarking (use compiled tools like hping3)
- Advanced penetration testing (use specialized security tools)

## Project Structure

```
NetStress/
├── ddos.py           # Main script
├── main.py           # Entry point
├── core/             # Core modules
├── config/           # Configuration
├── docs/             # Documentation
└── tests/            # Tests
```

## Safety Features

- Target validation
- Resource monitoring
- Emergency shutdown (Ctrl+C)
- Audit logging

## Documentation

- [Quick Start](docs/QUICK_START.md)
- [Usage Guide](docs/USAGE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## License

MIT License - see [LICENSE](LICENSE)

## Disclaimer

This is an educational tool for authorized testing only. The authors are not responsible for misuse. Users must comply with all applicable laws.
