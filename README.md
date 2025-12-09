# Destroyer-DoS Framework

Network stress testing and security assessment tool for authorized penetration testing.

## Legal Notice

**This tool is for authorized security testing only.** You must have written permission to test any target system. Unauthorized use is illegal. The authors are not responsible for misuse.

## Features

- 15 attack protocols (TCP, UDP, HTTP, HTTPS, DNS, ICMP, Slowloris, and more)
- Verified performance up to 16 Gbps throughput
- Cross-platform support (Windows, Linux, macOS)
- Built-in safety controls and audit logging
- AI-assisted parameter optimization

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Verify installation
python ddos.py --status

# Run a test (authorized targets only)
python ddos.py -i TARGET_IP -p 80 -t UDP -d 30
```

## Supported Protocols

| Protocol     | Description                | Requirements     |
| ------------ | -------------------------- | ---------------- |
| TCP          | TCP connection flood       | None             |
| UDP          | UDP packet flood           | None             |
| HTTP         | HTTP request flood         | Web server       |
| HTTPS        | HTTPS request flood        | SSL web server   |
| DNS          | DNS query flood            | None             |
| ICMP         | ICMP echo flood            | Admin privileges |
| SLOW         | Slowloris attack           | Web server       |
| TCP-SYN      | Raw SYN packets            | Admin + Scapy    |
| TCP-ACK      | Raw ACK packets            | Admin + Scapy    |
| PUSH-ACK     | TCP with payload           | Admin + Scapy    |
| SYN-SPOOF    | Spoofed SYN flood          | Admin + Scapy    |
| NTP          | NTP amplification          | None             |
| MEMCACHED    | Memcached amplification    | None             |
| WS-DISCOVERY | WS-Discovery amplification | None             |
| QUANTUM      | High-entropy packets       | None             |

## Performance Results

Tested on Windows with 4 CPU cores:

| Configuration              | Throughput | Packets/sec |
| -------------------------- | ---------- | ----------- |
| UDP 8192 bytes, 32 threads | 16.03 Gbps | 244,630     |
| UDP 4096 bytes, 32 threads | 8.40 Gbps  | 256,450     |
| UDP 1472 bytes, 64 threads | 2.60 Gbps  | 220,650     |
| QUANTUM 4096 bytes         | 1.95 Gbps  | 59,440      |

## Command Reference

```
python ddos.py [OPTIONS]

Required:
  -i, --ip      Target IP or hostname
  -p, --port    Target port
  -t, --type    Protocol (TCP, UDP, HTTP, etc.)

Optional:
  -d, --duration    Duration in seconds (default: 60)
  -x, --threads     Worker threads (default: 4)
  -s, --size        Packet size in bytes (default: 1472)
  --ai-optimize     Enable adaptive optimization
  --status          Show system status
  -v, --verbose     Verbose output
```

## Examples

```bash
# Basic UDP flood
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 60

# High throughput UDP
python ddos.py -i 192.168.1.100 -p 80 -t UDP -s 8192 -x 32 -d 60

# HTTP flood
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -x 8 -d 60

# Slowloris
python ddos.py -i 192.168.1.100 -p 80 -t SLOW -x 500 -d 300

# Check system status
python ddos.py --status
```

## System Requirements

- Python 3.8 or higher
- 4 GB RAM minimum
- Administrator/root access for raw packet protocols
- Scapy library for TCP-SYN, TCP-ACK, PUSH-ACK, SYN-SPOOF

## Installation

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies

Core dependencies are listed in `requirements.txt`:

- psutil
- numpy
- aiohttp
- scapy
- faker

## Project Structure

```
Destroyer-DoS/
├── ddos.py                 # Main attack engine
├── main.py                 # Entry point
├── comprehensive_stress_test.py  # Test suite
├── core/                   # Core modules
│   ├── ai/                 # Optimization
│   ├── analytics/          # Metrics
│   ├── safety/             # Safety controls
│   └── ...
├── config/                 # Configuration files
├── docs/                   # Documentation
└── tests/                  # Test suite
```

## Safety Features

- Target validation
- Resource monitoring (CPU, memory limits)
- Emergency shutdown (Ctrl+C)
- Audit logging
- Environment detection

## Running Tests

```bash
# Run comprehensive test
python real_comprehensive_test.py

# Test specific protocol
python comprehensive_stress_test.py -t 127.0.0.1 -p 80 --protocol UDP --duration 10

# Test all protocols
python comprehensive_stress_test.py -t 127.0.0.1 -p 80 --all --duration 5
```

## Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Usage Guide](docs/USAGE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Performance Results](docs/PERFORMANCE_RESULTS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This software is provided for educational and authorized testing purposes only. Users are responsible for complying with all applicable laws. The authors disclaim all liability for misuse.
