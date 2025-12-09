# Frequently Asked Questions

## General

### What is Destroyer-DoS?

A network stress testing tool for authorized security assessments. It supports 15 attack protocols and can achieve throughput up to 16 Gbps.

### Is this legal?

Using this tool on systems you own or have written permission to test is legal. Unauthorized use is illegal and may result in criminal charges.

### What platforms are supported?

Windows, Linux, and macOS. Some features require administrator privileges.

## Installation

### What Python version do I need?

Python 3.8 or higher.

### Do I need administrator access?

For basic protocols (UDP, TCP, HTTP), no. For raw packet protocols (TCP-SYN, ICMP), yes.

### What dependencies are required?

- psutil
- numpy
- aiohttp
- scapy
- faker

Install with: `pip install -r requirements.txt`

## Usage

### How do I start a basic test?

```bash
python ddos.py -i TARGET_IP -p 80 -t UDP -d 30
```

### How do I stop a test?

Press `Ctrl+C`.

### What's the fastest protocol?

UDP with large packets (8192 bytes) achieves the highest throughput.

### How many threads should I use?

- Low resource: 4-8 threads
- Normal: 16-32 threads
- Maximum: 32-64 threads

### What packet size should I use?

- 1472 bytes: MTU-optimized, good compatibility
- 4096 bytes: Balanced performance
- 8192 bytes: Maximum throughput

## Performance

### What throughput can I expect?

On localhost with 4 CPU cores:

- UDP 8192 bytes: ~16 Gbps
- UDP 4096 bytes: ~8 Gbps
- UDP 1472 bytes: ~2.6 Gbps

Real network targets will be limited by network bandwidth.

### Why is my throughput low?

1. Network bandwidth limits
2. Target server limits
3. Too few threads
4. Small packet size
5. Other applications using resources

### How do I maximize throughput?

```bash
python ddos.py -i TARGET -p PORT -t UDP -s 8192 -x 64
```

## Protocols

### Which protocol should I use?

| Goal                     | Protocol   |
| ------------------------ | ---------- |
| Maximum bandwidth        | UDP        |
| Test web server          | HTTP/HTTPS |
| Test connection handling | TCP        |
| Test DNS server          | DNS        |
| Exhaust connections      | SLOW       |

### What's the difference between TCP and TCP-SYN?

- TCP: Uses normal socket connections
- TCP-SYN: Sends raw SYN packets (requires admin)

### What are amplification attacks?

Attacks that use third-party servers to amplify traffic. NTP, DNS, Memcached, and WS-Discovery are amplification protocols.

## Troubleshooting

### "Permission denied" error

Run as administrator (Windows) or with sudo (Linux/macOS).

### "Module not found" error

```bash
pip install -r requirements.txt
```

### Low performance

Increase threads (`-x 32`) and packet size (`-s 8192`).

### Target not responding

Verify target is accessible and has a service running on the specified port.

## Safety

### Are there safety limits?

Yes. The framework includes:

- Resource monitoring
- Emergency shutdown (Ctrl+C)
- Audit logging

### Where are logs stored?

- Attack logs: `attack.log`
- Audit logs: `audit_logs/`

### Can I disable safety features?

Safety features are enabled by default and should not be disabled.
