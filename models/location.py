from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Matcha Cafe Location ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    name: str = Field(
        ...,
        description="Name of the cafe.",
        json_schema_extra={"example": "Sorate"},
    )
    street: str = Field(
        ...,
        description="Street address and number.",
        json_schema_extra={"example": "103 Sullivan St"},
    )
    city: str = Field(
        ...,
        description="City or locality.",
        json_schema_extra={"example": "New York"},
    )
    state: Optional[str] = Field(
        None,
        description="State/region code if applicable.",
        json_schema_extra={"example": "NY"},
    )
    postal_code: Optional[str] = Field(
        None,
        description="Postal or ZIP code.",
        json_schema_extra={"example": "10012"},
    )
    country: str = Field(
        ...,
        description="Country name or ISO label.",
        json_schema_extra={"example": "USA"},
    )
    best_drink: Optional[str] = Field(
        ...,
        description="Best drink from this cafe.",
        json_schema_extra={"example": "Lavender lemon matcha w/ honey"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Sorate",
                    "street": "103 Sullivan St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10012",
                    "country": "USA",
                    "best_drink": "Lavender lemon matcha w/ honey",
                }
            ]
        }
    }


class LocationCreate(LocationBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "name": "Isshiki",
                    "street": "183 Grand Street",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10013",
                    "country": "USA",
                    "best_drink": "Lavender lemon matcha w/ honey",
                }
            ]
        }
    }


class LocationUpdate(BaseModel):
    """Partial update; address ID is taken from the path, not the body."""
    name: Optional[str] = Field(
        None, description="Name of the cafe.", json_schema_extra={"example": "Isshiki"}
    )
    street: Optional[str] = Field(
        None, description="Street address and number.", json_schema_extra={"example": "183 Grand St"}
    )
    city: Optional[str] = Field(
        None, description="City or locality.", json_schema_extra={"example": "New York"}
    )
    state: Optional[str] = Field(
        None, description="State/region code if applicable.", json_schema_extra={"example": "NY"}
    )
    postal_code: Optional[str] = Field(
        None, description="Postal or ZIP code.", json_schema_extra={"example": "10013"}
    )
    country: Optional[str] = Field(
        None, description="Country name or ISO label.", json_schema_extra={"example": "USA"}
    )
    best_drink: Optional[str] = Field(
        None, description="Best drink from this cafe.", json_schema_extra={"example": "Lavender honey oat matcha latte"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Isshiki",
                    "street": "183 Grand St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10002",
                    "country": "USA",
                    "best_drink": "Lavender honey oat matcha latte",
                },
                {"name": "Isshiki"},
            ]
        }
    }


class LocationRead(LocationBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Sorate",
                    "street": "103 Sullivan St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10012",
                    "country": "USA",
                    "best_drink": "Lavender lemon matcha w/ honey",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
