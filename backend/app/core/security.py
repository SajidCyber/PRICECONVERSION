"""SSRF Security Validation and Safe HTTP Client."""

import ipaddress
import socket
import urllib.parse
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import SSRFSecurityError
from app.core.logging_config import logger

# Blocked IP Networks for SSRF Prevention
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),          # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),       # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),         # Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local / Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),       # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),        # IETF Protocol
    ipaddress.ip_network("192.0.2.0/24"),        # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),      # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),       # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),     # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),      # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 Blocked
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),            # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),           # IPv6 Link-Local
]

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}


def validate_url_for_ssrf(url: str) -> None:
    """Validates target URL against SSRF vulnerabilities before connection.

    Checks:
    1. Scheme is http or https.
    2. Port is standard (80 or 443).
    3. Hostname resolves only to public, non-private, non-link-local IP addresses.
    """
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise SSRFSecurityError(url, f"Malformed URL syntax: {str(e)}")

    # 1. Scheme Check
    if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFSecurityError(url, f"Invalid scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    # 2. Port Check
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise SSRFSecurityError(url, f"Invalid port {port}. Only standard web ports (80, 443) are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError(url, "Missing hostname in target URL.")

    # 3. Resolve DNS and inspect resolved IP addresses
    try:
        # Get all resolved IP addresses
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        ip_addresses = [info[4][0] for info in addr_info]
    except socket.gaierror as e:
        raise SSRFSecurityError(url, f"DNS resolution failed for hostname '{hostname}': {str(e)}")

    if not ip_addresses:
        raise SSRFSecurityError(url, f"No IP address found for hostname '{hostname}'.")

    for ip_str in ip_addresses:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFSecurityError(url, f"Invalid IP address format: {ip_str}")

        # Check against blacklist
        for blocked_net in BLOCKED_IP_NETWORKS:
            if ip_obj in blocked_net:
                raise SSRFSecurityError(
                    url,
                    f"Resolved IP {ip_str} falls within restricted network range {blocked_net}.",
                )


class SafeHttpClient:
    """HTTP Client wrapper enforcing SSRF protection, timeouts, and headers."""

    def __init__(self, timeout: float = 15.0, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent
            or "PricingIntelligenceEngine/1.0 (+https://example.com/bot; responsible price aggregator)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Executes a safe GET request after passing SSRF validation."""
        validate_url_for_ssrf(url)
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=False) as client:
            response = await client.get(url, params=params)

            # Manually validate redirect targets if 3xx
            if response.is_redirect and "location" in response.headers:
                redirect_url = urllib.parse.urljoin(url, response.headers["location"])
                logger.info("Following redirect to: %s", redirect_url)
                validate_url_for_ssrf(redirect_url)
                response = await client.get(redirect_url)

            return response
