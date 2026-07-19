# 07 — Incident state machine + acknowledge + timeline

**What to build:** `incidents` table. Wire into the check pipeline: 3 consecutive failed results with no open incident → open one; 2 consecutive successes while an incident is open → resolve it. Acknowledge (member+). Incident timeline UI per monitor + an open-incidents view.

**Blocked by:** 06

**Status:** done

- [x] 3 consecutive failures open exactly one incident; further failures don't duplicate it
- [x] 2 consecutive successes resolve the open incident
- [x] Member can acknowledge an open incident (records who/when; does not resolve)
- [x] Incident timeline + open-incidents list render
- [x] Incident lifecycle covered by a pipeline integration test (non-negotiable)
