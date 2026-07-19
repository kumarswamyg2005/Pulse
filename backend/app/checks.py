import socket
import ssl
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from app.models import Monitor, MonitorType


@dataclass
class CheckOutcome:
    up: bool
    status_code: int | None = None
    latency_ms: int | None = None
    error: str | None = None
    cert_expires_at: datetime | None = None


def _tls_expiry(url: str) -> datetime | None:
    """Best-effort TLS certificate expiry for an https URL. Never raises."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443
        if not host:
            return None
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter") if cert else None
        if not isinstance(not_after, str):
            return None
        return datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
    except Exception:
        return None


def http_check(monitor: Monitor, client: httpx.Client | None = None) -> CheckOutcome:
    owns = client is None
    client = client or httpx.Client(timeout=monitor.timeout_seconds, follow_redirects=True)
    try:
        start = time.perf_counter()
        resp = client.get(monitor.url or "")
        latency = int((time.perf_counter() - start) * 1000)
        up = monitor.expected_status_min <= resp.status_code <= monitor.expected_status_max
        error: str | None = None
        if not up:
            error = (
                f"status {resp.status_code} outside "
                f"{monitor.expected_status_min}-{monitor.expected_status_max}"
            )
        elif monitor.keyword and monitor.keyword not in resp.text:
            up = False
            error = "keyword not found"
        cert = _tls_expiry(monitor.url) if monitor.url and monitor.url.startswith("https") else None
        return CheckOutcome(
            up=up,
            status_code=resp.status_code,
            latency_ms=latency,
            error=error,
            cert_expires_at=cert,
        )
    except Exception as e:
        return CheckOutcome(up=False, error=str(e)[:500])
    finally:
        if owns:
            client.close()


def tcp_check(monitor: Monitor) -> CheckOutcome:
    start = time.perf_counter()
    try:
        with socket.create_connection(
            (monitor.host, monitor.port), timeout=monitor.timeout_seconds
        ):
            latency = int((time.perf_counter() - start) * 1000)
            return CheckOutcome(up=True, latency_ms=latency)
    except Exception as e:
        return CheckOutcome(up=False, error=str(e)[:500])


def ping_check(monitor: Monitor) -> CheckOutcome:
    # Uses the system `ping` (no raw-socket privilege needed). -c 1 = one echo.
    host = monitor.host or ""
    start = time.perf_counter()
    try:
        result = subprocess.run(
            ["ping", "-c", "1", host],
            capture_output=True,
            timeout=monitor.timeout_seconds + 2,
        )
        latency = int((time.perf_counter() - start) * 1000)
        up = result.returncode == 0
        return CheckOutcome(
            up=up, latency_ms=latency if up else None, error=None if up else "no reply"
        )
    except Exception as e:
        return CheckOutcome(up=False, error=str(e)[:500])


CHECKERS: dict[MonitorType, Callable[[Monitor], CheckOutcome]] = {
    MonitorType.http: http_check,
    MonitorType.tcp: tcp_check,
    MonitorType.ping: ping_check,
}


def run_monitor_check(monitor: Monitor) -> CheckOutcome:
    checker = CHECKERS.get(monitor.type)
    if checker is None:
        return CheckOutcome(up=False, error=f"unsupported monitor type {monitor.type}")
    return checker(monitor)
