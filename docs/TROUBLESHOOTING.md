# Troubleshooting Guide

## Common Issues

### Permission Denied

**Problem:** "Permission denied" or "Access denied" error.

**Solution:** Run as administrator.

Windows:

- Right-click Command Prompt → "Run as administrator"

Linux/macOS:

```bash
sudo python ddos.py -i TARGET -p PORT -t PROTOCOL
```

### Module Not Found

**Problem:** ImportError or ModuleNotFoundError.

**Solution:**

```bash
# Ensure virtual environment is active
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Low Performance

**Problem:** Throughput is lower than expected.

**Solutions:**

1. Increase packet size: `-s 8192`
2. Increase threads: `-x 32` or `-x 64`
3. Close other applications
4. Disable antivirus temporarily
5. Use UDP protocol for highest throughput

### Connection Refused

**Problem:** Target refuses connections.

**Causes:**

- Target is not running a service on that port
- Firewall is blocking connections
- Wrong IP or port

**Solution:** Verify target is accessible:

```bash
ping TARGET_IP
telnet TARGET_IP PORT
```

### WSAENOBUFS Error (Windows)

**Problem:** Socket buffer exhaustion.

**Solutions:**

1. Reduce thread count: `-x 4`
2. Add delay between packets
3. Restart the application

### Scapy Warnings

**Problem:** "No libpcap provider available" warning.

**Solution:** This is normal on Windows. Scapy will still work. To remove the warning, install Npcap from npcap.com.

### High CPU Usage

**Problem:** CPU usage is too high.

**Solution:** Reduce thread count:

```bash
python ddos.py -i TARGET -p PORT -t UDP -x 8
```

### Memory Issues

**Problem:** Out of memory errors.

**Solutions:**

1. Reduce thread count
2. Use smaller packet sizes
3. Close other applications

## Protocol-Specific Issues

### TCP Not Working

- Ensure target has a service listening on the port
- Try a different port (80, 443, 8080)

### HTTP/HTTPS Not Working

- Target must have a web server running
- Check if target responds: `curl http://TARGET:PORT`

### ICMP Not Working

- Requires administrator/root privileges
- Some networks block ICMP

### Raw Packet Protocols Not Working

TCP-SYN, TCP-ACK, PUSH-ACK, SYN-SPOOF require:

1. Administrator/root privileges
2. Scapy installed correctly
3. On Windows: Npcap installed

## Diagnostic Commands

### Check System Status

```bash
python ddos.py --status
```

### Verbose Output

```bash
python ddos.py -i TARGET -p PORT -t UDP -v
```

### Check Python Version

```bash
python --version
```

### Check Installed Packages

```bash
pip list
```

## Getting Help

1. Check this troubleshooting guide
2. Read the [FAQ](FAQ.md)
3. Search existing GitHub issues
4. Open a new issue with:
   - Error message
   - Command used
   - Operating system
   - Python version
