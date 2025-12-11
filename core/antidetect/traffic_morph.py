"""
Traffic Morphing Module

Transforms traffic to evade detection:
- Protocol mimicry
- Payload mutation
- Traffic shaping
- Timing manipulation
"""

import asyncio
import random
import struct
import base64
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MorphType(Enum):
    """Traffic morphing types"""
    HTTP = "http"
    DNS = "dns"
    TLS = "tls"
    WEBSOCKET = "websocket"
    CUSTOM = "custom"


@dataclass
class MorphConfig:
    """Morphing configuration"""
    morph_type: MorphType = MorphType.HTTP
    add_noise: bool = True
    noise_ratio: float = 0.1
    fragment: bool = False
    fragment_size: int = 100
    delay_range: Tuple[float, float] = (0.0, 0.1)


from typing import Tuple


class TrafficMorpher:
    """
    Traffic Morpher
    
    Transforms traffic to look like legitimate protocols.
    """
    
    def __init__(self, config: MorphConfig):
        self.config = config
        self._morphers = {
            MorphType.HTTP: self._morph_http,
            MorphType.DNS: self._morph_dns,
            MorphType.TLS: self._morph_tls,
            MorphType.WEBSOCKET: self._morph_websocket,
        }
        
    def morph(self, data: bytes) -> bytes:
        """Morph data to look like target protocol"""
        morpher = self._morphers.get(self.config.morph_type, self._morph_custom)
        morphed = morpher(data)
        
        if self.config.add_noise:
            morphed = self._add_noise(morphed)
            
        if self.config.fragment:
            return morphed  # Fragmentation handled at send time
            
        return morphed
        
    def demorph(self, data: bytes) -> bytes:
        """Extract original data from morphed traffic"""
        if self.config.morph_type == MorphType.HTTP:
            return self._demorph_http(data)
        elif self.config.morph_type == MorphType.DNS:
            return self._demorph_dns(data)
        elif self.config.morph_type == MorphType.WEBSOCKET:
            return self._demorph_websocket(data)
        return data
        
    def _morph_http(self, data: bytes) -> bytes:
        """Morph as HTTP traffic"""
        encoded = base64.b64encode(data).decode()
        
        # Create fake HTTP request
        paths = ['/api/v1/data', '/images/pixel.gif', '/static/app.js', '/analytics']
        path = random.choice(paths)
        
        request = f"POST {path} HTTP/1.1\r\n"
        request += f"Host: cdn{random.randint(1,99)}.example.com\r\n"
        request += "Content-Type: application/x-www-form-urlencoded\r\n"
        request += f"Content-Length: {len(encoded)}\r\n"
        request += "Connection: keep-alive\r\n"
        request += f"X-Request-ID: {hashlib.md5(data).hexdigest()[:16]}\r\n"
        request += "\r\n"
        request += f"data={encoded}"
        
        return request.encode()
        
    def _demorph_http(self, data: bytes) -> bytes:
        """Extract data from HTTP morphed traffic"""
        try:
            text = data.decode('utf-8', errors='ignore')
            if 'data=' in text:
                encoded = text.split('data=')[1].split('\r\n')[0]
                return base64.b64decode(encoded)
        except Exception:
            pass
        return data
        
    def _morph_dns(self, data: bytes) -> bytes:
        """Morph as DNS traffic"""
        # Encode data in DNS query format
        encoded = base64.b32encode(data).decode().lower().rstrip('=')
        
        # Split into labels (max 63 chars each)
        labels = [encoded[i:i+63] for i in range(0, len(encoded), 63)]
        
        # Build DNS query
        transaction_id = struct.pack('>H', random.randint(0, 65535))
        flags = struct.pack('>H', 0x0100)  # Standard query
        counts = struct.pack('>HHHH', 1, 0, 0, 0)  # 1 question
        
        qname = b''
        for label in labels:
            qname += bytes([len(label)]) + label.encode()
        qname += b'\x07example\x03com\x00'
        
        qtype = struct.pack('>H', 16)  # TXT
        qclass = struct.pack('>H', 1)  # IN
        
        return transaction_id + flags + counts + qname + qtype + qclass
        
    def _demorph_dns(self, data: bytes) -> bytes:
        """Extract data from DNS morphed traffic"""
        try:
            # Skip header (12 bytes)
            qname = data[12:]
            
            # Extract labels
            labels = []
            i = 0
            while qname[i] != 0 and i < len(qname):
                length = qname[i]
                label = qname[i+1:i+1+length].decode()
                if label not in ['example', 'com']:
                    labels.append(label)
                i += length + 1
                
            encoded = ''.join(labels).upper()
            # Add padding
            padding = (8 - len(encoded) % 8) % 8
            encoded += '=' * padding
            
            return base64.b32decode(encoded)
        except Exception:
            pass
        return data
        
    def _morph_tls(self, data: bytes) -> bytes:
        """Morph as TLS application data"""
        # TLS record header
        content_type = b'\x17'  # Application data
        version = b'\x03\x03'  # TLS 1.2
        length = struct.pack('>H', len(data))
        
        return content_type + version + length + data
        
    def _morph_websocket(self, data: bytes) -> bytes:
        """Morph as WebSocket frame"""
        # WebSocket frame
        fin_opcode = 0x82  # Final frame, binary
        
        if len(data) < 126:
            header = bytes([fin_opcode, 0x80 | len(data)])
        elif len(data) < 65536:
            header = bytes([fin_opcode, 0x80 | 126]) + struct.pack('>H', len(data))
        else:
            header = bytes([fin_opcode, 0x80 | 127]) + struct.pack('>Q', len(data))
            
        # Masking key
        mask = bytes(random.randint(0, 255) for _ in range(4))
        
        # Mask data
        masked = bytes(data[i] ^ mask[i % 4] for i in range(len(data)))
        
        return header + mask + masked
        
    def _demorph_websocket(self, data: bytes) -> bytes:
        """Extract data from WebSocket frame"""
        try:
            payload_len = data[1] & 0x7f
            mask_start = 2
            
            if payload_len == 126:
                payload_len = struct.unpack('>H', data[2:4])[0]
                mask_start = 4
            elif payload_len == 127:
                payload_len = struct.unpack('>Q', data[2:10])[0]
                mask_start = 10
                
            if data[1] & 0x80:  # Masked
                mask = data[mask_start:mask_start+4]
                payload = data[mask_start+4:mask_start+4+payload_len]
                return bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
            else:
                return data[mask_start:mask_start+payload_len]
        except Exception:
            pass
        return data
        
    def _morph_custom(self, data: bytes) -> bytes:
        """Custom morphing (XOR with key)"""
        key = b'NetStress'
        return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))
        
    def _add_noise(self, data: bytes) -> bytes:
        """Add random noise to data"""
        noise_len = int(len(data) * self.config.noise_ratio)
        noise = bytes(random.randint(0, 255) for _ in range(noise_len))
        
        # Append noise with length prefix
        return data + struct.pack('>H', noise_len) + noise


class ProtocolMimicry:
    """
    Protocol Mimicry
    
    Makes traffic look like specific applications.
    """
    
    # Application signatures
    SIGNATURES = {
        'chrome': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
            'headers': ['sec-ch-ua', 'sec-ch-ua-mobile', 'sec-fetch-site'],
            'tls_fingerprint': 'chrome_120',
        },
        'firefox': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'headers': ['te', 'upgrade-insecure-requests'],
            'tls_fingerprint': 'firefox_121',
        },
        'curl': {
            'user_agent': 'curl/8.0.0',
            'headers': [],
            'tls_fingerprint': 'curl',
        },
    }
    
    def __init__(self, application: str = 'chrome'):
        self.application = application
        self.signature = self.SIGNATURES.get(application, self.SIGNATURES['chrome'])
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for mimicked application"""
        headers = {
            'User-Agent': self.signature['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        if self.application == 'chrome':
            headers.update({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
            })
            
        return headers
        
    def build_request(self, method: str, path: str, host: str, body: bytes = b'') -> bytes:
        """Build HTTP request mimicking application"""
        headers = self.get_headers()
        headers['Host'] = host
        
        if body:
            headers['Content-Length'] = str(len(body))
            
        request = f"{method} {path} HTTP/1.1\r\n"
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"
        
        return request.encode() + body


class PayloadMutation:
    """
    Payload Mutation
    
    Mutates payloads to evade signature detection.
    """
    
    def __init__(self):
        self._mutations: List[Callable[[bytes], bytes]] = [
            self._xor_mutation,
            self._base64_mutation,
            self._padding_mutation,
            self._split_mutation,
            self._case_mutation,
        ]
        
    def mutate(self, payload: bytes, mutations: int = 1) -> bytes:
        """Apply random mutations to payload"""
        result = payload
        
        selected = random.sample(self._mutations, min(mutations, len(self._mutations)))
        for mutation in selected:
            result = mutation(result)
            
        return result
        
    def _xor_mutation(self, data: bytes) -> bytes:
        """XOR with random key"""
        key = random.randint(1, 255)
        return bytes([b ^ key for b in data]) + bytes([key])
        
    def _base64_mutation(self, data: bytes) -> bytes:
        """Base64 encode"""
        return base64.b64encode(data)
        
    def _padding_mutation(self, data: bytes) -> bytes:
        """Add random padding"""
        padding_len = random.randint(1, 32)
        padding = bytes(random.randint(0, 255) for _ in range(padding_len))
        return struct.pack('>H', len(data)) + data + padding
        
    def _split_mutation(self, data: bytes) -> bytes:
        """Split and interleave"""
        mid = len(data) // 2
        first = data[:mid]
        second = data[mid:]
        
        result = b''
        for i in range(max(len(first), len(second))):
            if i < len(first):
                result += bytes([first[i]])
            if i < len(second):
                result += bytes([second[i]])
                
        return struct.pack('>HH', len(first), len(second)) + result
        
    def _case_mutation(self, data: bytes) -> bytes:
        """Random case changes for text"""
        try:
            text = data.decode('utf-8')
            result = ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in text)
            return result.encode()
        except Exception:
            return data
