"""Grounded brief from an approved audience and one campaign.

The campaign chooser returns an id. Offer, channels, and constraint are copied
from that campaign. A draft audience, a missing id, or a failed brief returns
nothing. This module writes no file.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from builder.schemas import Audience, Brief, Campaign
from builder.tools import list_campaigns

CampaignChooser = Callable[[Audience, list[Campaign]], str]


class BriefError(ValueError):
    """The brief step could not choose a campaign."""


class ScriptedCampaignChooser:
    """Return one campaign id and record each call."""

    def __init__(self, campaign_id: str) -> None:
        self.campaign_id = campaign_id
        self.calls: list[tuple[Audience, list[Campaign]]] = []

    def __call__(self, audience: Audience, campaigns: list[Campaign]) -> str:
        self.calls.append((audience, list(campaigns)))
        return self.campaign_id


class XAICampaignChooser:
    """Default provider. The model id stays unset until the first live call."""

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id

    def __call__(self, audience: Audience, campaigns: list[Campaign]) -> str:
        raise BriefError("xAI model id is not chosen, so no live call is made")


def draft_brief(
    audience: Audience | dict,
    chooser: CampaignChooser | None = None,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> Brief | None:
    approved = _approved(audience)
    if approved is None:
        return None
    campaigns = list_campaigns(log_path=log_path, run_id=run_id).campaigns
    chosen = chooser if chooser is not None else XAICampaignChooser()
    try:
        campaign_id = chosen(approved, campaigns)
    except BriefError:
        return None
    if not isinstance(campaign_id, str):
        return None
    campaign = next((item for item in campaigns if item.id == campaign_id), None)
    if campaign is None:
        return None
    try:
        return Brief.model_validate(
            {
                "audience": approved.model_dump(),
                "campaign_id": campaign.id,
                "offer": campaign.offer,
                "channels": list(campaign.channels),
                "constraint": campaign.constraint,
            }
        )
    except ValidationError:
        return None


def _approved(audience: Audience | dict) -> Audience | None:
    try:
        parsed = audience if isinstance(audience, Audience) else Audience.model_validate(audience)
    except ValidationError:
        return None
    if parsed.status != "approved":
        return None
    return parsed
