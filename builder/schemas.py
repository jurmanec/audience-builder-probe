"""Shared audience, brief, and tool records.

Catalog checks stay in count_predicate. This module checks shape only.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Status = Literal["draft", "approved"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PredicateClause(StrictModel):
    field: str = Field(min_length=1)
    op: str = Field(min_length=1)
    value: int | bool | str | list[int] | list[str]


class Predicate(StrictModel):
    all: list[PredicateClause] = Field(min_length=1)


class Audience(StrictModel):
    predicates: Predicate
    estimated_size: int = Field(ge=0)
    status: Status


class Brief(StrictModel):
    audience: Audience
    campaign_id: str = Field(min_length=1)
    offer: str = Field(min_length=1)
    channels: list[str] = Field(min_length=1)
    constraint: str = Field(min_length=1)

    @model_validator(mode="after")
    def audience_is_approved(self) -> Self:
        if self.audience.status != "approved":
            raise ValueError("brief audience must be approved")
        if any(not channel for channel in self.channels):
            raise ValueError("brief channels must be non-empty")
        return self


class CountInput(StrictModel):
    predicate: Predicate


class CountResult(StrictModel):
    count: int | None = Field(default=None, ge=0)
    error_class: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def count_or_rejection(self) -> Self:
        has_count = self.count is not None
        has_error = self.error_class is not None
        if has_count == has_error:
            raise ValueError("count result must be a row count or a rejection")
        return self


class PriorAttempt(StrictModel):
    predicate: Predicate
    count: int | None = Field(default=None, ge=0)
    error_class: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def count_or_rejection(self) -> Self:
        has_count = self.count is not None
        has_error = self.error_class is not None
        if has_count == has_error:
            raise ValueError("prior attempt must be a row count or a rejection")
        return self


class CatalogResult(StrictModel):
    names: list[str]

    @model_validator(mode="after")
    def usable_names(self) -> Self:
        if any(not name for name in self.names) or len(self.names) != len(set(self.names)):
            raise ValueError("attribute names must be unique and non-empty")
        return self


class Campaign(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    offer: str = Field(min_length=1)
    channels: list[str] = Field(min_length=1)
    constraint: str = Field(min_length=1)
    outcome: str = Field(min_length=1)

    @model_validator(mode="after")
    def channels_are_present(self) -> Self:
        if any(not channel for channel in self.channels):
            raise ValueError("campaign channels must be non-empty")
        return self


class CampaignList(StrictModel):
    campaigns: list[Campaign] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        ids = [campaign.id for campaign in self.campaigns]
        if len(ids) != len(set(ids)):
            raise ValueError("campaign ids must be unique")
        return self
