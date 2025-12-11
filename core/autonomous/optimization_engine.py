"""
Intelligent Parameter Optimization Engine

Implements probabilistic genetic optimization algorithms, dynamic parameter adjustment
based on target responses, and performance prediction modeling.

Note: This uses standard probabilistic optimization techniques, not actual quantum computing.
"""

import asyncio
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptimizationParameters:
    """Configuration parameters for optimization algorithms"""
    packet_rate: int = 1000
    packet_size: int = 1460
    concurrency: int = 100
    burst_interval: float = 0.001
    protocol_weights: Dict[str, float] = field(default_factory=lambda: {
        'TCP': 0.3, 'UDP': 0.4, 'HTTP': 0.2, 'DNS': 0.1
    })
    evasion_techniques: List[str] = field(default_factory=lambda: [
        'ip_spoofing', 'fragmentation', 'timing_randomization'
    ])

@dataclass
class TargetResponse:
    """Represents target system response metrics"""
    response_time: float
    success_rate: float
    error_rate: float
    bandwidth_utilization: float
    connection_success: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class OptimizationResult:
    """Result of optimization process"""
    parameters: OptimizationParameters
    predicted_effectiveness: float
    confidence_score: float
    optimization_method: str

class QuantumOptimizationEngine:
    """
    Probabilistic genetic optimization engine for attack parameter optimization.
    
    Uses probabilistic sampling and evolutionary techniques to explore 
    parameter space efficiently. Despite the name, this is a standard
    genetic algorithm with probabilistic state representation.
    
    Note: The "quantum" naming is legacy - this uses classical algorithms.
    """
    
    def __init__(self, population_size: int = 50, max_iterations: int = 100):
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.quantum_population = []  # Legacy name - actually probabilistic population
        self.best_solution = None
        self.convergence_history = deque(maxlen=20)
        
    def initialize_quantum_population(self, bounds: Dict[str, Tuple[float, float]]):
        """Initialize population with probabilistic states for genetic optimization"""
        self.quantum_population = []
        
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in bounds.items():
                # Probabilistic representation: normalized weights for sampling
                individual[param] = {
                    'alpha': random.uniform(0, 1),  # Weight for lower bound
                    'beta': random.uniform(0, 1),   # Weight for upper bound
                    'min_val': min_val,
                    'max_val': max_val
                }
                # Normalize weights to sum to 1
                norm = math.sqrt(individual[param]['alpha']**2 + individual[param]['beta']**2)
                individual[param]['alpha'] /= norm
                individual[param]['beta'] /= norm
                
            self.quantum_population.append(individual)
    
    def collapse_quantum_state(self, individual: Dict) -> OptimizationParameters:
        """Sample concrete parameters from probabilistic state"""
        params = {}
        
        for param, prob_state in individual.items():
            # Probabilistic sampling based on weights
            probability = prob_state['alpha']**2
            if random.random() < probability:
                value = prob_state['min_val']
            else:
                value = prob_state['max_val']
            
            # Add Gaussian noise for exploration
            noise = random.gauss(0, 0.1) * (prob_state['max_val'] - prob_state['min_val'])
            value = max(prob_state['min_val'], 
                       min(prob_state['max_val'], value + noise))
            
            params[param] = value
        
        return OptimizationParameters(
            packet_rate=int(params.get('packet_rate', 1000)),
            packet_size=int(params.get('packet_size', 1460)),
            concurrency=int(params.get('concurrency', 100)),
            burst_interval=params.get('burst_interval', 0.001)
        )
    
    def quantum_rotation(self, individual: Dict, fitness: float, best_fitness: float):
        """Apply rotation transformation to adjust probability weights based on fitness"""
        rotation_angle = 0.01 * math.pi * (best_fitness - fitness) / (best_fitness + 1e-10)
        
        for param in individual:
            # Rotation transformation (standard genetic algorithm technique)
            cos_theta = math.cos(rotation_angle)
            sin_theta = math.sin(rotation_angle)
            
            old_alpha = individual[param]['alpha']
            old_beta = individual[param]['beta']
            
            individual[param]['alpha'] = cos_theta * old_alpha - sin_theta * old_beta
            individual[param]['beta'] = sin_theta * old_alpha + cos_theta * old_beta
    
    def quantum_entanglement(self, individual1: Dict, individual2: Dict) -> Tuple[Dict, Dict]:
        """Crossover operation between two individuals (genetic algorithm crossover)"""
        crossed1 = individual1.copy()
        crossed2 = individual2.copy()
        
        # Select random parameters for crossover
        crossover_params = random.sample(list(individual1.keys()), 
                                       k=random.randint(1, len(individual1)))
        
        for param in crossover_params:
            # Swap weights between individuals
            crossed1[param]['alpha'], crossed2[param]['alpha'] = \
                crossed2[param]['alpha'], crossed1[param]['alpha']
    
        return crossed1, crossed2
    
    async def optimize(self, fitness_function, bounds: Dict[str, Tuple[float, float]]) -> OptimizationResult:
        """Main genetic optimization loop"""
        self.initialize_quantum_population(bounds)
        best_fitness = float('-inf')
        
        for iteration in range(self.max_iterations):
            fitness_scores = []
            
            # Evaluate population
            for individual in self.quantum_population:
                params = self.collapse_quantum_state(individual)
                fitness = await fitness_function(params)
                fitness_scores.append(fitness)
                
                if fitness > best_fitness:
                    best_fitness = fitness
                    self.best_solution = params
            
            # Apply genetic operations (rotation/mutation)
            for i, individual in enumerate(self.quantum_population):
                self.quantum_rotation(individual, fitness_scores[i], best_fitness)
            
            # Crossover between best individuals
            if len(self.quantum_population) >= 2:
                best_indices = np.argsort(fitness_scores)[-2:]
                crossed1, crossed2 = self.quantum_entanglement(
                    self.quantum_population[best_indices[0]],
                    self.quantum_population[best_indices[1]]
                )
                self.quantum_population[best_indices[0]] = crossed1
                self.quantum_population[best_indices[1]] = crossed2
            
            self.convergence_history.append(best_fitness)
            
            # Check convergence
            if len(self.convergence_history) >= 10:
                recent_improvement = (self.convergence_history[-1] - 
                                    self.convergence_history[-10])
                if recent_improvement < 0.001:
                    logger.info(f"Genetic optimization converged at iteration {iteration}")
                    break
        
        confidence = self._calculate_confidence()
        
        return OptimizationResult(
            parameters=self.best_solution,
            predicted_effectiveness=best_fitness,
            confidence_score=confidence,
            optimization_method="genetic_probabilistic"
        )
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence score based on convergence stability"""
        if len(self.convergence_history) < 5:
            return 0.5
        
        recent_values = list(self.convergence_history)[-5:]
        variance = np.var(recent_values)
        mean_value = np.mean(recent_values)
        
        # Lower variance relative to mean indicates higher confidence
        confidence = 1.0 / (1.0 + variance / (mean_value + 1e-10))
        return min(1.0, max(0.0, confidence))

class ParameterOptimizer:
    """
    Dynamic parameter optimizer that adjusts attack parameters based on
    target responses and performance feedback.
    """
    
    def __init__(self, learning_rate: float = 0.1, momentum: float = 0.9):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.parameter_history = deque(maxlen=100)
        self.response_history = deque(maxlen=100)
        self.gradient_momentum = {}
        self.quantum_engine = QuantumOptimizationEngine()
        
    async def optimize_parameters(self, 
                                current_params: OptimizationParameters,
                                target_response: TargetResponse,
                                performance_metrics: Dict[str, float]) -> OptimizationParameters:
        """
        Optimize parameters based on target response and performance metrics
        """
        # Record current state
        self.parameter_history.append(current_params)
        self.response_history.append(target_response)
        
        # Calculate effectiveness score
        effectiveness = self._calculate_effectiveness(target_response, performance_metrics)
        
        # Use different optimization strategies based on performance
        if effectiveness < 0.3:
            # Poor performance - use quantum optimization for exploration
            return await self._quantum_optimization(current_params, effectiveness)
        elif effectiveness < 0.7:
            # Moderate performance - use gradient-based optimization
            return self._gradient_optimization(current_params, target_response)
        else:
            # Good performance - fine-tune with small adjustments
            return self._fine_tune_optimization(current_params, target_response)
    
    def _calculate_effectiveness(self, 
                               response: TargetResponse, 
                               metrics: Dict[str, float]) -> float:
        """Calculate overall attack effectiveness score"""
        # Weighted combination of multiple factors
        weights = {
            'success_rate': 0.3,
            'response_time': 0.2,
            'bandwidth_utilization': 0.2,
            'packet_rate': 0.15,
            'error_rate': -0.15  # Negative weight for errors
        }
        
        effectiveness = 0.0
        effectiveness += weights['success_rate'] * response.success_rate
        effectiveness += weights['response_time'] * (1.0 / (response.response_time + 1e-6))
        effectiveness += weights['bandwidth_utilization'] * response.bandwidth_utilization
        effectiveness += weights['packet_rate'] * min(1.0, metrics.get('pps', 0) / 10000)
        effectiveness += weights['error_rate'] * response.error_rate
        
        return max(0.0, min(1.0, effectiveness))
    
    async def _quantum_optimization(self, 
                                  current_params: OptimizationParameters,
                                  effectiveness: float) -> OptimizationParameters:
        """Use quantum optimization for parameter exploration"""
        bounds = {
            'packet_rate': (100, 100000),
            'packet_size': (64, 1500),
            'concurrency': (10, 1000),
            'burst_interval': (0.0001, 0.1)
        }
        
        async def fitness_function(params: OptimizationParameters) -> float:
            # Simulate fitness based on parameter combination
            # In real implementation, this would test the parameters
            base_fitness = effectiveness
            
            # Reward balanced parameters
            if 1000 <= params.packet_rate <= 50000:
                base_fitness += 0.1
            if 500 <= params.packet_size <= 1400:
                base_fitness += 0.1
            if 50 <= params.concurrency <= 500:
                base_fitness += 0.1
                
            return base_fitness + random.uniform(-0.05, 0.05)  # Add noise
        
        result = await self.quantum_engine.optimize(fitness_function, bounds)
        return result.parameters
    
    def _gradient_optimization(self, 
                             current_params: OptimizationParameters,
                             response: TargetResponse) -> OptimizationParameters:
        """Use gradient-based optimization for parameter adjustment"""
        if len(self.response_history) < 2:
            return current_params
        
        # Calculate gradients based on recent history
        prev_response = self.response_history[-2]
        prev_params = self.parameter_history[-2]
        
        # Compute parameter gradients
        gradients = {}
        
        # Packet rate gradient
        if prev_params.packet_rate != current_params.packet_rate:
            rate_gradient = ((response.success_rate - prev_response.success_rate) / 
                           (current_params.packet_rate - prev_params.packet_rate + 1e-10))
            gradients['packet_rate'] = rate_gradient
        
        # Packet size gradient  
        if prev_params.packet_size != current_params.packet_size:
            size_gradient = ((response.bandwidth_utilization - prev_response.bandwidth_utilization) /
                           (current_params.packet_size - prev_params.packet_size + 1e-10))
            gradients['packet_size'] = size_gradient
        
        # Apply momentum and update parameters
        new_packet_rate = current_params.packet_rate
        new_packet_size = current_params.packet_size
        
        if 'packet_rate' in gradients:
            momentum_rate = self.gradient_momentum.get('packet_rate', 0)
            momentum_rate = self.momentum * momentum_rate + self.learning_rate * gradients['packet_rate']
            self.gradient_momentum['packet_rate'] = momentum_rate
            new_packet_rate = max(100, min(100000, 
                                         current_params.packet_rate + int(momentum_rate * 1000)))
        
        if 'packet_size' in gradients:
            momentum_size = self.gradient_momentum.get('packet_size', 0)
            momentum_size = self.momentum * momentum_size + self.learning_rate * gradients['packet_size']
            self.gradient_momentum['packet_size'] = momentum_size
            new_packet_size = max(64, min(1500,
                                        current_params.packet_size + int(momentum_size * 100)))
        
        return OptimizationParameters(
            packet_rate=new_packet_rate,
            packet_size=new_packet_size,
            concurrency=current_params.concurrency,
            burst_interval=current_params.burst_interval,
            protocol_weights=current_params.protocol_weights,
            evasion_techniques=current_params.evasion_techniques
        )
    
    def _fine_tune_optimization(self, 
                              current_params: OptimizationParameters,
                              response: TargetResponse) -> OptimizationParameters:
        """Fine-tune parameters when performance is already good"""
        # Small random adjustments to maintain effectiveness
        adjustment_factor = 0.05
        
        rate_adjustment = int(current_params.packet_rate * 
                            random.uniform(-adjustment_factor, adjustment_factor))
        size_adjustment = int(current_params.packet_size * 
                            random.uniform(-adjustment_factor, adjustment_factor))
        
        new_packet_rate = max(100, min(100000, current_params.packet_rate + rate_adjustment))
        new_packet_size = max(64, min(1500, current_params.packet_size + size_adjustment))
        
        return OptimizationParameters(
            packet_rate=new_packet_rate,
            packet_size=new_packet_size,
            concurrency=current_params.concurrency,
            burst_interval=current_params.burst_interval,
            protocol_weights=current_params.protocol_weights,
            evasion_techniques=current_params.evasion_techniques
        )
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights about the optimization process"""
        if len(self.response_history) < 2:
            return {"status": "insufficient_data"}
        
        recent_responses = list(self.response_history)[-10:]
        
        return {
            "status": "active",
            "avg_success_rate": np.mean([r.success_rate for r in recent_responses]),
            "avg_response_time": np.mean([r.response_time for r in recent_responses]),
            "trend_success_rate": self._calculate_trend([r.success_rate for r in recent_responses]),
            "optimization_stability": self._calculate_stability(),
            "recommended_action": self._get_recommendation()
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 3:
            return "unknown"
        
        recent_avg = np.mean(values[-3:])
        earlier_avg = np.mean(values[:-3])
        
        if recent_avg > earlier_avg * 1.05:
            return "improving"
        elif recent_avg < earlier_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    def _calculate_stability(self) -> float:
        """Calculate optimization stability score"""
        if len(self.response_history) < 5:
            return 0.5
        
        recent_success_rates = [r.success_rate for r in list(self.response_history)[-10:]]
        variance = np.var(recent_success_rates)
        
        # Lower variance indicates higher stability
        stability = 1.0 / (1.0 + variance * 10)
        return min(1.0, max(0.0, stability))
    
    def _get_recommendation(self) -> str:
        """Get optimization recommendation based on current state"""
        if len(self.response_history) < 3:
            return "continue_monitoring"
        
        recent_effectiveness = [self._calculate_effectiveness(r, {}) 
                              for r in list(self.response_history)[-3:]]
        avg_effectiveness = np.mean(recent_effectiveness)
        
        if avg_effectiveness < 0.3:
            return "major_parameter_adjustment_needed"
        elif avg_effectiveness < 0.6:
            return "moderate_optimization_required"
        elif avg_effectiveness < 0.8:
            return "fine_tuning_recommended"
        else:
            return "maintain_current_parameters"