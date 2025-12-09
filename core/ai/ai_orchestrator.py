"""
AI Orchestrator - Main Integration Module

Integrates all AI components with the DDoS framework:
- ML Infrastructure
- Adaptive Strategy Engine  
- Defense Detection and Evasion AI
- Model Validation and Testing

Provides unified interface for AI-driven attack optimization.
"""

import logging
import threading
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .ml_infrastructure import MLModelManager, TrainingData
from .adaptive_strategy import AdaptiveStrategyEngine, AttackStrategy, EnvironmentState
from .defense_evasion import DefenseDetectionAI, DefenseSignature, EvasionStrategy
from .model_validation import ModelValidator, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class AIOptimizationResult:
    """Result of AI-driven attack optimization"""
    optimized_parameters: Dict[str, Any]
    confidence_score: float
    detected_defenses: List[DefenseSignature]
    selected_evasions: List[EvasionStrategy]
    predicted_effectiveness: float
    optimization_time: float
    recommendations: List[str]

class AIOrchestrator:
    """
    Main AI Orchestrator that coordinates all AI components
    Provides unified interface for AI-driven attack optimization
    """
    
    def __init__(self):
        # Initialize AI components
        self.ml_manager = MLModelManager()
        self.strategy_engine = AdaptiveStrategyEngine()
        self.defense_ai = DefenseDetectionAI()
        self.model_validator = ModelValidator()
        
        # State management
        self.is_initialized = False
        self.optimization_history = []
        self.performance_metrics = {}
        
        # Threading
        self._lock = threading.Lock()
        
        # Initialize models
        self._initialize_ai_models()
    
    def _initialize_ai_models(self):
        """Initialize all AI models"""
        try:
            # Initialize pattern recognition model
            pattern_model_id = self.ml_manager.initialize_pattern_recognition_model()
            logger.info(f"Initialized pattern recognition model: {pattern_model_id}")
            
            # Create validation benchmarks
            self._create_validation_benchmarks()
            
            # Set up initial training data collection
            self._setup_training_data_collection()
            
            self.is_initialized = True
            logger.info("AI Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.is_initialized = False
    
    def _create_validation_benchmarks(self):
        """Create performance benchmarks for model validation"""
        
        # Attack effectiveness benchmark
        self.model_validator.create_benchmark(
            benchmark_id='attack_effectiveness_v1',
            model_type='attack_effectiveness',
            baseline_accuracy=0.75,
            baseline_performance={
                'r2': 0.75,
                'mse': 0.05,
                'mae': 0.15
            },
            requirements={
                'max_inference_time': 0.1,  # 100ms
                'min_accuracy': 0.70
            }
        )
        
        # Defense detection benchmark
        self.model_validator.create_benchmark(
            benchmark_id='defense_detection_v1',
            model_type='defense_detection',
            baseline_accuracy=0.85,
            baseline_performance={
                'accuracy': 0.85,
                'precision': 0.80,
                'recall': 0.80,
                'f1_score': 0.80
            },
            requirements={
                'max_inference_time': 0.05,  # 50ms
                'min_accuracy': 0.80
            }
        )
    
    def _setup_training_data_collection(self):
        """Set up training data collection from attack sessions"""
        
        # Add feature extractors for different attack types
        def extract_tcp_features(attack_stats, target_response, network_conditions):
            return [
                attack_stats.get('tcp_syn_pps', 0) / 100000.0,
                attack_stats.get('tcp_ack_pps', 0) / 100000.0,
                target_response.get('tcp_response_time', 0) / 5000.0
            ]
        
        def extract_udp_features(attack_stats, target_response, network_conditions):
            return [
                attack_stats.get('udp_pps', 0) / 100000.0,
                target_response.get('udp_packet_loss', 0),
                network_conditions.get('udp_congestion', 0)
            ]
        
        def extract_http_features(attack_stats, target_response, network_conditions):
            return [
                attack_stats.get('http_rps', 0) / 10000.0,
                target_response.get('http_error_rate', 0),
                target_response.get('http_response_size', 0) / 10000.0
            ]
        
        # Register feature extractors
        self.ml_manager.data_collector.add_feature_extractor('tcp_features', extract_tcp_features)
        self.ml_manager.data_collector.add_feature_extractor('udp_features', extract_udp_features)
        self.ml_manager.data_collector.add_feature_extractor('http_features', extract_http_features)
    
    def optimize_attack_parameters(self, current_params: Dict[str, Any],
                                 attack_stats: Dict[str, Any],
                                 target_response: Dict[str, Any],
                                 network_conditions: Dict[str, Any]) -> AIOptimizationResult:
        """
        Main method for AI-driven attack parameter optimization
        Integrates all AI components to provide optimal attack configuration
        """
        
        if not self.is_initialized:
            logger.warning("AI Orchestrator not initialized, using default parameters")
            return AIOptimizationResult(
                optimized_parameters=current_params,
                confidence_score=0.0,
                detected_defenses=[],
                selected_evasions=[],
                predicted_effectiveness=0.5,
                optimization_time=0.0,
                recommendations=["AI system not initialized"]
            )
        
        start_time = datetime.now()
        
        with self._lock:
            try:
                # Step 1: Collect training data from current attack session
                self.ml_manager.update_model_with_attack_data(
                    attack_stats, target_response, network_conditions
                )
                
                # Step 2: Analyze target defenses from response history
                response_history = self._build_response_history(target_response)
                detected_defenses = self.defense_ai.analyze_target_defenses(response_history)
                
                # Step 3: Adapt attack strategy using reinforcement learning and genetic algorithms
                adapted_strategy = self.strategy_engine.adapt_strategy(
                    attack_stats, target_response, network_conditions
                )
                
                # Step 4: Generate evasion strategy for detected defenses
                evasion_strategy = self.defense_ai.generate_evasion_strategy(
                    detected_defenses, adapted_strategy
                )
                
                # Step 5: Predict effectiveness of optimized parameters
                predicted_effectiveness = self.ml_manager.predict_attack_effectiveness(
                    evasion_strategy
                )
                
                # Step 6: Combine all optimizations into final parameters
                optimized_params = self._combine_optimizations(
                    current_params, adapted_strategy, evasion_strategy
                )
                
                # Step 7: Calculate confidence score
                confidence_score = self._calculate_confidence_score(
                    detected_defenses, predicted_effectiveness, attack_stats
                )
                
                # Step 8: Generate recommendations
                recommendations = self._generate_recommendations(
                    detected_defenses, evasion_strategy, predicted_effectiveness
                )
                
                optimization_time = (datetime.now() - start_time).total_seconds()
                
                result = AIOptimizationResult(
                    optimized_parameters=optimized_params,
                    confidence_score=confidence_score,
                    detected_defenses=detected_defenses,
                    selected_evasions=evasion_strategy.get('evasion_techniques', []),
                    predicted_effectiveness=predicted_effectiveness,
                    optimization_time=optimization_time,
                    recommendations=recommendations
                )
                
                # Store optimization history
                self.optimization_history.append({
                    'timestamp': datetime.now(),
                    'result': result,
                    'input_params': current_params.copy(),
                    'attack_stats': attack_stats.copy()
                })
                
                logger.info(f"AI optimization completed in {optimization_time:.3f}s, "
                           f"confidence: {confidence_score:.3f}, "
                           f"predicted effectiveness: {predicted_effectiveness:.3f}")
                
                return result
                
            except Exception as e:
                logger.error(f"AI optimization failed: {e}")
                return AIOptimizationResult(
                    optimized_parameters=current_params,
                    confidence_score=0.0,
                    detected_defenses=[],
                    selected_evasions=[],
                    predicted_effectiveness=0.5,
                    optimization_time=(datetime.now() - start_time).total_seconds(),
                    recommendations=[f"Optimization failed: {str(e)}"]
                )
    
    def _build_response_history(self, current_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build response history for defense analysis"""
        
        # In a real implementation, this would maintain a history buffer
        # For now, we'll create a synthetic history based on current response
        history = []
        
        # Add current response
        history.append(current_response.copy())
        
        # Add some synthetic historical responses for analysis
        for i in range(5):
            synthetic_response = current_response.copy()
            
            # Add some variation
            if 'response_time' in synthetic_response:
                synthetic_response['response_time'] += np.random.normal(0, 100)
            
            if 'status_code' in synthetic_response:
                # Occasionally change status code to simulate defense activation
                if np.random.random() < 0.2:
                    synthetic_response['status_code'] = np.random.choice([403, 429, 503])
            
            history.append(synthetic_response)
        
        return history
    
    def _combine_optimizations(self, base_params: Dict[str, Any],
                             adapted_strategy: Dict[str, Any],
                             evasion_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Combine optimizations from different AI components"""
        
        optimized = base_params.copy()
        
        # Apply adaptive strategy optimizations
        for key, value in adapted_strategy.items():
            if key in ['packet_rate', 'packet_size', 'burst_duration', 'pause_duration']:
                # Use weighted average for numerical parameters
                if key in optimized:
                    optimized[key] = int(0.7 * value + 0.3 * optimized[key])
                else:
                    optimized[key] = value
            elif key in ['protocol', 'evasion_technique']:
                # Use strategy recommendation for categorical parameters
                optimized[key] = value
        
        # Apply evasion strategy optimizations
        for key, value in evasion_strategy.items():
            if key == 'evasion_techniques':
                optimized[key] = value
            elif key in ['spoofing_rate', 'randomization_level', 'fragmentation_rate']:
                optimized[key] = value
            elif key in ['rotation_interval', 'source_pool_size']:
                optimized[key] = value
        
        # Ensure parameters are within valid ranges
        optimized = self._validate_parameters(optimized)
        
        return optimized
    
    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and constrain parameters to valid ranges"""
        
        validated = params.copy()
        
        # Packet rate constraints
        if 'packet_rate' in validated:
            validated['packet_rate'] = max(1000, min(100000, validated['packet_rate']))
        
        # Packet size constraints
        if 'packet_size' in validated:
            validated['packet_size'] = max(64, min(1500, validated['packet_size']))
        
        # Timing constraints
        if 'burst_duration' in validated:
            validated['burst_duration'] = max(0.1, min(10.0, validated['burst_duration']))
        
        if 'pause_duration' in validated:
            validated['pause_duration'] = max(0.1, min(5.0, validated['pause_duration']))
        
        # Rate constraints (0-1 range)
        for rate_param in ['spoofing_rate', 'randomization_level', 'fragmentation_rate']:
            if rate_param in validated:
                validated[rate_param] = max(0.0, min(1.0, validated[rate_param]))
        
        return validated
    
    def _calculate_confidence_score(self, detected_defenses: List[DefenseSignature],
                                  predicted_effectiveness: float,
                                  attack_stats: Dict[str, Any]) -> float:
        """Calculate confidence score for optimization"""
        
        # Base confidence from model predictions
        base_confidence = 0.5
        
        # Boost confidence if defenses are detected with high confidence
        if detected_defenses:
            avg_defense_confidence = sum(d.confidence for d in detected_defenses) / len(detected_defenses)
            base_confidence += 0.2 * avg_defense_confidence
        
        # Boost confidence based on predicted effectiveness
        base_confidence += 0.2 * predicted_effectiveness
        
        # Boost confidence if we have sufficient attack data
        if attack_stats.get('duration', 0) > 30:  # More than 30 seconds of data
            base_confidence += 0.1
        
        # Reduce confidence if error rate is high
        error_rate = attack_stats.get('errors', 0) / max(1, attack_stats.get('packets_sent', 1))
        if error_rate > 0.1:  # More than 10% error rate
            base_confidence -= 0.2 * error_rate
        
        return max(0.0, min(1.0, base_confidence))
    
    def _generate_recommendations(self, detected_defenses: List[DefenseSignature],
                                evasion_strategy: Dict[str, Any],
                                predicted_effectiveness: float) -> List[str]:
        """Generate human-readable recommendations"""
        
        recommendations = []
        
        # Defense-specific recommendations
        if detected_defenses:
            defense_types = [d.defense_type.value for d in detected_defenses]
            recommendations.append(f"Detected defenses: {', '.join(defense_types)}")
            
            for defense in detected_defenses:
                if defense.confidence > 0.8:
                    recommendations.append(
                        f"High confidence {defense.defense_type.value} detection - "
                        f"applying advanced evasion techniques"
                    )
        
        # Evasion recommendations
        evasion_techniques = evasion_strategy.get('evasion_techniques', [])
        if evasion_techniques:
            recommendations.append(f"Applying evasion techniques: {', '.join(evasion_techniques)}")
        
        # Effectiveness recommendations
        if predicted_effectiveness > 0.8:
            recommendations.append("High predicted effectiveness - maintain current strategy")
        elif predicted_effectiveness < 0.3:
            recommendations.append("Low predicted effectiveness - consider changing attack vector")
        else:
            recommendations.append("Moderate effectiveness - continue with optimizations")
        
        # Parameter-specific recommendations
        if 'spoofing_rate' in evasion_strategy and evasion_strategy['spoofing_rate'] > 0.5:
            recommendations.append("High IP spoofing rate recommended for evasion")
        
        if 'randomization_level' in evasion_strategy and evasion_strategy['randomization_level'] > 0.7:
            recommendations.append("High randomization level applied to avoid pattern detection")
        
        return recommendations
    
    def update_performance_feedback(self, optimization_result: AIOptimizationResult,
                                  actual_results: Dict[str, Any]):
        """Update AI models with performance feedback"""
        
        with self._lock:
            try:
                # Calculate success metrics
                success = self._evaluate_optimization_success(optimization_result, actual_results)
                
                # Update strategy engine with feedback
                strategy_id = f"opt_{len(self.optimization_history)}"
                self.strategy_engine.update_performance_feedback(strategy_id, actual_results)
                
                # Update defense evasion AI with feedback
                evasion_techniques = [t.value if hasattr(t, 'value') else str(t) 
                                    for t in optimization_result.selected_evasions]
                self.defense_ai.update_evasion_feedback(evasion_techniques, actual_results, success)
                
                # Store performance metrics
                self.performance_metrics[datetime.now().isoformat()] = {
                    'predicted_effectiveness': optimization_result.predicted_effectiveness,
                    'actual_effectiveness': self._calculate_actual_effectiveness(actual_results),
                    'success': success,
                    'optimization_time': optimization_result.optimization_time
                }
                
                logger.info(f"Updated AI models with feedback - Success: {success}")
                
            except Exception as e:
                logger.error(f"Failed to update performance feedback: {e}")
    
    def _evaluate_optimization_success(self, optimization_result: AIOptimizationResult,
                                     actual_results: Dict[str, Any]) -> bool:
        """Evaluate if optimization was successful"""
        
        # Success criteria
        success_indicators = []
        
        # Check if predicted effectiveness was close to actual
        actual_effectiveness = self._calculate_actual_effectiveness(actual_results)
        prediction_error = abs(optimization_result.predicted_effectiveness - actual_effectiveness)
        success_indicators.append(prediction_error < 0.3)  # Within 30%
        
        # Check if attack performance improved
        pps = actual_results.get('pps', 0)
        success_indicators.append(pps > 1000)  # Minimum performance threshold
        
        # Check error rate
        error_rate = actual_results.get('errors', 0) / max(1, actual_results.get('packets_sent', 1))
        success_indicators.append(error_rate < 0.2)  # Less than 20% error rate
        
        # Overall success if majority of indicators are positive
        return sum(success_indicators) >= len(success_indicators) * 0.6
    
    def _calculate_actual_effectiveness(self, results: Dict[str, Any]) -> float:
        """Calculate actual effectiveness from attack results"""
        
        # Normalize PPS to 0-1 scale
        pps_score = min(results.get('pps', 0) / 50000.0, 1.0)
        
        # Error penalty
        error_rate = results.get('errors', 0) / max(1, results.get('packets_sent', 1))
        error_penalty = max(0.0, 1.0 - error_rate * 2)  # Penalty for errors
        
        # Bandwidth utilization
        bps_score = min(results.get('bps', 0) / 1e9, 1.0)  # Normalize to Gbps
        
        # Combined effectiveness
        effectiveness = 0.5 * pps_score + 0.3 * error_penalty + 0.2 * bps_score
        
        return max(0.0, min(1.0, effectiveness))
    
    def validate_ai_models(self) -> Dict[str, ValidationResult]:
        """Validate all AI models"""
        
        validation_results = {}
        
        try:
            # Validate pattern recognition model
            if 'pattern_recognition' in self.ml_manager.active_models:
                model_id = self.ml_manager.active_models['pattern_recognition']
                model_info = self.ml_manager.training_pipeline.load_model(model_id)
                
                if model_info:
                    architecture, metadata = model_info
                    test_data = self.model_validator.dataset_generator.generate_attack_effectiveness_dataset(200)
                    
                    result = self.model_validator.validate_neural_network(
                        architecture, test_data, model_id
                    )
                    validation_results['pattern_recognition'] = result
            
            # Validate defense detection model
            defense_result = self.model_validator.validate_defense_detection_model(
                self.defense_ai.pattern_classifier, 'defense_detection'
            )
            validation_results['defense_detection'] = defense_result
            
            logger.info(f"AI model validation completed - {len(validation_results)} models validated")
            
        except Exception as e:
            logger.error(f"AI model validation failed: {e}")
        
        return validation_results
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get comprehensive AI system status"""
        
        return {
            'initialized': self.is_initialized,
            'ml_manager_status': self.ml_manager.get_model_status(),
            'strategy_engine_status': self.strategy_engine.get_adaptation_status(),
            'defense_ai_status': self.defense_ai.get_defense_intelligence(),
            'optimization_count': len(self.optimization_history),
            'performance_metrics_count': len(self.performance_metrics),
            'recent_optimizations': [
                {
                    'timestamp': opt['timestamp'].isoformat(),
                    'confidence': opt['result'].confidence_score,
                    'predicted_effectiveness': opt['result'].predicted_effectiveness,
                    'optimization_time': opt['result'].optimization_time
                }
                for opt in self.optimization_history[-5:]
            ],
            'validation_summary': self.model_validator.get_validation_summary()
        }
    
    def evolve_strategies(self):
        """Trigger evolution in genetic algorithms"""
        self.strategy_engine.evolve_strategies()
    
    def reset_ai_state(self):
        """Reset AI system state"""
        with self._lock:
            self.optimization_history.clear()
            self.performance_metrics.clear()
            self.defense_ai.reset_defense_state()
            logger.info("AI system state reset")

# Global AI orchestrator instance
ai_orchestrator = AIOrchestrator()