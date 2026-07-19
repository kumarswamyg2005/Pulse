from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Workers legitimately operate across all tenants (scan every due monitor), so they connect
# as the admin role, which bypasses RLS. Rows they write still carry team_id, so the
# user-facing request path (pulse_app + RLS) stays correctly scoped.
sync_engine = create_engine(settings.admin_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)
