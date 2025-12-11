"""
Real HTTP request generator.

This module generates valid HTTP/1.1 requests per RFC 7230 specification.
Includes proper headers, methods, and body content for realistic HTTP floods.
"""

import socket
import ssl
import time
import logging
import random
import asyncio
import aiohttp
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlencode

logger = logging.getLogger(__name__)


@dataclass
class HTTPRequestStats:
    """Statistics for HTTP requests"""
    requests_sent: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    response_codes: Dict[int, int] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def requests_per_second(self) -> float:
        if self.duration > 0:
            return self.requests_sent / self.duration
        return 0.0
    
    @property
    def success_rate(self) -> float:
        if self.requests_sent > 0:
            return self.requests_successful / self.requests_sent
        return 0.0


class RealHTTPGenerator:
    """
    Real HTTP request generator using valid HTTP/1.1 protocol.
    
    Generates RFC 7230 compliant HTTP requests with proper headers,
    methods, and body content. Supports both HTTP and HTTPS.
    """
    
    def __init__(self, target_url: str, user_agent: Optional[str] = None):
        """
        Initialize HTTP generator.
        
        Args:
            target_url: Target URL (http:// or https://)
            user_agent: Custom User-Agent string
        """
        self.target_url = target_url
        self.parsed_url = urlparse(target_url)
        self.user_agent = user_agent or self._generate_user_agent()
        self.stats = HTTPRequestStats()
        
        # Extract connection details
        self.host = self.parsed_url.hostname
        self.port = self.parsed_url.port or (443 if self.parsed_url.scheme == 'https' else 80)
        self.path = self.parsed_url.path or '/'
        self.is_https = self.parsed_url.scheme == 'https'
        
        # Default headers
        self.default_headers = {
            'Host': f"{self.host}:{self.port}" if self.port not in (80, 443) else self.host,
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        
    def _generate_user_agent(self) -> str:
        """Generate realistic User-Agent string"""
        browsers = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        return random.choice(browsers)
        
    def _build_http_request(self, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                           body: Optional[bytes] = None, query_params: Optional[Dict[str, str]] = None) -> bytes:
        """
        Build valid HTTP/1.1 request per RFC 7230.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            headers: Additional headers
            body: Request body
            query_params: Query parameters to append to path
            
        Returns:
            Complete HTTP request as bytes
        """
        # Build request path with query parameters
        request_path = self.path
        if query_params:
            query_string = urlencode(query_params)
            request_path += f"?{query_string}"
            
        # Start with request line
        request_line = f"{method} {request_path} HTTP/1.1\r\n"
        
        # Combine default and custom headers
        all_headers = self.default_headers.copy()
        if headers:
            all_headers.update(headers)
            
        # Add Content-Length for requests with body
        if body:
            all_headers['Content-Length'] = str(len(body))
            
        # Build headers section
        headers_section = ""
        for name, value in all_headers.items():
            headers_section += f"{name}: {value}\r\n"
            
        # Complete request
        request = request_line + headers_section + "\r\n"
        request_bytes = request.encode('utf-8')
        
        if body:
            request_bytes += body
            
        return request_bytes
        
    def _create_socket_connection(self, timeout: float = 10.0) -> socket.socket:
        """Create socket connection to target"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        if self.is_https:
            # Wrap with SSL
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # For testing purposes
            sock = context.wrap_socket(sock, server_hostname=self.host)
            
        sock.connect((self.host, self.port))
        return sock
        
    def send_single_request(self, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                           body: Optional[bytes] = None, query_params: Optional[Dict[str, str]] = None,
                           timeout: float = 10.0) -> Tuple[int, bytes]:
        """
        Send a single HTTP request.
        
        Args:
            method: HTTP method
            headers: Additional headers
            body: Request body
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            Tuple of (status_code, response_body)
        """
        request_data = self._build_http_request(method, headers, body, query_params)
        
        try:
            sock = self._create_socket_connection(timeout)
            
            # Send request
            bytes_sent = sock.send(request_data)
            self.stats.bytes_sent += bytes_sent
            
            # Read response
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                # Simple check for end of headers
                if b"\r\n\r\n" in response_data:
                    break
                    
            sock.close()
            
            # Parse status code
            status_code = 0
            if response_data:
                try:
                    status_line = response_data.split(b'\r\n')[0].decode('utf-8')
                    status_code = int(status_line.split()[1])
                except:
                    status_code = 0
                    
            self.stats.requests_sent += 1
            self.stats.bytes_received += len(response_data)
            
            if 200 <= status_code < 400:
                self.stats.requests_successful += 1
            else:
                self.stats.requests_failed += 1
                
            # Track response codes
            if status_code in self.stats.response_codes:
                self.stats.response_codes[status_code] += 1
            else:
                self.stats.response_codes[status_code] = 1
                
            return status_code, response_data
            
        except Exception as e:
            logger.debug(f"HTTP request failed: {e}")
            self.stats.requests_sent += 1
            self.stats.requests_failed += 1
            return 0, b""
            
    def send_get_flood(self, request_count: int, concurrent_connections: int = 10,
                      delay_ms: float = 0, custom_headers: Optional[Dict[str, str]] = None) -> HTTPRequestStats:
        """
        Send GET request flood.
        
        Args:
            request_count: Number of requests to send
            concurrent_connections: Number of concurrent connections
            delay_ms: Delay between requests in milliseconds
            custom_headers: Additional headers for requests
            
        Returns:
            Request statistics
        """
        flood_stats = HTTPRequestStats()
        flood_stats.start_time = time.perf_counter()
        
        logger.info(f"Starting HTTP GET flood: {request_count} requests to {self.target_url}")
        
        # Simple threaded approach for concurrent requests
        import threading
        from queue import Queue
        
        request_queue = Queue()
        for i in range(request_count):
            request_queue.put(i)
            
        def worker():
            while not request_queue.empty():
                try:
                    request_queue.get_nowait()
                    status_code, response = self.send_single_request('GET', custom_headers)
                    
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)
                        
                except:
                    pass
                finally:
                    request_queue.task_done()
                    
        # Start worker threads
        threads = []
        for _ in range(min(concurrent_connections, request_count)):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
            
        # Wait for completion
        for t in threads:
            t.join()
            
        flood_stats.end_time = time.perf_counter()
        
        # Copy stats from main stats object
        flood_stats.requests_sent = self.stats.requests_sent
        flood_stats.requests_successful = self.stats.requests_successful
        flood_stats.requests_failed = self.stats.requests_failed
        flood_stats.bytes_sent = self.stats.bytes_sent
        flood_stats.bytes_received = self.stats.bytes_received
        flood_stats.response_codes = self.stats.response_codes.copy()
        
        logger.info(f"HTTP GET flood complete: {flood_stats.requests_successful}/{request_count} successful, "
                   f"{flood_stats.requests_per_second:.1f} req/sec, "
                   f"{flood_stats.success_rate:.1%} success rate")
        
        return flood_stats
        
    def send_post_flood(self, request_count: int, post_data: bytes,
                       content_type: str = 'application/x-www-form-urlencoded',
                       concurrent_connections: int = 10) -> HTTPRequestStats:
        """
        Send POST request flood.
        
        Args:
            request_count: Number of requests to send
            post_data: Data to POST
            content_type: Content-Type header value
            concurrent_connections: Number of concurrent connections
            
        Returns:
            Request statistics
        """
        flood_stats = HTTPRequestStats()
        flood_stats.start_time = time.perf_counter()
        
        headers = {'Content-Type': content_type}
        
        logger.info(f"Starting HTTP POST flood: {request_count} requests, {len(post_data)} bytes each")
        
        import threading
        from queue import Queue
        
        request_queue = Queue()
        for i in range(request_count):
            request_queue.put(i)
            
        def worker():
            while not request_queue.empty():
                try:
                    request_queue.get_nowait()
                    self.send_single_request('POST', headers, post_data)
                except:
                    pass
                finally:
                    request_queue.task_done()
                    
        # Start worker threads
        threads = []
        for _ in range(min(concurrent_connections, request_count)):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
            
        # Wait for completion
        for t in threads:
            t.join()
            
        flood_stats.end_time = time.perf_counter()
        
        # Copy stats
        flood_stats.requests_sent = self.stats.requests_sent
        flood_stats.requests_successful = self.stats.requests_successful
        flood_stats.requests_failed = self.stats.requests_failed
        flood_stats.bytes_sent = self.stats.bytes_sent
        flood_stats.bytes_received = self.stats.bytes_received
        flood_stats.response_codes = self.stats.response_codes.copy()
        
        logger.info(f"HTTP POST flood complete: {flood_stats.requests_successful}/{request_count} successful, "
                   f"{flood_stats.requests_per_second:.1f} req/sec")
        
        return flood_stats
        
    async def send_async_flood(self, request_count: int, method: str = 'GET',
                              post_data: Optional[bytes] = None,
                              concurrent_limit: int = 100) -> HTTPRequestStats:
        """
        Send HTTP flood using aiohttp for better performance.
        
        Args:
            request_count: Number of requests to send
            method: HTTP method
            post_data: Data for POST requests
            concurrent_limit: Maximum concurrent requests
            
        Returns:
            Request statistics
        """
        flood_stats = HTTPRequestStats()
        flood_stats.start_time = time.perf_counter()
        
        logger.info(f"Starting async HTTP {method} flood: {request_count} requests")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def make_request(session):
            async with semaphore:
                try:
                    if method.upper() == 'POST' and post_data:
                        async with session.post(self.target_url, data=post_data) as response:
                            await response.read()
                            return response.status
                    else:
                        async with session.get(self.target_url) as response:
                            await response.read()
                            return response.status
                except Exception as e:
                    logger.debug(f"Async request failed: {e}")
                    return 0
                    
        # Configure aiohttp session
        connector = aiohttp.TCPConnector(
            limit=concurrent_limit,
            limit_per_host=concurrent_limit,
            ssl=False if not self.is_https else None
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.user_agent}
        ) as session:
            # Create all request tasks
            tasks = [make_request(session) for _ in range(request_count)]
            
            # Execute requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                flood_stats.requests_sent += 1
                if isinstance(result, int) and 200 <= result < 400:
                    flood_stats.requests_successful += 1
                    if result in flood_stats.response_codes:
                        flood_stats.response_codes[result] += 1
                    else:
                        flood_stats.response_codes[result] = 1
                else:
                    flood_stats.requests_failed += 1
                    
        flood_stats.end_time = time.perf_counter()
        
        logger.info(f"Async HTTP flood complete: {flood_stats.requests_successful}/{request_count} successful, "
                   f"{flood_stats.requests_per_second:.1f} req/sec, "
                   f"{flood_stats.success_rate:.1%} success rate")
        
        return flood_stats
        
    def generate_random_query_params(self, param_count: int = 5) -> Dict[str, str]:
        """Generate random query parameters for varied requests"""
        params = {}
        for i in range(param_count):
            key = f"param{i}"
            value = f"value{random.randint(1000, 9999)}"
            params[key] = value
        return params
        
    def generate_form_data(self, field_count: int = 3) -> bytes:
        """Generate random form data for POST requests"""
        data = {}
        for i in range(field_count):
            key = f"field{i}"
            value = f"data{random.randint(1000, 9999)}"
            data[key] = value
        return urlencode(data).encode('utf-8')
        
    def get_stats(self) -> HTTPRequestStats:
        """Get current statistics"""
        return self.stats


def create_http_generator(target_url: str, user_agent: Optional[str] = None) -> RealHTTPGenerator:
    """
    Factory function to create HTTP generator.
    
    Args:
        target_url: Target URL (http:// or https://)
        user_agent: Custom User-Agent string
        
    Returns:
        Configured HTTP generator
    """
    return RealHTTPGenerator(target_url, user_agent) 