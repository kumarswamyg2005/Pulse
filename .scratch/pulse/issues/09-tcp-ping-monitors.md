# 09 — TCP + ping monitor types

**What to build:** `tcp` check (socket connect within timeout) and `ping` check (ICMP echo with a subprocess `ping` fallback where raw sockets are blocked) added to the check registry; create/edit forms accept type + target (host+port for TCP, host for ping). Reuses the 06 pipeline and 07 incidents/alerts.

**Blocked by:** 06

**Status:** done

- [x] Create/edit TCP (host+port) and ping (host) monitors
- [x] TCP/ping checks record results through the same pipeline (incidents + alerts apply)
- [x] ping works where raw ICMP is blocked (subprocess fallback)

## Comments

Verified live in Docker: TCP (1.1.1.1:443 up, 18ms) + ping (1.1.1.1 up, 23ms) via the real worker. Added iputils-ping to the image. Reuses the 06 pipeline + 07/08 incidents/alerts. Frontend create form gained type + host/port fields.
