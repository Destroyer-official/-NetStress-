# Audit System

Documentation for the audit logging and compliance features.

---

## Overview

The audit system tracks all framework activities for accountability and compliance.

---

## Components

### AuditLogger

Main logging interface.

```python
from core.safety.audit_logging import AuditLogger

logger = AuditLogger()
logger.log_attack_start(target, port, protocol, params)
logger.log_attack_end(stats)
logger.log_safety_violation(violation_type, details)
```

### SecureAuditLogger

Encrypted logging for sensitive data.

- AES-256 encryption
- SHA-256 integrity verification
- Tamper detection

### ComplianceReporter

Generates compliance reports.

```python
from core.safety.audit_logging import ComplianceReporter

reporter = ComplianceReporter()
report = reporter.generate_report(start_date, end_date)
reporter.export_json("compliance_report.json")
```

---

## Log Storage

### Database

Location: `audit_logs/audit.db`

Tables:

- `sessions` - Attack sessions
- `events` - Individual events
- `violations` - Safety violations
- `metrics` - Performance data

### Log Files

Location: `audit_logs/audit_YYYYMMDD.log`

Format:

```
2025-12-09 10:30:00 | INFO | Attack started | target=192.168.1.100 | protocol=UDP
2025-12-09 10:31:00 | INFO | Stats | pps=244630 | throughput=16.03Gbps
2025-12-09 10:32:00 | INFO | Attack ended | duration=60s | total_packets=14677800
```

---

## Logged Events

### Attack Events

- Attack start (target, port, protocol, parameters)
- Attack progress (periodic stats)
- Attack end (final statistics)

### Safety Events

- Target validation results
- Resource limit warnings
- Emergency shutdowns
- Safety bypasses

### System Events

- Framework startup/shutdown
- Configuration changes
- Errors and exceptions

---

## Retention

Default retention: 30 days

Configure in `config/production.conf`:

```ini
[audit]
retention_days = 30
max_log_size_mb = 100
compress_old_logs = true
```

---

## Compliance Reports

### Activity Report

Summary of all testing activity.

Contents:

- Total sessions
- Protocols used
- Targets tested
- Duration statistics

### Violation Report

Safety violations and warnings.

Contents:

- Violation types
- Frequency
- Resolution status

### Export Formats

- JSON
- CSV
- PDF (with additional dependencies)

---

## Best Practices

1. **Review logs regularly** - Check for unexpected activity
2. **Export before cleanup** - Save important logs before retention period
3. **Secure log access** - Restrict access to audit logs
4. **Monitor disk space** - Logs can grow large during intensive testing

---

## Files

| File                           | Purpose                     |
| ------------------------------ | --------------------------- |
| `core/safety/audit_logging.py` | Audit system implementation |
| `audit_logs/audit.db`          | SQLite database             |
| `audit_logs/audit_*.log`       | Daily log files             |
| `compliance_reports/`          | Generated reports           |

---

**Last Updated**: December 2025
