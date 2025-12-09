#!/usr/bin/env python3
"""
Comprehensive Validation Test Suite for Autonomous Configuration and Optimization System

This test suite validates:
- Parameter optimization accuracy and effectiveness
- Real-time adaptation and recovery mechanisms  
- Resource allocation and scaling capabilities
- Integration between all autonomous components
"""

import asyncio
import time
import random
import logging
import sys
import os
from typing import Dict, Any, List
from dataclasses import dataclass

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation test"""
    test_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    execution_time: float = 0.0

class OptimizationSystemValidator:
    """Comprehensive validator for the autonomous optimization system"""
    
    def __init__(self):
        self.validation_results = []
        self.overall_score = 0.0
        
        # Import autonomous components
        try:
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
                IntelligentResourceManager, LoadBalancer, ResourceUsage
            )
            
            self.components_available = True
            self.QuantumOptimizationEngine = QuantumOptimizationEngine
            self.ParameterOptimizer = ParameterOptimizer
            self.OptimizationParameters = OptimizationParameters
            self.TargetResponse = TargetResponse
            self.PerformancePredictionModel = PerformancePredictionModel
            self.EffectivenessPredictor = EffectivenessPredictor
            self.TargetProfile = TargetProfile
            self.RealTimeAdaptationSystem = RealTimeAdaptationSystem
            self.FeedbackLoop = FeedbackLoop
            self.SystemState = SystemState
            self.AutoRecoverySystem = AutoRecoverySystem
            self.IntelligentResourceManager = IntelligentResourceManager
            self.LoadBalancer = LoadBalancer
            self.ResourceUsage = ResourceUsage
            
        except ImportError as e:
            logger.error(f"Failed to import autonomous components: {e}")
            self.components_available = False
    
    async def run_all_validations(self) -> bool:
        """Run all validation tests"""
        
        if not self.components_available:
            logger.error("Autonomous components not available, skipping validation")
            return False
        
        logger.info("Starting comprehensive optimization system validation...")
        logger.info("=" * 80)
        
        # Run validation tests
        validation_tests = [
            self.validate_quantum_optimization_accuracy,
            self.validate_parameter_optimization_effectiveness,
            self.validate_performance_prediction_accuracy,
            self.validate_real_time_adaptation_responsiveness,
            self.validate_resource_allocation_efficiency,
            self.validate_load_balancing_fairness,
            self.validate_recovery_system_reliability,
            self.validate_system_integration_stability,
            self.validate_performance_under_load,
            self.validate_adaptation_convergence
        ]
        
        for test_func in validation_tests:
            try:
                start_time = time.time()
                result = await test_func()
                execution_time = time.time() - start_time
                
                result.execution_time = execution_time
                self.validation_results.append(result)
                
                status = "✓ PASSED" if result.passed else "✗ FAILED"
                logger.info(f"{result.test_name}: {status} (Score: {result.score:.3f}, Time: {execution_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"Validation test {test_func.__name__} failed with exception: {e}")
                self.validation_results.append(ValidationResult(
                    test_name=test_func.__name__,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    execution_time=0.0
                ))
        
        # Calculate overall results
        self.calculate_overall_score()
        self.print_validation_summary()
        
        return self.overall_score >= 0.8  # 80% threshold for success
    
    async def validate_quantum_optimization_accuracy(self) -> ValidationResult:
        """Validate quantum optimization algorithm accuracy"""
        
        engine = self.QuantumOptimizationEngine(population_size=20, max_iterations=30)
        
        # Test optimization with known optimal solution
        bounds = {
            'packet_rate': (1000, 10000),
            'packet_size': (500, 1500)
        }
        
        # Fitness function with known optimum at high packet rate
        async def fitness_function(params):
            # Optimal at packet_rate=10000, packet_size=1000
            rate_score = params.packet_rate / 10000.0
            size_score = 1.0 - abs(params.packet_size - 1000) / 500.0
            return (rate_score + size_score) / 2.0 + random.uniform(-0.05, 0.05)
        
        result = await engine.optimize(fitness_function, bounds)
        
        # Evaluate accuracy
        accuracy_score = 0.0
        
        # Check if found good parameters
        if result.parameters.packet_rate >= 8000:  # Close to optimum
            accuracy_score += 0.4
        if 800 <= result.parameters.packet_size <= 1200:  # Close to optimum
            accuracy_score += 0.4
        if result.confidence_score >= 0.5:
            accuracy_score += 0.2
        
        passed = accuracy_score >= 0.6
        
        return ValidationResult(
            test_name="Quantum Optimization Accuracy",
            passed=passed,
            score=accuracy_score,
            details={
                "optimized_packet_rate": result.parameters.packet_rate,
                "optimized_packet_size": result.parameters.packet_size,
                "confidence_score": result.confidence_score,
                "predicted_effectiveness": result.predicted_effectiveness
            }
        )
    
    async def validate_parameter_optimization_effectiveness(self) -> ValidationResult:
        """Validate parameter optimizer effectiveness"""
        
        optimizer = self.ParameterOptimizer(learning_rate=0.2, momentum=0.8)
        
        # Simulate optimization cycles with improving performance
        effectiveness_scores = []
        
        for cycle in range(5):
            current_params = self.OptimizationParameters(
                packet_rate=1000 + cycle * 500,
                packet_size=1000,
                concurrency=100
            )
            
            # Simulate improving target response
            target_response = self.TargetResponse(
                response_time=2.0 - cycle * 0.2,
                success_rate=0.4 + cycle * 0.1,
                error_rate=0.3 - cycle * 0.05,
                bandwidth_utilization=0.3 + cycle * 0.1,
                connection_success=0.4 + cycle * 0.1
            )
            
            performance_metrics = {'pps': 1000 + cycle * 200}
            
            optimized_params = await optimizer.optimize_parameters(
                current_params, target_response, performance_metrics
            )
            
            effectiveness = optimizer._calculate_effectiveness(target_response, performance_metrics)
            effectiveness_scores.append(effectiveness)
        
        # Check if effectiveness improved over time
        improvement = effectiveness_scores[-1] - effectiveness_scores[0]
        adaptation_quality = improvement / max(0.1, effectiveness_scores[0])
        
        score = min(1.0, max(0.0, adaptation_quality))
        passed = score >= 0.3  # At least 30% relative improvement
        
        return ValidationResult(
            test_name="Parameter Optimization Effectiveness",
            passed=passed,
            score=score,
            details={
                "initial_effectiveness": effectiveness_scores[0],
                "final_effectiveness": effectiveness_scores[-1],
                "improvement": improvement,
                "adaptation_quality": adaptation_quality
            }
        )
    
    async def validate_performance_prediction_accuracy(self) -> ValidationResult:
        """Validate performance prediction model accuracy"""
        
        model = self.PerformancePredictionModel()
        
        # Test predictions with known scenarios
        test_scenarios = [
            {
                "target": self.TargetProfile(
                    ip_address="192.168.1.1",
                    vulnerability_score=0.8,
                    defense_mechanisms=[],
                    bandwidth_capacity=10000.0
                ),
                "params": {"packet_rate": 5000, "packet_size": 1000},
                "expected_high_performance": True
            },
            {
                "target": self.TargetProfile(
                    ip_address="192.168.1.2",
                    vulnerability_score=0.2,
                    defense_mechanisms=["firewall", "rate_limiting", "ddos_protection"],
                    bandwidth_capacity=1000.0
                ),
                "params": {"packet_rate": 10000, "packet_size": 1500},
                "expected_high_performance": False
            }
        ]
        
        prediction_accuracy = 0.0
        
        for scenario in test_scenarios:
            prediction = await model.predict_performance(
                scenario["target"], scenario["params"]
            )
            
            # Check if prediction aligns with expectations
            high_performance = (prediction.predicted_success_rate > 0.6 and 
                              prediction.predicted_pps > 5000)
            
            if high_performance == scenario["expected_high_performance"]:
                prediction_accuracy += 0.5
        
        passed = prediction_accuracy >= 0.5
        
        return ValidationResult(
            test_name="Performance Prediction Accuracy",
            passed=passed,
            score=prediction_accuracy,
            details={
                "scenarios_tested": len(test_scenarios),
                "correct_predictions": prediction_accuracy * 2
            }
        )
    
    async def validate_real_time_adaptation_responsiveness(self) -> ValidationResult:
        """Validate real-time adaptation system responsiveness"""
        
        adaptation_system = self.RealTimeAdaptationSystem(
            adaptation_interval=0.05,  # Fast for testing
            max_adaptations_per_minute=20
        )
        
        adaptations_triggered = []
        
        def adaptation_callback(params):
            adaptations_triggered.append(time.time())
        
        # Register callbacks for different adaptation types
        adaptation_system.register_adaptation_callback("reduce_packet_rate", adaptation_callback)
        adaptation_system.register_adaptation_callback("reduce_concurrency", adaptation_callback)
        adaptation_system.register_adaptation_callback("optimize_memory_usage", adaptation_callback)
        
        # Mock metrics that should trigger adaptations
        def get_problematic_metrics():
            return {
                'success_rate': 0.2,  # Low success rate
                'error_rate': 0.4,    # High error rate
                'packet_rate': 1000
            }
        
        def get_problematic_system_state():
            return self.SystemState(
                packet_rate=1000,
                success_rate=0.2,
                error_rate=0.4,
                bandwidth_utilization=0.5,
                cpu_usage=0.95,  # High CPU usage
                memory_usage=0.9,  # High memory usage
                network_latency=1.0
            )
        
        # Start monitoring
        monitoring_task = asyncio.create_task(
            adaptation_system.start_monitoring(
                get_problematic_metrics, 
                get_problematic_system_state
            )
        )
        
        # Let it run and collect adaptations
        await asyncio.sleep(0.5)
        adaptation_system.stop_monitoring()
        
        try:
            await asyncio.wait_for(monitoring_task, timeout=1.0)
        except asyncio.TimeoutError:
            pass
        
        # Evaluate responsiveness
        responsiveness_score = 0.0
        
        if len(adaptations_triggered) > 0:
            responsiveness_score += 0.5  # Adaptations were triggered
        
        if len(adaptation_system.system_state_history) >= 5:
            responsiveness_score += 0.3  # System collected enough data
        
        if len(adaptation_system.adaptation_history) > 0:
            responsiveness_score += 0.2  # Adaptations were recorded
        
        passed = responsiveness_score >= 0.5
        
        return ValidationResult(
            test_name="Real-Time Adaptation Responsiveness",
            passed=passed,
            score=responsiveness_score,
            details={
                "adaptations_triggered": len(adaptations_triggered),
                "system_states_collected": len(adaptation_system.system_state_history),
                "adaptation_history": len(adaptation_system.adaptation_history)
            }
        )
    
    async def validate_resource_allocation_efficiency(self) -> ValidationResult:
        """Validate resource allocation efficiency"""
        
        resource_manager = self.IntelligentResourceManager()
        
        # Test different resource allocation scenarios
        allocation_efficiency = 0.0
        
        # Import ResourceType
        from core.autonomous.resource_manager import ResourceType
        
        # Test CPU allocation
        cpu_requirements = {'cores': 2, 'priority': 'high'}
        cpu_allocation = resource_manager.allocate_resources(
            ResourceType.CPU, cpu_requirements
        )
        
        if 'allocated_cores' in cpu_allocation and len(cpu_allocation['allocated_cores']) > 0:
            allocation_efficiency += 0.25
        
        # Test memory allocation
        memory_requirements = {'memory_mb': 1024}
        memory_allocation = resource_manager.allocate_resources(
            ResourceType.MEMORY, memory_requirements
        )
        
        if 'allocated_memory_mb' in memory_allocation and memory_allocation['allocated_memory_mb'] > 0:
            allocation_efficiency += 0.25
        
        # Test worker process registration
        process_id = 12345
        worker_id = resource_manager.register_worker_process(process_id, [0, 1], 1024*1024*1024)
        
        if worker_id and process_id in resource_manager.worker_processes:
            allocation_efficiency += 0.25
        
        # Test resource statistics
        stats = resource_manager.get_resource_statistics()
        
        if 'current_usage' in stats and 'worker_processes' in stats:
            allocation_efficiency += 0.25
        
        passed = allocation_efficiency >= 0.75
        
        return ValidationResult(
            test_name="Resource Allocation Efficiency",
            passed=passed,
            score=allocation_efficiency,
            details={
                "cpu_allocation": cpu_allocation,
                "memory_allocation": memory_allocation,
                "worker_registered": worker_id is not None,
                "statistics_available": 'current_usage' in stats
            }
        )
    
    async def validate_load_balancing_fairness(self) -> ValidationResult:
        """Validate load balancer fairness and efficiency"""
        
        load_balancer = self.LoadBalancer(balancing_strategy="round_robin")
        
        # Register multiple workers
        num_workers = 5
        for i in range(num_workers):
            load_balancer.register_worker(f"worker_{i}", capacity=100, weight=1.0)
        
        # Test round-robin distribution
        selections = []
        for _ in range(num_workers * 3):  # 3 full rounds
            worker = load_balancer.select_worker()
            selections.append(worker)
        
        # Check distribution fairness
        worker_counts = {}
        for worker in selections:
            worker_counts[worker] = worker_counts.get(worker, 0) + 1
        
        # Calculate fairness (should be roughly equal)
        expected_count = len(selections) / num_workers
        fairness_score = 0.0
        
        for count in worker_counts.values():
            deviation = abs(count - expected_count) / expected_count
            fairness_score += max(0, 1.0 - deviation)
        
        fairness_score /= num_workers
        
        # Test least-loaded strategy
        load_balancer.balancing_strategy = "least_loaded"
        load_balancer.update_worker_load("worker_0", 90)
        load_balancer.update_worker_load("worker_1", 10)
        
        selected_worker = load_balancer.select_worker()
        least_loaded_correct = selected_worker == "worker_1"
        
        if least_loaded_correct:
            fairness_score += 0.2
        
        passed = fairness_score >= 0.7
        
        return ValidationResult(
            test_name="Load Balancing Fairness",
            passed=passed,
            score=fairness_score,
            details={
                "worker_distribution": worker_counts,
                "fairness_score": fairness_score,
                "least_loaded_correct": least_loaded_correct
            }
        )
    
    async def validate_recovery_system_reliability(self) -> ValidationResult:
        """Validate recovery system reliability"""
        
        recovery_system = self.AutoRecoverySystem()
        
        reliability_score = 0.0
        
        # Test recovery strategy registration and execution
        recovery_executed = False
        
        def mock_recovery_strategy(context):
            nonlocal recovery_executed
            recovery_executed = True
            return True
        
        recovery_system.register_recovery_strategy("test_failure", mock_recovery_strategy)
        
        # Test critical failure handling
        success = await recovery_system.handle_critical_failure(
            "test_failure", 
            {"error": "test_error", "severity": "high"}
        )
        
        if success and recovery_executed:
            reliability_score += 0.4
        
        # Test backup configuration management
        test_config = {"param1": "value1", "param2": "value2"}
        recovery_system.save_backup_configuration(test_config)
        
        restored_config = recovery_system.get_latest_backup_configuration()
        
        if restored_config == test_config:
            reliability_score += 0.3
        
        # Test failure history tracking
        if len(recovery_system.failure_history) > 0:
            reliability_score += 0.3
        
        passed = reliability_score >= 0.7
        
        return ValidationResult(
            test_name="Recovery System Reliability",
            passed=passed,
            score=reliability_score,
            details={
                "recovery_success": success,
                "recovery_executed": recovery_executed,
                "backup_restored": restored_config == test_config,
                "failure_history_entries": len(recovery_system.failure_history)
            }
        )
    
    async def validate_system_integration_stability(self) -> ValidationResult:
        """Validate overall system integration stability"""
        
        # Initialize all components
        optimizer = self.ParameterOptimizer()
        predictor = self.PerformancePredictionModel()
        adaptation_system = self.RealTimeAdaptationSystem(adaptation_interval=0.1)
        resource_manager = self.IntelligentResourceManager()
        
        stability_score = 0.0
        
        # Test component initialization
        if all([optimizer, predictor, adaptation_system, resource_manager]):
            stability_score += 0.2
        
        # Test basic workflow integration
        try:
            # Parameter optimization
            params = self.OptimizationParameters()
            response = self.TargetResponse(
                response_time=1.0, success_rate=0.6, error_rate=0.2,
                bandwidth_utilization=0.5, connection_success=0.6
            )
            
            optimized_params = await optimizer.optimize_parameters(params, response, {})
            
            if optimized_params:
                stability_score += 0.2
            
            # Performance prediction
            target_profile = self.TargetProfile(ip_address="192.168.1.1")
            prediction = await predictor.predict_performance(target_profile, {})
            
            if prediction:
                stability_score += 0.2
            
            # Resource allocation
            from core.autonomous.resource_manager import ResourceType
            allocation = resource_manager.allocate_resources(
                ResourceType.CPU, {'cores': 1}
            )
            
            if allocation:
                stability_score += 0.2
            
            # System runs without exceptions
            stability_score += 0.2
            
        except Exception as e:
            logger.error(f"Integration stability test failed: {e}")
        
        passed = stability_score >= 0.8
        
        return ValidationResult(
            test_name="System Integration Stability",
            passed=passed,
            score=stability_score,
            details={
                "components_initialized": stability_score >= 0.2,
                "parameter_optimization": optimized_params is not None,
                "performance_prediction": prediction is not None,
                "resource_allocation": allocation is not None
            }
        )
    
    async def validate_performance_under_load(self) -> ValidationResult:
        """Validate system performance under simulated load"""
        
        performance_score = 0.0
        
        # Test quantum optimization with larger population
        engine = self.QuantumOptimizationEngine(population_size=50, max_iterations=20)
        
        start_time = time.time()
        
        # Perform multiple optimizations
        for _ in range(5):
            bounds = {'packet_rate': (100, 10000), 'packet_size': (64, 1500)}
            
            async def simple_fitness(params):
                return random.uniform(0.3, 0.9)
            
            result = await engine.optimize(simple_fitness, bounds)
            
            if result and result.parameters:
                performance_score += 0.1
        
        optimization_time = time.time() - start_time
        
        # Should complete within reasonable time
        if optimization_time < 10.0:
            performance_score += 0.3
        
        # Test resource manager with multiple workers
        resource_manager = self.IntelligentResourceManager()
        
        start_time = time.time()
        
        # Register many workers
        for i in range(20):
            resource_manager.register_worker_process(1000 + i, [i % 4], 1024*1024*512)
        
        registration_time = time.time() - start_time
        
        if registration_time < 1.0 and len(resource_manager.worker_processes) == 20:
            performance_score += 0.2
        
        passed = performance_score >= 0.7
        
        return ValidationResult(
            test_name="Performance Under Load",
            passed=passed,
            score=performance_score,
            details={
                "optimization_time": optimization_time,
                "registration_time": registration_time,
                "workers_registered": len(resource_manager.worker_processes)
            }
        )
    
    async def validate_adaptation_convergence(self) -> ValidationResult:
        """Validate adaptation system convergence behavior"""
        
        feedback_loop = self.FeedbackLoop({
            'success_rate': 0.8,
            'packet_rate': 5000
        })
        
        convergence_score = 0.0
        
        # Simulate convergence scenario
        metrics_sequence = [
            {'success_rate': 0.4, 'packet_rate': 2000},  # Start poor
            {'success_rate': 0.5, 'packet_rate': 2500},  # Improving
            {'success_rate': 0.6, 'packet_rate': 3000},  # Still improving
            {'success_rate': 0.7, 'packet_rate': 4000},  # Getting closer
            {'success_rate': 0.75, 'packet_rate': 4500}, # Close to target
            {'success_rate': 0.78, 'packet_rate': 4800}, # Very close
        ]
        
        control_signals_history = []
        
        for metrics in metrics_sequence:
            control_signals = feedback_loop.update(metrics)
            control_signals_history.append(control_signals)
        
        # Check if control signals are decreasing (converging)
        if len(control_signals_history) >= 3:
            recent_signals = control_signals_history[-3:]
            
            # Check convergence for success_rate
            success_signals = [abs(s.get('success_rate', 0)) for s in recent_signals]
            if len(success_signals) >= 2 and success_signals[-1] < success_signals[0]:
                convergence_score += 0.3
            
            # Check convergence for packet_rate
            rate_signals = [abs(s.get('packet_rate', 0)) for s in recent_signals]
            if len(rate_signals) >= 2 and rate_signals[-1] < rate_signals[0]:
                convergence_score += 0.3
        
        # Test stability metrics
        stability_metrics = feedback_loop.get_stability_metrics()
        
        if stability_metrics.get('overall_stability', 0) > 0.5:
            convergence_score += 0.4
        
        passed = convergence_score >= 0.6
        
        return ValidationResult(
            test_name="Adaptation Convergence",
            passed=passed,
            score=convergence_score,
            details={
                "control_signals_count": len(control_signals_history),
                "stability_metrics": stability_metrics,
                "final_control_signals": control_signals_history[-1] if control_signals_history else {}
            }
        )
    
    def calculate_overall_score(self):
        """Calculate overall validation score"""
        if not self.validation_results:
            self.overall_score = 0.0
            return
        
        total_score = sum(result.score for result in self.validation_results)
        self.overall_score = total_score / len(self.validation_results)
    
    def print_validation_summary(self):
        """Print comprehensive validation summary"""
        
        logger.info("\n" + "=" * 80)
        logger.info("AUTONOMOUS OPTIMIZATION SYSTEM VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        passed_tests = sum(1 for result in self.validation_results if result.passed)
        total_tests = len(self.validation_results)
        
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Overall Score: {self.overall_score:.3f}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nDetailed Results:")
        logger.info("-" * 80)
        
        for result in self.validation_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            logger.info(f"{result.test_name:<40} {status} (Score: {result.score:.3f})")
        
        logger.info("\nPerformance Metrics:")
        logger.info("-" * 80)
        
        total_execution_time = sum(result.execution_time for result in self.validation_results)
        avg_execution_time = total_execution_time / len(self.validation_results)
        
        logger.info(f"Total Execution Time: {total_execution_time:.2f}s")
        logger.info(f"Average Test Time: {avg_execution_time:.2f}s")
        
        # Categorize results
        excellent_tests = [r for r in self.validation_results if r.score >= 0.9]
        good_tests = [r for r in self.validation_results if 0.7 <= r.score < 0.9]
        fair_tests = [r for r in self.validation_results if 0.5 <= r.score < 0.7]
        poor_tests = [r for r in self.validation_results if r.score < 0.5]
        
        logger.info(f"\nScore Distribution:")
        logger.info(f"Excellent (≥0.9): {len(excellent_tests)}")
        logger.info(f"Good (0.7-0.9): {len(good_tests)}")
        logger.info(f"Fair (0.5-0.7): {len(fair_tests)}")
        logger.info(f"Poor (<0.5): {len(poor_tests)}")
        
        if self.overall_score >= 0.9:
            logger.info("\n🎉 EXCELLENT! Autonomous optimization system is performing exceptionally well!")
        elif self.overall_score >= 0.8:
            logger.info("\n✅ GOOD! Autonomous optimization system is performing well!")
        elif self.overall_score >= 0.6:
            logger.info("\n⚠️  FAIR! Autonomous optimization system needs some improvements!")
        else:
            logger.info("\n❌ POOR! Autonomous optimization system requires significant improvements!")
        
        logger.info("=" * 80)

async def main():
    """Main validation function"""
    
    validator = OptimizationSystemValidator()
    
    print("Autonomous Configuration and Optimization System - Comprehensive Validation")
    print("=" * 80)
    
    success = await validator.run_all_validations()
    
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL! System is ready for production use.")
        return True
    else:
        print("\n❌ VALIDATION FAILED! System requires improvements before production use.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)