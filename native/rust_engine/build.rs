//! Build script for netstress_engine
//! Compiles C driver shim and links with Rust

use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    // Get the C driver directory
    let c_driver_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .parent()
        .unwrap()
        .join("c_driver");

    // Skip C compilation for now to focus on Rust syntax checking
    if false && c_driver_dir.exists() {
        println!("cargo:rerun-if-changed={}", c_driver_dir.display());

        let mut build = cc::Build::new();
        build
            .file(c_driver_dir.join("driver_shim.c"))
            .include(&c_driver_dir)
            .opt_level(3)
            .warnings(true);

        // Platform-specific flags and feature detection
        #[cfg(target_os = "linux")]
        {
            build.flag("-D_GNU_SOURCE");

            // Always enable sendmmsg on Linux (available since 3.0)
            build.flag("-DHAS_SENDMMSG");
            println!("cargo:rustc-cfg=feature=\"sendmmsg\"");

            // Check for DPDK
            if check_dpdk_available() {
                build.flag("-DHAS_DPDK");
                println!("cargo:rustc-cfg=feature=\"dpdk\"");
                link_dpdk_libraries();
            }

            // Check for AF_XDP (requires libbpf and kernel 4.18+)
            if check_af_xdp_available() {
                build.flag("-DHAS_AF_XDP");
                println!("cargo:rustc-cfg=feature=\"af_xdp\"");
                println!("cargo:rustc-link-lib=bpf");
                println!("cargo:rustc-link-lib=xdp");
            }

            // Check for io_uring (requires liburing and kernel 5.1+)
            if check_io_uring_available() {
                build.flag("-DHAS_IO_URING");
                println!("cargo:rustc-cfg=feature=\"io_uring\"");
                println!("cargo:rustc-link-lib=uring");
            }
        }

        #[cfg(target_os = "windows")]
        {
            // Enable Windows features
            build.flag("-DHAS_IOCP");
            build.flag("-DHAS_REGISTERED_IO");
            println!("cargo:rustc-cfg=feature=\"iocp\"");
            println!("cargo:rustc-cfg=feature=\"registered_io\"");
        }

        #[cfg(target_os = "macos")]
        {
            // Enable macOS features
            build.flag("-DHAS_KQUEUE");
            println!("cargo:rustc-cfg=feature=\"kqueue\"");
        }

        build.compile("driver_shim");

        println!("cargo:rustc-link-lib=static=driver_shim");
    }

    // Link system libraries
    #[cfg(target_os = "linux")]
    {
        println!("cargo:rustc-link-lib=pthread");
        println!("cargo:rustc-link-lib=rt"); // For clock functions
    }

    #[cfg(target_os = "windows")]
    {
        // Link Windows libraries
        println!("cargo:rustc-link-lib=ws2_32");
        println!("cargo:rustc-link-lib=kernel32");
    }

    #[cfg(target_os = "macos")]
    {
        // Link macOS libraries
        println!("cargo:rustc-link-lib=c");
    }
}

/// Check if DPDK is available on the system
#[cfg(target_os = "linux")]
fn check_dpdk_available() -> bool {
    // Check environment variable first
    if env::var("DPDK_DIR").is_ok() {
        return true;
    }

    // Check for pkg-config
    if let Ok(output) = Command::new("pkg-config")
        .args(&["--exists", "libdpdk"])
        .output()
    {
        if output.status.success() {
            return true;
        }
    }

    // Check common installation paths
    let dpdk_paths = [
        "/usr/local/lib/x86_64-linux-gnu/pkgconfig/libdpdk.pc",
        "/usr/lib/x86_64-linux-gnu/pkgconfig/libdpdk.pc",
        "/opt/dpdk/lib/pkgconfig/libdpdk.pc",
    ];

    for path in &dpdk_paths {
        if std::path::Path::new(path).exists() {
            return true;
        }
    }

    false
}

/// Check if AF_XDP is available (requires libbpf)
#[cfg(target_os = "linux")]
fn check_af_xdp_available() -> bool {
    // Check environment variable first
    if env::var("XDP_DIR").is_ok() {
        return true;
    }

    // Check for libbpf
    if let Ok(output) = Command::new("pkg-config")
        .args(&["--exists", "libbpf"])
        .output()
    {
        if output.status.success() {
            return true;
        }
    }

    // Check for header files
    let xdp_headers = [
        "/usr/include/bpf/xsk.h",
        "/usr/include/linux/if_xdp.h",
        "/usr/local/include/bpf/xsk.h",
    ];

    for header in &xdp_headers {
        if std::path::Path::new(header).exists() {
            return true;
        }
    }

    false
}

/// Check if io_uring is available (requires liburing)
#[cfg(target_os = "linux")]
fn check_io_uring_available() -> bool {
    // Check for liburing
    if let Ok(output) = Command::new("pkg-config")
        .args(&["--exists", "liburing"])
        .output()
    {
        if output.status.success() {
            return true;
        }
    }

    // Check for header files
    let uring_headers = [
        "/usr/include/liburing.h",
        "/usr/local/include/liburing.h",
        "/usr/include/liburing/io_uring.h",
    ];

    for header in &uring_headers {
        if std::path::Path::new(header).exists() {
            return true;
        }
    }

    false
}

/// Link DPDK libraries
#[cfg(target_os = "linux")]
fn link_dpdk_libraries() {
    // Try pkg-config first
    if let Ok(output) = Command::new("pkg-config")
        .args(&["--libs", "libdpdk"])
        .output()
    {
        if output.status.success() {
            let libs = String::from_utf8_lossy(&output.stdout);
            for lib in libs.split_whitespace() {
                if lib.starts_with("-l") {
                    println!("cargo:rustc-link-lib={}", &lib[2..]);
                } else if lib.starts_with("-L") {
                    println!("cargo:rustc-link-search=native={}", &lib[2..]);
                }
            }
            return;
        }
    }

    // Fallback to common DPDK libraries
    let dpdk_libs = [
        "rte_eal",
        "rte_ethdev",
        "rte_mbuf",
        "rte_mempool",
        "rte_ring",
        "rte_pci",
        "rte_bus_pci",
        "rte_kvargs",
    ];

    for lib in &dpdk_libs {
        println!("cargo:rustc-link-lib={}", lib);
    }
}

#[cfg(not(target_os = "linux"))]
fn check_dpdk_available() -> bool {
    false
}

#[cfg(not(target_os = "linux"))]
fn check_af_xdp_available() -> bool {
    false
}

#[cfg(not(target_os = "linux"))]
fn check_io_uring_available() -> bool {
    false
}

#[cfg(not(target_os = "linux"))]
fn link_dpdk_libraries() {}
