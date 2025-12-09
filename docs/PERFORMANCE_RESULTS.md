# Performance Results

Verified test results from December 2025.

## Test Environment

- OS: Windows 10/11
- CPU: 4 cores
- Target: localhost (127.0.0.1)
- Duration: 5 seconds per test

## UDP Flood Results

| Packet Size | Threads | Throughput | Packets/sec | Total Packets |
| ----------- | ------- | ---------- | ----------- | ------------- |
| 8192        | 32      | 16.03 Gbps | 244,630     | 2,177,498     |
| 8192        | 64      | 15.39 Gbps | 234,850     | 3,531,644     |
| 4096        | 32      | 8.40 Gbps  | 256,450     | 2,002,839     |
| 4096        | 64      | 8.28 Gbps  | 252,760     | 3,480,294     |
| 1472        | 64      | 2.60 Gbps  | 220,650     | 4,038,339     |
| 1472        | 32      | 2.10 Gbps  | 178,310     | 2,078,699     |
| 1472        | 16      | 1.58 Gbps  | 134,070     | 1,162,255     |

## QUANTUM Protocol Results

| Packet Size | Threads | Throughput | Packets/sec |
| ----------- | ------- | ---------- | ----------- |
| 4096        | 32      | 1.95 Gbps  | 59,440      |
| 1024        | 32      | 449 Mbps   | 54,890      |

## Amplification Protocol Results

| Protocol     | Throughput | Packets/sec | Total Packets |
| ------------ | ---------- | ----------- | ------------- |
| WS-DISCOVERY | 291 Mbps   | 260,510     | 1,389,744     |
| DNS          | 68 Mbps    | 268,470     | 1,517,045     |
| MEMCACHED    | 28 Mbps    | 235,060     | 1,346,556     |
| NTP          | 16 Mbps    | 250,970     | 1,333,364     |

## Summary

| Metric             | Value      |
| ------------------ | ---------- |
| Maximum throughput | 16.03 Gbps |
| Maximum PPS        | 268,470    |
| Total packets sent | 24,359,724 |
| Total data sent    | 81.45 GB   |

## Optimal Settings

For maximum throughput:

```bash
python ddos.py -i TARGET -p PORT -t UDP -s 8192 -x 32
```

For maximum packets per second:

```bash
python ddos.py -i TARGET -p 53 -t DNS -x 16
```

## Notes

1. Results may vary based on hardware and network conditions
2. Localhost testing eliminates network latency
3. Real network targets will have lower throughput due to network limits
4. Raw packet protocols require administrator privileges
