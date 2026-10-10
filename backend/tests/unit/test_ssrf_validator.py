"""Unit tests for SSRF Security Validator."""

import socket
import pytest
from unittest.mock import patch
from app.core.exceptions import SSRFSecurityError
from app.core.security import validate_url_for_ssrf


def test_ssrf_blocks_private_and_loopback_ips():
    """Verify SSRF blocks loopback, private subnets, and cloud metadata."""

    # 1. Loopback
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]):
        with pytest.raises(SSRFSecurityError) as exc_info:
            validate_url_for_ssrf("http://127.0.0.1/admin")
        assert "restricted network range" in str(exc_info.value)

    # 2. Cloud Metadata (AWS / GCP / Azure 169.254.169.254)
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))]):
        with pytest.raises(SSRFSecurityError) as exc_info:
            validate_url_for_ssrf("http://169.254.169.254/latest/meta-data")
        assert "restricted network range" in str(exc_info.value)

    # 3. RFC 1918 Class A (10.0.0.1)
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80))]):
        with pytest.raises(SSRFSecurityError):
            validate_url_for_ssrf("http://internal-router.corp/status")

    # 4. RFC 1918 Class C (192.168.1.1)
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]):
        with pytest.raises(SSRFSecurityError):
            validate_url_for_ssrf("http://192.168.1.1/config")


def test_ssrf_blocks_invalid_schemes_and_ports():
    """Verify non-http schemes and non-standard ports are rejected."""
    with pytest.raises(SSRFSecurityError) as exc:
        validate_url_for_ssrf("ftp://example.com/file.txt")
    assert "Invalid scheme" in str(exc.value)

    with pytest.raises(SSRFSecurityError) as exc:
        validate_url_for_ssrf("file:///etc/passwd")
    assert "Invalid scheme" in str(exc.value)

    with pytest.raises(SSRFSecurityError) as exc:
        validate_url_for_ssrf("http://example.com:8080/data")
    assert "Invalid port" in str(exc.value)


def test_ssrf_permits_public_ips():
    """Verify legitimate public IP addresses pass validation."""
    with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]):
        # Should not raise exception
        validate_url_for_ssrf("http://example.com")
        validate_url_for_ssrf("https://books.toscrape.com/catalogue/page-1.html")
