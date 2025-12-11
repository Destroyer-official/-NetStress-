# Frequently Asked Questions

## General

### What is NetStress?

A Python-based network stress testing tool for authorized security testing. It can generate various types of network traffic to test how systems handle load.

### Is this a high-performance tool?

No. This is a Python script with inherent performance limitations:

- Python's Global Interpreter Lock (GIL) limits parallelism
- Standard OS network stack (no kernel bypass)
- Interpreter overhead

For high-performance testing, use compiled tools like iperf3, hping3, or wrk.

### What throughput can I expect?

It depends on your hardware and network. Localhost tests show theoretical maximums but don't reflect real-world performance. On actual networks, expect significantly lower throughput than localhost tests suggest.

### Is this legal?

Using this tool on systems you own or have written permission to test is legal. Unauthorized use is illegal and may result in criminal charges.

## Installation

### What Python version do I need?

Python 3.8 or higher.

### What dependencies are required?

Core dependencies:

- psutil
- numpy
- aiohttp
- scapy
- faker

Install with: `pip install -r requirements.txt`

### Do I need admin/root access?

For basic protocols (UDP, TCP, HTTP): No
For raw packet protocols (TCP-SYN, ICMP): Yes

## Usage

### How do I run a basic test?

```bash
python ddos.py -i TARGET -p PORT -t PROTOCOL -d DURATION
```

### How do I stop a test?

Press Ctrl+C.

### Which protocol should I use?

| Goal                 | Protocol   |
| -------------------- | ---------- |
| Basic bandwidth test | UDP        |
| Web server test      | HTTP/HTTPS |
| Connection handling  | TCP        |
| DNS server test      | DNS        |

## Troubleshooting

### "Permission denied" error

Run as administrator (Windows) or with sudo (Linux/macOS) for raw packet protocols.

### "Module not found" error

```bash
pip install -r requirements.txt
```

### Low performance

This is expected for a Python-based tool. For higher performance, use compiled tools like iperf3 or hping3.

## Technical

### Does this use kernel bypass (XDP/DPDK)?

No. The code contains placeholder/simulation code for these features, but they are not actually implemented. The tool uses standard OS network sockets.

### Is the "AI optimization" real?

The tool includes parameter tuning algorithms, but calling it "AI" is an overstatement. It's basic heuristic optimization, not machine learning.

### Why is localhost performance different from real network?

Localhost testing bypasses the actual network interface. It only measures CPU/memory speed, not network performance.
