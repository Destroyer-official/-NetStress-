"""
Anti-Detection Module

Advanced techniques to evade detection:
- IP rotation and proxy chains
- Traffic morphing
- Behavioral mimicry
- Fingerprint randomization
"""

from .proxy_chain import ProxyChain, ProxyRotator, SOCKSProxy, HTTPProxy
from .traffic_morph import TrafficMorpher, ProtocolMimicry, PayloadMutation
from .behavioral import BehavioralMimicry, HumanSimulator, SessionManager
from .fingerprint_random import FingerprintRandomizer, JA3Randomizer, HeaderRandomizer

__all__ = [
    'ProxyChain', 'ProxyRotator', 'SOCKSProxy', 'HTTPProxy',
    'TrafficMorpher', 'ProtocolMimicry', 'PayloadMutation',
    'BehavioralMimicry', 'HumanSimulator', 'SessionManager',
    'FingerprintRandomizer', 'JA3Randomizer', 'HeaderRandomizer',
]
