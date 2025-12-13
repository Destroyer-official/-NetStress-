//! Backend auto-detection and selection
//! Implements priority-based backend selection with graceful fallback

use crate::backend::{create_best_backend, detect_system_capabilities, select_best_backend};
use crate::backend::{Backend, BackendError, BackendType, StandardBackend, SystemCapabilities};
use parking_lot::RwLock;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tracing::{debug, info, warn};

/// Backend selector with automatic fallback
pub struct BackendSelector {
    /// Current active backend
    active_backend: Arc<RwLock<Box<dyn Backend>>>,
    /// System capabilities
    capabilities: SystemCapabilities,
    /// Preferred backend (user override)
    preferred: Option<BackendType>,
    /// Whether fallback is enabled
    fallback_enabled: AtomicBool,
    /// Backend priority order
    priority: Vec<BackendType>,
}

impl BackendSelector {
    /// Get platform-specific backend priority
    fn get_platform_priority() -> Vec<BackendType> {
        #[cfg(target_os = "linux")]
        {
            vec![
                BackendType::Dpdk,
                BackendType::AfXdp,
                BackendType::IoUring,
                BackendType::Sendmmsg,
                BackendType::RawSocket,
            ]
        }
        #[cfg(target_os = "windows")]
        {
            vec![
                BackendType::RegisteredIO,
                BackendType::IOCP,
                BackendType::RawSocket,
            ]
        }
        #[cfg(target_os = "macos")]
        {
            vec![BackendType::Kqueue, BackendType::RawSocket]
        }
        #[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
        {
            vec![BackendType::RawSocket]
        }
    }

    /// Create a new backend selector with auto-detection
    pub fn new() -> Self {
        let capabilities = detect_system_capabilities();
        let best = select_best_backend(&capabilities);
        let backend = create_best_backend();

        info!("Auto-detected backend: {:?}", best);

        Self {
            active_backend: Arc::new(RwLock::new(backend)),
            capabilities,
            preferred: None,
            fallback_enabled: AtomicBool::new(true),
            priority: Self::get_platform_priority(),
        }
    }

    /// Create with a specific preferred backend
    pub fn with_preferred(preferred: BackendType) -> Result<Self, BackendError> {
        let mut selector = Self::new();
        selector.set_preferred(preferred)?;
        Ok(selector)
    }

    /// Set preferred backend
    pub fn set_preferred(&mut self, backend_type: BackendType) -> Result<(), BackendError> {
        if !self.is_backend_available(backend_type) {
            return Err(BackendError::NotAvailable(format!(
                "Backend {:?} is not available on this system",
                backend_type
            )));
        }

        self.preferred = Some(backend_type);
        self.switch_to(backend_type)?;
        Ok(())
    }

    /// Check if a backend is available
    pub fn is_backend_available(&self, backend_type: BackendType) -> bool {
        match backend_type {
            BackendType::None => false,
            BackendType::RawSocket => self.capabilities.has_raw_socket,
            BackendType::Sendmmsg => self.capabilities.has_sendmmsg,
            BackendType::IoUring => self.capabilities.has_io_uring,
            BackendType::AfXdp => self.capabilities.has_af_xdp,
            BackendType::Dpdk => self.capabilities.has_dpdk,
            BackendType::IOCP => self.capabilities.has_iocp,
            BackendType::RegisteredIO => self.capabilities.has_registered_io,
            BackendType::Kqueue => self.capabilities.has_kqueue,
        }
    }

    /// Get list of available backends
    pub fn available_backends(&self) -> Vec<BackendType> {
        self.priority
            .iter()
            .filter(|&&bt| self.is_backend_available(bt))
            .copied()
            .collect()
    }

    /// Switch to a specific backend
    fn switch_to(&mut self, backend_type: BackendType) -> Result<(), BackendError> {
        let mut backend: Box<dyn Backend> = match backend_type {
            BackendType::RawSocket | BackendType::None => Box::new(StandardBackend::new()),
            #[cfg(target_os = "linux")]
            BackendType::Sendmmsg
            | BackendType::IoUring
            | BackendType::AfXdp
            | BackendType::Dpdk => Box::new(crate::backend::NativeBackend::new(backend_type)),
            #[cfg(target_os = "windows")]
            BackendType::IOCP => Box::new(crate::windows_backend::IOCPBackend::new()),
            #[cfg(target_os = "windows")]
            BackendType::RegisteredIO => {
                Box::new(crate::windows_backend::RegisteredIOBackend::new())
            }
            #[cfg(target_os = "macos")]
            BackendType::Kqueue => Box::new(crate::macos_backend::KqueueBackend::new()),
            #[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
            _ => Box::new(StandardBackend::new()),
            #[cfg(any(target_os = "windows", target_os = "macos"))]
            _ => Box::new(StandardBackend::new()),
        };

        backend.init()?;

        let mut active = self.active_backend.write();
        let _ = active.cleanup();
        *active = backend;

        info!("Switched to backend: {:?}", backend_type);
        Ok(())
    }

    /// Get the current active backend type
    pub fn current_backend(&self) -> BackendType {
        self.active_backend.read().backend_type()
    }

    /// Get system capabilities
    pub fn capabilities(&self) -> &SystemCapabilities {
        &self.capabilities
    }

    /// Enable or disable automatic fallback
    pub fn set_fallback_enabled(&self, enabled: bool) {
        self.fallback_enabled.store(enabled, Ordering::SeqCst);
    }

    /// Check if fallback is enabled
    pub fn is_fallback_enabled(&self) -> bool {
        self.fallback_enabled.load(Ordering::Relaxed)
    }

    /// Try to send with automatic fallback on failure
    pub fn send_with_fallback(
        &self,
        data: &[u8],
        dest: std::net::SocketAddr,
    ) -> Result<usize, BackendError> {
        let backend = self.active_backend.read();

        match backend.send(data, dest) {
            Ok(n) => Ok(n),
            Err(e) => {
                if self.fallback_enabled.load(Ordering::Relaxed) {
                    warn!("Send failed, attempting fallback: {}", e);
                    drop(backend);
                    self.try_fallback()?;
                    self.active_backend.read().send(data, dest)
                } else {
                    Err(e)
                }
            }
        }
    }

    /// Try to send batch with automatic fallback
    pub fn send_batch_with_fallback(
        &self,
        packets: &[&[u8]],
        dest: std::net::SocketAddr,
    ) -> Result<usize, BackendError> {
        let backend = self.active_backend.read();

        match backend.send_batch(packets, dest) {
            Ok(n) => Ok(n),
            Err(e) => {
                if self.fallback_enabled.load(Ordering::Relaxed) {
                    warn!("Batch send failed, attempting fallback: {}", e);
                    drop(backend);
                    self.try_fallback()?;
                    self.active_backend.read().send_batch(packets, dest)
                } else {
                    Err(e)
                }
            }
        }
    }

    /// Attempt to fall back to the next available backend
    fn try_fallback(&self) -> Result<(), BackendError> {
        let current = self.current_backend();
        let current_idx = self.priority.iter().position(|&b| b == current);

        // Try each backend in priority order after current
        let start_idx = current_idx.map(|i| i + 1).unwrap_or(0);

        for &backend_type in &self.priority[start_idx..] {
            if self.is_backend_available(backend_type) {
                debug!("Attempting fallback to {:?}", backend_type);

                let mut backend: Box<dyn Backend> = match backend_type {
                    BackendType::RawSocket | BackendType::None => Box::new(StandardBackend::new()),
                    #[cfg(target_os = "linux")]
                    BackendType::Sendmmsg
                    | BackendType::IoUring
                    | BackendType::AfXdp
                    | BackendType::Dpdk => {
                        Box::new(crate::backend::NativeBackend::new(backend_type))
                    }
                    #[cfg(target_os = "windows")]
                    BackendType::IOCP => Box::new(crate::windows_backend::IOCPBackend::new()),
                    #[cfg(target_os = "windows")]
                    BackendType::RegisteredIO => {
                        Box::new(crate::windows_backend::RegisteredIOBackend::new())
                    }
                    #[cfg(target_os = "macos")]
                    BackendType::Kqueue => Box::new(crate::macos_backend::KqueueBackend::new()),
                    #[cfg(not(any(
                        target_os = "linux",
                        target_os = "windows",
                        target_os = "macos"
                    )))]
                    _ => Box::new(StandardBackend::new()),
                    #[cfg(any(target_os = "windows", target_os = "macos"))]
                    _ => Box::new(StandardBackend::new()),
                };

                if backend.init().is_ok() {
                    let mut active = self.active_backend.write();
                    let _ = active.cleanup();
                    *active = backend;
                    info!("Fallback successful: {:?}", backend_type);
                    return Ok(());
                }
            }
        }

        Err(BackendError::NotAvailable(
            "No fallback backend available".into(),
        ))
    }

    /// Get backend for direct access
    pub fn backend(&self) -> impl std::ops::Deref<Target = Box<dyn Backend>> + '_ {
        self.active_backend.read()
    }

    /// Initialize the active backend
    pub fn init(&self) -> Result<(), BackendError> {
        self.active_backend.write().init()
    }

    /// Cleanup the active backend
    pub fn cleanup(&self) -> Result<(), BackendError> {
        self.active_backend.write().cleanup()
    }
}

impl Default for BackendSelector {
    fn default() -> Self {
        Self::new()
    }
}

/// Backend capability report for Python
#[derive(Debug, Clone)]
pub struct CapabilityReport {
    pub platform: String,
    pub arch: String,
    pub cpu_count: i32,
    pub available_backends: Vec<String>,
    pub active_backend: String,
    pub has_dpdk: bool,
    pub has_af_xdp: bool,
    pub has_io_uring: bool,
    pub has_sendmmsg: bool,
    pub kernel_version: String,
}

impl CapabilityReport {
    pub fn generate(selector: &BackendSelector) -> Self {
        let caps = selector.capabilities();
        Self {
            platform: std::env::consts::OS.to_string(),
            arch: std::env::consts::ARCH.to_string(),
            cpu_count: caps.cpu_count,
            available_backends: selector
                .available_backends()
                .iter()
                .map(|b| b.name().to_string())
                .collect(),
            active_backend: selector.current_backend().name().to_string(),
            has_dpdk: caps.has_dpdk,
            has_af_xdp: caps.has_af_xdp,
            has_io_uring: caps.has_io_uring,
            has_sendmmsg: caps.has_sendmmsg,
            kernel_version: format!("{}.{}", caps.kernel_version.0, caps.kernel_version.1),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backend_selector_creation() {
        let selector = BackendSelector::new();
        assert!(selector.is_backend_available(BackendType::RawSocket));
    }

    #[test]
    fn test_available_backends() {
        let selector = BackendSelector::new();
        let available = selector.available_backends();
        assert!(!available.is_empty());
        assert!(available.contains(&BackendType::RawSocket));
    }

    #[test]
    fn test_fallback_enabled() {
        let selector = BackendSelector::new();
        assert!(selector.is_fallback_enabled());

        selector.set_fallback_enabled(false);
        assert!(!selector.is_fallback_enabled());
    }

    #[test]
    fn test_capability_report() {
        let selector = BackendSelector::new();
        let report = CapabilityReport::generate(&selector);

        assert!(!report.platform.is_empty());
        assert!(!report.arch.is_empty());
        assert!(report.cpu_count > 0);
    }
}
