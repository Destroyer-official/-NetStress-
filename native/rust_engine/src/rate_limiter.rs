//! Precision rate limiting with nanosecond timing
//! Implements token bucket algorithm for accurate rate control

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::time::{Duration, Instant};

/// High-precision token bucket rate limiter
pub struct TokenBucket {
    /// Tokens per second (rate limit)
    rate: AtomicU64,
    /// Maximum burst size
    burst: AtomicU64,
    /// Current available tokens (scaled by 1000 for precision)
    tokens: AtomicU64,
    /// Last refill timestamp (nanoseconds since start)
    last_refill: AtomicU64,
    /// Start time for nanosecond calculations
    start: Instant,
    /// Whether rate limiting is enabled
    enabled: AtomicBool,
}

impl TokenBucket {
    /// Create a new token bucket rate limiter
    ///
    /// # Arguments
    /// * `rate` - Tokens per second (packets per second)
    /// * `burst` - Maximum burst size (tokens that can accumulate)
    pub fn new(rate: u64, burst: u64) -> Self {
        let burst = if burst == 0 { rate } else { burst };
        Self {
            rate: AtomicU64::new(rate),
            burst: AtomicU64::new(burst),
            tokens: AtomicU64::new(burst * 1000), // Start with full bucket, scaled
            last_refill: AtomicU64::new(0),
            start: Instant::now(),
            enabled: AtomicBool::new(rate > 0),
        }
    }

    /// Create an unlimited rate limiter (no limiting)
    pub fn unlimited() -> Self {
        Self {
            rate: AtomicU64::new(0),
            burst: AtomicU64::new(0),
            tokens: AtomicU64::new(u64::MAX),
            last_refill: AtomicU64::new(0),
            start: Instant::now(),
            enabled: AtomicBool::new(false),
        }
    }

    /// Try to acquire tokens (non-blocking)
    /// Returns true if tokens were acquired, false if rate limited
    #[inline]
    pub fn try_acquire(&self, count: u64) -> bool {
        if !self.enabled.load(Ordering::Relaxed) {
            return true;
        }

        self.refill();

        let needed = count * 1000; // Scale for precision
        let current = self.tokens.load(Ordering::Relaxed);

        if current >= needed {
            // Try to consume tokens atomically
            self.tokens.fetch_sub(needed, Ordering::Relaxed);
            true
        } else {
            false
        }
    }

    /// Acquire tokens, blocking if necessary
    /// Returns the time waited
    pub fn acquire(&self, count: u64) -> Duration {
        if !self.enabled.load(Ordering::Relaxed) {
            return Duration::ZERO;
        }

        let start = Instant::now();

        while !self.try_acquire(count) {
            // Calculate wait time based on token deficit
            let rate = self.rate.load(Ordering::Relaxed);
            if rate == 0 {
                return Duration::ZERO;
            }

            let needed = count * 1000;
            let current = self.tokens.load(Ordering::Relaxed);
            let deficit = needed.saturating_sub(current);

            // Wait time = deficit / (rate * 1000) seconds
            // Convert to nanoseconds for precision
            let wait_ns = (deficit * 1_000_000_000) / (rate * 1000);

            if wait_ns > 0 {
                std::thread::sleep(Duration::from_nanos(wait_ns.min(1_000_000)));
            // Max 1ms sleep
            } else {
                std::hint::spin_loop();
            }
        }

        start.elapsed()
    }

    /// Refill tokens based on elapsed time
    #[inline]
    fn refill(&self) {
        let now_ns = self.start.elapsed().as_nanos() as u64;
        let last = self.last_refill.load(Ordering::Relaxed);
        let elapsed_ns = now_ns.saturating_sub(last);

        if elapsed_ns == 0 {
            return;
        }

        // Calculate tokens to add: rate * elapsed_time
        // tokens = rate * (elapsed_ns / 1_000_000_000) * 1000 (scaled)
        let rate = self.rate.load(Ordering::Relaxed);
        let new_tokens = (rate * elapsed_ns) / 1_000_000; // Simplified calculation

        if new_tokens > 0 {
            let burst = self.burst.load(Ordering::Relaxed) * 1000;
            let current = self.tokens.load(Ordering::Relaxed);
            let new_total = (current + new_tokens).min(burst);

            self.tokens.store(new_total, Ordering::Relaxed);
            self.last_refill.store(now_ns, Ordering::Relaxed);
        }
    }

    /// Set new rate limit
    pub fn set_rate(&self, rate: u64) {
        self.rate.store(rate, Ordering::SeqCst);
        self.enabled.store(rate > 0, Ordering::SeqCst);

        if rate > 0 {
            let burst = self.burst.load(Ordering::Relaxed);
            if burst < rate {
                self.burst.store(rate, Ordering::SeqCst);
            }
        }
    }

    /// Set burst size
    pub fn set_burst(&self, burst: u64) {
        self.burst.store(burst, Ordering::SeqCst);
    }

    /// Get current rate
    pub fn rate(&self) -> u64 {
        self.rate.load(Ordering::Relaxed)
    }

    /// Get current burst size
    pub fn burst(&self) -> u64 {
        self.burst.load(Ordering::Relaxed)
    }

    /// Get available tokens
    pub fn available(&self) -> u64 {
        self.refill();
        self.tokens.load(Ordering::Relaxed) / 1000
    }

    /// Check if rate limiting is enabled
    pub fn is_enabled(&self) -> bool {
        self.enabled.load(Ordering::Relaxed)
    }

    /// Reset the rate limiter
    pub fn reset(&self) {
        let burst = self.burst.load(Ordering::Relaxed);
        self.tokens.store(burst * 1000, Ordering::SeqCst);
        self.last_refill.store(0, Ordering::SeqCst);
    }
}

/// Sliding window rate limiter for more accurate rate measurement
pub struct SlidingWindowLimiter {
    /// Window size in milliseconds
    window_ms: u64,
    /// Maximum count per window
    max_count: AtomicU64,
    /// Timestamps of recent events (circular buffer)
    timestamps: Vec<AtomicU64>,
    /// Current write position
    write_pos: AtomicU64,
    /// Start time
    start: Instant,
    /// Enabled flag
    enabled: AtomicBool,
}

impl SlidingWindowLimiter {
    pub fn new(rate_per_second: u64, window_ms: u64) -> Self {
        let max_count = (rate_per_second * window_ms) / 1000;
        let buffer_size = max_count.max(1000) as usize;

        Self {
            window_ms,
            max_count: AtomicU64::new(max_count),
            timestamps: (0..buffer_size).map(|_| AtomicU64::new(0)).collect(),
            write_pos: AtomicU64::new(0),
            start: Instant::now(),
            enabled: AtomicBool::new(rate_per_second > 0),
        }
    }

    /// Try to record an event, returns false if rate limited
    pub fn try_record(&self) -> bool {
        if !self.enabled.load(Ordering::Relaxed) {
            return true;
        }

        let now_ms = self.start.elapsed().as_millis() as u64;
        let window_start = now_ms.saturating_sub(self.window_ms);

        // Count events in window
        let mut count = 0u64;
        for ts in &self.timestamps {
            let t = ts.load(Ordering::Relaxed);
            if t >= window_start && t <= now_ms {
                count += 1;
            }
        }

        let max = self.max_count.load(Ordering::Relaxed);
        if count >= max {
            return false;
        }

        // Record this event
        let pos = self.write_pos.fetch_add(1, Ordering::Relaxed) as usize % self.timestamps.len();
        self.timestamps[pos].store(now_ms, Ordering::Relaxed);

        true
    }

    /// Get current rate (events per second)
    pub fn current_rate(&self) -> u64 {
        let now_ms = self.start.elapsed().as_millis() as u64;
        let window_start = now_ms.saturating_sub(self.window_ms);

        let mut count = 0u64;
        for ts in &self.timestamps {
            let t = ts.load(Ordering::Relaxed);
            if t >= window_start && t <= now_ms {
                count += 1;
            }
        }

        (count * 1000) / self.window_ms
    }

    /// Set new rate limit
    pub fn set_rate(&self, rate_per_second: u64) {
        let max_count = (rate_per_second * self.window_ms) / 1000;
        self.max_count.store(max_count, Ordering::SeqCst);
        self.enabled.store(rate_per_second > 0, Ordering::SeqCst);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use std::thread;

    #[test]
    fn test_token_bucket_basic() {
        let limiter = TokenBucket::new(1000, 100);

        // Should be able to acquire burst amount immediately
        for _ in 0..100 {
            assert!(limiter.try_acquire(1));
        }

        // Next acquisition should fail (bucket empty)
        assert!(!limiter.try_acquire(1));
    }

    #[test]
    fn test_token_bucket_unlimited() {
        let limiter = TokenBucket::unlimited();

        // Should always succeed
        for _ in 0..10000 {
            assert!(limiter.try_acquire(1));
        }

        assert!(!limiter.is_enabled());
    }

    #[test]
    fn test_token_bucket_refill() {
        let limiter = TokenBucket::new(10000, 100);

        // Drain the bucket
        for _ in 0..100 {
            limiter.try_acquire(1);
        }

        assert_eq!(limiter.available(), 0);

        // Wait for refill
        thread::sleep(Duration::from_millis(50));

        // Should have some tokens now
        assert!(limiter.available() > 0);
    }

    #[test]
    fn test_token_bucket_acquire_blocking() {
        let limiter = TokenBucket::new(1000, 10);

        // Drain the bucket
        for _ in 0..10 {
            limiter.try_acquire(1);
        }

        let start = std::time::Instant::now();
        let wait_time = limiter.acquire(1);
        let elapsed = start.elapsed();

        // Should have waited some time
        assert!(wait_time > Duration::ZERO);
        assert!(elapsed >= wait_time);
    }

    #[test]
    fn test_token_bucket_multi_token() {
        let limiter = TokenBucket::new(1000, 100);

        // Should be able to acquire multiple tokens
        assert!(limiter.try_acquire(50));
        assert!(limiter.try_acquire(50));

        // Should fail to acquire more
        assert!(!limiter.try_acquire(1));
    }

    #[test]
    fn test_set_rate() {
        let limiter = TokenBucket::new(1000, 100);
        assert_eq!(limiter.rate(), 1000);
        assert_eq!(limiter.burst(), 100);

        limiter.set_rate(5000);
        assert_eq!(limiter.rate(), 5000);
        assert!(limiter.is_enabled());

        limiter.set_rate(0);
        assert_eq!(limiter.rate(), 0);
        assert!(!limiter.is_enabled());
    }

    #[test]
    fn test_set_burst() {
        let limiter = TokenBucket::new(1000, 100);
        assert_eq!(limiter.burst(), 100);

        limiter.set_burst(200);
        assert_eq!(limiter.burst(), 200);
    }

    #[test]
    fn test_token_bucket_reset() {
        let limiter = TokenBucket::new(1000, 100);

        // Drain the bucket
        for _ in 0..100 {
            limiter.try_acquire(1);
        }

        assert_eq!(limiter.available(), 0);

        limiter.reset();

        // Should be full again
        assert_eq!(limiter.available(), 100);
    }

    #[test]
    fn test_sliding_window() {
        let limiter = SlidingWindowLimiter::new(100, 1000);

        // Should allow up to 100 events per second
        let mut allowed = 0;
        for _ in 0..150 {
            if limiter.try_record() {
                allowed += 1;
            }
        }

        // Should have limited some events
        assert!(allowed <= 100);
        assert!(allowed > 50); // But should allow a reasonable number
    }

    #[test]
    fn test_sliding_window_rate_calculation() {
        let limiter = SlidingWindowLimiter::new(1000, 1000);

        // Record some events
        for _ in 0..100 {
            limiter.try_record();
        }

        let rate = limiter.current_rate();
        assert!(rate > 0);
        assert!(rate <= 1000);
    }

    #[test]
    fn test_sliding_window_set_rate() {
        let limiter = SlidingWindowLimiter::new(100, 1000);

        limiter.set_rate(200);

        // Should now allow more events
        let mut allowed = 0;
        for _ in 0..250 {
            if limiter.try_record() {
                allowed += 1;
            }
        }

        assert!(allowed > 100); // Should allow more than original limit
        assert!(allowed <= 200); // But not more than new limit
    }

    // Property-based tests
    proptest! {
        #[test]
        fn test_token_bucket_properties(
            rate in 1u64..100_000,
            burst in 1u64..1000
        ) {
            let limiter = TokenBucket::new(rate, burst);

            prop_assert_eq!(limiter.rate(), rate);
            prop_assert_eq!(limiter.burst(), burst);
            prop_assert!(limiter.is_enabled());

            // Should be able to acquire up to burst tokens
            let mut acquired = 0;
            while limiter.try_acquire(1) {
                acquired += 1;
                if acquired > burst * 2 {
                    break; // Safety check
                }
            }

            prop_assert_eq!(acquired, burst);
        }

        #[test]
        fn test_token_bucket_rate_changes(
            initial_rate in 1u64..10_000,
            new_rate in 1u64..10_000,
            burst in 1u64..100
        ) {
            let limiter = TokenBucket::new(initial_rate, burst);
            prop_assert_eq!(limiter.rate(), initial_rate);

            limiter.set_rate(new_rate);
            prop_assert_eq!(limiter.rate(), new_rate);
            prop_assert!(limiter.is_enabled());
        }

        #[test]
        fn test_sliding_window_properties(
            rate_per_second in 1u64..1000,
            window_ms in 100u64..5000,
            events_to_try in 1usize..2000
        ) {
            let limiter = SlidingWindowLimiter::new(rate_per_second, window_ms);

            let mut allowed = 0;
            for _ in 0..events_to_try {
                if limiter.try_record() {
                    allowed += 1;
                }
            }

            let max_expected = (rate_per_second * window_ms) / 1000;
            prop_assert!(allowed <= max_expected as usize + 10); // Small tolerance
        }

        #[test]
        fn test_token_bucket_acquire_properties(
            rate in 100u64..10_000,
            tokens_to_acquire in 1u64..50
        ) {
            let limiter = TokenBucket::new(rate, tokens_to_acquire);

            // Should be able to acquire immediately (bucket starts full)
            let wait_time = limiter.acquire(tokens_to_acquire);
            prop_assert_eq!(wait_time, Duration::ZERO);

            // Next acquisition should require waiting
            let start = std::time::Instant::now();
            let wait_time2 = limiter.acquire(1);
            let elapsed = start.elapsed();

            prop_assert!(wait_time2 > Duration::ZERO);
            prop_assert!(elapsed >= wait_time2);
        }
    }
}
