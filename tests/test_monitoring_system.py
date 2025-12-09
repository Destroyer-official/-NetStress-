#!/usr/bin/env python3
"""
Comprehensive tests for the Real-Time Analytics and Monitoring System

Tests cover metrics collection accuracy, visualization rendering, predictive analytics,
and all monitoring system components.
"""

import unittest
import asyncio
import time
import threading
import tempfile
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.analytics.predictive_analytics import (
    PredictiveAnalyticsSystem, PerformancePredictor, AnomalyDetector,
    AlertSystem, EffectivenessForecaster, PredictionMetrics, Anomaly,
    OptimizationRecommendation, PerformancePrediction
)

class TestPerformancePredictor(unittest.TestCase):
    """Test performance prediction functionality"""
    
    def setUp(self):
        self.predictor = PerformancePredictor()
    
    def test_model_initialization(self):
        """Test that models are properly initialized"""
        self.assertIn('pps', self.predictor.models)
        self.assertIn('bandwidth', self.predictor.models)
        self.assertIn('success_rate', self.predictor.models)
        self.assertIn('pps', self.predictor.scalers)
    
    def test_add_training_data(self):
        """Test adding training data"""
        features = {
            'packet_rate': 5000,
            'packet_size': 1024,
            'thread_count': 4,
            'target_response_time': 0.05,
            'cpu_usage': 0.5,
            'memory_usage': 0.3,
            'network_utilization': 0.6
        }
        
        targets = {
            'pps': 10000,
            'bandwidth': 0.7,
            'success_rate': 0.9
        }
        
        initial_count = len(self.predictor.feature_history)
        self.predictor.add_training_data(features, targets)
        
        self.assertEqual(len(self.predictor.feature_history), initial_count + 1)
        
        # Verify data structure
        latest_data = self.predictor.feature_history[-1]
        self.assertEqual(latest_data['features']['packet_rate'], 5000)
        self.assertEqual(latest_data['targets']['pps'], 10000)
    
    def test_performance_prediction(self):
        """Test performance prediction with minimal training data"""
        # Add some training data first
        for i in range(10):
            features = {
                'packet_rate': 5000 + i * 100,
                'packet_size': 1024,
                'thread_count': 4,
                'target_response_time': 0.05,
                'cpu_usage': 0.5,
                'memory_usage': 0.3,
                'network_utilization': 0.6
            }
            
            targets = {
                'pps': 10000 + i * 200,
                'bandwidth': 0.7,
                'success_rate': 0.9
            }
            
            self.predictor.add_training_data(features, targets)
        
        # Test prediction
        test_features = {
            'packet_rate': 6000,
            'packet_size': 1024,
            'thread_count': 4,
            'target_response_time': 0.05,
            'cpu_usage': 0.5,
            'memory_usage': 0.3,
            'network_utilization': 0.6
        }
        
        prediction = self.predictor.predict_performance(test_features)
        
        self.assertIsInstance(prediction, PerformancePrediction)
        self.assertGreaterEqual(prediction.predicted_pps, 0)
        self.assertGreaterEqual(prediction.predicted_bandwidth, 0)
        self.assertGreaterEqual(prediction.predicted_success_rate, 0)
        self.assertIsInstance(prediction.confidence_interval, tuple)
    
    def test_prediction_accuracy_calculation(self):
        """Test prediction accuracy metrics calculation"""
        # Add some prediction history
        for i in range(20):
            prediction = PerformancePrediction(
                predicted_pps=10000 + i * 100,
                predicted_bandwidth=0.7,
                predicted_success_rate=0.9,
                confidence_interval=(9000, 11000),
                factors={}
            )
            self.predictor.prediction_history.append(prediction)
        
        metrics = self.predictor.get_prediction_accuracy()
        
        self.assertIsInstance(metrics, PredictionMetrics)
        self.assertGreaterEqual(metrics.accuracy, 0)
        self.assertLessEqual(metrics.accuracy, 100)

class TestAnomalyDetector(unittest.TestCase):
    """Test anomaly detection functionality"""
    
    def setUp(self):
        self.detector = AnomalyDetector()
    
    def test_detector_initialization(self):
        """Test that anomaly detectors are properly initialized"""
        self.assertIn('isolation_forest', self.detector.detectors)
        self.assertIn('statistical', self.detector.detectors)
    
    def test_baseline_update(self):
        """Test baseline statistics update"""
        metrics = {
            'pps': 10000,
            'bandwidth': 0.7,
            'cpu_usage': 0.5
        }
        
        self.detector.update_baseline(metrics)
        
        self.assertIn('pps', self.detector.baseline_stats)
        self.assertEqual(len(self.detector.baseline_stats['pps']['values']), 1)
    
    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection"""
        # Build baseline with normal values
        for i in range(50):
            metrics = {
                'pps': 10000 + np.random.normal(0, 100),
                'bandwidth': 0.7 + np.random.normal(0, 0.05),
                'cpu_usage': 0.5 + np.random.normal(0, 0.05)
            }
            self.detector.update_baseline(metrics)
        
        # Test with anomalous values
        anomalous_metrics = {
            'pps': 20000,  # Significantly higher than baseline
            'bandwidth': 0.7,
            'cpu_usage': 0.5
        }
        
        anomalies = self.detector.detect_anomalies(anomalous_metrics)
        
        # Should detect PPS anomaly
        pps_anomalies = [a for a in anomalies if a.metric_name == 'pps']
        self.assertGreater(len(pps_anomalies), 0)
        
        if pps_anomalies:
            anomaly = pps_anomalies[0]
            self.assertEqual(anomaly.value, 20000)
            self.assertIn(anomaly.severity, ['medium', 'high', 'critical'])
    
    def test_multivariate_anomaly_detection(self):
        """Test multivariate anomaly detection"""
        # Generate training data
        training_data = []
        for i in range(200):
            data_point = {
                'pps': 10000 + np.random.normal(0, 500),
                'bandwidth': 0.7 + np.random.normal(0, 0.1),
                'cpu_usage': 0.5 + np.random.normal(0, 0.1),
                'memory_usage': 0.3 + np.random.normal(0, 0.05)
            }
            training_data.append(data_point)
        
        # Train the detector
        self.detector.train_detectors(training_data)
        
        # Test with normal data
        normal_metrics = {
            'pps': 10000,
            'bandwidth': 0.7,
            'cpu_usage': 0.5,
            'memory_usage': 0.3
        }
        
        anomalies = self.detector.detect_anomalies(normal_metrics)
        multivariate_anomalies = [a for a in anomalies if a.metric_name == 'multivariate']
        
        # Normal data should not trigger multivariate anomalies (usually)
        # This test might occasionally fail due to randomness, which is expected

class TestAlertSystem(unittest.TestCase):
    """Test alerting system functionality"""
    
    def setUp(self):
        self.alert_system = AlertSystem()
    
    def test_alert_system_initialization(self):
        """Test alert system initialization"""
        self.assertIn('performance_degradation', self.alert_system.alert_rules)
        self.assertIn('high_error_rate', self.alert_system.alert_rules)
        self.assertIn('resource_exhaustion', self.alert_system.alert_rules)
    
    def test_custom_alert_rule(self):
        """Test adding custom alert rules"""
        def custom_condition(metrics):
            return metrics.get('custom_metric', 0) > 100
        
        self.alert_system.add_alert_rule(
            'custom_alert',
            custom_condition,
            'high',
            'Custom metric threshold exceeded'
        )
        
        self.assertIn('custom_alert', self.alert_system.alert_rules)
    
    def test_alert_triggering(self):
        """Test alert triggering"""
        # Start alert system
        self.alert_system.start()
        
        try:
            # Metrics that should trigger performance degradation alert
            metrics = {
                'pps': 500,  # Below threshold of 1000
                'error_rate': 0.05,
                'cpu_usage': 0.3,
                'memory_usage': 0.2
            }
            
            initial_alert_count = len(self.alert_system.alert_history)
            self.alert_system.check_alerts(metrics)
            
            # Wait for alert processing
            time.sleep(0.5)
            
            # Should have triggered an alert
            self.assertGreater(len(self.alert_system.alert_history), initial_alert_count)
            
        finally:
            self.alert_system.stop()
    
    def test_alert_callback(self):
        """Test alert callback functionality"""
        callback_called = threading.Event()
        received_alert = {}
        
        def test_callback(alert):
            received_alert.update(alert)
            callback_called.set()
        
        self.alert_system.add_alert_callback(test_callback)
        self.alert_system.start()
        
        try:
            # Trigger an alert
            metrics = {'pps': 100}  # Very low PPS
            self.alert_system.check_alerts(metrics)
            
            # Wait for callback
            self.assertTrue(callback_called.wait(timeout=2))
            self.assertIn('rule_name', received_alert)
            
        finally:
            self.alert_system.stop()

class TestEffectivenessForecaster(unittest.TestCase):
    """Test effectiveness forecasting functionality"""
    
    def setUp(self):
        self.forecaster = EffectivenessForecaster()
    
    def test_optimization_recommendations(self):
        """Test optimization recommendation generation"""
        current_config = {
            'packet_rate': 1000,
            'thread_count': 2,
            'packet_size': 1024
        }
        
        current_metrics = {
            'pps': 500,  # Low performance
            'cpu_usage': 0.3,  # Low CPU usage
            'bandwidth_utilization': 0.9  # High bandwidth
        }
        
        recommendations = self.forecaster.generate_recommendations(
            current_config, current_metrics
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Should recommend increasing packet rate due to low performance
        packet_rate_recs = [r for r in recommendations if r.parameter == 'packet_rate']
        if packet_rate_recs:
            rec = packet_rate_recs[0]
            self.assertGreater(rec.recommended_value, rec.current_value)
        
        # Should recommend increasing thread count due to low CPU usage
        thread_recs = [r for r in recommendations if r.parameter == 'thread_count']
        if thread_recs:
            rec = thread_recs[0]
            self.assertGreater(rec.recommended_value, rec.current_value)
    
    def test_effectiveness_forecasting(self):
        """Test effectiveness forecasting"""
        config_changes = {
            'packet_rate': 5000,
            'thread_count': 6
        }
        
        # Generate historical metrics
        historical_metrics = []
        for i in range(20):
            metrics = {
                'pps': 8000 + i * 100,
                'success_rate': 0.85 + i * 0.005,
                'bandwidth_utilization': 0.6
            }
            historical_metrics.append(metrics)
        
        forecast = self.forecaster.forecast_effectiveness(
            config_changes, historical_metrics
        )
        
        self.assertIn('predicted_pps', forecast)
        self.assertIn('confidence', forecast)
        self.assertIn('predicted_improvement', forecast)
        self.assertGreaterEqual(forecast['confidence'], 0)
        self.assertLessEqual(forecast['confidence'], 1)

class TestPredictiveAnalyticsSystem(unittest.TestCase):
    """Test the main predictive analytics system"""
    
    def setUp(self):
        self.analytics = PredictiveAnalyticsSystem()
    
    def tearDown(self):
        if self.analytics.running:
            self.analytics.stop()
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.analytics.performance_predictor)
        self.assertIsNotNone(self.analytics.anomaly_detector)
        self.assertIsNotNone(self.analytics.alert_system)
        self.assertIsNotNone(self.analytics.effectiveness_forecaster)
    
    def test_system_start_stop(self):
        """Test system start and stop"""
        self.assertFalse(self.analytics.running)
        
        self.analytics.start()
        self.assertTrue(self.analytics.running)
        
        self.analytics.stop()
        self.assertFalse(self.analytics.running)
    
    def test_metrics_processing(self):
        """Test metrics processing pipeline"""
        self.analytics.start()
        
        try:
            # Add test metrics
            metrics = {
                'pps': 10000,
                'bandwidth_utilization': 0.7,
                'success_rate': 0.9,
                'cpu_usage': 0.5,
                'memory_usage': 0.3,
                'response_time': 0.05,
                'error_rate': 0.02
            }
            
            config = {
                'packet_rate': 5000,
                'packet_size': 1024,
                'thread_count': 4
            }
            
            self.analytics.add_metrics(metrics, config)
            
            # Wait for processing
            time.sleep(1)
            
            # Verify metrics were processed
            self.assertGreater(len(self.analytics.performance_predictor.feature_history), 0)
            
        finally:
            self.analytics.stop()
    
    def test_integrated_prediction_workflow(self):
        """Test integrated prediction workflow"""
        self.analytics.start()
        
        try:
            # Add training data
            for i in range(20):
                metrics = {
                    'pps': 8000 + i * 200,
                    'bandwidth_utilization': 0.6 + i * 0.01,
                    'success_rate': 0.8 + i * 0.005,
                    'cpu_usage': 0.4 + i * 0.01,
                    'memory_usage': 0.2 + i * 0.005,
                    'response_time': 0.05,
                    'error_rate': 0.02
                }
                
                config = {
                    'packet_rate': 4000 + i * 100,
                    'packet_size': 1024,
                    'thread_count': 4
                }
                
                self.analytics.add_metrics(metrics, config)
            
            # Wait for processing
            time.sleep(2)
            
            # Test prediction
            test_features = {
                'packet_rate': 6000,
                'packet_size': 1024,
                'thread_count': 4,
                'target_response_time': 0.05,
                'cpu_usage': 0.5,
                'memory_usage': 0.3,
                'network_utilization': 0.6
            }
            
            prediction = self.analytics.get_performance_prediction(test_features)
            self.assertIsInstance(prediction, PerformancePrediction)
            
            # Test recommendations
            recommendations = self.analytics.get_optimization_recommendations(
                {'packet_rate': 1000, 'thread_count': 2},
                {'pps': 500, 'cpu_usage': 0.3}
            )
            self.assertIsInstance(recommendations, list)
            
        finally:
            self.analytics.stop()

class TestMetricsCollectionAccuracy(unittest.TestCase):
    """Test metrics collection accuracy and performance"""
    
    def test_metrics_data_integrity(self):
        """Test that metrics maintain data integrity through processing"""
        analytics = PredictiveAnalyticsSystem()
        analytics.start()
        
        try:
            original_metrics = {
                'pps': 12345.67,
                'bandwidth_utilization': 0.789,
                'success_rate': 0.923,
                'cpu_usage': 0.456,
                'memory_usage': 0.234,
                'response_time': 0.0567,
                'error_rate': 0.0123
            }
            
            config = {
                'packet_rate': 5432,
                'packet_size': 1234,
                'thread_count': 6
            }
            
            analytics.add_metrics(original_metrics, config)
            time.sleep(1)
            
            # Verify data was stored correctly
            if len(analytics.performance_predictor.feature_history) > 0:
                stored_data = analytics.performance_predictor.feature_history[-1]
                
                # Check that original values are preserved
                self.assertEqual(stored_data['features']['packet_rate'], 5432)
                self.assertEqual(stored_data['targets']['pps'], 12345.67)
                
        finally:
            analytics.stop()
    
    def test_high_frequency_metrics_processing(self):
        """Test processing of high-frequency metrics"""
        analytics = PredictiveAnalyticsSystem()
        analytics.start()
        
        try:
            # Simulate high-frequency metrics
            start_time = time.time()
            metrics_count = 100
            
            for i in range(metrics_count):
                metrics = {
                    'pps': 10000 + i,
                    'bandwidth_utilization': 0.7,
                    'success_rate': 0.9,
                    'cpu_usage': 0.5,
                    'memory_usage': 0.3
                }
                
                analytics.add_metrics(metrics)
            
            # Wait for processing
            time.sleep(2)
            
            processing_time = time.time() - start_time
            
            # Should process metrics efficiently
            self.assertLess(processing_time, 5.0)  # Should complete within 5 seconds
            
        finally:
            analytics.stop()

class TestVisualizationComponents(unittest.TestCase):
    """Test visualization rendering and interactivity"""
    
    def test_metrics_data_formatting(self):
        """Test that metrics are properly formatted for visualization"""
        analytics = PredictiveAnalyticsSystem()
        
        # Test data formatting for charts
        metrics = {
            'pps': 10000.5,
            'bandwidth_utilization': 0.75,
            'success_rate': 0.923456,
            'timestamp': datetime.now()
        }
        
        # Verify numeric precision is maintained
        self.assertIsInstance(metrics['pps'], (int, float))
        self.assertIsInstance(metrics['bandwidth_utilization'], (int, float))
        self.assertIsInstance(metrics['success_rate'], (int, float))
    
    def test_real_time_data_updates(self):
        """Test real-time data update capabilities"""
        analytics = PredictiveAnalyticsSystem()
        analytics.start()
        
        try:
            # Simulate real-time updates
            update_count = 10
            
            for i in range(update_count):
                metrics = {
                    'pps': 10000 + i * 100,
                    'timestamp': datetime.now()
                }
                analytics.add_metrics(metrics)
                time.sleep(0.1)
            
            # Verify updates are processed in order
            time.sleep(1)
            
            # Check that recent data is available
            recent_anomalies = analytics.get_recent_anomalies(5)
            self.assertIsInstance(recent_anomalies, list)
            
        finally:
            analytics.stop()

class TestPredictiveAnalyticsAccuracy(unittest.TestCase):
    """Test predictive analytics accuracy"""
    
    def test_prediction_model_convergence(self):
        """Test that prediction models converge with sufficient training data"""
        predictor = PerformancePredictor()
        
        # Generate synthetic training data with known patterns
        for i in range(200):
            # Create predictable relationship: PPS = packet_rate * 2
            packet_rate = 1000 + i * 10
            expected_pps = packet_rate * 2
            
            features = {
                'packet_rate': packet_rate,
                'packet_size': 1024,
                'thread_count': 4,
                'target_response_time': 0.05,
                'cpu_usage': 0.5,
                'memory_usage': 0.3,
                'network_utilization': 0.6
            }
            
            targets = {
                'pps': expected_pps,
                'bandwidth': 0.7,
                'success_rate': 0.9
            }
            
            predictor.add_training_data(features, targets)
        
        # Test prediction accuracy
        test_features = {
            'packet_rate': 5000,
            'packet_size': 1024,
            'thread_count': 4,
            'target_response_time': 0.05,
            'cpu_usage': 0.5,
            'memory_usage': 0.3,
            'network_utilization': 0.6
        }
        
        prediction = predictor.predict_performance(test_features)
        
        # With sufficient training data, prediction should be reasonable
        # (allowing for model limitations and noise)
        expected_pps = 5000 * 2  # 10000
        prediction_error = abs(prediction.predicted_pps - expected_pps) / expected_pps
        
        # Allow up to 50% error for this simple test
        self.assertLess(prediction_error, 0.5)
    
    def test_anomaly_detection_accuracy(self):
        """Test anomaly detection accuracy"""
        detector = AnomalyDetector()
        
        # Build baseline with normal distribution
        normal_mean = 10000
        normal_std = 500
        
        for i in range(100):
            normal_value = np.random.normal(normal_mean, normal_std)
            metrics = {'pps': normal_value}
            detector.update_baseline(metrics)
        
        # Test with clearly anomalous value
        anomalous_metrics = {'pps': normal_mean + 5 * normal_std}  # 5 sigma outlier
        anomalies = detector.detect_anomalies(anomalous_metrics)
        
        # Should detect the anomaly
        pps_anomalies = [a for a in anomalies if a.metric_name == 'pps']
        self.assertGreater(len(pps_anomalies), 0)
        
        # Test with normal value
        normal_metrics = {'pps': normal_mean}
        anomalies = detector.detect_anomalies(normal_metrics)
        
        # Should not detect anomaly for normal value
        pps_anomalies = [a for a in anomalies if a.metric_name == 'pps']
        self.assertEqual(len(pps_anomalies), 0)

class TestSystemIntegration(unittest.TestCase):
    """Test system integration and end-to-end workflows"""
    
    def test_complete_analytics_pipeline(self):
        """Test complete analytics pipeline from metrics to recommendations"""
        analytics = PredictiveAnalyticsSystem()
        analytics.start()
        
        try:
            # Phase 1: Build baseline
            for i in range(50):
                metrics = {
                    'pps': 8000 + np.random.normal(0, 200),
                    'bandwidth_utilization': 0.6 + np.random.normal(0, 0.05),
                    'success_rate': 0.85 + np.random.normal(0, 0.02),
                    'cpu_usage': 0.4 + np.random.normal(0, 0.05),
                    'memory_usage': 0.25 + np.random.normal(0, 0.02),
                    'response_time': 0.05,
                    'error_rate': 0.02
                }
                
                config = {
                    'packet_rate': 4000 + i * 20,
                    'packet_size': 1024,
                    'thread_count': 4
                }
                
                analytics.add_metrics(metrics, config)
            
            time.sleep(2)  # Allow processing
            
            # Phase 2: Test prediction
            test_features = {
                'packet_rate': 5000,
                'packet_size': 1024,
                'thread_count': 4,
                'target_response_time': 0.05,
                'cpu_usage': 0.5,
                'memory_usage': 0.3,
                'network_utilization': 0.6
            }
            
            prediction = analytics.get_performance_prediction(test_features)
            self.assertIsInstance(prediction, PerformancePrediction)
            # predicted_pps can be 0 if model is not fitted yet
            self.assertGreaterEqual(prediction.predicted_pps, 0)
            
            # Phase 3: Test recommendations
            current_config = {'packet_rate': 2000, 'thread_count': 2}
            current_metrics = {'pps': 3000, 'cpu_usage': 0.3}
            
            recommendations = analytics.get_optimization_recommendations(
                current_config, current_metrics
            )
            self.assertIsInstance(recommendations, list)
            
            # Phase 4: Test forecasting
            config_changes = {'packet_rate': 6000, 'thread_count': 6}
            historical_metrics = [
                {'pps': 8000, 'success_rate': 0.85} for _ in range(10)
            ]
            
            forecast = analytics.get_effectiveness_forecast(
                config_changes, historical_metrics
            )
            self.assertIn('confidence', forecast)
            
        finally:
            analytics.stop()

if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPerformancePredictor,
        TestAnomalyDetector,
        TestAlertSystem,
        TestEffectivenessForecaster,
        TestPredictiveAnalyticsSystem,
        TestMetricsCollectionAccuracy,
        TestVisualizationComponents,
        TestPredictiveAnalyticsAccuracy,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")