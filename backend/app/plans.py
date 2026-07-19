"""Plan (tier) limits — the single source enforcement reads. Preset A from the spec."""

from typing import TypedDict


class PlanLimits(TypedDict):
    max_monitors: int  # -1 = unlimited
    min_interval: int  # seconds
    max_seats: int
    webhooks: bool
    retention_days: int
    max_status_pages: int


PLANS: dict[str, PlanLimits] = {
    "free": {
        "max_monitors": 3,
        "min_interval": 300,
        "max_seats": 1,
        "webhooks": False,
        "retention_days": 7,
        "max_status_pages": 1,
    },
    "pro": {
        "max_monitors": 25,
        "min_interval": 60,
        "max_seats": 5,
        "webhooks": True,
        "retention_days": 90,
        "max_status_pages": 1,
    },
    "team": {
        "max_monitors": 100,
        "min_interval": 30,
        "max_seats": 25,
        "webhooks": True,
        "retention_days": 365,
        "max_status_pages": 3,
    },
}


def limits(tier: str) -> PlanLimits:
    return PLANS.get(tier, PLANS["free"])
