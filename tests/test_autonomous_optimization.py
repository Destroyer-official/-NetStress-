"""
Test suite for the Autonomous Configuration and Optimization System

Tests parameter optimization accuracy and effectiveness, real-time adaptation
and recovery mechanisms, and resource allocation and scaling capabilities.
"""

import asyncio
import pytest
import time
import random
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the autonomous system components
try:
    from core.autonomous.optimization_engine import (
        QuantumOptimizationEngine, ParameterOptimizer, 
        OptimizationParameters, TargetResponse, OptimizationResult
    )
    from core.autonomous.performance_predictor import (
        PerformancePredictionModel, EffectivenessPredictor, TargetProfile
    )
    from core.autonomous.adaptation_system import (
        RealTimeAdaptationSystem, FeedbackLoop, AdaptationEvent, 
        AdaptationTrigger, SystemState, AutoRecoverySystem
    )
    from core.autonomous.resource_manager import (
        IntelligentResourceManager, LoadBalancer, ResourceUsage, 
        ResourceLimits, ResourceType
    )
    AUTONOMOUS_AVAILABLE = True
except ImportError:
    AUTONOMOUS_AVAILABLE = False

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestQuantumOptimizationEngine:
    """Test quantum-inspired optimization algorithms"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = QuantumOptimizationEngine(population_size=10, max_iterations=20)
    
    def test_quantum_population_initialization(self):
        """Test quantum population initialization"""
        bounds = {
            'packet_rate': (100, 10000),
            'packet_size': (64, 1500),
            'concurrency': (10, 100)
        }
        
        self.engine.initialize_quantum_population(bounds)
        
        assert len(self.engine.quantum_population) == 10
        
        # Check that each individual has quantum states for all parameters
        for individual in self.engine.quantum_population:
            assert 'packet_rate' in individual
            assert 'packet_size' in individual
            assert 'concurrency' in individual
            
            # Check quantum state structure
            for param in individual:
                assert 'alpha' in individual[param]
                assert 'beta' in individual[param]
                assert 'min_val' in individual[param]
                assert 'max_val' in individual[param]
                
                # Check normalization
                alpha = individual[param]['alpha']
                beta = individual[param]['beta']
                norm = alpha**2 + beta**2
                assert abs(norm - 1.0) < 0.01  # Should be normalized
    
    def test_quantum_state_collapse(self):
        """Test quantum state collapse to classical parameters"""
        bounds = {
            'packet_rate': (1000, 5000),
            'packet_size': (500, 1000)
        }
        
        self.engine.initialize_quantum_population(bounds)
        individual = self.engine.quantum_population[0]
        
        # Collapse multiple times to check randomness
        collapsed_values = []
        for _ in range(10):
            params = self.engine.collapse_quantum_state(individual)
            collapsed_values.append(params.packet_rate)
            
            # Check bounds
            assert 1000 <= params.packet_rate <= 5000
            assert 500 <= params.packet_size <= 1000
        
        # Should have some variation due to quantum noise
        assert len(set(collapsed_values)) > 1
    
    @pytest.mark.asyncio
    async def test_quantum_optimization(self):
        """Test complete quantum optimization process"""
        bounds = {
            'packet_rate': (100, 1000),
            'packet_size': (64, 1500)
        }
        
        # Mock fitness function that prefers higher packet rates
        async def mock_fitness(params: OptimizationParameters) -> float:
            return params.packet_rate / 1000.0 + random.uniform(-0.1, 0.1)
        
        result = await self.engine.optimize(mock_fitness, bounds)
        
        assert isinstance(result, OptimizationResult)
        assert result.parameters is not None
        # Effectiveness can slightly exceed 1.0 due to random noise in fitness function
        assert 0.0 <= result.predicted_effectiveness <= 1.5
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.optimization_method == "quantum_inspired"
        
        # Should find parameters with relatively high packet rate
        assert result.parameters.packet_rate > 500

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestParameterOptimizer:
    """Test dynamic parameter optimization"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.optimizer = ParameterOptimizer(learning_rate=0.2, momentum=0.8)
    
    @pytest.mark.asyncio
    async def test_parameter_optimization_poor_performance(self):
        """Test optimization with poor performance (should use quantum optimization)"""
        current_params = OptimizationParameters(
            packet_rate=1000,
            packet_size=1000,
            concurrency=50
        )
        
        target_response = TargetResponse(
            response_time=5.0,
            success_rate=0.2,  # Poor success rate
            error_rate=0.3,
            bandwidth_utilization=0.1,
            connection_success=0.1
        )
        
        performance_metrics = {'pps': 500}
        
        optimized_params = await self.optimizer.optimize_parameters(
            current_params, target_response, performance_metrics
        )
        
        assert isinstance(optimized_params, OptimizationParameters)
        # Parameters should be different from original
        assert (optimized_params.packet_rate != current_params.packet_rate or
                optimized_params.packet_size != current_params.packet_size)
    
    def test_effectiveness_calculation(self):
        """Test effectiveness score calculation"""
        response = TargetResponse(
            response_time=1.0,
            success_rate=0.8,
            error_rate=0.1,
            bandwidth_utilization=0.7,
            connection_success=0.9
        )
        
        metrics = {'pps': 5000}
        
        effectiveness = self.optimizer._calculate_effectiveness(response, metrics)
        
        assert 0.0 <= effectiveness <= 1.0
        assert effectiveness > 0.5  # Should be good with these metrics
    
    def test_gradient_optimization(self):
        """Test gradient-based optimization"""
        # Add some history
        params1 = OptimizationParameters(packet_rate=1000, packet_size=1000)
        params2 = OptimizationParameters(packet_rate=1200, packet_size=1000)
        
        response1 = TargetResponse(response_time=1.0, success_rate=0.6, 
                                 error_rate=0.2, bandwidth_utilization=0.5, 
                                 connection_success=0.6)
        response2 = TargetResponse(response_time=1.0, success_rate=0.8, 
                                 error_rate=0.1, bandwidth_utilization=0.7, 
                                 connection_success=0.8)
        
        self.optimizer.parameter_history.extend([params1, params2])
        self.optimizer.response_history.extend([response1, response2])
        
        # Test gradient optimization
        optimized_params = self.optimizer._gradient_optimization(params2, response2)
        
        assert isinstance(optimized_params, OptimizationParameters)
        # Should adjust based on positive gradient
        assert optimized_params.packet_rate >= params2.packet_rate
    
    def test_optimization_insights(self):
        """Test optimization insights generation"""
        # Add some history
        for i in range(5):
            response = TargetResponse(
                response_time=1.0 + i * 0.1,
                success_rate=0.5 + i * 0.1,
                error_rate=0.2 - i * 0.02,
                bandwidth_utilization=0.5 + i * 0.05,
                connection_success=0.6 + i * 0.05
            )
            self.optimizer.response_history.append(response)
        
        insights = self.optimizer.get_optimization_insights()
        
        assert insights['status'] == 'active'
        assert 'avg_success_rate' in insights
        assert 'trend_success_rate' in insights
        assert insights['trend_success_rate'] in ['improving', 'declining', 'stable']
        assert 'recommended_action' in insights

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestPerformancePredictionModel:
    """Test performance prediction and effectiveness modeling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.model = PerformancePredictionModel()
    
    def test_feature_extraction(self):
        """Test feature extraction from target profile and attack parameters"""
        target_profile = TargetProfile(
            ip_address="192.168.1.1",
            response_times=[0.1, 0.2, 0.15],
            bandwidth_capacity=1000.0,
            defense_mechanisms=['firewall', 'rate_limiting'],
            service_types=['http', 'ssh'],
            vulnerability_score=0.6
        )
        
        attack_params = {
            'packet_rate': 5000,
            'packet_size': 1200,
            'concurrency': 200,
            'burst_interval': 0.001
        }
        
        features = self.model.extract_features(target_profile, attack_params)
        
        assert len(features) == 10  # Expected number of features
        assert all(isinstance(f, (int, float)) for f in features)
        
        # Check feature ranges (normalized values)
        assert 0.0 <= features[0] <= 1.0  # vulnerability_score
        assert features[1] == 2  # defense_mechanisms count
        assert features[2] > 0  # avg response time
    
    @pytest.mark.asyncio
    async def test_performance_prediction(self):
        """Test performance prediction"""
        target_profile = TargetProfile(
            ip_address="192.168.1.1",
            vulnerability_score=0.7,
            defense_mechanisms=['firewall'],
            bandwidth_capacity=5000.0
        )
        
        attack_params = {
            'packet_rate': 10000,
            'packet_size': 1000,
            'concurrency': 100
        }
        
        prediction = await self.model.predict_performance(target_profile, attack_params)
        
        assert prediction.predicted_pps > 0
        assert 0.0 <= prediction.predicted_success_rate <= 1.0
        assert prediction.predicted_bandwidth > 0
        assert len(prediction.confidence_interval) == 2
        assert isinstance(prediction.risk_factors, list)
        assert isinstance(prediction.recommended_parameters, dict)
    
    def test_model_update(self):
        """Test model update with actual results"""
        target_profile = TargetProfile(ip_address="192.168.1.1")
        attack_params = {'packet_rate': 1000, 'packet_size': 1000}
        actual_results = {'pps': 800, 'success_rate': 0.7, 'bandwidth': 5000}
        
        initial_data_count = len(self.model.training_data)
        
        self.model.update_model(target_profile, attack_params, actual_results)
        
        assert len(self.model.training_data) == initial_data_count + 1

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestRealTimeAdaptationSystem:
    """Test real-time adaptation and feedback systems"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.adaptation_system = RealTimeAdaptationSystem(
            adaptation_interval=0.1,  # Fast for testing
            max_adaptations_per_minute=20
        )
    
    def test_feedback_loop(self):
        """Test PID feedback loop"""
        target_metrics = {'success_rate': 0.8, 'packet_rate': 5000}
        feedback_loop = FeedbackLoop(target_metrics)
        
        # Test with metrics below target
        current_metrics = {'success_rate': 0.6, 'packet_rate': 3000}
        control_signals = feedback_loop.update(current_metrics)
        
        assert 'success_rate' in control_signals
        assert 'packet_rate' in control_signals
        
        # Control signals should be positive (need to increase)
        assert control_signals['success_rate'] > 0
        assert control_signals['packet_rate'] > 0
    
    def test_adaptation_trigger_detection(self):
        """Test detection of adaptation triggers"""
        # Create system state with high error rate
        metrics = {'success_rate': 0.3, 'error_rate': 0.4}
        state = SystemState(
            packet_rate=1000,
            success_rate=0.3,
            error_rate=0.4,
            bandwidth_utilization=0.5,
            cpu_usage=0.9,  # High CPU usage
            memory_usage=0.8,
            network_latency=0.1
        )
        
        # Add some history
        for _ in range(5):
            self.adaptation_system.system_state_history.append(state)
        
        events = self.adaptation_system._analyze_for_adaptation_triggers(metrics, state)
        
        assert len(events) > 0
        
        # Should detect at least one issue (error rate or resource exhaustion)
        trigger_types = [event.trigger for event in events]
        # At minimum, error rate increase should be detected with 0.4 error rate
        assert AdaptationTrigger.ERROR_RATE_INCREASE in trigger_types or AdaptationTrigger.SUCCESS_RATE_DROP in trigger_types
    
    def test_adaptation_action_generation(self):
        """Test generation of adaptation actions"""
        event = AdaptationEvent(
            trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
            severity=0.8,
            metrics={'success_rate': 0.2}
        )
        
        actions = self.adaptation_system._generate_default_actions(event)
        
        assert len(actions) > 0
        assert all(hasattr(action, 'action_type') for action in actions)
        assert all(hasattr(action, 'priority') for action in actions)
        assert all(hasattr(action, 'estimated_impact') for action in actions)
    
    @pytest.mark.asyncio
    async def test_adaptation_callback_registration(self):
        """Test registration and execution of adaptation callbacks"""
        callback_called = False
        callback_params = None
        
        def test_callback(params):
            nonlocal callback_called, callback_params
            callback_called = True
            callback_params = params
        
        self.adaptation_system.register_adaptation_callback("test_action", test_callback)
        
        from core.autonomous.adaptation_system import AdaptationAction
        action = AdaptationAction(
            action_type="test_action",
            parameters={"test_param": "test_value"},
            priority=1,
            estimated_impact=0.5
        )
        
        await self.adaptation_system._execute_adaptation_action(action)
        
        assert callback_called
        assert callback_params == {"test_param": "test_value"}
    
    def test_adaptation_statistics(self):
        """Test adaptation statistics collection"""
        # Add some adaptation history
        for i in range(5):
            event = AdaptationEvent(
                trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
                severity=0.5 + i * 0.1
            )
            from core.autonomous.adaptation_system import AdaptationAction
            action = AdaptationAction(
                action_type="test_action",
                parameters={},
                priority=1,
                estimated_impact=0.6 + i * 0.05
            )
            
            self.adaptation_system.adaptation_history.append({
                'timestamp': time.time(),
                'event': event,
                'action': action
            })
        
        stats = self.adaptation_system.get_adaptation_statistics()
        
        assert stats['total_adaptations'] == 5
        assert 'adaptations_by_trigger' in stats
        assert 'avg_adaptation_effectiveness' in stats
        assert stats['system_responsive'] == False  # Not monitoring

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestAutoRecoverySystem:
    """Test automatic recovery and failover mechanisms"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.recovery_system = AutoRecoverySystem()
    
    def test_recovery_strategy_registration(self):
        """Test registration of recovery strategies"""
        def mock_strategy(context):
            return True
        
        self.recovery_system.register_recovery_strategy("test_failure", mock_strategy)
        
        assert "test_failure" in self.recovery_system.recovery_strategies
    
    @pytest.mark.asyncio
    async def test_critical_failure_handling(self):
        """Test handling of critical failures"""
        recovery_called = False
        
        def mock_recovery_strategy(context):
            nonlocal recovery_called
            recovery_called = True
            return True
        
        self.recovery_system.register_recovery_strategy("network_failure", mock_recovery_strategy)
        
        success = await self.recovery_system.handle_critical_failure(
            "network_failure", 
            {"error": "connection_lost"}
        )
        
        assert success
        assert recovery_called
        assert len(self.recovery_system.failure_history) == 1
    
    @pytest.mark.asyncio
    async def test_emergency_recovery(self):
        """Test emergency recovery procedures"""
        # Test with unregistered failure type (should trigger emergency recovery)
        success = await self.recovery_system.handle_critical_failure(
            "unknown_failure",
            {"error": "unknown_error"}
        )
        
        # Emergency recovery should attempt to handle it
        assert isinstance(success, bool)
        assert len(self.recovery_system.failure_history) == 1
    
    def test_backup_configuration_management(self):
        """Test backup configuration save and restore"""
        config = {"param1": "value1", "param2": "value2"}
        
        self.recovery_system.save_backup_configuration(config)
        
        restored_config = self.recovery_system.get_latest_backup_configuration()
        
        assert restored_config == config
        assert len(self.recovery_system.backup_configurations) == 1

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestIntelligentResourceManager:
    """Test intelligent resource allocation and management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.resource_manager = IntelligentResourceManager(
            monitoring_interval=0.1  # Fast for testing
        )
    
    @pytest.mark.asyncio
    async def test_resource_usage_collection(self):
        """Test resource usage data collection"""
        usage = await self.resource_manager._collect_resource_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert usage.cpu_percent >= 0
        assert usage.memory_percent >= 0
        assert usage.process_count >= 0
        assert usage.thread_count >= 0
    
    def test_cpu_resource_allocation(self):
        """Test CPU resource allocation"""
        requirements = {'cores': 2, 'priority': 'high'}
        
        allocation = self.resource_manager._allocate_cpu_resources(requirements)
        
        assert 'allocated_cores' in allocation
        assert 'worker_id' in allocation
        assert 'cpu_affinity' in allocation
        assert len(allocation['allocated_cores']) <= 2
    
    def test_memory_resource_allocation(self):
        """Test memory resource allocation"""
        requirements = {'memory_mb': 1024}
        
        allocation = self.resource_manager._allocate_memory_resources(requirements)
        
        assert 'allocated_memory_mb' in allocation
        assert 'memory_limit' in allocation
        assert allocation['allocated_memory_mb'] > 0
    
    def test_worker_process_registration(self):
        """Test worker process registration and management"""
        process_id = 12345
        cpu_affinity = [0, 1]
        memory_limit = 1024 * 1024 * 1024
        
        worker_id = self.resource_manager.register_worker_process(
            process_id, cpu_affinity, memory_limit
        )
        
        assert worker_id.startswith("worker_")
        assert process_id in self.resource_manager.worker_processes
        
        worker = self.resource_manager.worker_processes[process_id]
        assert worker.process_id == process_id
        assert worker.cpu_affinity == cpu_affinity
        assert worker.memory_limit == memory_limit
    
    def test_worker_heartbeat_update(self):
        """Test worker heartbeat and metrics update"""
        process_id = 12345
        self.resource_manager.register_worker_process(process_id, [0], 1024*1024*1024)
        
        initial_heartbeat = self.resource_manager.worker_processes[process_id].last_heartbeat
        
        time.sleep(0.01)  # Small delay
        self.resource_manager.update_worker_heartbeat(process_id, 0.5, 10)
        
        worker = self.resource_manager.worker_processes[process_id]
        assert worker.last_heartbeat > initial_heartbeat
        assert worker.current_load == 0.5
        assert worker.task_count == 10
    
    def test_resource_statistics(self):
        """Test resource statistics generation"""
        # Add some resource history
        usage = ResourceUsage(
            cpu_percent=50.0,
            memory_percent=40.0,
            memory_bytes=1024*1024*1024,
            network_bytes_sent=1000,
            network_bytes_recv=2000,
            disk_read_bytes=500,
            disk_write_bytes=300,
            process_count=10,
            thread_count=50
        )
        self.resource_manager.resource_history.append(usage)
        
        stats = self.resource_manager.get_resource_statistics()
        
        assert 'current_usage' in stats
        assert 'average_usage' in stats
        assert 'resource_limits' in stats
        assert 'worker_processes' in stats
        assert 'cpu_allocation' in stats

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestLoadBalancer:
    """Test load balancing across multiple cores and processes"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.load_balancer = LoadBalancer(balancing_strategy="round_robin")
    
    def test_worker_registration(self):
        """Test worker registration and unregistration"""
        self.load_balancer.register_worker("worker1", capacity=100, weight=1.0)
        self.load_balancer.register_worker("worker2", capacity=200, weight=2.0)
        
        assert "worker1" in self.load_balancer.workers
        assert "worker2" in self.load_balancer.workers
        assert self.load_balancer.workers["worker1"]["capacity"] == 100
        assert self.load_balancer.workers["worker2"]["weight"] == 2.0
        
        self.load_balancer.unregister_worker("worker1")
        assert "worker1" not in self.load_balancer.workers
    
    def test_round_robin_selection(self):
        """Test round-robin worker selection"""
        self.load_balancer.register_worker("worker1")
        self.load_balancer.register_worker("worker2")
        self.load_balancer.register_worker("worker3")
        
        selections = []
        for _ in range(6):
            worker = self.load_balancer.select_worker()
            selections.append(worker)
        
        # Should cycle through workers
        assert selections[0] == selections[3]
        assert selections[1] == selections[4]
        assert selections[2] == selections[5]
    
    def test_least_loaded_selection(self):
        """Test least-loaded worker selection"""
        self.load_balancer.balancing_strategy = "least_loaded"
        
        self.load_balancer.register_worker("worker1")
        self.load_balancer.register_worker("worker2")
        
        # Set different loads
        self.load_balancer.update_worker_load("worker1", 80)
        self.load_balancer.update_worker_load("worker2", 20)
        
        selected_worker = self.load_balancer.select_worker()
        assert selected_worker == "worker2"  # Should select less loaded worker
    
    def test_worker_health_management(self):
        """Test worker health status management"""
        self.load_balancer.register_worker("worker1")
        
        # Mark as unhealthy
        self.load_balancer.mark_worker_unhealthy("worker1")
        assert not self.load_balancer.workers["worker1"]["active"]
        
        # Should not select unhealthy worker
        selected_worker = self.load_balancer.select_worker()
        assert selected_worker is None
        
        # Mark as healthy again
        self.load_balancer.mark_worker_healthy("worker1")
        assert self.load_balancer.workers["worker1"]["active"]
        
        selected_worker = self.load_balancer.select_worker()
        assert selected_worker == "worker1"
    
    def test_load_balancer_statistics(self):
        """Test load balancer statistics"""
        self.load_balancer.register_worker("worker1", capacity=100, weight=1.0)
        self.load_balancer.register_worker("worker2", capacity=200, weight=2.0)
        self.load_balancer.update_worker_load("worker1", 50)
        self.load_balancer.update_worker_load("worker2", 80)
        
        stats = self.load_balancer.get_load_balancer_statistics()
        
        assert stats["strategy"] == "round_robin"
        assert stats["total_workers"] == 2
        assert stats["active_workers"] == 2
        assert stats["total_load"] == 130
        assert "worker_details" in stats

@pytest.mark.skipif(not AUTONOMOUS_AVAILABLE, reason="Autonomous system not available")
class TestIntegrationScenarios:
    """Integration tests for complete optimization system scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self):
        """Test complete optimization workflow from parameter optimization to adaptation"""
        
        # Initialize components
        optimizer = ParameterOptimizer()
        adaptation_system = RealTimeAdaptationSystem(adaptation_interval=0.1)
        resource_manager = IntelligentResourceManager(monitoring_interval=0.1)
        
        # Mock metrics and system state
        def get_mock_metrics():
            return {
                'success_rate': random.uniform(0.4, 0.9),
                'packet_rate': random.uniform(1000, 5000),
                'error_rate': random.uniform(0.0, 0.3),
                'bandwidth_utilization': random.uniform(0.3, 0.8)
            }
        
        def get_mock_system_state():
            return SystemState(
                packet_rate=random.uniform(1000, 5000),
                success_rate=random.uniform(0.4, 0.9),
                error_rate=random.uniform(0.0, 0.3),
                bandwidth_utilization=random.uniform(0.3, 0.8),
                cpu_usage=random.uniform(0.3, 0.9),
                memory_usage=random.uniform(0.3, 0.8),
                network_latency=random.uniform(0.05, 0.5)
            )
        
        # Test parameter optimization
        current_params = OptimizationParameters()
        target_response = TargetResponse(
            response_time=1.0,
            success_rate=0.6,
            error_rate=0.2,
            bandwidth_utilization=0.5,
            connection_success=0.6
        )
        
        optimized_params = await optimizer.optimize_parameters(
            current_params, target_response, get_mock_metrics()
        )
        
        assert isinstance(optimized_params, OptimizationParameters)
        
        # Test adaptation system with callbacks
        adaptation_triggered = False
        
        def adaptation_callback(params):
            nonlocal adaptation_triggered
            adaptation_triggered = True
        
        adaptation_system.register_adaptation_callback("reduce_packet_rate", adaptation_callback)
        
        # Simulate monitoring for a short time
        monitoring_task = asyncio.create_task(
            adaptation_system.start_monitoring(get_mock_metrics, get_mock_system_state)
        )
        
        await asyncio.sleep(0.5)  # Let it run for a bit
        adaptation_system.stop_monitoring()
        
        try:
            await asyncio.wait_for(monitoring_task, timeout=1.0)
        except asyncio.TimeoutError:
            pass
        
        # Check that system collected some data
        assert len(adaptation_system.system_state_history) > 0
    
    def test_performance_under_load(self):
        """Test system performance under simulated load"""
        
        # Test quantum optimization with larger population
        engine = QuantumOptimizationEngine(population_size=50, max_iterations=10)
        
        bounds = {
            'packet_rate': (100, 10000),
            'packet_size': (64, 1500),
            'concurrency': (10, 1000),
            'burst_interval': (0.0001, 0.1)
        }
        
        start_time = time.time()
        engine.initialize_quantum_population(bounds)
        
        # Perform multiple optimizations
        for _ in range(10):
            individual = engine.quantum_population[0]
            params = engine.collapse_quantum_state(individual)
            assert isinstance(params, OptimizationParameters)
        
        elapsed_time = time.time() - start_time
        
        # Should complete reasonably quickly
        assert elapsed_time < 5.0
        
        # Test resource manager with multiple workers
        resource_manager = IntelligentResourceManager()
        
        # Register multiple workers
        for i in range(10):
            process_id = 1000 + i
            resource_manager.register_worker_process(process_id, [i % 4], 1024*1024*512)
        
        assert len(resource_manager.worker_processes) == 10
        
        # Test load balancer with many workers
        load_balancer = LoadBalancer()
        
        for i in range(20):
            load_balancer.register_worker(f"worker_{i}", capacity=100)
        
        # Test selection performance
        start_time = time.time()
        for _ in range(1000):
            worker = load_balancer.select_worker()
            assert worker is not None
        
        elapsed_time = time.time() - start_time
        assert elapsed_time < 1.0  # Should be fast

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])