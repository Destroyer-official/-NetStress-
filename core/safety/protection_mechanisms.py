#!/usr/bin/env python3
"""
Safety and Protection Mechanisms
Implements comprehensive safety controls for the DDoS testing framework
"""

import os
import time
import socket
import psutil
import logging
import threading
import ipaddress
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ResourceLimits:
    """Resource usage limits for safety"""
    max_cpu_percent: float = 99.0  # Maximum CPU for stress testing
    max_memory_percent: float = 99.0  # Maximum memory for stress testing
    max_network_mbps: float = 90000.0  # 90 Gbps limit for high throughput
    max_connections: int = 900000  # High connection limit
    max_packets_per_second: int = 90000000  # 90M PPS limit
    max_duration_minutes: int = 360

@dataclass
class TargetInfo:
    """Information about attack target"""
    ip_address: str
    hostname: Optional[str]
    is_production: bool
    is_internal: bool
    risk_level: str  # 'low', 'medium', 'high', 'critical'

class TargetValidator:
    """Validates targets to prevent accidental production system attacks"""
    
    def __init__(self):
        self.production_indicators = {
            # Common production domain patterns
            'domains': [
                'amazonaws.com', 'azure.com', 'googlecloud.com',
                'cloudflare.com', 'fastly.com', 'akamai.com',
                'github.com', 'gitlab.com', 'bitbucket.com',
                'google.com', 'microsoft.com', 'apple.com',
                'facebook.com', 'twitter.com', 'linkedin.com'
            ],
            # Production IP ranges (examples - should be comprehensive)
            'ip_ranges': [
                '8.8.8.0/24',      # Google DNS
                '1.1.1.0/24',      # Cloudflare DNS
                '208.67.222.0/24', # OpenDNS
            ],
            # Common production ports
            'ports': [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
        }
        
        # Safe testing ranges (RFC 1918 private networks + test networks)
        self.safe_ranges = [
            '10.0.0.0/8',
            '172.16.0.0/12', 
            '192.168.0.0/16',
            '127.0.0.0/8',     # Loopback
            '169.254.0.0/16',  # Link-local
            '198.51.100.0/24', # TEST-NET-2
            '203.0.113.0/24',  # TEST-NET-3
        ]
        
        self.blocked_targets: Set[str] = set()
        self._load_blocked_targets()
    
    def _load_blocked_targets(self):
        """Load blocked targets from configuration file"""
        try:
            blocked_file = os.path.join(os.path.dirname(__file__), 'blocked_targets.txt')
            if os.path.exists(blocked_file):
                with open(blocked_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.blocked_targets.add(line)
        except Exception as e:
            logger.warning(f"Could not load blocked targets: {e}")
    
    def validate_target(self, target: str, port: int) -> Tuple[bool, str, TargetInfo]:
        """
        Validates if target is safe for testing
        Returns: (is_safe, reason, target_info)
        """
        try:
            # Resolve hostname to IP if needed
            ip_address = self._resolve_target(target)
            hostname = target if target != ip_address else None
            
            # Check if target is explicitly blocked
            if target in self.blocked_targets or ip_address in self.blocked_targets:
                return False, "Target is in blocked list", TargetInfo(
                    ip_address, hostname, True, False, 'critical'
                )
            
            # Check if target is in safe testing ranges
            is_safe_range = self._is_safe_ip_range(ip_address)
            if is_safe_range:
                return True, "Target is in safe testing range", TargetInfo(
                    ip_address, hostname, False, True, 'low'
                )
            
            # Check production indicators
            is_production = self._is_production_target(target, ip_address, port)
            is_internal = self._is_internal_network(ip_address)
            
            if is_production:
                risk_level = 'critical' if not is_internal else 'high'
                return False, "Target appears to be production system", TargetInfo(
                    ip_address, hostname, True, is_internal, risk_level
                )
            
            # Default to medium risk for external targets
            risk_level = 'medium' if not is_internal else 'low'
            return True, "Target validation passed", TargetInfo(
                ip_address, hostname, False, is_internal, risk_level
            )
            
        except Exception as e:
            logger.error(f"Target validation error: {e}")
            return False, f"Validation error: {e}", TargetInfo(
                target, None, True, False, 'critical'
            )
    
    def _resolve_target(self, target: str) -> str:
        """Resolve hostname to IP address"""
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            # If resolution fails, assume it's already an IP
            return target
    
    def _is_safe_ip_range(self, ip: str) -> bool:
        """Check if IP is in safe testing ranges"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for safe_range in self.safe_ranges:
                if ip_obj in ipaddress.ip_network(safe_range):
                    return True
            return False
        except ValueError:
            return False
    
    def _is_production_target(self, target: str, ip: str, port: int) -> bool:
        """Check if target has production indicators"""
        # Check domain patterns
        if any(domain in target.lower() for domain in self.production_indicators['domains']):
            return True
        
        # Check IP ranges
        try:
            ip_obj = ipaddress.ip_address(ip)
            for prod_range in self.production_indicators['ip_ranges']:
                if ip_obj in ipaddress.ip_network(prod_range):
                    return True
        except ValueError:
            pass
        
        # Check if it's a common production port
        if port in self.production_indicators['ports']:
            # Additional checks for production services
            if self._has_production_service(ip, port):
                return True
        
        return False
    
    def _is_internal_network(self, ip: str) -> bool:
        """Check if IP is in internal/private network"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            return False
    
    def _has_production_service(self, ip: str, port: int) -> bool:
        """Check if target has production service indicators"""
        try:
            # Quick connection test to see if service responds
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            # If service is running, it might be production
            return result == 0
        except Exception:
            return False

class ResourceMonitor:
    """Monitors system resources and enforces limits"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.monitoring = False
        self.start_time = None
        self.violation_count = 0
        self.max_violations = 5
        self._monitor_thread = None
        self._shutdown_callback = None
        
        # Resource tracking
        self.cpu_history = []
        self.memory_history = []
        self.network_history = []
        
    def start_monitoring(self, shutdown_callback=None):
        """Start resource monitoring"""
        self.monitoring = True
        self.start_time = time.time()
        self._shutdown_callback = shutdown_callback
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check duration limit - this is a hard limit, trigger immediately
                if self.start_time and self.limits.max_duration_minutes > 0:
                    elapsed_minutes = (time.time() - self.start_time) / 60
                    if elapsed_minutes > self.limits.max_duration_minutes:
                        logger.critical("Duration limit exceeded. Triggering emergency shutdown.")
                        if self._shutdown_callback:
                            self._shutdown_callback("Duration limit exceeded")
                        self.monitoring = False
                        break
                
                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_history.append((time.time(), cpu_percent))
                if cpu_percent > self.limits.max_cpu_percent:
                    self._handle_violation(f"CPU usage {cpu_percent:.1f}% exceeds limit {self.limits.max_cpu_percent}%")
                
                # Check memory usage
                memory = psutil.virtual_memory()
                self.memory_history.append((time.time(), memory.percent))
                if memory.percent > self.limits.max_memory_percent:
                    self._handle_violation(f"Memory usage {memory.percent:.1f}% exceeds limit {self.limits.max_memory_percent}%")
                
                # Check network usage
                network_stats = psutil.net_io_counters()
                if hasattr(self, '_last_network_stats'):
                    bytes_sent = network_stats.bytes_sent - self._last_network_stats.bytes_sent
                    mbps = (bytes_sent * 8) / (1024 * 1024)  # Convert to Mbps
                    self.network_history.append((time.time(), mbps))
                    
                    if mbps > self.limits.max_network_mbps:
                        self._handle_violation(f"Network usage {mbps:.1f} Mbps exceeds limit {self.limits.max_network_mbps} Mbps")
                
                self._last_network_stats = network_stats
                
                # Clean old history (keep last hour)
                cutoff_time = time.time() - 3600
                self.cpu_history = [(t, v) for t, v in self.cpu_history if t > cutoff_time]
                self.memory_history = [(t, v) for t, v in self.memory_history if t > cutoff_time]
                self.network_history = [(t, v) for t, v in self.network_history if t > cutoff_time]
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
            
            time.sleep(1)
    
    def _handle_violation(self, reason: str):
        """Handle resource limit violation"""
        self.violation_count += 1
        logger.warning(f"Resource violation #{self.violation_count}: {reason}")
        
        if self.violation_count >= self.max_violations:
            logger.critical(f"Maximum violations ({self.max_violations}) reached. Triggering emergency shutdown.")
            if self._shutdown_callback:
                self._shutdown_callback(f"Resource violations: {reason}")
            self.monitoring = False
    
    def get_current_usage(self) -> Dict:
        """Get current resource usage"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            network_stats = psutil.net_io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'network_bytes_sent': network_stats.bytes_sent,
                'network_bytes_recv': network_stats.bytes_recv,
                'violation_count': self.violation_count,
                'monitoring_duration': time.time() - self.start_time if self.start_time else 0
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {}

class SafetyManager:
    """Main safety management coordinator"""
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.target_validator = TargetValidator()
        self.resource_monitor = ResourceMonitor(self.limits)
        self.active_attacks = {}
        self.safety_enabled = True
        self.emergency_shutdown_triggered = False
        
        # Safety callbacks
        self._pre_attack_callbacks = []
        self._post_attack_callbacks = []
        self._shutdown_callbacks = []
    
    def register_pre_attack_callback(self, callback):
        """Register callback to run before attack starts"""
        self._pre_attack_callbacks.append(callback)
    
    def register_post_attack_callback(self, callback):
        """Register callback to run after attack ends"""
        self._post_attack_callbacks.append(callback)
    
    def register_shutdown_callback(self, callback):
        """Register callback for emergency shutdown"""
        self._shutdown_callbacks.append(callback)
    
    def validate_attack_request(self, target: str, port: int, protocol: str, 
                              duration: int = 0) -> Tuple[bool, str]:
        """Validate attack request for safety"""
        if not self.safety_enabled:
            return True, "Safety checks disabled"
        
        # Validate target
        is_safe, reason, target_info = self.target_validator.validate_target(target, port)
        if not is_safe:
            logger.error(f"Attack blocked: {reason}")
            return False, reason
        
        # Check if attack duration is reasonable
        if duration > self.limits.max_duration_minutes * 60:
            return False, f"Attack duration {duration}s exceeds limit {self.limits.max_duration_minutes * 60}s"
        
        # Run pre-attack callbacks
        for callback in self._pre_attack_callbacks:
            try:
                callback_result = callback(target, port, protocol, duration)
                if not callback_result:
                    return False, "Pre-attack callback rejected request"
            except Exception as e:
                logger.error(f"Pre-attack callback error: {e}")
                return False, f"Pre-attack callback error: {e}"
        
        return True, "Attack request validated"
    
    def start_attack_monitoring(self, attack_id: str, target: str, port: int):
        """Start monitoring for an attack"""
        if not self.safety_enabled:
            return
        
        self.active_attacks[attack_id] = {
            'target': target,
            'port': port,
            'start_time': time.time(),
            'status': 'active'
        }
        
        # Start resource monitoring if not already running
        if not self.resource_monitor.monitoring:
            self.resource_monitor.start_monitoring(self.emergency_shutdown)
        
        logger.info(f"Started monitoring attack {attack_id} on {target}:{port}")
    
    def stop_attack_monitoring(self, attack_id: str):
        """Stop monitoring for an attack"""
        if attack_id in self.active_attacks:
            attack_info = self.active_attacks[attack_id]
            attack_info['status'] = 'completed'
            attack_info['end_time'] = time.time()
            
            # Run post-attack callbacks
            for callback in self._post_attack_callbacks:
                try:
                    callback(attack_id, attack_info)
                except Exception as e:
                    logger.error(f"Post-attack callback error: {e}")
            
            del self.active_attacks[attack_id]
            logger.info(f"Stopped monitoring attack {attack_id}")
        
        # Stop resource monitoring if no active attacks
        if not self.active_attacks and self.resource_monitor.monitoring:
            self.resource_monitor.stop_monitoring()
    
    def emergency_shutdown(self, reason: str):
        """Trigger emergency shutdown of all attacks"""
        if self.emergency_shutdown_triggered:
            return
        
        self.emergency_shutdown_triggered = True
        logger.critical(f"EMERGENCY SHUTDOWN TRIGGERED: {reason}")
        
        # Stop all active attacks
        for attack_id in list(self.active_attacks.keys()):
            self.stop_attack_monitoring(attack_id)
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        
        # Run shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Shutdown callback error: {e}")
        
        logger.critical("Emergency shutdown completed")
    
    def get_safety_status(self) -> Dict:
        """Get current safety status"""
        return {
            'safety_enabled': self.safety_enabled,
            'emergency_shutdown_triggered': self.emergency_shutdown_triggered,
            'active_attacks': len(self.active_attacks),
            'resource_monitoring': self.resource_monitor.monitoring,
            'resource_violations': self.resource_monitor.violation_count,
            'current_usage': self.resource_monitor.get_current_usage()
        }
    
    def disable_safety(self, confirmation_code: str):
        """Disable safety checks (requires confirmation)"""
        expected_code = "DISABLE_SAFETY_CONTROLS_I_UNDERSTAND_THE_RISKS"
        if confirmation_code == expected_code:
            self.safety_enabled = False
            logger.warning("SAFETY CONTROLS DISABLED - USE WITH EXTREME CAUTION")
            return True
        else:
            logger.error("Invalid confirmation code for disabling safety")
            return False
    
    def enable_safety(self):
        """Re-enable safety checks"""
        self.safety_enabled = True
        self.emergency_shutdown_triggered = False
        logger.info("Safety controls re-enabled")