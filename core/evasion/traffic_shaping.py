"""
Traffic Shaping Module

Implements sophisticated traffic shaping to evade rate-based detection:
- Burst patterns (mimic legitimate traffic bursts)
- Slow ramp-up (gradual increase to avoid threshold triggers)
- Random jitter (avoid predictable timing patterns)
- Legitimate traffic mimicry (match normal user patterns)
"""

import asyncio
import random
import time
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List, Dict, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ShapingProfile(Enum):
    """Pre-defined traffic shaping profiles"""
    AGGRESSIVE = "aggressive"      # Maximum rate, minimal shaping
    STEALTHY = "stealthy"          # Low rate, high randomization
    BURST = "burst"                # Periodic bursts with quiet periods
    GRADUAL = "gradual"            # Slow ramp-up over time
    MIMICRY = "mimicry"            # Mimic legitimate user traffic
    RANDOM = "random"              # Fully randomized timing
    PULSE = "pulse"                # On-off pattern
    SAWTOOTH = "sawtooth"          # Gradual increase, sudden drop


@dataclass
class ShapingConfig:
    """Configuration for traffic shaping"""
    profile: ShapingProfile = ShapingProfile.AGGRESSIVE
    base_rate: int = 1000                    # Base packets per second
    max_rate: int = 100000                   # Maximum packets per second
    min_rate: int = 10                       # Minimum packets per second
    jitter_percent: float = 0.2              # Random timing variation (0-1)
    burst_size: int = 100                    # Packets per burst
    burst_interval: float = 1.0              # Seconds between bursts
    ramp_duration: float = 60.0              # Seconds to reach max rate
    quiet_period: float = 0.5                # Seconds of quiet in pulse mode
    active_period: float = 2.0               # Seconds of activity in pulse mode


class TrafficShaper:
    """
    Advanced traffic shaper for evasion.
    
    Shapes outgoing traffic to evade detection systems that look for:
    - Constant high-rate traffic
    - Predictable timing patterns
    - Sudden traffic spikes
    """
    
    def __init__(self, config: Optional[ShapingConfig] = None):
        self.config = config or ShapingConfig()
        self.start_time = time.monotonic()
        self.packets_sent = 0
        self.current_rate = self.config.base_rate
        self._rate_history = deque(maxlen=100)
        self._last_send_time = 0.0
        self._burst_count = 0
        self._in_quiet_period = False
        self._quiet_until = 0.0
        
    def reset(self):
        """Reset shaper state"""
        self.start_time = time.monotonic()
        self.packets_sent = 0
        self.current_rate = self.config.base_rate
        self._rate_history.clear()
        self._last_send_time = 0.0
        self._burst_count = 0
        self._in_quiet_period = False
        self._quiet_until = 0.0
        
    def get_delay(self) -> float:
        """
        Calculate delay before next packet based on shaping profile.
        Returns delay in seconds.
        """
        now = time.monotonic()
        elapsed = now - self.start_time
        
        # Check quiet period for pulse mode
        if self._in_quiet_period and now < self._quiet_until:
            return self._quiet_until - now
        self._in_quiet_period = False
        
        # Calculate base delay from current rate
        if self.current_rate <= 0:
            self.current_rate = self.config.min_rate
        base_delay = 1.0 / self.current_rate
        
        # Apply profile-specific shaping
        if self.config.profile == ShapingProfile.AGGRESSIVE:
            delay = self._shape_aggressive(base_delay)
        elif self.config.profile == ShapingProfile.STEALTHY:
            delay = self._shape_stealthy(base_delay, elapsed)
        elif self.config.profile == ShapingProfile.BURST:
            delay = self._shape_burst(base_delay)
        elif self.config.profile == ShapingProfile.GRADUAL:
            delay = self._shape_gradual(base_delay, elapsed)
        elif self.config.profile == ShapingProfile.MIMICRY:
            delay = self._shape_mimicry(base_delay, elapsed)
        elif self.config.profile == ShapingProfile.RANDOM:
            delay = self._shape_random(base_delay)
        elif self.config.profile == ShapingProfile.PULSE:
            delay = self._shape_pulse(base_delay, elapsed)
        elif self.config.profile == ShapingProfile.SAWTOOTH:
            delay = self._shape_sawtooth(base_delay, elapsed)
        else:
            delay = base_delay
            
        # Apply jitter
        if self.config.jitter_percent > 0:
            jitter = delay * self.config.jitter_percent * (random.random() * 2 - 1)
            delay = max(0.0001, delay + jitter)
            
        self._last_send_time = now
        return delay
    
    def _shape_aggressive(self, base_delay: float) -> float:
        """Aggressive: Maximum rate with minimal delay"""
        self.current_rate = self.config.max_rate
        return 1.0 / self.config.max_rate
    
    def _shape_stealthy(self, base_delay: float, elapsed: float) -> float:
        """Stealthy: Low rate with high randomization"""
        # Use lower rate
        stealth_rate = min(self.config.base_rate, self.config.max_rate * 0.1)
        self.current_rate = stealth_rate
        
        # Add significant random delays
        extra_delay = random.expovariate(1.0 / 0.5)  # Exponential distribution
        return (1.0 / stealth_rate) + extra_delay
    
    def _shape_burst(self, base_delay: float) -> float:
        """Burst: Send packets in bursts with quiet periods"""
        self._burst_count += 1
        
        if self._burst_count >= self.config.burst_size:
            # End of burst - enter quiet period
            self._burst_count = 0
            self._in_quiet_period = True
            self._quiet_until = time.monotonic() + self.config.burst_interval
            return self.config.burst_interval
        
        # During burst - send fast
        self.current_rate = self.config.max_rate
        return 1.0 / self.config.max_rate
    
    def _shape_gradual(self, base_delay: float, elapsed: float) -> float:
        """Gradual: Slowly ramp up rate over time"""
        if elapsed >= self.config.ramp_duration:
            progress = 1.0
        else:
            # Smooth S-curve ramp
            progress = elapsed / self.config.ramp_duration
            progress = progress * progress * (3 - 2 * progress)  # Smoothstep
            
        rate_range = self.config.max_rate - self.config.min_rate
        self.current_rate = int(self.config.min_rate + rate_range * progress)
        return 1.0 / max(1, self.current_rate)
    
    def _shape_mimicry(self, base_delay: float, elapsed: float) -> float:
        """Mimicry: Simulate legitimate user traffic patterns"""
        # Simulate human browsing patterns
        # - Bursts of activity (page loads)
        # - Quiet periods (reading)
        # - Variable timing
        
        # Determine if in "active" or "reading" phase
        cycle_duration = 10.0  # 10 second cycles
        cycle_position = (elapsed % cycle_duration) / cycle_duration
        
        if cycle_position < 0.3:
            # Active phase - burst of requests
            self.current_rate = int(self.config.base_rate * 2)
            delay = 1.0 / self.current_rate
            # Add human-like micro-delays
            delay += random.uniform(0.01, 0.1)
        else:
            # Reading phase - occasional requests
            self.current_rate = int(self.config.base_rate * 0.1)
            delay = 1.0 / max(1, self.current_rate)
            # Add longer think-time delays
            delay += random.uniform(0.5, 2.0)
            
        return delay
    
    def _shape_random(self, base_delay: float) -> float:
        """Random: Fully randomized timing"""
        # Random rate between min and max
        self.current_rate = random.randint(self.config.min_rate, self.config.max_rate)
        base = 1.0 / self.current_rate
        
        # Add random delay component
        return base * random.uniform(0.5, 2.0)
    
    def _shape_pulse(self, base_delay: float, elapsed: float) -> float:
        """Pulse: On-off pattern"""
        cycle = self.config.active_period + self.config.quiet_period
        position = elapsed % cycle
        
        if position < self.config.active_period:
            # Active period
            self.current_rate = self.config.max_rate
            return 1.0 / self.config.max_rate
        else:
            # Quiet period
            self._in_quiet_period = True
            remaining = cycle - position
            self._quiet_until = time.monotonic() + remaining
            return remaining
    
    def _shape_sawtooth(self, base_delay: float, elapsed: float) -> float:
        """Sawtooth: Gradual increase, sudden drop"""
        cycle_duration = self.config.ramp_duration
        position = elapsed % cycle_duration
        progress = position / cycle_duration
        
        rate_range = self.config.max_rate - self.config.min_rate
        self.current_rate = int(self.config.min_rate + rate_range * progress)
        return 1.0 / max(1, self.current_rate)
    
    def record_send(self, packet_count: int = 1):
        """Record that packets were sent"""
        self.packets_sent += packet_count
        self._rate_history.append((time.monotonic(), packet_count))
        
    def get_actual_rate(self) -> float:
        """Calculate actual packets per second over recent history"""
        if len(self._rate_history) < 2:
            return 0.0
            
        oldest = self._rate_history[0]
        newest = self._rate_history[-1]
        duration = newest[0] - oldest[0]
        
        if duration <= 0:
            return 0.0
            
        total_packets = sum(p[1] for p in self._rate_history)
        return total_packets / duration
    
    def get_stats(self) -> Dict[str, Any]:
        """Get shaping statistics"""
        return {
            'profile': self.config.profile.value,
            'target_rate': self.current_rate,
            'actual_rate': self.get_actual_rate(),
            'packets_sent': self.packets_sent,
            'elapsed': time.monotonic() - self.start_time,
            'jitter_percent': self.config.jitter_percent,
        }


class AdaptiveShaper(TrafficShaper):
    """
    Adaptive traffic shaper that adjusts based on feedback.
    
    Monitors for signs of detection and automatically adjusts:
    - Reduces rate if errors increase
    - Increases randomization if patterns detected
    - Switches profiles based on effectiveness
    """
    
    def __init__(self, config: Optional[ShapingConfig] = None):
        super().__init__(config)
        self.error_count = 0
        self.success_count = 0
        self.detection_score = 0.0
        self._profile_history: List[ShapingProfile] = []
        
    def record_result(self, success: bool, detected: bool = False):
        """Record result of a send attempt"""
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            
        if detected:
            self.detection_score += 1.0
        else:
            self.detection_score = max(0, self.detection_score - 0.1)
            
        # Adapt if detection score is high
        if self.detection_score > 5.0:
            self._adapt_to_detection()
            
    def _adapt_to_detection(self):
        """Adapt shaping to avoid detection"""
        logger.info("Detection suspected - adapting traffic pattern")
        
        # Record current profile
        self._profile_history.append(self.config.profile)
        
        # Switch to more evasive profile
        evasive_profiles = [
            ShapingProfile.STEALTHY,
            ShapingProfile.MIMICRY,
            ShapingProfile.RANDOM,
        ]
        
        # Avoid recently used profiles
        available = [p for p in evasive_profiles if p not in self._profile_history[-3:]]
        if not available:
            available = evasive_profiles
            
        self.config.profile = random.choice(available)
        self.config.jitter_percent = min(0.5, self.config.jitter_percent + 0.1)
        self.config.max_rate = int(self.config.max_rate * 0.7)
        
        # Reset detection score
        self.detection_score = 0.0
        
        logger.info(f"Switched to profile: {self.config.profile.value}")


class AdvancedEvasionShaper(AdaptiveShaper):
    """
    Advanced evasion shaper with ML-inspired pattern generation.
    
    Features:
    - Markov chain-based timing patterns
    - Entropy-maximizing payload variations
    - Protocol-aware traffic mimicry
    - Real-time defense detection response
    """
    
    def __init__(self, config: Optional[ShapingConfig] = None):
        super().__init__(config)
        
        # Markov chain transition probabilities for timing
        self._timing_states = ['fast', 'medium', 'slow', 'pause']
        self._current_timing_state = 'medium'
        self._transition_matrix = {
            'fast': {'fast': 0.6, 'medium': 0.3, 'slow': 0.08, 'pause': 0.02},
            'medium': {'fast': 0.25, 'medium': 0.5, 'slow': 0.2, 'pause': 0.05},
            'slow': {'fast': 0.1, 'medium': 0.3, 'slow': 0.5, 'pause': 0.1},
            'pause': {'fast': 0.3, 'medium': 0.4, 'slow': 0.25, 'pause': 0.05},
        }
        
        # Defense detection state
        self._defense_signatures = {
            'rate_limit': {'error_burst': 0, 'last_seen': 0},
            'waf': {'blocked_count': 0, 'pattern_detected': False},
            'behavioral': {'anomaly_score': 0.0},
        }
        
        # Protocol mimicry patterns (based on real traffic analysis)
        self._browser_patterns = {
            'chrome': {'burst_size': (3, 8), 'think_time': (0.5, 3.0), 'parallel_conn': 6},
            'firefox': {'burst_size': (2, 6), 'think_time': (0.8, 4.0), 'parallel_conn': 4},
            'safari': {'burst_size': (2, 5), 'think_time': (1.0, 5.0), 'parallel_conn': 4},
            'mobile': {'burst_size': (1, 4), 'think_time': (2.0, 8.0), 'parallel_conn': 2},
        }
        self._current_browser = 'chrome'
        
    def get_delay(self) -> float:
        """Get delay using Markov chain timing model"""
        # Transition to next timing state
        self._transition_timing_state()
        
        # Get base delay from parent
        base_delay = super().get_delay()
        
        # Apply state-specific modifications
        state_multipliers = {
            'fast': 0.3,
            'medium': 1.0,
            'slow': 2.5,
            'pause': 10.0,
        }
        
        delay = base_delay * state_multipliers.get(self._current_timing_state, 1.0)
        
        # Add entropy-maximizing noise
        entropy_noise = self._generate_entropy_noise()
        delay *= (1.0 + entropy_noise)
        
        return max(0.0001, delay)
    
    def _transition_timing_state(self):
        """Transition to next timing state using Markov chain"""
        probs = self._transition_matrix[self._current_timing_state]
        r = random.random()
        cumulative = 0.0
        
        for state, prob in probs.items():
            cumulative += prob
            if r <= cumulative:
                self._current_timing_state = state
                break
    
    def _generate_entropy_noise(self) -> float:
        """Generate high-entropy noise to avoid pattern detection"""
        # Combine multiple random sources for higher entropy
        sources = [
            random.gauss(0, 0.1),  # Gaussian
            random.uniform(-0.1, 0.1),  # Uniform
            (random.random() ** 2 - 0.5) * 0.2,  # Quadratic
        ]
        
        # Mix sources with time-varying weights
        t = time.time() % 10.0
        weights = [
            math.sin(t * 0.5) * 0.5 + 0.5,
            math.cos(t * 0.7) * 0.5 + 0.5,
            math.sin(t * 1.1 + 1.0) * 0.5 + 0.5,
        ]
        
        total_weight = sum(weights)
        noise = sum(s * w for s, w in zip(sources, weights)) / total_weight
        
        return noise
    
    def mimic_browser(self, browser: str = 'chrome') -> Dict[str, Any]:
        """Get traffic pattern mimicking specific browser"""
        if browser not in self._browser_patterns:
            browser = 'chrome'
        
        self._current_browser = browser
        pattern = self._browser_patterns[browser]
        
        return {
            'burst_size': random.randint(*pattern['burst_size']),
            'think_time': random.uniform(*pattern['think_time']),
            'parallel_connections': pattern['parallel_conn'],
        }
    
    def detect_defense(self, response_code: int, response_time: float, 
                       error_message: str = '') -> str:
        """Detect type of defense based on response characteristics"""
        now = time.time()
        
        # Rate limiting detection
        if response_code == 429 or 'rate' in error_message.lower():
            self._defense_signatures['rate_limit']['error_burst'] += 1
            self._defense_signatures['rate_limit']['last_seen'] = now
            if self._defense_signatures['rate_limit']['error_burst'] > 3:
                return 'rate_limit'
        
        # WAF detection
        if response_code in (403, 406, 418) or any(
            sig in error_message.lower() 
            for sig in ['blocked', 'forbidden', 'waf', 'firewall', 'cloudflare', 'akamai']
        ):
            self._defense_signatures['waf']['blocked_count'] += 1
            if self._defense_signatures['waf']['blocked_count'] > 2:
                return 'waf'
        
        # Behavioral analysis detection (unusual response patterns)
        if response_time > 5.0 or response_code == 503:
            self._defense_signatures['behavioral']['anomaly_score'] += 0.5
            if self._defense_signatures['behavioral']['anomaly_score'] > 2.0:
                return 'behavioral'
        
        # Decay old signatures
        if now - self._defense_signatures['rate_limit']['last_seen'] > 10:
            self._defense_signatures['rate_limit']['error_burst'] = max(
                0, self._defense_signatures['rate_limit']['error_burst'] - 1
            )
        
        self._defense_signatures['behavioral']['anomaly_score'] *= 0.95
        
        return 'none'
    
    def evade_defense(self, defense_type: str):
        """Apply evasion strategy for detected defense"""
        logger.info(f"Evading {defense_type} defense")
        
        if defense_type == 'rate_limit':
            # Reduce rate and add more jitter
            self.config.max_rate = int(self.config.max_rate * 0.5)
            self.config.jitter_percent = min(0.8, self.config.jitter_percent + 0.2)
            self.config.profile = ShapingProfile.STEALTHY
            
        elif defense_type == 'waf':
            # Switch to mimicry mode with browser patterns
            self.config.profile = ShapingProfile.MIMICRY
            self._current_browser = random.choice(list(self._browser_patterns.keys()))
            
        elif defense_type == 'behavioral':
            # Maximize randomness
            self.config.profile = ShapingProfile.RANDOM
            self.config.jitter_percent = 0.5
            
        # Reset detection signatures
        self._defense_signatures[defense_type] = {
            'error_burst': 0, 'last_seen': 0, 'blocked_count': 0, 
            'pattern_detected': False, 'anomaly_score': 0.0
        }.get(defense_type, {})
