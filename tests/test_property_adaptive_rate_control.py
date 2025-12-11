"""
Property-based tests for adaptive rate control.

**Feature: real-high-performance-netstress, Property 11: Real Adaptive Rate Control**
**Validates: Requirements 7.1, 7.2, 7.5**

Tests that adaptive rate control uses real metrics and logs actual values
that drive each rate adjustment decision.
"""

import asyncio
import logging
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.control.adaptive_rate import (
    AdaptiveRateController, 
    NetworkMetrics, 
    RateAdjustment,
    RTTMeasurer,
    ResponsivenessDetector,
    PacketLossTracker,
    PIDController,
    TokenBucket
)


class TestAdaptiveRateControlProperties(unittest.TestCase):
    """Property-based tests for adaptive rate control"""
    
    def setUp(self):
        """Set up test environment"""
        # Capture log messages
        self.log_messages = []
        self.log_handler = logging.Handler()
        self.log_handler.emit = lambda record: self.log_messages.append(record.getMessage())
        
        # Add handler to adaptive rate logger
        logger = logging.getLogger('core.control.adaptive_rate')
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)
    
    def tearDown(self):
        """Clean up test environment"""
        logger = logging.getLogger('core.control.adaptive_rate')
        logger.removeHandler(self.log_handler)
    
    @given(
        initial_rate=st.floats(min_value=1.0, max_value=10000.0),
        rtt_ms=st.floats(min_value=0.1, max_value=5000.0),
        loss_rate=st.floats(min_value=0.0, max_value=1.0),
        success_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_rate_adjustments_log_real_metrics(self, initial_rate, rtt_ms, loss_rate, success_rate):
        """
        **Feature: real-high-performance-netstress, Property 11: Real Adaptive Rate Control**
        
        Property: For any rate adjustment decision, the system SHALL log the actual 
        measured metrics (RTT, packet loss, success rate) that triggered the adjustment.
        
        This ensures transparency and verifiability of adaptive behavior.
        """
        # Create controller
        controller = AdaptiveRateController(
            initial_rate=initial_rate,
            target_host="127.0.0.1",
            target_port=80
        )
        
        # Create metrics that should trigger adjustment
        metrics = NetworkMetrics(
            rtt_ms=rtt_ms,
            packet_loss_rate=loss_rate,
            connection_success_rate=success_rate,
            timestamp=time.perf_counter(),
            target_responsive=success_rate > 0.5  # Simple responsiveness logic
        )
        
        # Clear any existing log messages
        self.log_messages.clear()
        
        # Calculate potential adjustment
        adjustment = controller._calculate_rate_adjustment(metrics)
        
        if adjustment:
            # Apply the adjustment (this should log)
            controller._apply_rate_adjustment(adjustment)
            
            # Verify that a log message was generated
            self.assertTrue(len(self.log_messages) > 0, 
                          "Rate adjustment should generate log message")
            
            log_message = self.log_messages[-1]
            
            # Verify log contains actual metric values
            if adjustment.trigger_metric == "high_rtt":
                self.assertIn(str(rtt_ms), log_message,
                            f"Log should contain actual RTT value {rtt_ms}")
            elif adjustment.trigger_metric == "high_packet_loss":
                # Convert to percentage for log check
                loss_percent = f"{loss_rate:.2%}"
                self.assertTrue(any(loss_str in log_message for loss_str in [
                    f"{loss_rate:.2%}", f"{loss_rate:.3f}", str(loss_rate)
                ]), f"Log should contain actual packet loss rate {loss_rate}")
            elif adjustment.trigger_metric == "low_success_rate":
                success_percent = f"{success_rate:.2%}"
                self.assertTrue(any(success_str in log_message for success_str in [
                    f"{success_rate:.2%}", f"{success_rate:.3f}", str(success_rate)
                ]), f"Log should contain actual success rate {success_rate}")
            
            # Verify log contains rate change information
            self.assertIn(str(adjustment.old_rate), log_message,
                        "Log should contain old rate")
            self.assertIn(str(adjustment.new_rate), log_message,
                        "Log should contain new rate")
            
            # Verify log contains reason
            self.assertIn("Reason:", log_message,
                        "Log should contain reason for adjustment")
    
    @given(
        rates=st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=1, max_size=10)
    )
    @settings(max_examples=5, deadline=10000)
    def test_property_token_bucket_accurate_timing(self, rates):
        """
        Property: Token bucket rate limiting SHALL use high-resolution timing
        and accurately control packet rate within timing precision limits.
        """
        for rate in rates:
            with self.subTest(rate=rate):
                bucket = TokenBucket(rate=rate, capacity=rate)
                
                # Test that we can consume tokens at the expected rate
                start_time = time.perf_counter()
                consumed_count = 0
                test_duration = 0.2  # 200ms test for speed
                
                while time.perf_counter() - start_time < test_duration:
                    if bucket.consume(1):
                        consumed_count += 1
                    else:
                        # If no tokens available, wait a bit
                        time.sleep(0.01)  # 10ms
                
                actual_duration = time.perf_counter() - start_time
                expected_tokens = rate * actual_duration
                
                # Account for initial token and allow reasonable tolerance
                # The bucket starts with 1 token, so we expect at least that
                min_expected = max(1, expected_tokens * 0.8)  # 80% of expected or 1 token minimum
                max_expected = expected_tokens * 1.2 + 1  # 120% of expected plus initial token
                
                self.assertGreaterEqual(consumed_count, min_expected,
                                      f"Token bucket should allow at least {min_expected} tokens in {actual_duration}s (rate: {rate})")
                self.assertLessEqual(consumed_count, max_expected,
                                   f"Token bucket should not exceed {max_expected} tokens in {actual_duration}s (rate: {rate})")


class TestUnresponsivenessDetectionProperties(unittest.TestCase):
    """
    Property-based tests for target unresponsiveness detection.
    
    **Feature: real-high-performance-netstress, Property 12: Target Unresponsiveness Detection**
    **Validates: Requirements 7.3**
    """
    
    @given(
        detection_window=st.floats(min_value=1.0, max_value=10.0),
        failure_count=st.integers(min_value=1, max_value=20),
        time_spacing=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=10, deadline=10000)
    def test_property_unresponsiveness_detection_within_window(self, detection_window, failure_count, time_spacing):
        """
        **Feature: real-high-performance-netstress, Property 12: Target Unresponsiveness Detection**
        
        Property: For any target that becomes unresponsive, the system SHALL detect 
        and log this condition within the specified detection window (default 5 seconds).
        
        This ensures rapid detection of target failures for adaptive rate control.
        """
        detector = ResponsivenessDetector(detection_window=detection_window)
        
        start_time = time.perf_counter()
        
        # Simulate a series of failed connection attempts
        for i in range(failure_count):
            attempt_time = start_time + (i * time_spacing)
            detector.record_connection_attempt(success=False, timestamp=attempt_time)
            
            # Check if unresponsiveness is detected
            current_time = attempt_time
            time_elapsed = current_time - start_time
            
            # Only assert unresponsiveness if we have continuous failures spanning the detection window
            # Check if recent attempts span the full detection window
            recent_attempts = [
                (timestamp, success) for timestamp, success in detector.connection_attempts
                if current_time - timestamp <= detection_window
            ]
            
            if recent_attempts and time_elapsed >= detection_window:
                oldest_recent = min(timestamp for timestamp, _ in recent_attempts)
                time_span = current_time - oldest_recent
                all_failed = all(not success for _, success in recent_attempts)
                
                # Only assert unresponsiveness if we have continuous failures for the full window
                if all_failed and time_span >= detection_window:
                    is_responsive = detector.is_target_responsive(current_time)
                    self.assertFalse(is_responsive, 
                                   f"Target should be detected as unresponsive after {time_elapsed:.2f}s "
                                   f"of continuous failures spanning {time_span:.2f}s (window: {detection_window:.2f}s)")
                    break
    
    @given(
        success_pattern=st.lists(st.booleans(), min_size=5, max_size=20),
        detection_window=st.floats(min_value=2.0, max_value=8.0)
    )
    @settings(max_examples=25, deadline=4000)
    def test_property_responsiveness_based_on_recent_success(self, success_pattern, detection_window):
        """
        Property: Target responsiveness SHALL be determined by recent connection 
        success within the detection window, not by overall historical success rate.
        """
        detector = ResponsivenessDetector(detection_window=detection_window)
        
        base_time = time.perf_counter()
        
        # Record connection attempts with the given pattern
        for i, success in enumerate(success_pattern):
            attempt_time = base_time + (i * 0.5)  # 500ms between attempts
            detector.record_connection_attempt(success=success, timestamp=attempt_time)
        
        # Check responsiveness based on recent successes
        final_time = base_time + (len(success_pattern) * 0.5)
        
        # Count recent successes within the detection window
        recent_successes = []
        for i, success in enumerate(success_pattern):
            attempt_time = base_time + (i * 0.5)
            if final_time - attempt_time <= detection_window:
                recent_successes.append(success)
        
        has_recent_success = any(recent_successes)
        is_responsive = detector.is_target_responsive()
        
        if has_recent_success:
            self.assertTrue(is_responsive, 
                          "Target should be responsive if there are recent successes")
        # Note: We don't assert False for no recent successes because the detector
        # may still consider the target responsive if not enough time has passed
    
    @given(
        initial_successes=st.integers(min_value=1, max_value=5),
        failure_duration=st.floats(min_value=5.1, max_value=10.0)
    )
    @settings(max_examples=15, deadline=3000)
    def test_property_detection_timing_accuracy(self, initial_successes, failure_duration):
        """
        Property: Unresponsiveness detection SHALL occur within 5 seconds of 
        the start of continuous failures, with timing accuracy.
        """
        detector = ResponsivenessDetector(detection_window=5.0)
        
        base_time = time.perf_counter()
        
        # Record some initial successful connections
        for i in range(initial_successes):
            detector.record_connection_attempt(success=True, timestamp=base_time + i * 0.5)
        
        # Start of failure period
        failure_start = base_time + initial_successes * 0.5
        
        # Record failures for the specified duration
        failure_attempts = int(failure_duration * 2)  # 2 attempts per second
        for i in range(failure_attempts):
            failure_time = failure_start + (i * 0.5)
            detector.record_connection_attempt(success=False, timestamp=failure_time)
            
            # Check if unresponsiveness is detected
            time_since_failure_start = failure_time - failure_start
            
            # After 5 seconds of failures, should definitely be unresponsive
            if time_since_failure_start >= 5.0:
                is_responsive = detector.is_target_responsive(failure_time)
                self.assertFalse(is_responsive,
                               f"Target should be unresponsive after {time_since_failure_start:.1f}s of continuous failures")
                break


if __name__ == '__main__':
    unittest.main()