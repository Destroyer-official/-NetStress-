"""
Tests for Advanced Features

Tests for:
- Payload generation
- Attack orchestration
- Adaptive attacks
- Packet crafting
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestPayloadGenerator:
    """Tests for payload generation"""
    
    def test_random_payload(self):
        """Test random payload generation"""
        from core.attacks.payload_generator import RandomPayload, PayloadConfig
        
        config = PayloadConfig(min_size=64, max_size=128)
        generator = RandomPayload(config)
        
        payload = generator.generate()
        
        assert len(payload) >= 64
        assert len(payload) <= 128
        
    def test_pattern_payload(self):
        """Test pattern payload generation"""
        from core.attacks.payload_generator import PatternPayload, PayloadConfig
        
        config = PayloadConfig(min_size=100, max_size=200)
        generator = PatternPayload(config)
        
        payload = generator.generate()
        
        assert len(payload) >= 100
        assert len(payload) <= 200
        
    def test_polymorphic_payload(self):
        """Test polymorphic payload generation"""
        from core.attacks.payload_generator import PolymorphicPayload, PayloadConfig
        
        config = PayloadConfig(min_size=50, max_size=100, mutation_rate=0.2)
        generator = PolymorphicPayload(config)
        
        payloads = [generator.generate() for _ in range(10)]
        
        # Should generate different payloads
        unique = len(set(payloads))
        assert unique > 1
        
    def test_fuzzing_payload(self):
        """Test fuzzing payload generation"""
        from core.attacks.payload_generator import FuzzingPayload, PayloadConfig
        
        config = PayloadConfig()
        generator = FuzzingPayload(config, fuzz_type='overflow')
        
        payload = generator.generate()
        
        assert len(payload) > 0
        
    def test_protocol_payload_http(self):
        """Test HTTP protocol payload"""
        from core.attacks.payload_generator import ProtocolPayload, PayloadConfig
        
        config = PayloadConfig()
        generator = ProtocolPayload(config, protocol='http')
        
        payload = generator.generate()
        
        assert b'HTTP/1.1' in payload
        
    def test_protocol_payload_dns(self):
        """Test DNS protocol payload"""
        from core.attacks.payload_generator import ProtocolPayload, PayloadConfig
        
        config = PayloadConfig()
        generator = ProtocolPayload(config, protocol='dns')
        
        payload = generator.generate()
        
        assert len(payload) > 12  # DNS header size
        
    def test_evasion_payload(self):
        """Test evasion payload generation"""
        from core.attacks.payload_generator import EvasionPayload, PayloadConfig
        
        config = PayloadConfig(min_size=50, max_size=100)
        generator = EvasionPayload(config)
        
        payload = generator.generate()
        
        assert len(payload) > 0
        
    def test_payload_factory(self):
        """Test payload factory"""
        from core.attacks.payload_generator import PayloadFactory, PayloadType
        
        generator = PayloadFactory.create(PayloadType.RANDOM)
        payload = generator.generate()
        
        assert len(payload) > 0
        
    def test_payload_batch(self):
        """Test batch payload generation"""
        from core.attacks.payload_generator import RandomPayload, PayloadConfig
        
        config = PayloadConfig()
        generator = RandomPayload(config)
        
        payloads = generator.generate_batch(10)
        
        assert len(payloads) == 10


class TestAttackOrchestrator:
    """Tests for attack orchestration"""
    
    def test_attack_config(self):
        """Test attack configuration"""
        from core.attacks.orchestrator import AttackConfig, AttackVector
        
        config = AttackConfig(
            target='127.0.0.1',
            port=80,
            duration=60,
            vectors=[AttackVector.VOLUMETRIC, AttackVector.APPLICATION]
        )
        
        assert config.target == '127.0.0.1'
        assert len(config.vectors) == 2
        
    def test_attack_metrics(self):
        """Test attack metrics"""
        from core.attacks.orchestrator import AttackMetrics
        
        metrics = AttackMetrics()
        metrics.update(sent=100, received=90, errors=10)
        
        assert metrics.requests_sent == 100
        assert metrics.responses_received == 90
        assert metrics.errors == 10
        
    def test_target_analyzer(self):
        """Test target analyzer"""
        from core.attacks.orchestrator import TargetAnalyzer
        
        analyzer = TargetAnalyzer()
        
        # Record some responses
        for _ in range(10):
            analyzer.record_response(0.1, 200)
            
        health = analyzer.get_health_score()
        
        assert 0 <= health <= 1
        
    def test_orchestrator_init(self):
        """Test orchestrator initialization"""
        from core.attacks.orchestrator import AttackOrchestrator, AttackConfig
        
        config = AttackConfig(target='127.0.0.1', port=80)
        orchestrator = AttackOrchestrator(config)
        
        assert orchestrator.config.target == '127.0.0.1'


class TestAdaptiveAttacks:
    """Tests for adaptive attacks"""
    
    def test_adaptive_config(self):
        """Test adaptive configuration"""
        from core.attacks.adaptive import AdaptiveConfig, AdaptationStrategy
        
        config = AdaptiveConfig(
            strategy=AdaptationStrategy.BALANCED,
            min_rate=100,
            max_rate=10000
        )
        
        assert config.strategy == AdaptationStrategy.BALANCED
        assert config.min_rate == 100
        
    def test_response_analyzer(self):
        """Test response analyzer"""
        from core.attacks.adaptive import ResponseAnalyzer, ResponseMetrics, TargetState
        
        analyzer = ResponseAnalyzer()
        
        # Record healthy responses
        for _ in range(20):
            analyzer.record(ResponseMetrics(response_time=0.1))
            
        state = analyzer.get_state()
        
        assert state == TargetState.HEALTHY
        
    def test_response_analyzer_stressed(self):
        """Test response analyzer with stressed target"""
        from core.attacks.adaptive import ResponseAnalyzer, ResponseMetrics, TargetState
        
        analyzer = ResponseAnalyzer()
        analyzer.set_baseline(0.1)
        
        # Record slow responses
        for _ in range(20):
            analyzer.record(ResponseMetrics(response_time=0.5))
            
        state = analyzer.get_state()
        
        assert state in [TargetState.STRESSED, TargetState.DEGRADED]
        
    def test_adaptive_controller_init(self):
        """Test adaptive controller initialization"""
        from core.attacks.adaptive import AdaptiveController, AdaptiveConfig
        
        config = AdaptiveConfig()
        controller = AdaptiveController(config)
        
        assert controller.current_rate == config.min_rate
        
    def test_pattern_learner(self):
        """Test pattern learner"""
        from core.attacks.adaptive import PatternLearner
        
        learner = PatternLearner()
        
        # Record some data
        for rate in [1000, 2000, 3000]:
            for _ in range(5):
                learner.record_rate_impact(rate, rate / 5000)
                
        optimal = learner.get_optimal_rate()
        
        # Should recommend highest rate with best impact
        assert optimal is not None
        
    def test_multi_strategy_adapter(self):
        """Test multi-strategy adapter"""
        from core.attacks.adaptive import MultiStrategyAdapter, AdaptiveConfig, AdaptationStrategy
        
        config = AdaptiveConfig()
        adapter = MultiStrategyAdapter(config)
        
        strategy = adapter.select_strategy()
        
        assert strategy in AdaptationStrategy


class TestPacketCrafting:
    """Tests for packet crafting"""
    
    def test_ip_header(self):
        """Test IP header creation"""
        from core.networking.packet_craft import IPHeader
        
        header = IPHeader(
            src_addr='192.168.1.1',
            dst_addr='192.168.1.2',
            ttl=64
        )
        
        packed = header.pack()
        
        assert len(packed) == 20  # Standard IP header
        
    def test_tcp_header(self):
        """Test TCP header creation"""
        from core.networking.packet_craft import TCPHeader, TCPFlags
        
        header = TCPHeader(
            src_port=12345,
            dst_port=80,
            flags=TCPFlags.SYN.value
        )
        
        packed = header.pack('192.168.1.1', '192.168.1.2')
        
        assert len(packed) == 20  # Standard TCP header
        
    def test_udp_header(self):
        """Test UDP header creation"""
        from core.networking.packet_craft import UDPHeader
        
        header = UDPHeader(
            src_port=12345,
            dst_port=53
        )
        
        packed = header.pack('192.168.1.1', '192.168.1.2', b'test')
        
        assert len(packed) == 8  # UDP header size
        
    def test_icmp_header(self):
        """Test ICMP header creation"""
        from core.networking.packet_craft import ICMPHeader
        
        header = ICMPHeader(type=8, code=0)
        
        packed = header.pack(b'test payload')
        
        assert len(packed) == 8  # ICMP header size
        
    def test_packet_crafter_syn(self):
        """Test SYN packet crafting"""
        from core.networking.packet_craft import PacketCrafter
        
        crafter = PacketCrafter()
        
        packet = crafter.craft_tcp_syn(
            '192.168.1.1', '192.168.1.2', 12345, 80
        )
        
        assert len(packet) == 40  # IP + TCP headers
        
    def test_packet_crafter_udp(self):
        """Test UDP packet crafting"""
        from core.networking.packet_craft import PacketCrafter
        
        crafter = PacketCrafter()
        
        packet = crafter.craft_udp(
            '192.168.1.1', '192.168.1.2', 12345, 53, b'test'
        )
        
        assert len(packet) == 32  # IP + UDP + payload
        
    def test_ip_spoof_helper(self):
        """Test IP spoof helper"""
        from core.networking.packet_craft import IPSpoofHelper
        
        ip = IPSpoofHelper.random_ip()
        
        parts = ip.split('.')
        assert len(parts) == 4
        
    def test_port_helper(self):
        """Test port helper"""
        from core.networking.packet_craft import PortHelper
        
        port = PortHelper.random_port()
        
        assert 1024 <= port <= 65535
        
        ephemeral = PortHelper.random_ephemeral_port()
        
        assert 49152 <= ephemeral <= 65535
