from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from parser_core import Area


class AreaRequest(BaseModel):
    type: Literal["bbox", "polygon"]
    coordinates: list[Any]

    def to_core(self) -> Area:
        return Area.from_dict(self.model_dump())


class JobCreate(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    area: AreaRequest
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


class ResultPage(BaseModel):
    items: list[dict[str, Any]]
    total: int
    offset: int
    limit: int

