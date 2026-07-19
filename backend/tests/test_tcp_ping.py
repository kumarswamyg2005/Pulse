import socket

from app.checks import ping_check, tcp_check
from app.models import Monitor, MonitorType


def test_tcp_check_up_then_down():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    up = tcp_check(Monitor(type=MonitorType.tcp, host="127.0.0.1", port=port, timeout_seconds=2))
    assert up.up is True
    assert up.latency_ms is not None

    server.close()
    down = tcp_check(Monitor(type=MonitorType.tcp, host="127.0.0.1", port=port, timeout_seconds=1))
    assert down.up is False


def test_ping_localhost_up():
    out = ping_check(Monitor(type=MonitorType.ping, host="127.0.0.1", timeout_seconds=3))
    assert out.up is True


async def test_create_tcp_and_ping_monitors(clients):
    c = await clients()
    await c.post("/auth/signup", json={"email": "np@x.com", "password": "password123"})

    r = await c.post(
        "/monitors", json={"name": "DB", "type": "tcp", "host": "db.example.com", "port": 5432}
    )
    assert r.status_code == 201
    assert r.json()["type"] == "tcp"

    r = await c.post("/monitors", json={"name": "Gateway", "type": "ping", "host": "1.1.1.1"})
    assert r.status_code == 201
    assert r.json()["type"] == "ping"

    # missing host is rejected
    assert (await c.post("/monitors", json={"name": "x", "type": "tcp"})).status_code == 422
