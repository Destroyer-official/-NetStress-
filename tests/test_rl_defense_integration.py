#!/usr/bin/env python3
"""
Integration tests for Reinforcement Learning and Defense Detection systems

Tests the integration between:
- RL agent for attack optimization
- Advanced defense detection
- Evasion strategy generation
- Feedback loop between detection and optimization
"""

import pytest
import numpy as np
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.ai.reinforcement_learning import (
    QLearningAgent, PolicyGradientAgent, ReinforcementLearningOptimizer,
    State, Action, ActionType, Experience
)
from core.ai.advanced_defense_detection import (
    AdvancedDefenseDetectionSystem, DefenseMetrics, RateLimitDetector,
    WAFDetector, BehavioralDefenseDetector
)
from core.ai.defense_evasion import DefenseType, DefenseSignature


class TestRLAgentBasics:
    """Test basic RL agent functionality"""
    
    def test_q_learning_agent_initialization(self):
        """Test Q-learning agent initializes correctly"""
        agent = QLearningAgent()
        
        assert agent.learning_rate == 0.1
        assert agent.discount_factor == 0.95
        assert agent.epsilon == 0.3
        assert len(agent.q_table) == 0
        assert agent.episode_count == 0
    
    def test_policy_gradient_agent_initialization(self):
        """Test policy gradient agent initializes correctly"""
        agent = PolicyGradientAgent()
        
        assert agent.state_dim == 15
        assert agent.action_dim == len(ActionType)
        assert agent.learning_rate == 0.01
        assert agent.gamma == 0.99
        assert agent.policy_weights.shape == (15, len(ActionType))
    
    def test_state_creation_and_vectorization(self):
        """Test State creation and vector conversion"""
        state = State(
            packet_rate=50000,
            packet_size=1472,
            success_rate=0.95,
            response_time=0.1,
            error_rate=0.05
        )
        
        # Test that state can be vectorized
        vector = state.to_vector()
        assert len(vector) == 15  # Expected state dimension
        assert isinstance(vector, np.ndarray)
        
        # Test that values are normalized properly
        assert all(0 <= v <= 1 for v in vector)
        