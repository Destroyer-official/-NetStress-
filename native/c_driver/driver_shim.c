/**
 * NetStress C Driver Shim Implementation
 * Platform-specific low-level networking operations
 */

#include "driver_shim.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #define CLOSE_SOCKET closesocket
#else
    #include <sys/socket.h>
    #include <sys/time.h>
    #include <netinet/in.h>
    #include <netinet/ip.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <errno.h>
    #define CLOSE_SOCKET close
    #define SOCKET int
    #define INVALID_SOCKET -1
#endif

#ifdef __linux__
    #include <sched.h>
    #include <pthread.h>
    #include <sys/utsname.h>
    #include <sys/sendfile.h>
#endif

/* ============================================================================
 * Raw Socket Implementation
 * ============================================================================ */

int raw_socket_create(int protocol) {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        return -1;
    }
    SOCKET sock = socket(AF_INET, SOCK_RAW, protocol);
    if (sock == INVALID_SOCKET) {
        return -1;
    }
    return (int)sock;
#else
    int sock = socket(AF_INET, SOCK_RAW, protocol);
    if (sock < 0) {
        return -1;
    }
    return sock;
#endif
}

int raw_socket_set_hdrincl(int sockfd) {
    int one = 1;
#ifdef _WIN32
    return setsockopt((SOCKET)sockfd, IPPROTO_IP, IP_HDRINCL, 
                      (const char*)&one, sizeof(one));
#else
    return setsockopt(sockfd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));
#endif
}

int raw_socket_send(int sockfd, uint32_t dst_ip, const uint8_t* data, uint32_t len) {
    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = dst_ip;

#ifdef _WIN32
    int sent = sendto((SOCKET)sockfd, (const char*)data, len, 0,
                      (struct sockaddr*)&dest, sizeof(dest));
#else
    ssize_t sent = sendto(sockfd, data, len, 0,
                          (struct sockaddr*)&dest, sizeof(dest));
#endif
    return (int)sent;
}

int raw_socket_send_ip(int sockfd, const uint8_t* data, uint32_t len) {
    /* Extract destination IP from IP header */
    if (len < 20) {
        return -1;  /* Too short for IP header */
    }
    
    uint32_t dst_ip;
    memcpy(&dst_ip, data + 16, 4);  /* Destination IP at offset 16 */
    
    return raw_socket_send(sockfd, dst_ip, data, len);
}

void raw_socket_close(int sockfd) {
#ifdef _WIN32
    CLOSE_SOCKET((SOCKET)sockfd);
    WSACleanup();
#else
    CLOSE_SOCKET(sockfd);
#endif
}

/* ============================================================================
 * Checksum Calculations
 * ============================================================================ */

uint16_t calculate_checksum(const uint8_t* data, size_t len) {
    uint32_t sum = 0;
    size_t i;

    /* Sum 16-bit words */
    for (i = 0; i + 1 < len; i += 2) {
        sum += ((uint16_t)data[i] << 8) | data[i + 1];
    }

    /* Add odd byte if present */
    if (i < len) {
        sum += (uint16_t)data[i] << 8;
    }

    /* Fold 32-bit sum to 16 bits */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return (uint16_t)(~sum);
}

uint16_t calculate_transport_checksum(uint32_t src_ip, uint32_t dst_ip,
                                       uint8_t protocol, const uint8_t* data, size_t len) {
    uint32_t sum = 0;
    size_t i;

    /* Pseudo-header */
    sum += (src_ip >> 16) & 0xFFFF;
    sum += src_ip & 0xFFFF;
    sum += (dst_ip >> 16) & 0xFFFF;
    sum += dst_ip & 0xFFFF;
    sum += protocol;
    sum += len;

    /* Data */
    for (i = 0; i + 1 < len; i += 2) {
        sum += ((uint16_t)data[i] << 8) | data[i + 1];
    }
    if (i < len) {
        sum += (uint16_t)data[i] << 8;
    }

    /* Fold */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return (uint16_t)(~sum);
}

/* ============================================================================
 * Utility Functions
 * ============================================================================ */

uint64_t get_timestamp_us(void) {
#ifdef _WIN32
    LARGE_INTEGER freq, count;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);
    return (uint64_t)(count.QuadPart * 1000000 / freq.QuadPart);
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000 + tv.tv_usec;
#endif
}

int get_cpu_count(void) {
#ifdef _WIN32
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);
    return sysinfo.dwNumberOfProcessors;
#elif defined(__linux__)
    return sysconf(_SC_NPROCESSORS_ONLN);
#else
    return 1;
#endif
}

int pin_to_cpu(int cpu_id) {
#ifdef __linux__
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    return pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
#else
    (void)cpu_id;
    return -1;  /* Not supported */
#endif
}

/* ============================================================================
 * DPDK Implementation (when available)
 * ============================================================================ */

#ifdef HAS_DPDK

#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mbuf.h>
#include <rte_mempool.h>

static struct rte_mempool* mbuf_pool = NULL;
static int dpdk_initialized = 0;

int dpdk_init(int argc, char** argv) {
    int ret = rte_eal_init(argc, argv);
    if (ret < 0) {
        return -1;
    }
    
    /* Create mbuf pool */
    mbuf_pool = rte_pktmbuf_pool_create("MBUF_POOL", 8192,
                                         256, 0, RTE_MBUF_DEFAULT_BUF_SIZE,
                                         rte_socket_id());
    if (mbuf_pool == NULL) {
        return -1;
    }
    
    dpdk_initialized = 1;
    return ret;
}

int init_dpdk_port(int port_id) {
    if (!dpdk_initialized) {
        return -1;
    }
    
    struct rte_eth_conf port_conf = {0};
    struct rte_eth_dev_info dev_info;
    
    int ret = rte_eth_dev_info_get(port_id, &dev_info);
    if (ret != 0) {
        return ret;
    }
    
    /* Configure port */
    ret = rte_eth_dev_configure(port_id, 1, 1, &port_conf);
    if (ret != 0) {
        return ret;
    }
    
    /* Setup RX queue */
    ret = rte_eth_rx_queue_setup(port_id, 0, 1024,
                                  rte_eth_dev_socket_id(port_id),
                                  NULL, mbuf_pool);
    if (ret < 0) {
        return ret;
    }
    
    /* Setup TX queue */
    ret = rte_eth_tx_queue_setup(port_id, 0, 1024,
                                  rte_eth_dev_socket_id(port_id),
                                  NULL);
    if (ret < 0) {
        return ret;
    }
    
    /* Start port */
    ret = rte_eth_dev_start(port_id);
    if (ret < 0) {
        return ret;
    }
    
    /* Enable promiscuous mode */
    ret = rte_eth_promiscuous_enable(port_id);
    
    return 0;
}

int dpdk_send_burst(int port_id, const uint8_t** packets, const uint32_t* lengths, uint32_t count) {
    if (!dpdk_initialized || mbuf_pool == NULL) {
        return -1;
    }
    
    struct rte_mbuf* mbufs[count];
    uint32_t i;
    
    /* Allocate mbufs and copy data */
    for (i = 0; i < count; i++) {
        mbufs[i] = rte_pktmbuf_alloc(mbuf_pool);
        if (mbufs[i] == NULL) {
            /* Free already allocated */
            for (uint32_t j = 0; j < i; j++) {
                rte_pktmbuf_free(mbufs[j]);
            }
            return -1;
        }
        
        char* data = rte_pktmbuf_append(mbufs[i], lengths[i]);
        if (data == NULL) {
            rte_pktmbuf_free(mbufs[i]);
            for (uint32_t j = 0; j < i; j++) {
                rte_pktmbuf_free(mbufs[j]);
            }
            return -1;
        }
        memcpy(data, packets[i], lengths[i]);
    }
    
    /* Send burst */
    uint16_t sent = rte_eth_tx_burst(port_id, 0, mbufs, count);
    
    /* Free unsent mbufs */
    for (i = sent; i < count; i++) {
        rte_pktmbuf_free(mbufs[i]);
    }
    
    return sent;
}

int dpdk_recv_burst(int port_id, uint8_t** packets, uint32_t max_count) {
    if (!dpdk_initialized) {
        return -1;
    }
    
    struct rte_mbuf* mbufs[max_count];
    uint16_t received = rte_eth_rx_burst(port_id, 0, mbufs, max_count);
    
    for (uint16_t i = 0; i < received; i++) {
        packets[i] = rte_pktmbuf_mtod(mbufs[i], uint8_t*);
    }
    
    return received;
}

int dpdk_get_stats(int port_id, driver_stats_t* stats) {
    struct rte_eth_stats eth_stats;
    int ret = rte_eth_stats_get(port_id, &eth_stats);
    if (ret != 0) {
        return ret;
    }
    
    stats->packets_sent = eth_stats.opackets;
    stats->packets_received = eth_stats.ipackets;
    stats->bytes_sent = eth_stats.obytes;
    stats->bytes_received = eth_stats.ibytes;
    stats->errors = eth_stats.oerrors + eth_stats.ierrors;
    
    return 0;
}

int cleanup_dpdk(void) {
    if (dpdk_initialized) {
        rte_eal_cleanup();
        dpdk_initialized = 0;
    }
    return 0;
}

#endif /* HAS_DPDK */

/* ============================================================================
 * AF_XDP Implementation (when available)
 * ============================================================================ */

#ifdef HAS_AF_XDP

#include <linux/if_xdp.h>
#include <linux/if_link.h>
#include <bpf/xsk.h>
#include <bpf/libbpf.h>
#include <net/if.h>

static struct xsk_socket* xsk = NULL;
static struct xsk_umem* umem = NULL;
static void* umem_area = NULL;
static struct xsk_ring_prod tx_ring;
static struct xsk_ring_cons rx_ring;
static struct xsk_ring_prod fq;
static struct xsk_ring_cons cq;

#define FRAME_SIZE XSK_UMEM__DEFAULT_FRAME_SIZE
#define NUM_FRAMES 4096

int init_af_xdp(const char* ifname) {
    int ifindex = if_nametoindex(ifname);
    if (ifindex == 0) {
        return -1;
    }
    
    /* Allocate UMEM area */
    size_t umem_size = NUM_FRAMES * FRAME_SIZE;
    umem_area = aligned_alloc(getpagesize(), umem_size);
    if (umem_area == NULL) {
        return -1;
    }
    
    /* Create UMEM */
    struct xsk_umem_config umem_cfg = {
        .fill_size = NUM_FRAMES,
        .comp_size = NUM_FRAMES,
        .frame_size = FRAME_SIZE,
        .frame_headroom = XSK_UMEM__DEFAULT_FRAME_HEADROOM,
    };
    
    int ret = xsk_umem__create(&umem, umem_area, umem_size, &fq, &cq, &umem_cfg);
    if (ret) {
        free(umem_area);
        return ret;
    }
    
    /* Create XSK socket */
    struct xsk_socket_config xsk_cfg = {
        .rx_size = NUM_FRAMES,
        .tx_size = NUM_FRAMES,
        .libbpf_flags = XSK_LIBBPF_FLAGS__INHIBIT_PROG_LOAD,
        .xdp_flags = XDP_FLAGS_DRV_MODE,
        .bind_flags = XDP_USE_NEED_WAKEUP,
    };
    
    ret = xsk_socket__create(&xsk, ifname, 0, umem, &rx_ring, &tx_ring, &xsk_cfg);
    if (ret) {
        xsk_umem__delete(umem);
        free(umem_area);
        return ret;
    }
    
    /* Populate fill ring */
    uint32_t idx;
    ret = xsk_ring_prod__reserve(&fq, NUM_FRAMES, &idx);
    for (uint32_t i = 0; i < NUM_FRAMES; i++) {
        *xsk_ring_prod__fill_addr(&fq, idx++) = i * FRAME_SIZE;
    }
    xsk_ring_prod__submit(&fq, NUM_FRAMES);
    
    return xsk_socket__fd(xsk);
}

int af_xdp_send(const uint8_t* data, uint32_t len) {
    if (xsk == NULL) {
        return -1;
    }
    
    uint32_t idx;
    if (xsk_ring_prod__reserve(&tx_ring, 1, &idx) != 1) {
        return -1;
    }
    
    struct xdp_desc* desc = xsk_ring_prod__tx_desc(&tx_ring, idx);
    desc->addr = idx * FRAME_SIZE;
    desc->len = len;
    
    memcpy((uint8_t*)umem_area + desc->addr, data, len);
    
    xsk_ring_prod__submit(&tx_ring, 1);
    
    /* Kick TX */
    if (xsk_ring_prod__needs_wakeup(&tx_ring)) {
        sendto(xsk_socket__fd(xsk), NULL, 0, MSG_DONTWAIT, NULL, 0);
    }
    
    return len;
}

int af_xdp_send_batch(const uint8_t** packets, const uint32_t* lengths, uint32_t count) {
    if (xsk == NULL) {
        return -1;
    }
    
    uint32_t idx;
    uint32_t reserved = xsk_ring_prod__reserve(&tx_ring, count, &idx);
    
    for (uint32_t i = 0; i < reserved; i++) {
        struct xdp_desc* desc = xsk_ring_prod__tx_desc(&tx_ring, idx + i);
        desc->addr = (idx + i) * FRAME_SIZE;
        desc->len = lengths[i];
        memcpy((uint8_t*)umem_area + desc->addr, packets[i], lengths[i]);
    }
    
    xsk_ring_prod__submit(&tx_ring, reserved);
    
    if (xsk_ring_prod__needs_wakeup(&tx_ring)) {
        sendto(xsk_socket__fd(xsk), NULL, 0, MSG_DONTWAIT, NULL, 0);
    }
    
    return reserved;
}

int af_xdp_recv(uint8_t* buffer, uint32_t max_len) {
    if (xsk == NULL) {
        return -1;
    }
    
    uint32_t idx;
    if (xsk_ring_cons__peek(&rx_ring, 1, &idx) != 1) {
        return 0;
    }
    
    const struct xdp_desc* desc = xsk_ring_cons__rx_desc(&rx_ring, idx);
    uint32_t len = desc->len < max_len ? desc->len : max_len;
    
    memcpy(buffer, (uint8_t*)umem_area + desc->addr, len);
    
    xsk_ring_cons__release(&rx_ring, 1);
    
    /* Refill fill ring */
    uint32_t fq_idx;
    if (xsk_ring_prod__reserve(&fq, 1, &fq_idx) == 1) {
        *xsk_ring_prod__fill_addr(&fq, fq_idx) = desc->addr;
        xsk_ring_prod__submit(&fq, 1);
    }
    
    return len;
}

int cleanup_af_xdp(void) {
    if (xsk) {
        xsk_socket__delete(xsk);
        xsk = NULL;
    }
    if (umem) {
        xsk_umem__delete(umem);
        umem = NULL;
    }
    if (umem_area) {
        free(umem_area);
        umem_area = NULL;
    }
    return 0;
}

#endif /* HAS_AF_XDP */

/* ============================================================================
 * io_uring Implementation (when available)
 * ============================================================================ */

#ifdef HAS_IO_URING

#include <liburing.h>
#include <sys/uio.h>

static struct io_uring ring;
static int io_uring_initialized = 0;
static int io_uring_sockfd = -1;
static driver_stats_t io_uring_stats = {0};

#define URING_QUEUE_DEPTH 256
#define URING_BATCH_SIZE 32

int init_io_uring(int queue_depth) {
    int ret = io_uring_queue_init(queue_depth > 0 ? queue_depth : URING_QUEUE_DEPTH, &ring, 0);
    if (ret < 0) {
        return ret;
    }
    
    /* Create UDP socket for sending */
    io_uring_sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (io_uring_sockfd < 0) {
        io_uring_queue_exit(&ring);
        return -1;
    }
    
    io_uring_initialized = 1;
    return 0;
}

int io_uring_send_batch(const uint8_t** packets, const uint32_t* lengths, 
                        const struct sockaddr_in* dests, uint32_t count) {
    if (!io_uring_initialized) {
        return -1;
    }
    
    struct io_uring_sqe* sqe;
    struct msghdr* msgs;
    struct iovec* iovs;
    uint32_t i;
    
    /* Allocate message structures */
    msgs = (struct msghdr*)calloc(count, sizeof(struct msghdr));
    iovs = (struct iovec*)calloc(count, sizeof(struct iovec));
    if (!msgs || !iovs) {
        free(msgs);
        free(iovs);
        return -1;
    }
    
    /* Prepare submission queue entries */
    for (i = 0; i < count; i++) {
        sqe = io_uring_get_sqe(&ring);
        if (!sqe) {
            break;
        }
        
        iovs[i].iov_base = (void*)packets[i];
        iovs[i].iov_len = lengths[i];
        
        msgs[i].msg_name = (void*)&dests[i];
        msgs[i].msg_namelen = sizeof(struct sockaddr_in);
        msgs[i].msg_iov = &iovs[i];
        msgs[i].msg_iovlen = 1;
        msgs[i].msg_control = NULL;
        msgs[i].msg_controllen = 0;
        msgs[i].msg_flags = 0;
        
        io_uring_prep_sendmsg(sqe, io_uring_sockfd, &msgs[i], 0);
        sqe->user_data = i;
    }
    
    /* Submit all at once */
    int submitted = io_uring_submit(&ring);
    
    /* Wait for completions */
    struct io_uring_cqe* cqe;
    int completed = 0;
    
    for (int j = 0; j < submitted; j++) {
        int ret = io_uring_wait_cqe(&ring, &cqe);
        if (ret < 0) {
            break;
        }
        if (cqe->res >= 0) {
            completed++;
            io_uring_stats.packets_sent++;
            io_uring_stats.bytes_sent += cqe->res;
        } else {
            io_uring_stats.errors++;
        }
        io_uring_cqe_seen(&ring, cqe);
    }
    
    free(msgs);
    free(iovs);
    
    return completed;
}

int io_uring_send_single(const uint8_t* data, uint32_t len, const struct sockaddr_in* dest) {
    if (!io_uring_initialized) {
        return -1;
    }
    
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring);
    if (!sqe) {
        return -1;
    }
    
    struct msghdr msg = {0};
    struct iovec iov = {
        .iov_base = (void*)data,
        .iov_len = len
    };
    
    msg.msg_name = (void*)dest;
    msg.msg_namelen = sizeof(struct sockaddr_in);
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
    
    io_uring_prep_sendmsg(sqe, io_uring_sockfd, &msg, 0);
    
    int ret = io_uring_submit(&ring);
    if (ret < 0) {
        return ret;
    }
    
    struct io_uring_cqe* cqe;
    ret = io_uring_wait_cqe(&ring, &cqe);
    if (ret < 0) {
        return ret;
    }
    
    int result = cqe->res;
    io_uring_cqe_seen(&ring, cqe);
    
    return result;
}

int io_uring_get_stats(driver_stats_t* stats) {
    if (!io_uring_initialized || !stats) {
        return -1;
    }
    
    *stats = io_uring_stats;
    return 0;
}

int cleanup_io_uring(void) {
    if (io_uring_initialized) {
        if (io_uring_sockfd >= 0) {
            close(io_uring_sockfd);
            io_uring_sockfd = -1;
        }
        io_uring_queue_exit(&ring);
        io_uring_initialized = 0;
        memset(&io_uring_stats, 0, sizeof(io_uring_stats));
    }
    return 0;
}

#endif /* HAS_IO_URING */

/* ============================================================================
 * sendmmsg Batch Sending (Linux)
 * ============================================================================ */

#ifdef __linux__

int sendmmsg_batch(int sockfd, const uint8_t** packets, const uint32_t* lengths,
                   const struct sockaddr_in* dests, uint32_t count) {
    struct mmsghdr* msgs;
    struct iovec* iovs;
    uint32_t i;
    int sent;
    
    msgs = (struct mmsghdr*)calloc(count, sizeof(struct mmsghdr));
    iovs = (struct iovec*)calloc(count, sizeof(struct iovec));
    if (!msgs || !iovs) {
        free(msgs);
        free(iovs);
        return -1;
    }
    
    for (i = 0; i < count; i++) {
        iovs[i].iov_base = (void*)packets[i];
        iovs[i].iov_len = lengths[i];
        
        msgs[i].msg_hdr.msg_name = (void*)&dests[i];
        msgs[i].msg_hdr.msg_namelen = sizeof(struct sockaddr_in);
        msgs[i].msg_hdr.msg_iov = &iovs[i];
        msgs[i].msg_hdr.msg_iovlen = 1;
        msgs[i].msg_hdr.msg_control = NULL;
        msgs[i].msg_hdr.msg_controllen = 0;
        msgs[i].msg_hdr.msg_flags = 0;
    }
    
    sent = sendmmsg(sockfd, msgs, count, 0);
    
    free(msgs);
    free(iovs);
    
    return sent;
}

int sendmmsg_batch_same_dest(int sockfd, const uint8_t** packets, const uint32_t* lengths,
                              uint32_t dst_ip, uint16_t dst_port, uint32_t count) {
    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = dst_ip;
    dest.sin_port = htons(dst_port);
    
    struct mmsghdr* msgs;
    struct iovec* iovs;
    uint32_t i;
    int sent;
    
    msgs = (struct mmsghdr*)calloc(count, sizeof(struct mmsghdr));
    iovs = (struct iovec*)calloc(count, sizeof(struct iovec));
    if (!msgs || !iovs) {
        free(msgs);
        free(iovs);
        return -1;
    }
    
    for (i = 0; i < count; i++) {
        iovs[i].iov_base = (void*)packets[i];
        iovs[i].iov_len = lengths[i];
        
        msgs[i].msg_hdr.msg_name = &dest;
        msgs[i].msg_hdr.msg_namelen = sizeof(dest);
        msgs[i].msg_hdr.msg_iov = &iovs[i];
        msgs[i].msg_hdr.msg_iovlen = 1;
        msgs[i].msg_hdr.msg_control = NULL;
        msgs[i].msg_hdr.msg_controllen = 0;
        msgs[i].msg_hdr.msg_flags = 0;
    }
    
    sent = sendmmsg(sockfd, msgs, count, 0);
    
    free(msgs);
    free(iovs);
    
    return sent;
}

#else

/* Fallback for non-Linux systems */
int sendmmsg_batch(int sockfd, const uint8_t** packets, const uint32_t* lengths,
                   const struct sockaddr_in* dests, uint32_t count) {
    int sent = 0;
    for (uint32_t i = 0; i < count; i++) {
        ssize_t ret = sendto(sockfd, packets[i], lengths[i], 0,
                             (struct sockaddr*)&dests[i], sizeof(struct sockaddr_in));
        if (ret > 0) {
            sent++;
        }
    }
    return sent;
}

int sendmmsg_batch_same_dest(int sockfd, const uint8_t** packets, const uint32_t* lengths,
                              uint32_t dst_ip, uint16_t dst_port, uint32_t count) {
    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = dst_ip;
#ifdef _WIN32
    dest.sin_port = htons(dst_port);
#else
    dest.sin_port = htons(dst_port);
#endif
    
    int sent = 0;
    for (uint32_t i = 0; i < count; i++) {
        ssize_t ret = sendto(sockfd, packets[i], lengths[i], 0,
                             (struct sockaddr*)&dest, sizeof(dest));
        if (ret > 0) {
            sent++;
        }
    }
    return sent;
}

#endif /* __linux__ */

/* ============================================================================
 * Backend Detection and Selection
 * ============================================================================ */

typedef enum {
    BACKEND_NONE = 0,
    BACKEND_RAW_SOCKET = 1,
    BACKEND_SENDMMSG = 2,
    BACKEND_IO_URING = 3,
    BACKEND_AF_XDP = 4,
    BACKEND_DPDK = 5
} backend_type_t;

typedef struct {
    int has_dpdk;
    int has_af_xdp;
    int has_io_uring;
    int has_sendmmsg;
    int has_raw_socket;
    int kernel_version_major;
    int kernel_version_minor;
    int cpu_count;
    int numa_nodes;
} system_capabilities_t;

int detect_capabilities(system_capabilities_t* caps) {
    memset(caps, 0, sizeof(system_capabilities_t));
    
    /* Always have raw sockets */
    caps->has_raw_socket = 1;
    
    /* CPU count */
    caps->cpu_count = get_cpu_count();
    
#ifdef __linux__
    /* Check kernel version */
    struct utsname uts;
    if (uname(&uts) == 0) {
        sscanf(uts.release, "%d.%d", &caps->kernel_version_major, &caps->kernel_version_minor);
    }
    
    /* sendmmsg available on Linux 3.0+ */
    if (caps->kernel_version_major >= 3) {
        caps->has_sendmmsg = 1;
    }
    
    /* io_uring available on Linux 5.1+ */
    if (caps->kernel_version_major > 5 || 
        (caps->kernel_version_major == 5 && caps->kernel_version_minor >= 1)) {
#ifdef HAS_IO_URING
        caps->has_io_uring = 1;
#endif
    }
    
    /* AF_XDP available on Linux 4.18+ */
    if (caps->kernel_version_major > 4 ||
        (caps->kernel_version_major == 4 && caps->kernel_version_minor >= 18)) {
#ifdef HAS_AF_XDP
        caps->has_af_xdp = 1;
#endif
    }
    
    /* NUMA detection */
    FILE* f = fopen("/sys/devices/system/node/online", "r");
    if (f) {
        char buf[64];
        if (fgets(buf, sizeof(buf), f)) {
            /* Parse "0-N" format */
            int start, end;
            if (sscanf(buf, "%d-%d", &start, &end) == 2) {
                caps->numa_nodes = end - start + 1;
            } else {
                caps->numa_nodes = 1;
            }
        }
        fclose(f);
    }
#endif

#ifdef HAS_DPDK
    caps->has_dpdk = 1;
#endif

    return 0;
}

backend_type_t select_best_backend(const system_capabilities_t* caps) {
    /* Priority: DPDK > AF_XDP > io_uring > sendmmsg > raw_socket */
    if (caps->has_dpdk) {
        return BACKEND_DPDK;
    }
    if (caps->has_af_xdp) {
        return BACKEND_AF_XDP;
    }
    if (caps->has_io_uring) {
        return BACKEND_IO_URING;
    }
    if (caps->has_sendmmsg) {
        return BACKEND_SENDMMSG;
    }
    return BACKEND_RAW_SOCKET;
}

const char* backend_name(backend_type_t backend) {
    switch (backend) {
        case BACKEND_DPDK: return "DPDK";
        case BACKEND_AF_XDP: return "AF_XDP";
        case BACKEND_IO_URING: return "io_uring";
        case BACKEND_SENDMMSG: return "sendmmsg";
        case BACKEND_RAW_SOCKET: return "raw_socket";
        default: return "unknown";
    }
}
