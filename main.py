from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi import Query, Path
from typing import Optional

from models.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from models.location import LocationCreate, LocationRead, LocationUpdate

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Fake in-memory "databases"
# -----------------------------------------------------------------------------
expenses: Dict[UUID, ExpenseRead] = {}
locations: Dict[UUID, LocationRead] = {}

app = FastAPI(
    title="Matcha Budget Tracker API",
    description="Demo FastAPI app using Pydantic v2 models for Matcha Budget Tracker",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Expense endpoints
# -----------------------------------------------------------------------------

@app.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(expense: ExpenseCreate):
    if expense.id in expenses:
        raise HTTPException(status_code=400, detail="Expense with this ID already exists")
    expenses[expense.id] = ExpenseRead(**expense.model_dump())
    return expenses[expense.id]

@app.get("/expenses", response_model=List[ExpenseRead])
def list_expenses(
    expense_date: Optional[str] = Query(None, description="Filter by expense date"),
    order_name: Optional[str] = Query(None, description="Filter by order name"),
    type: Optional[str] = Query(None, description="Filter by type of expense"),
    location: Optional[str] = Query(None, description="Filter by location of purchase"),
    cost: Optional[str] = Query(None, description="Filter by cost of matcha"),
):
    results = list(expenses.values())

    if expense_date is not None:
        results = [a for a in results if str(a.expense_date) == expense_date]
    if order_name is not None:
        results = [a for a in results if a.order_name == order_name]
    if type is not None:
        results = [a for a in results if a.type == type]
    if location is not None:
        results = [a for a in results if a.location == location]
    if cost is not None:
        results = [a for a in results if a.cost == cost]

    return results

@app.get("/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: UUID):
    if expense_id not in expenses:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expenses[expense_id]

@app.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: UUID, update: ExpenseUpdate):
    if expense_id not in expenses:
        raise HTTPException(status_code=404, detail="Expense not found")
    stored = expenses[expense_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    expenses[expense_id] = ExpenseRead(**stored)
    return expenses[expense_id]

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: UUID):
    if expense_id not in expenses:
        raise HTTPException(status_code=404, detail="Expense not found")
    del expenses[expense_id]
    return None

# -----------------------------------------------------------------------------
# Location endpoints
# -----------------------------------------------------------------------------
@app.post("/locations", response_model=LocationRead, status_code=201)
def create_location(location: LocationCreate):
    # Each person gets its own UUID; stored as PersonRead
    location_read = LocationRead(**location.model_dump())
    locations[location_read.id] = location_read
    return location_read

@app.get("/locations", response_model=List[LocationRead])
def list_locations(
    name: Optional[str] = Query(None, description="Filter by name of cafe"),
    street: Optional[str] = Query(None, description="Filter by street"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state/region"),
    postal_code: Optional[str] = Query(None, description="Filter by postal code"),
    country: Optional[str] = Query(None, description="Filter by country"),
    best_drink: Optional[str] = Query(None, description="Filter by best drink"),
):
    results = list(locations.values())

    if name is not None:
        results = [p for p in results if p.name == name]
    if street is not None:
        results = [p for p in results if p.street == street]
    if city is not None:
        results = [p for p in results if p.city == city]
    if state is not None:
        results = [p for p in results if p.state == state]
    if postal_code is not None:
        results = [p for p in results if p.postal_code == postal_code]
    if country is not None:
        results = [p for p in results if p.country == country]
    if best_drink is not None:
        results = [p for p in results if p.best_drink == best_drink]

    # nested address filtering
    if city is not None:
        results = [p for p in results if any(addr.city == city for addr in p.locations)]
    if country is not None:
        results = [p for p in results if any(addr.country == country for addr in p.locations)]

    return results

@app.get("/locations/{location_id}", response_model=LocationRead)
def get_location(location_id: UUID):
    if location_id not in locations:
        raise HTTPException(status_code=404, detail="Location not found")
    return locations[location_id]

@app.patch("/locations/{location_id}", response_model=LocationRead)
def update_location(location_id: UUID, update: LocationUpdate):
    if location_id not in locations:
        raise HTTPException(status_code=404, detail="Location not found")
    stored = locations[location_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    locations[location_id] = LocationRead(**stored)
    return locations[location_id]

@app.delete("/locations/{location_id}", status_code=204)
def delete_location(location_id: UUID):
    if location_id not in locations:
        raise HTTPException(status_code=404, detail="Location not found")
    del locations[location_id]
    return None

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Matcha Budget API. See /docs for OpenAPI UI."}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
