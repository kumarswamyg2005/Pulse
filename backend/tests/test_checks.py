import httpx

from app.checks import http_check
from app.models import Monitor, MonitorType


def _monitor(url="http://x.test", keyword=None, smin=200, smax=399):
    return Monitor(
        name="t",
        type=MonitorType.http,
        url=url,
        keyword=keyword,
        expected_status_min=smin,
        expected_status_max=smax,
        timeout_seconds=5,
    )


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_http_check_up_with_keyword():
    out = http_check(
        _monitor(keyword="hello"), client=_client(lambda r: httpx.Response(200, text="hello world"))
    )
    assert out.up is True
    assert out.status_code == 200
    assert out.latency_ms is not None


def test_http_check_bad_status():
    out = http_check(_monitor(), client=_client(lambda r: httpx.Response(500, text="boom")))
    assert out.up is False
    assert out.status_code == 500


def test_http_check_missing_keyword():
    out = http_check(
        _monitor(keyword="expected"), client=_client(lambda r: httpx.Response(200, text="nope"))
    )
    assert out.up is False
    assert out.error == "keyword not found"


def test_http_check_connection_error():
    def boom(request):
        raise httpx.ConnectError("connection refused")

    out = http_check(_monitor(), client=_client(boom))
    assert out.up is False
    assert out.error
