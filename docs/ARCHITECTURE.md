# Architecture

System architecture of Destroyer-DoS Framework.

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Command Line Interface                │
├─────────────────────────────────────────────────────────┤
│                      Main Engine (ddos.py)               │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Safety  │   AI/ML  │ Analytics│ Platform │ Performance │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    Attack Protocols                      │
│  TCP │ UDP │ HTTP │ DNS │ ICMP │ SLOW │ QUANTUM │ ...   │
├─────────────────────────────────────────────────────────┤
│                    Network Layer                         │
│              Sockets │ Raw Packets │ Async I/O          │
└─────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Safety (core/safety/)

Controls and limits to prevent misuse.

- Target validation
- Resource monitoring
- Emergency shutdown
- Audit logging
- Environment detection

### 2. AI/ML (core/ai/)

Parameter optimization and adaptation.

- Attack pattern optimization
- Defense detection
- Performance prediction
- Adaptive strategies

### 3. Analytics (core/analytics/)

Metrics collection and reporting.

- Real-time metrics
- Performance tracking
- Visualization
- Predictive analytics

### 4. Autonomous (core/autonomous/)

Self-adapting systems.

- Parameter optimization
- Performance prediction
- Resource management
- Load balancing

### 5. Memory (core/memory/)

Memory management.

- Memory pools
- Packet buffers
- Lock-free data structures
- Garbage collection optimization

### 6. Performance (core/performance/)

System optimization.

- Kernel optimization
- Hardware acceleration
- Zero-copy operations
- Performance validation

### 7. Platform (core/platform/)

Cross-platform support.

- Platform detection
- Capability mapping
- Socket configuration
- OS-specific optimizations

### 8. Target (core/target/)

Target analysis.

- Target resolution
- Defense profiling
- Vulnerability scanning
- Attack surface analysis

### 9. Testing (core/testing/)

Testing utilities.

- Performance testing
- Benchmark suite
- Validation engine
- Test coordination

### 10. Integration (core/integration/)

External integrations.

- Framework integration
- Module coordination

## Data Flow

```
User Input
    │
    ▼
┌─────────────┐
│   CLI       │ Parse arguments
└─────────────┘
    │
    ▼
┌─────────────┐
│  Validation │ Check target, parameters
└─────────────┘
    │
    ▼
┌─────────────┐
│ Optimization│ AI parameter tuning
└─────────────┘
    │
    ▼
┌─────────────┐
│   Attack    │ Execute protocol
└─────────────┘
    │
    ▼
┌─────────────┐
│  Reporting  │ Statistics, logs
└─────────────┘
```

## Attack Execution

1. Parse command line arguments
2. Validate target and parameters
3. Initialize safety systems
4. Apply performance optimizations
5. Start statistics reporter
6. Start AI optimizer (if enabled)
7. Launch attack workers
8. Monitor and adapt
9. Generate final report
10. Cleanup and exit

## Threading Model

```
Main Thread
    │
    ├── Stats Reporter (async)
    │
    ├── AI Optimizer (async)
    │
    └── Attack Workers
        ├── Worker 1 (thread)
        ├── Worker 2 (thread)
        ├── Worker 3 (thread)
        └── Worker N (thread)
```

## Protocol Implementation

Each protocol follows this pattern:

```python
async def protocol_flood(target, port, packet_size):
    # 1. Create socket/connection
    # 2. Prepare payload
    # 3. Start sender threads
    # 4. Update statistics
    # 5. Handle errors
    # 6. Cleanup
```

## Configuration

Settings are loaded from:

1. Default constants in code
2. Configuration files (config/)
3. Command line arguments
4. Environment variables

Priority: CLI > Environment > Config > Defaults

## Logging

- Console: Real-time status
- attack.log: Detailed attack logs
- audit_logs/: Compliance audit trail

## Error Handling

- Graceful degradation
- Automatic retry with backoff
- Resource cleanup on exit
- Emergency shutdown on Ctrl+C
