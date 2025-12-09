"""
Simple test runner for autonomous optimization system tests
"""

import sys
import os
import asyncio
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_function(test_func, test_name):
    """Run a single test function"""
    try:
        if asyncio.iscoroutinefunction(test_func):
            asyncio.run(test_func())
        else:
            test_func()
        print(f"✓ {test_name} - PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} - FAILED: {str(e)}")
        traceback.print_exc()
        return False

def run_autonomous_tests():
    """Run autonomous optimization system tests"""
    
    print("Running Autonomous Configuration and Optimization System Tests")
    print("=" * 70)
    
    # Check if autonomous modules are available
    try:
        from core.autonomous.optimization_engine import QuantumOptimizationEngine, ParameterOptimizer
        from core.autonomous.performance_predictor import PerformancePredictionModel
        from core.autonomous.adaptation_system import RealTimeAdaptationSystem
        from core.autonomous.resource_manager import IntelligentResourceManager, LoadBalancer
        print("✓ All autonomous modules imported successfully")
        modules_available = True
    except ImportError as e:
        print(f"✗ Autonomous modules not available: {e}")
        modules_available = False
    
    if not modules_available:
        print("Skipping tests - autonomous modules not available")
        return
    
    passed_tests = 0
    total_tests = 0
    
    # Test 1: Quantum Optimization Engine
    print("\n--- Testing Quantum Optimization Engine ---")
    
    def test_quantum_engine_basic():
        from core.autonomous.optimization_engine import QuantumOptimizationEngine
        engine = QuantumOptimizationEngine(population_size=5, max_iterations=5)
        
        bounds = {'packet_rate': (100, 1000), 'packet_size': (64, 1500)}
        engine.initialize_quantum_population(bounds)
        
        assert len(engine.quantum_population) == 5
        
        # Test quantum state collapse
        individual = engine.quantum_population[0]
        params = engine.collapse_quantum_state(individual)
        
        assert 100 <= params.packet_rate <= 1000
        assert 64 <= params.packet_size <= 1500
    
    total_tests += 1
    if run_test_function(test_quantum_engine_basic, "Quantum Engine Basic Functionality"):
        passed_tests += 1
    
    # Test 2: Parameter Optimizer
    print("\n--- Testing Parameter Optimizer ---")
    
    def test_parameter_optimizer():
        from core.autonomous.optimization_engine import (
            ParameterOptimizer, OptimizationParameters, TargetResponse
        )
        
        optimizer = ParameterOptimizer()
        
        # Test effectiveness calculation
        response = TargetResponse(
            response_time=1.0,
            success_rate=0.8,
            error_rate=0.1,
            bandwidth_utilization=0.7,
            connection_success=0.9
        )
        
        metrics = {'pps': 5000}
        effectiveness = optimizer._calculate_effectiveness(response, metrics)
        
        assert 0.0 <= effectiveness <= 1.0
        assert effectiveness > 0.5  # Should be good with these metrics
    
    total_tests += 1
    if run_test_function(test_parameter_optimizer, "Parameter Optimizer"):
        passed_tests += 1
    
    # Test 3: Performance Prediction Model
    print("\n--- Testing Performance Prediction Model ---")
    
    async def test_performance_predictor():
        from core.autonomous.performance_predictor import (
            PerformancePredictionModel, TargetProfile
        )
        
        model = PerformancePredictionModel()
        
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
        
        prediction = await model.predict_performance(target_profile, attack_params)
        
        assert prediction.predicted_pps > 0
        assert 0.0 <= prediction.predicted_success_rate <= 1.0
        assert prediction.predicted_bandwidth > 0
        assert len(prediction.confidence_interval) == 2
    
    total_tests += 1
    if run_test_function(test_performance_predictor, "Performance Prediction Model"):
        passed_tests += 1
    
    # Test 4: Real-Time Adaptation System
    print("\n--- Testing Real-Time Adaptation System ---")
    
    def test_adaptation_system():
        from core.autonomous.adaptation_system import (
            RealTimeAdaptationSystem, FeedbackLoop, AdaptationEvent, 
            AdaptationTrigger, SystemState
        )
        
        # Test feedback loop
        target_metrics = {'success_rate': 0.8, 'packet_rate': 5000}
        feedback_loop = FeedbackLoop(target_metrics)
        
        current_metrics = {'success_rate': 0.6, 'packet_rate': 3000}
        control_signals = feedback_loop.update(current_metrics)
        
        assert 'success_rate' in control_signals
        assert 'packet_rate' in control_signals
        
        # Test adaptation system
        adaptation_system = RealTimeAdaptationSystem()
        
        # Test event generation
        metrics = {'success_rate': 0.3, 'error_rate': 0.4}
        state = SystemState(
            packet_rate=1000, success_rate=0.3, error_rate=0.4,
            bandwidth_utilization=0.5, cpu_usage=0.9, memory_usage=0.8,
            network_latency=0.1
        )
        
        # Add history
        for _ in range(5):
            adaptation_system.system_state_history.append(state)
        
        events = adaptation_system._analyze_for_adaptation_triggers(metrics, state)
        assert len(events) > 0
    
    total_tests += 1
    if run_test_function(test_adaptation_system, "Real-Time Adaptation System"):
        passed_tests += 1
    
    # Test 5: Resource Manager
    print("\n--- Testing Resource Manager ---")
    
    def test_resource_manager():
        from core.autonomous.resource_manager import (
            IntelligentResourceManager, LoadBalancer, ResourceType
        )
        
        # Test resource manager
        resource_manager = IntelligentResourceManager()
        
        # Test CPU allocation
        requirements = {'cores': 2, 'priority': 'high'}
        allocation = resource_manager._allocate_cpu_resources(requirements)
        
        assert 'allocated_cores' in allocation
        assert 'worker_id' in allocation
        
        # Test worker registration
        process_id = 12345
        worker_id = resource_manager.register_worker_process(
            process_id, [0, 1], 1024*1024*1024
        )
        
        assert worker_id.startswith("worker_")
        assert process_id in resource_manager.worker_processes
        
        # Test load balancer
        load_balancer = LoadBalancer()
        load_balancer.register_worker("worker1", capacity=100)
        load_balancer.register_worker("worker2", capacity=200)
        
        selected_worker = load_balancer.select_worker()
        assert selected_worker in ["worker1", "worker2"]
    
    total_tests += 1
    if run_test_function(test_resource_manager, "Resource Manager"):
        passed_tests += 1
    
    # Test 6: Integration Test
    print("\n--- Testing Integration Scenario ---")
    
    async def test_integration():
        from core.autonomous.optimization_engine import ParameterOptimizer, OptimizationParameters, TargetResponse
        from core.autonomous.adaptation_system import RealTimeAdaptationSystem, SystemState
        
        # Test parameter optimization
        optimizer = ParameterOptimizer()
        current_params = OptimizationParameters()
        target_response = TargetResponse(
            response_time=1.0, success_rate=0.6, error_rate=0.2,
            bandwidth_utilization=0.5, connection_success=0.6
        )
        
        optimized_params = await optimizer.optimize_parameters(
            current_params, target_response, {'pps': 1000}
        )
        
        assert isinstance(optimized_params, OptimizationParameters)
        
        # Test adaptation system initialization
        adaptation_system = RealTimeAdaptationSystem(adaptation_interval=0.1)
        
        callback_called = False
        def test_callback(params):
            nonlocal callback_called
            callback_called = True
        
        adaptation_system.register_adaptation_callback("test_action", test_callback)
        
        # Verify callback registration
        assert "test_action" in adaptation_system.adaptation_callbacks
    
    total_tests += 1
    if run_test_function(test_integration, "Integration Scenario"):
        passed_tests += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✓ All tests passed! Autonomous optimization system is working correctly.")
        return True
    else:
        print(f"✗ {total_tests - passed_tests} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_autonomous_tests()
    sys.exit(0 if success else 1)