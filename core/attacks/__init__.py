"""
Advanced Attack Vectors Module

Provides sophisticated attack methods beyond basic flooding:
- Amplification attacks (DNS, NTP, SSDP, Memcached, Chargen, SNMP)
- Layer 7 intelligent attacks (HTTP Flood, Slowloris, Slow POST, Smuggling)
- Connection-level attacks (SYN, ACK, RST, FIN, XMAS floods)
- SSL/TLS attacks (Exhaustion, Renegotiation, Heartbleed)
- Protocol-specific attacks (DNS, SMTP, FTP, SSH, MySQL, Redis)
- Application attacks (WordPress, API, WebSocket, GraphQL)
"""

from .amplification import (
    AmplificationAttack, DNSAmplification, NTPAmplification,
    SSDPAmplification, MemcachedAmplification, ChargenAmplification,
    SNMPAmplification
)
from .layer7 import (
    Layer7Attack, HTTPFlood, SlowlorisAttack, SlowPOST,
    RUDYAttack, HTTPSmuggling, CacheBypass
)
from .connection import (
    ConnectionExhaustion, SYNFlood, ACKFlood, RSTFlood,
    FINFlood, XMASFlood, NullScan, PushAckFlood, SYNACKFlood
)
from .ssl_attacks import (
    SSLExhaustion, SSLRenegotiation, HeartbleedTest, THCSSLDoS
)
from .protocol_specific import (
    DNSFlood, SMTPFlood, FTPBounce, SSHBruteforce,
    MySQLFlood, RedisFlood
)
from .application import (
    WordPressAttack, APIFlood, WebSocketFlood, GraphQLAttack
)

__all__ = [
    # Amplification
    'AmplificationAttack', 'DNSAmplification', 'NTPAmplification',
    'SSDPAmplification', 'MemcachedAmplification', 'ChargenAmplification',
    'SNMPAmplification',
    # Layer 7
    'Layer7Attack', 'HTTPFlood', 'SlowlorisAttack', 'SlowPOST',
    'RUDYAttack', 'HTTPSmuggling', 'CacheBypass',
    # Connection
    'ConnectionExhaustion', 'SYNFlood', 'ACKFlood', 'RSTFlood',
    'FINFlood', 'XMASFlood', 'NullScan', 'PushAckFlood', 'SYNACKFlood',
    # SSL
    'SSLExhaustion', 'SSLRenegotiation', 'HeartbleedTest', 'THCSSLDoS',
    # Protocol-specific
    'DNSFlood', 'SMTPFlood', 'FTPBounce', 'SSHBruteforce',
    'MySQLFlood', 'RedisFlood',
    # Application
    'WordPressAttack', 'APIFlood', 'WebSocketFlood', 'GraphQLAttack',
]
