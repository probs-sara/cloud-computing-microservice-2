from __future__ import annotations

from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr, StringConstraints

ExpenseType = Annotated[str, StringConstraints(pattern=r"^(Cafe|Self-made)$")]

class ExpenseBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Expense ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    expense_date: date = Field(
        ...,
        description="Date of the Matcha order/creation.",
        json_schema_extra={"example": "2025-01-01"},
    )
    order_name: str = Field(
        ...,
        description="Name of the Matcha order.",
        json_schema_extra={"example": "Lavender Matcha Latte w/ Oat Milk"},
    )
    type: ExpenseType = Field(
        ...,
        description="Type of matcha purchased/made.",
        json_schema_extra={"example": "Cafe"},
    )
    location: Optional[str] = Field(
        None,
        description="Where the matcha was purchased.",
        json_schema_extra={"example": "Isshiki Kijitora"},
    )
    cost: float = Field(
        ...,
        description="How much the matcha cost.",
        json_schema_extra={"example": 9.99},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "expense_date": "2025-01-01",
                    "order_name": "Lavender Matcha Latte w/ Oat Milk",
                    "type": "Cafe",
                    "location": "Isshiki Kijitora",
                    "cost": 9.99,
                }
            ]
        }
    }


class ExpenseCreate(ExpenseBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "expense_date": "2020-01-20",
                    "order_name": "Matcha latte w/ oat milk",
                    "type": "Self-made",
                    "location": "Home",
                    "cost": 0.40,
                }
            ]
        }
    }


class ExpenseUpdate(BaseModel):
    """Partial update; address ID is taken from the path, not the body."""
    expense_date: Optional[date] = Field(
        None, description="Date of the matcha order/creation.", json_schema_extra={"example": "2025-01-02"}
    )
    order_name: Optional[str] = Field(
        None, description="Name of the matcha order.", json_schema_extra={"example": "Matcha latte w/ almond milk"}
    )
    type: Optional[ExpenseType] = Field(
        None, description="Type of matcha purchase/made.", json_schema_extra={"example": "Cafe"}
    )
    location: Optional[str] = Field(
        None, description="Where the matcha was purchased.", json_schema_extra={"example": "Sorate"}
    )
    cost: Optional[float] = Field(
        None, description="How much the matcha cost.", json_schema_extra={"example": 9.57}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "expense_date": "2025-01-02",
                    "order_name": "Matcha latte w/ almond milk",
                    "type": "Cafe",
                    "location": "Sorate",
                    "cost": 9.57,
                },
                {"location": "Isshiki Kijitora"},
            ]
        }
    }


class ExpenseRead(ExpenseBase):
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
                    "expense_date": "2025-01-01",
                    "order_name": "Lavender Matcha Latte w/ Oat Milk",
                    "type": "Cafe",
                    "location": "Isshiki Kijitora",
                    "cost": 9.99,
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
