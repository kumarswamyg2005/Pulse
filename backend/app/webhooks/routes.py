import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_membership, get_db, require_role
from app.models import Membership, Role, Team, Webhook
from app.plans import limits

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: str


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    active: bool


@router.post("", status_code=201, response_model=WebhookOut)
async def create_webhook(
    body: WebhookCreate,
    membership: Membership = Depends(require_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> WebhookOut:
    team = await db.get(Team, membership.team_id)
    assert team is not None
    if not limits(team.tier)["webhooks"]:
        raise HTTPException(402, "Webhooks require the Pro plan or higher.")
    webhook = Webhook(team_id=membership.team_id, url=body.url)
    db.add(webhook)
    await db.flush()
    return WebhookOut.model_validate(webhook)


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookOut]:
    rows = (await db.execute(select(Webhook).order_by(Webhook.created_at))).scalars().all()
    return [WebhookOut.model_validate(w) for w in rows]


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: uuid.UUID,
    _: Membership = Depends(require_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> None:
    webhook = await db.get(Webhook, webhook_id)
    if webhook is None:
        raise HTTPException(404, "Webhook not found")
    await db.delete(webhook)
