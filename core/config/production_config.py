"""
Production Configuration Management

Centralized configuration for production deployments.
Supports environment variables, config files, and runtime overrides.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SafetyConfig:
    """Safety and security configuration"""
    enable_target_validation: bool = True
    enable_rate_limiting: bool = True
    max_rate_pps: int = 10_000_000
    enable_resource_monitoring: bool = True
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 85.0
    enable_audit_logging: bool = True
    audit_log_path: str = "audit_logs"
    blocked_targets_file: str = "core/safety/blocked_targets.txt"
    require_authorization: bool = True
    emergency_shutdown_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Performance tuning configuration"""
    default_threads: int = 0  # 0 = auto-detect
    default_processes: int = 0  # 0 = auto-detect
    default_packet_size: int = 1472
    socket_buffer_size: int = 16 * 1024 * 1024
    batch_size: int = 64
    use_native_engine: bool = True
    use_zero_copy: bool = True
    use_sendmmsg: bool = True
    use_io_uring: bool = True
    cpu_affinity: bool = True
    numa_aware: bool = True


@dataclass
class NetworkConfig:
    """Network configuration"""
    default_timeout_ms: int = 5000
    connection_timeout_ms: int = 10000
    max_connections: int = 10000
    dns_timeout_ms: int = 3000
    retry_count: int = 3
    retry_delay_ms: int = 1000


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "netstress.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    console_output: bool = True
    json_format: bool = False


@dataclass
class ReportingConfig:
    """Reporting configuration"""
    enable_reports: bool = True
    report_dir: str = "reports"
    report_format: str = "json"  # json, html, markdown, text
    include_timestamps: bool = True
    include_system_info: bool = True
    real_time_stats_interval_ms: int = 1000


@dataclass
class ProductionConfig:
    """Main production configuration"""
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    
    # Environment
    environment: str = "production"  # development, staging, production
    debug_mode: bool = False
    dry_run: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductionConfig':
        """Create from dictionary"""
        config = cls()
        
        if 'safety' in data:
            config.safety = SafetyConfig(**data['safety'])
        if 'performance' in data:
            config.performance = PerformanceConfig(**data['performance'])
        if 'network' in data:
            config.network = NetworkConfig(**data['network'])
        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])
        if 'reporting' in data:
            config.reporting = ReportingConfig(**data['reporting'])
        
        config.environment = data.get('environment', config.environment)
        config.debug_mode = data.get('debug_mode', config.debug_mode)
        config.dry_run = data.get('dry_run', config.dry_run)
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProductionConfig':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_file(cls, filepath: str) -> 'ProductionConfig':
        """Load from config file"""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Config file not found: {filepath}, using defaults")
            return cls()
        
        with open(path, 'r') as f:
            if path.suffix == '.json':
                return cls.from_json(f.read())
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
    
    @classmethod
    def from_env(cls) -> 'ProductionConfig':
        """Load from environment variables"""
        config = cls()
        
        # Safety
        if os.getenv('NETSTRESS_MAX_RATE'):
            config.safety.max_rate_pps = int(os.getenv('NETSTRESS_MAX_RATE'))
        if os.getenv('NETSTRESS_AUDIT_LOG'):
            config.safety.audit_log_path = os.getenv('NETSTRESS_AUDIT_LOG')
        
        # Performance
        if os.getenv('NETSTRESS_THREADS'):
            config.performance.default_threads = int(os.getenv('NETSTRESS_THREADS'))
        if os.getenv('NETSTRESS_NATIVE_ENGINE'):
            config.performance.use_native_engine = os.getenv('NETSTRESS_NATIVE_ENGINE').lower() == 'true'
        
        # Logging
        if os.getenv('NETSTRESS_LOG_LEVEL'):
            config.logging.level = os.getenv('NETSTRESS_LOG_LEVEL')
        if os.getenv('NETSTRESS_LOG_FILE'):
            config.logging.file_path = os.getenv('NETSTRESS_LOG_FILE')
        
        # Environment
        if os.getenv('NETSTRESS_ENV'):
            config.environment = os.getenv('NETSTRESS_ENV')
        if os.getenv('NETSTRESS_DEBUG'):
            config.debug_mode = os.getenv('NETSTRESS_DEBUG').lower() == 'true'
        
        return config
    
    def save(self, filepath: str):
        """Save configuration to file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(self.to_json())
        
        logger.info(f"Configuration saved to {filepath}")
    
    def validate(self) -> List[str]:
        """Validate configuration, return list of errors"""
        errors = []
        
        if self.safety.max_rate_pps < 0:
            errors.append("max_rate_pps must be non-negative")
        
        if self.safety.max_cpu_percent < 0 or self.safety.max_cpu_percent > 100:
            errors.append("max_cpu_percent must be between 0 and 100")
        
        if self.safety.max_memory_percent < 0 or self.safety.max_memory_percent > 100:
            errors.append("max_memory_percent must be between 0 and 100")
        
        if self.performance.default_packet_size < 1 or self.performance.default_packet_size > 65535:
            errors.append("default_packet_size must be between 1 and 65535")
        
        if self.network.default_timeout_ms < 0:
            errors.append("default_timeout_ms must be non-negative")
        
        return errors


class ConfigManager:
    """Configuration manager singleton"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[ProductionConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_config(cls) -> ProductionConfig:
        """Get current configuration"""
        if cls._config is None:
            cls._config = ProductionConfig()
        return cls._config
    
    @classmethod
    def set_config(cls, config: ProductionConfig):
        """Set configuration"""
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {errors}")
        cls._config = config
    
    @classmethod
    def load_config(cls, filepath: Optional[str] = None) -> ProductionConfig:
        """Load configuration from file or environment"""
        if filepath:
            cls._config = ProductionConfig.from_file(filepath)
        else:
            # Try default locations
            default_paths = [
                'netstress.json',
                'config/netstress.json',
                os.path.expanduser('~/.netstress/config.json'),
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    cls._config = ProductionConfig.from_file(path)
                    logger.info(f"Loaded config from {path}")
                    break
            else:
                # Fall back to environment variables
                cls._config = ProductionConfig.from_env()
        
        return cls._config
    
    @classmethod
    def reset(cls):
        """Reset to default configuration"""
        cls._config = ProductionConfig()


# Convenience function
def get_config() -> ProductionConfig:
    """Get current configuration"""
    return ConfigManager.get_config()


def load_config(filepath: Optional[str] = None) -> ProductionConfig:
    """Load configuration"""
    return ConfigManager.load_config(filepath)


__all__ = [
    'SafetyConfig', 'PerformanceConfig', 'NetworkConfig',
    'LoggingConfig', 'ReportingConfig', 'ProductionConfig',
    'ConfigManager', 'get_config', 'load_config', 'LogLevel',
]
