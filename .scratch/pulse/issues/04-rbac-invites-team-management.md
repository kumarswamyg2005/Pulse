# 04 — RBAC + invites + team/member management

**What to build:** An authorization dependency that resolves the caller's role in the current team and enforces permissions (owner ⊃ admin ⊃ member). Invite by email (hashed, expiring token, pre-assigned role); accept invite as a new or existing user; list/change-role/remove members; transfer ownership; delete team; switch current team. Frontend team settings + members UI + invite-accept page.

**Blocked by:** 02

**Status:** done

- [x] Owner/admin can invite by email; accepting the tokenized link joins the team with the assigned role
- [x] Members are read-only; management writes return 403 (`team_role` dependency)
- [x] Role change / member removal / ownership transfer / team delete enforced by role; owner protected
- [x] User can switch current team (session GUC updates); UI switcher reflects it
- [x] Expired/used invite tokens rejected; accept requires matching email

## Comments

Backend green: ruff + mypy + 23 pytest. Verified live in Docker across two users: invite→201, accept→201, members=2. Frontend adds team switcher, members page (invite/role/remove gated by role), invite-accept page; build green. `/auth/me` now returns each team's role for UI gating.
