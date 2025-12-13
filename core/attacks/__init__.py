"""
Advanced Attack Vectors Module

Provides sophisticated attack methods beyond basic flooding:
- Amplification attacks (DNS, NTP, SSDP, Memcached, Chargen, SNMP)
- Layer 7 intelligent attacks (HTTP Flood, Slowloris, Slow POST, Smuggling)
- Connection-level attacks (SYN, ACK, RST, FIN, XMAS floods)
- SSL/TLS attacks (Exhaustion, Renegotiation, Heartbleed)
- Protocol-specific attacks (DNS, SMTP, FTP, SSH, MySQL, Redis)
- Application attacks (WordPress, API, WebSocket, GraphQL)
- Payload generation (Polymorphic, Fuzzing, Protocol-specific)
- Attack orchestration (Multi-vector, Adaptive, Intelligent)
- Real-time adaptation (Response-based, Learning, Multi-strategy)
- Botnet simulation (Distributed coordination, C2 simulation)
- Attack chaining (Sequential, Parallel, Conditional flows)
- Steganography (LSB, Whitespace, Protocol header hiding)
- Timing attacks (Slow-rate, Slowloris advanced, Side-channel)
"""

from .amplification import (
    AmplificationAttack, DNSAmplification, NTPAmplification,
    SSDPAmplification, MemcachedAmplification, ChargenAmplification,
    SNMPAmplification
)
from .layer7 import (
    Layer7Attack, HTTPFlood, SlowlorisAttack, SlowPOST,
    RUDYAttack, HTTPSmuggling, CacheBypass
)
from .connection import (
    ConnectionExhaustion, SYNFlood, ACKFlood, RSTFlood,
    FINFlood, XMASFlood, NullScan, PushAckFlood, SYNACKFlood
)
from .ssl_attacks import (
    SSLExhaustion, SSLRenegotiation, HeartbleedTest, THCSSLDoS
)
from .protocol_specific import (
    DNSFlood, SMTPFlood, FTPBounce, SSHBruteforce,
    MySQLFlood, RedisFlood
)
from .application import (
    WordPressAttack, APIFlood, WebSocketFlood, GraphQLAttack
)
from .payload_generator import (
    PayloadGenerator, PayloadFactory, PayloadType, PayloadConfig,
    RandomPayload, PatternPayload, PolymorphicPayload,
    FuzzingPayload, ProtocolPayload, EvasionPayload
)
from .orchestrator import (
    AttackOrchestrator, MultiTargetOrchestrator,
    AttackConfig, AttackPhase, AttackVector
)
from .adaptive import (
    AdaptiveController, AdaptiveAttackEngine, AdaptiveConfig,
    AdaptationStrategy, TargetState, ResponseAnalyzer,
    PatternLearner, MultiStrategyAdapter
)
from .botnet_sim import (
    BotState, CommandType, BotConfig, Command, SimulatedBot,
    BotnetController, HierarchicalBotnet, AttackWave
)
from .attack_chains import (
    ChainResult, AttackStage, ChainConfig, AttackStep, StepResult,
    AttackExecutor, SimulatedExecutor, AttackChain, ParallelChain,
    ConditionalChain, EscalationChain, ChainBuilder
)
from .steganography import (
    StegoMethod, StegoConfig, StegoEncoder, LSBEncoder,
    WhitespaceEncoder, UnicodeEncoder, ProtocolHeaderEncoder,
    TimingEncoder, StegoFactory, CovertChannel
)
from .timing_attacks import (
    TimingPattern, TimingConfig, TimingGenerator,
    SlowRateAttack, SlowlorisAdvanced, ResourceExhaustionTiming,
    SynchronizedTimingAttack, TimingSideChannel
)
from .mutation_engine import (
    MutationType, MutationConfig, Individual, FitnessFunction,
    EntropyFitness, UniqueFitness, SizeFitness, CompositeFitness,
    MutationOperator, CrossoverOperator, MutationEngine, AdaptiveMutationEngine
)
from .protocol_fuzzer import (
    FuzzStrategy, FuzzConfig, FuzzResult, CrashInfo,
    ProtocolGrammar, Mutator, ProtocolFuzzer,
    HTTPFuzzer, DNSFuzzer, TCPFuzzer, create_fuzzer
)
from .advanced_vectors import (
    AttackCategory, AttackWaveConfig, PayloadEngine, EvasionEngine,
    MultiVectorAttack, AdaptiveAttackController,
    ATTACK_PROFILES, get_attack_profile
)

__all__ = [
    # Amplification
    'AmplificationAttack', 'DNSAmplification', 'NTPAmplification',
    'SSDPAmplification', 'MemcachedAmplification', 'ChargenAmplification',
    'SNMPAmplification',
    # Layer 7
    'Layer7Attack', 'HTTPFlood', 'SlowlorisAttack', 'SlowPOST',
    'RUDYAttack', 'HTTPSmuggling', 'CacheBypass',
    # Connection
    'ConnectionExhaustion', 'SYNFlood', 'ACKFlood', 'RSTFlood',
    'FINFlood', 'XMASFlood', 'NullScan', 'PushAckFlood', 'SYNACKFlood',
    # SSL
    'SSLExhaustion', 'SSLRenegotiation', 'HeartbleedTest', 'THCSSLDoS',
    # Protocol-specific
    'DNSFlood', 'SMTPFlood', 'FTPBounce', 'SSHBruteforce',
    'MySQLFlood', 'RedisFlood',
    # Application
    'WordPressAttack', 'APIFlood', 'WebSocketFlood', 'GraphQLAttack',
    # Payload Generation
    'PayloadGenerator', 'PayloadFactory', 'PayloadType', 'PayloadConfig',
    'RandomPayload', 'PatternPayload', 'PolymorphicPayload',
    'FuzzingPayload', 'ProtocolPayload', 'EvasionPayload',
    # Orchestration
    'AttackOrchestrator', 'MultiTargetOrchestrator',
    'AttackConfig', 'AttackPhase', 'AttackVector',
    # Adaptive
    'AdaptiveController', 'AdaptiveAttackEngine', 'AdaptiveConfig',
    'AdaptationStrategy', 'TargetState', 'ResponseAnalyzer',
    'PatternLearner', 'MultiStrategyAdapter',
    # Botnet Simulation
    'BotState', 'CommandType', 'BotConfig', 'Command', 'SimulatedBot',
    'BotnetController', 'HierarchicalBotnet', 'AttackWave',
    # Attack Chains
    'ChainResult', 'AttackStage', 'ChainConfig', 'AttackStep', 'StepResult',
    'AttackExecutor', 'SimulatedExecutor', 'AttackChain', 'ParallelChain',
    'ConditionalChain', 'EscalationChain', 'ChainBuilder',
    # Steganography
    'StegoMethod', 'StegoConfig', 'StegoEncoder', 'LSBEncoder',
    'WhitespaceEncoder', 'UnicodeEncoder', 'ProtocolHeaderEncoder',
    'TimingEncoder', 'StegoFactory', 'CovertChannel',
    # Timing Attacks
    'TimingPattern', 'TimingConfig', 'TimingGenerator',
    'SlowRateAttack', 'SlowlorisAdvanced', 'ResourceExhaustionTiming',
    'SynchronizedTimingAttack', 'TimingSideChannel',
    # Mutation Engine
    'MutationType', 'MutationConfig', 'Individual', 'FitnessFunction',
    'EntropyFitness', 'UniqueFitness', 'SizeFitness', 'CompositeFitness',
    'MutationOperator', 'CrossoverOperator', 'MutationEngine', 'AdaptiveMutationEngine',
    # Protocol Fuzzer
    'FuzzStrategy', 'FuzzConfig', 'FuzzResult', 'CrashInfo',
    'ProtocolGrammar', 'Mutator', 'ProtocolFuzzer',
    'HTTPFuzzer', 'DNSFuzzer', 'TCPFuzzer', 'create_fuzzer',
    # Advanced Vectors
    'AttackCategory', 'AttackWaveConfig', 'PayloadEngine', 'EvasionEngine',
    'MultiVectorAttack', 'AdaptiveAttackController',
    'ATTACK_PROFILES', 'get_attack_profile',
]
