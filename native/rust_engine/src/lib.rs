//! NetStress Native Engine
//! High-performance packet generation using Rust with PyO3 bindings

mod atomic_stats;
mod audit;
mod backend;
mod backend_selector;
mod engine;
mod packet;
mod pool;
mod protocol_builder;
mod queue;
mod rate_limiter;
mod safety;
mod simd;
mod stats;

#[cfg(target_os = "linux")]
mod linux_optimizations;

#[cfg(target_os = "windows")]
mod windows_backend;

#[cfg(target_os = "macos")]
mod macos_backend;

use parking_lot::RwLock;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyModule;
use std::sync::Arc;
use std::time::{Duration, Instant};

pub use atomic_stats::{AtomicStats, StatsCollector, StatsSnapshot, ThreadStats};
pub use audit::{AuditEntry, AuditEventType, AuditLogger, ChainVerificationResult};
pub use backend_selector::{BackendSelector, CapabilityReport};
pub use engine::{EngineConfig, EngineState, FloodEngine};
pub use packet::{PacketBuilder, PacketFlags, Protocol};
pub use pool::PacketPool;
pub use protocol_builder::{BatchPacketGenerator, FragmentConfig, ProtocolBuilder, SpoofConfig};
pub use safety::{EmergencyStop, SafetyController, SafetyError, TargetAuthorization};
pub use stats::Stats;
// Note: StatsSnapshot is already exported from atomic_stats

#[cfg(target_os = "linux")]
pub use linux_optimizations::LinuxOptimizer;

#[cfg(target_os = "windows")]
pub use windows_backend::{IOCPBackend, RegisteredIOBackend, WindowsOptimizer};

#[cfg(target_os = "macos")]
pub use macos_backend::{KqueueBackend, MacOSOptimizer};

// FFI declarations for C driver
#[cfg(feature = "dpdk")]
extern "C" {
    fn init_dpdk_port(port_id: i32) -> i32;
    fn dpdk_send_burst(
        port_id: i32,
        packets: *const *const u8,
        lengths: *const u32,
        count: u32,
    ) -> i32;
    fn cleanup_dpdk() -> i32;
}

#[cfg(feature = "af_xdp")]
extern "C" {
    fn init_af_xdp(ifname: *const i8) -> i32;
    fn af_xdp_send(data: *const u8, len: u32) -> i32;
    fn cleanup_af_xdp() -> i32;
}

// Fallback stubs when features not enabled
#[cfg(not(feature = "dpdk"))]
mod dpdk_stub {
    pub unsafe fn init_dpdk_port(_port_id: i32) -> i32 {
        -1
    }
    pub unsafe fn dpdk_send_burst(
        _port_id: i32,
        _packets: *const *const u8,
        _lengths: *const u32,
        _count: u32,
    ) -> i32 {
        -1
    }
    pub unsafe fn cleanup_dpdk() -> i32 {
        0
    }
}
#[cfg(not(feature = "dpdk"))]
use dpdk_stub::*;

/// Python-exposed PacketEngine class
#[pyclass]
pub struct PacketEngine {
    target: String,
    port: u16,
    engine: Arc<RwLock<FloodEngine>>,
    stats: Arc<RwLock<Stats>>,
}

#[pymethods]
impl PacketEngine {
    #[new]
    #[pyo3(signature = (target, port, threads=4, packet_size=1472))]
    fn new(target: String, port: u16, threads: usize, packet_size: usize) -> PyResult<Self> {
        let config = EngineConfig {
            target: target.clone(),
            port,
            threads,
            packet_size,
            ..Default::default()
        };

        let engine = FloodEngine::new(config)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create engine: {}", e)))?;

        Ok(Self {
            target,
            port,
            engine: Arc::new(RwLock::new(engine)),
            stats: Arc::new(RwLock::new(Stats::new())),
        })
    }

    /// Start the packet engine
    fn start(&self) -> PyResult<()> {
        let mut engine = self.engine.write();
        engine
            .start()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to start: {}", e)))
    }

    /// Stop the packet engine
    fn stop(&self) -> PyResult<()> {
        let mut engine = self.engine.write();
        engine
            .stop()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to stop: {}", e)))
    }

    /// Get current statistics
    fn get_stats(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let engine = self.engine.read();
            let snapshot = engine.get_stats();

            let dict = pyo3::types::PyDict::new_bound(py);
            dict.set_item("packets_sent", snapshot.packets_sent)?;
            dict.set_item("bytes_sent", snapshot.bytes_sent)?;
            dict.set_item("packets_per_second", snapshot.pps)?;
            dict.set_item("bytes_per_second", snapshot.bps)?;
            dict.set_item("errors", snapshot.errors)?;
            dict.set_item("duration_secs", snapshot.duration.as_secs_f64())?;

            Ok(dict.into())
        })
    }

    /// Check if engine is running
    fn is_running(&self) -> bool {
        let engine = self.engine.read();
        engine.is_running()
    }

    /// Set target rate (packets per second)
    fn set_rate(&self, pps: u64) -> PyResult<()> {
        let mut engine = self.engine.write();
        engine.set_rate(pps);
        Ok(())
    }

    /// Get target info
    fn __repr__(&self) -> String {
        format!("PacketEngine(target='{}', port={})", self.target, self.port)
    }
}

/// High-level flood function exposed to Python
#[pyfunction]
#[pyo3(signature = (target, port, duration=60, rate=100000, threads=4, packet_size=1472, protocol="udp"))]
fn start_flood(
    target: &str,
    port: u16,
    duration: u64,
    rate: u64,
    threads: usize,
    packet_size: usize,
    protocol: &str,
) -> PyResult<PyObject> {
    let proto = match protocol.to_lowercase().as_str() {
        "udp" => Protocol::UDP,
        "tcp" => Protocol::TCP,
        "icmp" => Protocol::ICMP,
        "http" => Protocol::HTTP,
        _ => {
            return Err(PyRuntimeError::new_err(format!(
                "Unknown protocol: {}",
                protocol
            )))
        }
    };

    let config = EngineConfig {
        target: target.to_string(),
        port,
        threads,
        packet_size,
        protocol: proto,
        rate_limit: Some(rate),
        ..Default::default()
    };

    let mut engine = FloodEngine::new(config)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to create engine: {}", e)))?;

    engine
        .start()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to start: {}", e)))?;

    // Run for specified duration
    std::thread::sleep(Duration::from_secs(duration));

    engine
        .stop()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to stop: {}", e)))?;

    // Return final stats
    Python::with_gil(|py| {
        let snapshot = engine.get_stats();
        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("packets_sent", snapshot.packets_sent)?;
        dict.set_item("bytes_sent", snapshot.bytes_sent)?;
        dict.set_item("average_pps", snapshot.pps)?;
        dict.set_item("average_bps", snapshot.bps)?;
        dict.set_item("errors", snapshot.errors)?;
        dict.set_item("duration_secs", snapshot.duration.as_secs_f64())?;
        Ok(dict.into())
    })
}

/// Build a custom packet
#[pyfunction]
#[pyo3(signature = (src_ip, dst_ip, src_port, dst_port, protocol="udp", payload=None))]
fn build_packet(
    src_ip: &str,
    dst_ip: &str,
    src_port: u16,
    dst_port: u16,
    protocol: &str,
    payload: Option<&[u8]>,
) -> PyResult<Vec<u8>> {
    let proto = match protocol.to_lowercase().as_str() {
        "udp" => Protocol::UDP,
        "tcp" => Protocol::TCP,
        "icmp" => Protocol::ICMP,
        _ => {
            return Err(PyRuntimeError::new_err(format!(
                "Unknown protocol: {}",
                protocol
            )))
        }
    };

    let builder = PacketBuilder::new()
        .src_ip(src_ip)
        .dst_ip(dst_ip)
        .src_port(src_port)
        .dst_port(dst_port)
        .protocol(proto);

    let builder = if let Some(data) = payload {
        builder.payload(data)
    } else {
        builder
    };

    builder
        .build()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to build packet: {}", e)))
}

/// Get system capabilities
#[pyfunction]
fn get_capabilities() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new_bound(py);

        // Check DPDK availability
        #[cfg(feature = "dpdk")]
        dict.set_item("dpdk", true)?;
        #[cfg(not(feature = "dpdk"))]
        dict.set_item("dpdk", false)?;

        // Check AF_XDP availability
        #[cfg(feature = "af_xdp")]
        dict.set_item("af_xdp", true)?;
        #[cfg(not(feature = "af_xdp"))]
        dict.set_item("af_xdp", false)?;

        // Platform info
        dict.set_item("platform", std::env::consts::OS)?;
        dict.set_item("arch", std::env::consts::ARCH)?;

        // Thread count
        dict.set_item(
            "cpu_count",
            std::thread::available_parallelism()
                .map(|p| p.get())
                .unwrap_or(1),
        )?;

        Ok(dict.into())
    })
}

/// Get current statistics snapshot
#[pyfunction]
fn get_stats() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("status", "idle")?;
        dict.set_item("packets_sent", 0u64)?;
        dict.set_item("bytes_sent", 0u64)?;
        Ok(dict.into())
    })
}

/// Build UDP packet with optional spoofing
#[pyfunction]
#[pyo3(signature = (dst_ip, dst_port, payload, spoof_cidr=None))]
fn build_udp_packet(
    dst_ip: &str,
    dst_port: u16,
    payload: &[u8],
    spoof_cidr: Option<&str>,
) -> PyResult<Vec<u8>> {
    let mut builder = protocol_builder::ProtocolBuilder::new();

    if let Some(cidr) = spoof_cidr {
        builder = builder
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    builder
        .build_udp(dst_ip, dst_port, payload)
        .map_err(|e| PyRuntimeError::new_err(format!("Build failed: {}", e)))
}

/// Build TCP SYN packet with optional spoofing
#[pyfunction]
#[pyo3(signature = (dst_ip, dst_port, spoof_cidr=None))]
fn build_tcp_syn(dst_ip: &str, dst_port: u16, spoof_cidr: Option<&str>) -> PyResult<Vec<u8>> {
    let mut builder = protocol_builder::ProtocolBuilder::new();

    if let Some(cidr) = spoof_cidr {
        builder = builder
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    builder
        .build_tcp_syn(dst_ip, dst_port)
        .map_err(|e| PyRuntimeError::new_err(format!("Build failed: {}", e)))
}

/// Build ICMP echo request with optional spoofing
#[pyfunction]
#[pyo3(signature = (dst_ip, payload, spoof_cidr=None))]
fn build_icmp_echo(dst_ip: &str, payload: &[u8], spoof_cidr: Option<&str>) -> PyResult<Vec<u8>> {
    let mut builder = protocol_builder::ProtocolBuilder::new();

    if let Some(cidr) = spoof_cidr {
        builder = builder
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    builder
        .build_icmp_echo(dst_ip, payload)
        .map_err(|e| PyRuntimeError::new_err(format!("Build failed: {}", e)))
}

/// Build HTTP GET request packet
#[pyfunction]
#[pyo3(signature = (dst_ip, dst_port, host, path="/", spoof_cidr=None))]
fn build_http_get(
    dst_ip: &str,
    dst_port: u16,
    host: &str,
    path: &str,
    spoof_cidr: Option<&str>,
) -> PyResult<Vec<u8>> {
    let mut builder = protocol_builder::ProtocolBuilder::new();

    if let Some(cidr) = spoof_cidr {
        builder = builder
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    builder
        .build_http_get(dst_ip, dst_port, host, path)
        .map_err(|e| PyRuntimeError::new_err(format!("Build failed: {}", e)))
}

/// Build DNS query packet
#[pyfunction]
#[pyo3(signature = (dst_ip, domain, spoof_cidr=None))]
fn build_dns_query(dst_ip: &str, domain: &str, spoof_cidr: Option<&str>) -> PyResult<Vec<u8>> {
    let mut builder = protocol_builder::ProtocolBuilder::new();

    if let Some(cidr) = spoof_cidr {
        builder = builder
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    builder
        .build_dns_query(dst_ip, domain)
        .map_err(|e| PyRuntimeError::new_err(format!("Build failed: {}", e)))
}

/// Generate batch of packets for high-throughput scenarios
#[pyfunction]
#[pyo3(signature = (dst_ip, dst_port, protocol, payload_size, count, spoof_cidr=None))]
fn generate_packet_batch(
    dst_ip: &str,
    dst_port: u16,
    protocol: &str,
    payload_size: usize,
    count: usize,
    spoof_cidr: Option<&str>,
) -> PyResult<Vec<Vec<u8>>> {
    let proto = match protocol.to_lowercase().as_str() {
        "udp" => Protocol::UDP,
        "tcp" => Protocol::TCP,
        "icmp" => Protocol::ICMP,
        "http" => Protocol::HTTP,
        _ => {
            return Err(PyRuntimeError::new_err(format!(
                "Unknown protocol: {}",
                protocol
            )))
        }
    };

    let mut gen =
        protocol_builder::BatchPacketGenerator::new(dst_ip, dst_port, proto, payload_size);

    if let Some(cidr) = spoof_cidr {
        gen = gen
            .with_spoofing(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("Invalid CIDR: {}", e)))?;
    }

    Ok(gen.generate_batch(count))
}

/// Get detailed capability report
#[pyfunction]
fn get_capability_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let selector = backend_selector::BackendSelector::new();
        let report = backend_selector::CapabilityReport::generate(&selector);

        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", report.platform)?;
        dict.set_item("arch", report.arch)?;
        dict.set_item("cpu_count", report.cpu_count)?;
        dict.set_item("available_backends", report.available_backends)?;
        dict.set_item("active_backend", report.active_backend)?;
        dict.set_item("has_dpdk", report.has_dpdk)?;
        dict.set_item("has_af_xdp", report.has_af_xdp)?;
        dict.set_item("has_io_uring", report.has_io_uring)?;
        dict.set_item("has_sendmmsg", report.has_sendmmsg)?;
        dict.set_item("kernel_version", report.kernel_version)?;

        Ok(dict.into())
    })
}

/// Get list of available backends
#[pyfunction]
fn get_available_backends() -> PyResult<Vec<String>> {
    let selector = backend_selector::BackendSelector::new();
    Ok(selector
        .available_backends()
        .iter()
        .map(|b| b.name().to_string())
        .collect())
}

/// Get real-time statistics in JSON format
#[pyfunction]
fn get_realtime_stats_json() -> PyResult<String> {
    let collector = atomic_stats::StatsCollector::new();
    Ok(collector.json_metrics())
}

/// Get Prometheus-format metrics
#[pyfunction]
fn get_prometheus_metrics() -> PyResult<String> {
    let collector = atomic_stats::StatsCollector::new();
    Ok(collector.prometheus_metrics())
}

/// Get Linux optimization report (Linux only)
#[cfg(target_os = "linux")]
#[pyfunction]
fn get_linux_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let optimizer = linux_optimizations::LinuxOptimizer::new();
        let caps = optimizer.capabilities();

        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", "linux")?;
        dict.set_item(
            "kernel_version",
            format!("{}.{}", caps.kernel_version.0, caps.kernel_version.1),
        )?;
        dict.set_item("cpu_count", caps.cpu_count)?;
        dict.set_item("numa_nodes", caps.numa_nodes)?;

        // Feature availability
        dict.set_item("has_dpdk", caps.has_dpdk)?;
        dict.set_item("has_af_xdp", caps.has_af_xdp)?;
        dict.set_item("has_io_uring", caps.has_io_uring)?;
        dict.set_item("has_sendmmsg", caps.has_sendmmsg)?;
        dict.set_item("has_raw_socket", caps.has_raw_socket)?;

        // Enabled features
        dict.set_item("enabled_features", optimizer.enabled_features())?;

        // Recommended backend
        dict.set_item(
            "recommended_backend",
            optimizer.get_recommended_backend().name(),
        )?;

        // Performance recommendations
        dict.set_item(
            "performance_recommendations",
            optimizer.get_performance_recommendations(),
        )?;

        Ok(dict.into())
    })
}

/// Get Linux optimization report (stub for non-Linux)
#[cfg(not(target_os = "linux"))]
#[pyfunction]
fn get_linux_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", std::env::consts::OS)?;
        dict.set_item(
            "error",
            "Linux optimizations not available on this platform",
        )?;
        Ok(dict.into())
    })
}

/// Get Windows optimization report (Windows only)
#[cfg(target_os = "windows")]
#[pyfunction]
fn get_windows_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let optimizer = windows_backend::WindowsOptimizer::new();
        let caps = optimizer.capabilities();

        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", "windows")?;
        dict.set_item(
            "winsock_version",
            format!("{}.{}", caps.winsock_version.0, caps.winsock_version.1),
        )?;
        dict.set_item("cpu_count", caps.cpu_count)?;

        // Feature availability
        dict.set_item("has_iocp", caps.has_iocp)?;
        dict.set_item("has_registered_io", caps.has_registered_io)?;

        // Recommended backend
        dict.set_item(
            "recommended_backend",
            optimizer.get_recommended_backend().name(),
        )?;

        // Performance recommendations
        dict.set_item(
            "performance_recommendations",
            optimizer.get_performance_recommendations(),
        )?;

        // Windows version info
        let (major, minor) = optimizer.get_windows_version();
        dict.set_item("windows_version", format!("{}.{}", major, minor))?;
        dict.set_item("is_server", optimizer.is_windows_server())?;

        Ok(dict.into())
    })
}

/// Get Windows optimization report (stub for non-Windows)
#[cfg(not(target_os = "windows"))]
#[pyfunction]
fn get_windows_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", std::env::consts::OS)?;
        dict.set_item(
            "error",
            "Windows optimizations not available on this platform",
        )?;
        Ok(dict.into())
    })
}

/// Get macOS optimization report (macOS only)
#[cfg(target_os = "macos")]
#[pyfunction]
fn get_macos_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let optimizer = macos_backend::MacOSOptimizer::new();
        let caps = optimizer.capabilities();

        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", "macos")?;
        dict.set_item(
            "darwin_version",
            format!("{}.{}", caps.darwin_version.0, caps.darwin_version.1),
        )?;
        dict.set_item("cpu_count", caps.cpu_count)?;

        // Feature availability
        dict.set_item("has_kqueue", caps.has_kqueue)?;
        dict.set_item("has_sendfile", caps.has_sendfile)?;
        dict.set_item("has_so_nosigpipe", caps.has_so_nosigpipe)?;
        dict.set_item("has_so_reuseport", caps.has_so_reuseport)?;

        // Enabled features
        dict.set_item("enabled_features", optimizer.enabled_features())?;

        // Recommended backend
        dict.set_item(
            "recommended_backend",
            optimizer.get_recommended_backend().name(),
        )?;

        // Performance recommendations
        dict.set_item(
            "performance_recommendations",
            optimizer.get_performance_recommendations(),
        )?;

        // macOS version info
        let (major, minor) = optimizer.get_darwin_version();
        dict.set_item("darwin_version", format!("{}.{}", major, minor))?;
        dict.set_item("is_server", optimizer.is_macos_server())?;

        Ok(dict.into())
    })
}

/// Get macOS optimization report (stub for non-macOS)
#[cfg(not(target_os = "macos"))]
#[pyfunction]
fn get_macos_optimization_report() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let dict = pyo3::types::PyDict::new_bound(py);
        dict.set_item("platform", std::env::consts::OS)?;
        dict.set_item(
            "error",
            "macOS optimizations not available on this platform",
        )?;
        Ok(dict.into())
    })
}

/// Python-exposed SafetyController
#[pyclass]
pub struct PySafetyController {
    inner: safety::SafetyController,
}

#[pymethods]
impl PySafetyController {
    #[new]
    #[pyo3(signature = (max_pps=0))]
    fn new(max_pps: u64) -> Self {
        Self {
            inner: safety::SafetyController::new(max_pps),
        }
    }

    /// Create permissive controller (for testing)
    #[staticmethod]
    fn permissive() -> Self {
        Self {
            inner: safety::SafetyController::permissive(),
        }
    }

    /// Authorize an IP address
    fn authorize_ip(&self, ip: &str) -> PyResult<()> {
        let addr: std::net::IpAddr = ip
            .parse()
            .map_err(|_| PyRuntimeError::new_err(format!("Invalid IP: {}", ip)))?;
        self.inner.authorization.authorize_ip(addr);
        Ok(())
    }

    /// Authorize a CIDR range
    fn authorize_cidr(&self, cidr: &str) -> PyResult<()> {
        self.inner
            .authorization
            .authorize_cidr(cidr)
            .map_err(|e| PyRuntimeError::new_err(format!("{}", e)))
    }

    /// Authorize a domain
    fn authorize_domain(&self, domain: &str) {
        self.inner.authorization.authorize_domain(domain);
    }

    /// Check if target is authorized
    fn is_authorized(&self, target: &str) -> PyResult<bool> {
        match self.inner.authorization.is_authorized(target) {
            Ok(()) => Ok(true),
            Err(_) => Ok(false),
        }
    }

    /// Set strict mode
    fn set_strict_mode(&self, strict: bool) {
        self.inner.authorization.set_strict_mode(strict);
    }

    /// Allow localhost
    fn set_allow_localhost(&self, allow: bool) {
        self.inner.authorization.set_allow_localhost(allow);
    }

    /// Allow private networks
    fn set_allow_private(&self, allow: bool) {
        self.inner.authorization.set_allow_private(allow);
    }

    /// Set maximum PPS
    fn set_max_pps(&self, max_pps: u64) {
        self.inner.rate_limiter.set_max_pps(max_pps);
    }

    /// Get current PPS
    fn current_pps(&self) -> u64 {
        self.inner.rate_limiter.current_pps()
    }

    /// Trigger emergency stop
    fn emergency_stop(&self, reason: &str) {
        self.inner.emergency_stop.trigger(reason);
    }

    /// Check if emergency stopped
    fn is_stopped(&self) -> bool {
        self.inner.emergency_stop.is_stopped()
    }

    /// Reset emergency stop
    fn reset_emergency_stop(&self) {
        self.inner.emergency_stop.reset();
    }

    /// Get stop reason
    fn stop_reason(&self) -> Option<String> {
        self.inner.emergency_stop.reason()
    }

    /// Perform all safety checks
    fn check_all(&self, target: &str) -> PyResult<()> {
        self.inner
            .check_all(target)
            .map_err(|e| PyRuntimeError::new_err(format!("{}", e)))
    }
}

/// Python-exposed AuditLogger
#[pyclass]
pub struct PyAuditLogger {
    inner: Arc<audit::AuditLogger>,
}

#[pymethods]
impl PyAuditLogger {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(audit::AuditLogger::new()),
        }
    }

    /// Create with file output
    #[staticmethod]
    fn with_file(path: &str) -> PyResult<Self> {
        let logger = audit::AuditLogger::with_file(path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create audit log: {}", e)))?;
        Ok(Self {
            inner: Arc::new(logger),
        })
    }

    /// Log engine start
    fn log_engine_start(&self, target: &str, config: &str) {
        self.inner.log_engine_start(target, config);
    }

    /// Log engine stop
    fn log_engine_stop(&self, stats: &str) {
        self.inner.log_engine_stop(stats);
    }

    /// Log target authorized
    fn log_target_authorized(&self, target: &str) {
        self.inner.log_target_authorized(target);
    }

    /// Log target rejected
    fn log_target_rejected(&self, target: &str, reason: &str) {
        self.inner.log_target_rejected(target, reason);
    }

    /// Log emergency stop
    fn log_emergency_stop(&self, reason: &str) {
        self.inner.log_emergency_stop(reason);
    }

    /// Log error
    fn log_error(&self, error: &str) {
        self.inner.log_error(error);
    }

    /// Verify chain integrity
    fn verify_chain(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let result = self.inner.verify_chain();
            let dict = pyo3::types::PyDict::new_bound(py);
            dict.set_item("valid", result.valid)?;
            dict.set_item("entries_checked", result.entries_checked)?;
            dict.set_item("first_invalid", result.first_invalid)?;
            dict.set_item("error", result.error)?;
            Ok(dict.into())
        })
    }

    /// Export to JSON
    fn export_json(&self) -> String {
        self.inner.export_json()
    }

    /// Get entry count
    fn entry_count(&self) -> usize {
        self.inner.entries().len()
    }
}

/// Python module definition
#[pymodule]
fn netstress_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Core classes
    m.add_class::<PacketEngine>()?;
    m.add_class::<PySafetyController>()?;
    m.add_class::<PyAuditLogger>()?;

    // Core functions
    m.add_function(wrap_pyfunction!(start_flood, m)?)?;
    m.add_function(wrap_pyfunction!(build_packet, m)?)?;
    m.add_function(wrap_pyfunction!(get_capabilities, m)?)?;
    m.add_function(wrap_pyfunction!(get_stats, m)?)?;

    // Protocol builder functions
    m.add_function(wrap_pyfunction!(build_udp_packet, m)?)?;
    m.add_function(wrap_pyfunction!(build_tcp_syn, m)?)?;
    m.add_function(wrap_pyfunction!(build_icmp_echo, m)?)?;
    m.add_function(wrap_pyfunction!(build_http_get, m)?)?;
    m.add_function(wrap_pyfunction!(build_dns_query, m)?)?;
    m.add_function(wrap_pyfunction!(generate_packet_batch, m)?)?;

    // Backend selection functions
    m.add_function(wrap_pyfunction!(get_capability_report, m)?)?;
    m.add_function(wrap_pyfunction!(get_available_backends, m)?)?;

    // Statistics functions
    m.add_function(wrap_pyfunction!(get_realtime_stats_json, m)?)?;
    m.add_function(wrap_pyfunction!(get_prometheus_metrics, m)?)?;

    // Platform optimization functions
    m.add_function(wrap_pyfunction!(get_linux_optimization_report, m)?)?;
    m.add_function(wrap_pyfunction!(get_windows_optimization_report, m)?)?;
    m.add_function(wrap_pyfunction!(get_macos_optimization_report, m)?)?;

    // Version info
    m.add("__version__", "2.0.0")?;
    m.add("__author__", "NetStress Team")?;

    Ok(())
}
