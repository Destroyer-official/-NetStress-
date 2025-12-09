# Installation Guide

## Requirements

- Python 3.8 or higher
- pip package manager
- Git
- 4 GB RAM minimum
- Administrator/root access (for some protocols)

## Quick Installation

```bash
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Detailed Installation

### Windows

1. Install Python 3.8+ from python.org
2. Open Command Prompt as Administrator
3. Run:

```cmd
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python ddos.py --status
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ddos.py --status
```

### macOS

```bash
brew install python3 git
git clone https://github.com/Destroyer-official/Destroyer-DoS.git
cd Destroyer-DoS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ddos.py --status
```

## Dependencies

The following packages are installed from requirements.txt:

| Package | Purpose                |
| ------- | ---------------------- |
| psutil  | System monitoring      |
| numpy   | Numerical operations   |
| aiohttp | Async HTTP client      |
| scapy   | Raw packet crafting    |
| faker   | Random data generation |

## Verification

After installation, verify all modules are available:

```bash
python ddos.py --status
```

Expected output:

```
=== Destroyer-DoS System Status ===
Safety Systems:    Available
AI/ML Systems:     Available
Autonomous:        Available
Analytics:         Available
Memory Management: Available
Performance:       Available
Platform:          Available
Target Intel:      Available
Testing:           Available
Integration:       Available
```

## Troubleshooting

### "Module not found" error

```bash
pip install -r requirements.txt
```

### Permission errors on Linux

```bash
sudo python ddos.py -i TARGET -p PORT -t ICMP
```

### Scapy warnings

The "No libpcap provider" warning is normal on Windows. Scapy will still work for most operations.

## Updating

```bash
cd Destroyer-DoS
git pull origin main
pip install -r requirements.txt --upgrade
```

## Uninstallation

```bash
deactivate  # Exit virtual environment
cd ..
rm -rf Destroyer-DoS  # Linux/macOS
# rmdir /s Destroyer-DoS  # Windows
```
