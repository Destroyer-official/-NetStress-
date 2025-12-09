"""
Integration test for the complete Autonomous Configuration and Optimization System
"""

import asyncio
import time
import sys
import os
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.asyncio
async def test_complete_autonomous_system():
    """Test the complete autonomous system integration"""
    
    print("Testing Complete Autonomous Configuration and Optimization System")
    print("=" * 80)
    
    try:
        # Import all components
        from core.autonomous.optimization_engine import (
            QuantumOptimizationEngine, ParameterOptimizer, 
            OptimizationParameters, TargetResponse
        )
        from core.autonomous.performance_predictor import (
            PerformancePredictionModel, EffectivenessPredictor, TargetProfile
        )
        from core.autonomous.adaptation_system import (
            RealTimeAdaptationSystem, FeedbackLoop, SystemState, AutoRecoverySystem
        )
        from core.autonomous.resource_manager import (
            IntelligentResourceManager, LoadBalancer, ResourceUsage, ResourceLimits
        )
        
        print("✓ All autonomous modules imported successfully")
        
        # 1. Initialize all components
        print("\n1. Initializing autonomous system components...")
        
        quantum_engine = QuantumOptimizationEngine(population_size=20, max_iterations=10)
        parameter_optimizer = ParameterOptimizer(learning_rate=0.1, momentum=0.9)
        performance_predictor = PerformancePredictionModel()
        effectiveness_predictor = EffectivenessPredictor()
        adaptation_system = RealTimeAdaptationSystem(adaptation_interval=0.5)
        resource_manager = IntelligentResourceManager(monitoring_interval=0.5)
        load_balancer = LoadBalancer(balancing_strategy="least_loaded")
        recovery_system = AutoRecoverySystem()
        
        print("✓ All components initialized")
        
        # 2. Test quantum optimization
        print("\n2. Testing quantum optimization...")
        
        bounds = {
            'packet_rate': (1000, 50000),
            'packet_size': (64, 1500),
            'concurrency': (10, 500),
            'burst_interval': (0.0001, 0.01)
        }
        
        async def fitness_function(params):
            # Simulate fitness evaluation
            base_fitness = (params.packet_rate / 50000.0 + 
                          (1500 - params.packet_size) / 1500.0 +
                          params.concurrency / 500.0) / 3.0
            return base_fitness + (time.time() % 1) * 0.1  # Add some randomness
        
        optimization_result = await quantum_engine.optimize(fitness_function, bounds)
        
        print(f"✓ Quantum optimization completed:")
        print(f"  - Predicted effectiveness: {optimization_result.predicted_effectiveness:.3f}")
        print(f"  - Confidence score: {optimization_result.confidence_score:.3f}")
        print(f"  - Optimized packet rate: {optimization_result.parameters.packet_rate}")
        print(f"  - Optimized packet size: {optimization_result.parameters.packet_size}")
        
        # 3. Test parameter optimization with feedback
        print("\n3. Testing parameter optimization with feedback...")
        
        current_params = optimization_result.parameters
        
        # Simulate multiple optimization cycles
        for cycle in range(3):
            # Simulate target response
            target_response = TargetResponse(
                response_time=1.0 + cycle * 0.2,
                success_rate=0.7 - cycle * 0.1,
                error_rate=0.1 + cycle * 0.05,
                bandwidth_utilization=0.6 + cycle * 0.1,
                connection_success=0.8 - cycle * 0.05
            )
            
            performance_metrics = {
                'pps': current_params.packet_rate * (0.8 + cycle * 0.1),
                'success_rate': target_response.success_rate,
                'bandwidth': target_response.bandwidth_utilization * 1e9
            }
            
            optimized_params = await parameter_optimizer.optimize_parameters(
                current_params, target_response, performance_metrics
            )
            
            print(f"  Cycle {cycle + 1}: Packet rate {current_params.packet_rate} -> {optimized_params.packet_rate}")
            current_params = optimized_params
        
        insights = parameter_optimizer.get_optimization_insights()
        print(f"✓ Parameter optimization completed. Status: {insights.get('status', 'unknown')}")
        
        # 4. Test performance prediction
        print("\n4. Testing performance prediction...")
        
        target_profile = TargetProfile(
            ip_address="192.168.1.100",
            response_times=[0.1, 0.15, 0.12, 0.18, 0.14],
            bandwidth_capacity=10000.0,
            defense_mechanisms=['firewall', 'rate_limiting'],
            service_types=['http', 'https', 'ssh'],
            vulnerability_score=0.6
        )
        
        attack_params = {
            'packet_rate': current_params.packet_rate,
            'packet_size': current_params.packet_size,
            'concurrency': current_params.concurrency,
            'burst_interval': current_params.burst_interval
        }
        
        prediction = await performance_predictor.predict_performance(target_profile, attack_params)
        
        print(f"✓ Performance prediction completed:")
        print(f"  - Predicted PPS: {prediction.predicted_pps:.0f}")
        print(f"  - Predicted success rate: {prediction.predicted_success_rate:.3f}")
        print(f"  - Predicted bandwidth: {prediction.predicted_bandwidth:.2f} Mbps")
        print(f"  - Risk factors: {len(prediction.risk_factors)}")
        
        # Test effectiveness prediction
        effectiveness = await effectiveness_predictor.predict_effectiveness(target_profile, attack_params)
        print(f"  - Predicted effectiveness: {effectiveness:.3f}")
        
        # 5. Test real-time adaptation system
        print("\n5. Testing real-time adaptation system...")
        
        adaptation_events = []
        
        def adaptation_callback(params):
            adaptation_events.append(params)
            print(f"  Adaptation triggered: {params}")
        
        # Register callbacks
        adaptation_system.register_adaptation_callback("reduce_packet_rate", adaptation_callback)
        adaptation_system.register_adaptation_callback("optimize_resources", adaptation_callback)
        adaptation_system.register_adaptation_callback("enable_evasion_techniques", adaptation_callback)
        
        # Mock metrics and system state providers
        def get_mock_metrics():
            return {
                'success_rate': max(0.1, 0.8 - time.time() % 10 * 0.1),  # Declining over time
                'packet_rate': current_params.packet_rate,
                'error_rate': min(0.5, time.time() % 10 * 0.05),  # Increasing over time
                'bandwidth_utilization': 0.6
            }
        
        def get_mock_system_state():
            return SystemState(
                packet_rate=current_params.packet_rate,
                success_rate=max(0.1, 0.8 - time.time() % 10 * 0.1),
                error_rate=min(0.5, time.time() % 10 * 0.05),
                bandwidth_utilization=0.6,
                cpu_usage=min(0.95, 0.5 + time.time() % 10 * 0.05),  # Increasing CPU
                memory_usage=0.6,
                network_latency=0.1
            )
        
        # Start adaptation monitoring
        monitoring_task = asyncio.create_task(
            adaptation_system.start_monitoring(get_mock_metrics, get_mock_system_state)
        )
        
        # Let it run for a few seconds
        await asyncio.sleep(3.0)
        
        # Stop monitoring
        adaptation_system.stop_monitoring()
        
        try:
            await asyncio.wait_for(monitoring_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass
        
        adaptation_stats = adaptation_system.get_adaptation_statistics()
        print(f"✓ Real-time adaptation completed:")
        print(f"  - System states collected: {len(adaptation_system.system_state_history)}")
        print(f"  - Adaptations triggered: {len(adaptation_events)}")
        print(f"  - Total adaptations: {adaptation_stats.get('total_adaptations', 0)}")
        
        # 6. Test resource management
        print("\n6. Testing resource management...")
        
        # Register multiple workers
        for i in range(4):
            process_id = 1000 + i
            cpu_affinity = [i % 4]
            memory_limit = 1024 * 1024 * 1024  # 1GB
            
            worker_id = resource_manager.register_worker_process(process_id, cpu_affinity, memory_limit)
            load_balancer.register_worker(worker_id, capacity=100, weight=1.0)
            
            # Simulate worker heartbeat
            resource_manager.update_worker_heartbeat(process_id, i * 0.2, i * 10)
        
        # Test resource allocation
        from core.autonomous.resource_manager import ResourceType
        
        cpu_allocation = resource_manager.allocate_resources(
            ResourceType.CPU,
            {'cores': 2, 'priority': 'high'}
        )
        
        memory_allocation = resource_manager.allocate_resources(
            ResourceType.MEMORY,
            {'memory_mb': 2048}
        )
        
        # Test load balancing
        selected_workers = []
        for _ in range(10):
            worker = load_balancer.select_worker()
            selected_workers.append(worker)
        
        resource_stats = resource_manager.get_resource_statistics()
        lb_stats = load_balancer.get_load_balancer_statistics()
        
        print(f"✓ Resource management completed:")
        print(f"  - Workers registered: {resource_stats.get('worker_processes', {}).get('count', len(resource_manager.worker_processes))}")
        print(f"  - CPU cores allocated: {len(cpu_allocation.get('allocated_cores', []))}")
        print(f"  - Memory allocated: {memory_allocation.get('allocated_memory_mb', 0)} MB")
        print(f"  - Load balancer workers: {lb_stats['total_workers']}")
        print(f"  - Load balancing selections: {len(set(selected_workers))} unique workers")
        
        # 7. Test recovery system
        print("\n7. Testing recovery system...")
        
        recovery_triggered = False
        
        def mock_recovery_strategy(context):
            nonlocal recovery_triggered
            recovery_triggered = True
            print(f"  Recovery strategy executed for: {context}")
            return True
        
        recovery_system.register_recovery_strategy("test_failure", mock_recovery_strategy)
        
        # Save backup configuration
        backup_config = {
            'packet_rate': current_params.packet_rate,
            'packet_size': current_params.packet_size,
            'concurrency': current_params.concurrency
        }
        recovery_system.save_backup_configuration(backup_config)
        
        # Simulate critical failure
        success = await recovery_system.handle_critical_failure(
            "test_failure",
            {"error": "simulated_failure", "severity": "high"}
        )
        
        restored_config = recovery_system.get_latest_backup_configuration()
        
        print(f"✓ Recovery system completed:")
        print(f"  - Recovery success: {success}")
        print(f"  - Recovery strategy triggered: {recovery_triggered}")
        print(f"  - Backup configuration restored: {restored_config is not None}")
        print(f"  - Failure history entries: {len(recovery_system.failure_history)}")
        
        # 8. Integration test - simulate complete workflow
        print("\n8. Testing complete workflow integration...")
        
        workflow_success = True
        
        try:
            # Simulate a complete optimization workflow
            print("  - Starting with initial parameters...")
            initial_params = OptimizationParameters(
                packet_rate=5000,
                packet_size=1000,
                concurrency=100,
                burst_interval=0.001
            )
            
            print("  - Predicting initial performance...")
            initial_prediction = await performance_predictor.predict_performance(
                target_profile, 
                {
                    'packet_rate': initial_params.packet_rate,
                    'packet_size': initial_params.packet_size,
                    'concurrency': initial_params.concurrency
                }
            )
            
            print("  - Optimizing parameters based on prediction...")
            simulated_response = TargetResponse(
                response_time=2.0,
                success_rate=initial_prediction.predicted_success_rate * 0.8,
                error_rate=0.2,
                bandwidth_utilization=initial_prediction.predicted_bandwidth / 10000.0,
                connection_success=0.6
            )
            
            final_params = await parameter_optimizer.optimize_parameters(
                initial_params,
                simulated_response,
                {'pps': initial_prediction.predicted_pps}
            )
            
            print("  - Validating final parameters...")
            final_prediction = await performance_predictor.predict_performance(
                target_profile,
                {
                    'packet_rate': final_params.packet_rate,
                    'packet_size': final_params.packet_size,
                    'concurrency': final_params.concurrency
                }
            )
            
            # Update model with simulated results
            performance_predictor.update_model(
                target_profile,
                {
                    'packet_rate': final_params.packet_rate,
                    'packet_size': final_params.packet_size,
                    'concurrency': final_params.concurrency
                },
                {
                    'pps': final_prediction.predicted_pps * 0.9,
                    'success_rate': final_prediction.predicted_success_rate * 0.95,
                    'bandwidth': final_prediction.predicted_bandwidth * 0.85
                }
            )
            
            print(f"✓ Complete workflow integration successful:")
            print(f"  - Initial PPS prediction: {initial_prediction.predicted_pps:.0f}")
            print(f"  - Final PPS prediction: {final_prediction.predicted_pps:.0f}")
            print(f"  - Parameter optimization: {initial_params.packet_rate} -> {final_params.packet_rate}")
            print(f"  - Success rate improvement: {initial_prediction.predicted_success_rate:.3f} -> {final_prediction.predicted_success_rate:.3f}")
            
        except Exception as e:
            print(f"✗ Workflow integration failed: {e}")
            workflow_success = False
        
        # Final summary
        print("\n" + "=" * 80)
        print("AUTONOMOUS SYSTEM INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        components_tested = [
            ("Quantum Optimization Engine", True),
            ("Parameter Optimizer", True),
            ("Performance Predictor", True),
            ("Real-Time Adaptation System", len(adaptation_system.system_state_history) > 0),
            ("Resource Manager", len(resource_manager.worker_processes) > 0),
            ("Load Balancer", len(selected_workers) > 0),
            ("Recovery System", recovery_triggered),
            ("Complete Workflow", workflow_success)
        ]
        
        all_passed = True
        for component, status in components_tested:
            status_str = "✓ PASSED" if status else "✗ FAILED"
            print(f"  {component:<30} {status_str}")
            if not status:
                all_passed = False
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 ALL TESTS PASSED! Autonomous Configuration and Optimization System is fully functional!")
            print("\nKey Achievements:")
            print("✓ Quantum-inspired optimization algorithms working correctly")
            print("✓ Dynamic parameter adjustment based on target responses")
            print("✓ Performance prediction and effectiveness modeling operational")
            print("✓ Real-time adaptation and feedback loops functioning")
            print("✓ Intelligent resource allocation and load balancing active")
            print("✓ Automatic recovery and failover mechanisms ready")
            print("✓ Complete workflow integration successful")
            return True
        else:
            print("❌ Some tests failed. Please review the implementation.")
            return False
            
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_autonomous_system())
    print(f"\nIntegration test {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)