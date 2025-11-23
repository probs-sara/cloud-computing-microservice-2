from __future__ import annotations

import os
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, DECIMAL, DateTime, Text, Date, Float
from sqlalchemy.orm import Session, sessionmaker, declarative_base

import hashlib
import threading
import time

from models.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from models.location import LocationCreate, LocationRead, LocationUpdate

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://matcha:4566427@localhost:3306/matcha_budget"
)

print(f"🔍 Using DATABASE_URL: {DATABASE_URL}")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    print("Database engine created successfully")
except Exception as e:
    print(f"Error creating database engine: {e}")
    raise

# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------
class ExpenseModel(Base):
    __tablename__ = "expenses"
    
    id = Column(String(36), primary_key=True)
    expense_date = Column(Date, nullable=False)
    order_name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    location_url = Column(String(512), nullable=True)
    cost = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class LocationModel(Base):
    __tablename__ = "locations"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    street = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False)
    best_drink = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class AsyncJobModel(Base):
    __tablename__ = "async_jobs"
    
    job_id = Column(String(36), primary_key=True)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating tables: {e}")
    raise

# -----------------------------------------------------------------------------
# Dependency
# -----------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# FastAPI App
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Matcha Budget Tracker API",
    description="Demo FastAPI app using Pydantic v2 models with SQLAlchemy + MySQL",
    version="0.2.0",
)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def generate_etag(items: List[ExpenseRead | LocationRead]) -> str:
    combined = "-".join([str(item.updated_at.timestamp()) for item in items])
    return hashlib.sha256(combined.encode()).hexdigest()

def paginate(items: List[ExpenseRead | LocationRead], limit: int, offset: int):
    total = len(items)
    paged = items[offset: offset + limit]
    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset - limit >= 0 else None
    links = {}
    if next_offset is not None:
        links["next"] = f"?limit={limit}&offset={next_offset}"
    if prev_offset is not None:
        links["prev"] = f"?limit={limit}&offset={prev_offset}"
    return paged, links

def expense_model_to_read(expense: ExpenseModel) -> ExpenseRead:
    return ExpenseRead(
        id=UUID(expense.id),
        expense_date=expense.expense_date,
        order_name=expense.order_name,
        type=expense.type,
        location=expense.location,
        cost=expense.cost,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )

def location_model_to_read(location: LocationModel) -> LocationRead:
    return LocationRead(
        id=UUID(location.id),
        name=location.name,
        street=location.street,
        city=location.city,
        state=location.state,
        postal_code=location.postal_code,
        country=location.country,
        best_drink=location.best_drink,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )

# -----------------------------------------------------------------------------
# Expense endpoints
# -----------------------------------------------------------------------------

@app.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    existing = db.query(ExpenseModel).filter(ExpenseModel.id == str(expense.id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Expense with this ID already exists")
    
    now = datetime.utcnow()
    
    db_expense = ExpenseModel(
        id=str(expense.id),
        expense_date=expense.expense_date,
        order_name=expense.order_name,
        type=expense.type,
        location=expense.location,
        cost=expense.cost,
        created_at=now,
        updated_at=now
    )
    
    if db_expense.location:
        location = db.query(LocationModel).filter(LocationModel.name == db_expense.location).first()
        if location:
            db_expense.location_url = f"/locations/{location.id}"
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    return expense_model_to_read(db_expense)

@app.get("/expenses", response_model=List[ExpenseRead])
def list_expenses(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    if_none_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    all_expenses = db.query(ExpenseModel).order_by(ExpenseModel.created_at.desc()).all()
    items = [expense_model_to_read(exp) for exp in all_expenses]
    
    paged, links = paginate(items, limit, offset)
    etag = generate_etag(paged)
    
    if if_none_match == etag:
        return JSONResponse(status_code=304)
    
    content = [item.model_dump(mode='json') | {"links": links} for item in paged]
    return JSONResponse(content=content, headers={"ETag": etag})

@app.get("/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: UUID,
    if_none_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    db_expense = db.query(ExpenseModel).filter(ExpenseModel.id == str(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    item = expense_model_to_read(db_expense)
    etag = generate_etag([item])
    
    if if_none_match == etag:
        return JSONResponse(status_code=304)
    
    return JSONResponse(content=item.model_dump(mode='json'), headers={"ETag": etag})

@app.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: UUID,
    update: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    db_expense = db.query(ExpenseModel).filter(ExpenseModel.id == str(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    db_expense.updated_at = datetime.utcnow()
    
    if db_expense.location:
        location = db.query(LocationModel).filter(LocationModel.name == db_expense.location).first()
        if location:
            db_expense.location_url = f"/locations/{location.id}"
        else:
            db_expense.location_url = None
    
    db.commit()
    db.refresh(db_expense)
    
    return expense_model_to_read(db_expense)

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: UUID, db: Session = Depends(get_db)):
    db_expense = db.query(ExpenseModel).filter(ExpenseModel.id == str(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return None

# -----------------------------------------------------------------------------
# Async 202 endpoint
# -----------------------------------------------------------------------------
@app.post("/expenses/async-process", status_code=202)
def async_process_expense(db: Session = Depends(get_db)):
    job_id = str(uuid4())
    now = datetime.utcnow()
    
    db_job = AsyncJobModel(
        job_id=job_id,
        status="pending",
        created_at=now,
        updated_at=now
    )
    db.add(db_job)
    db.commit()
    
    def complete_job():
        time.sleep(5)
        job_db = SessionLocal()
        try:
            job = job_db.query(AsyncJobModel).filter(AsyncJobModel.job_id == job_id).first()
            if job:
                job.status = "completed"
                job.updated_at = datetime.utcnow()
                job_db.commit()
        finally:
            job_db.close()
    
    threading.Thread(target=complete_job).start()
    
    return {
        "job_id": job_id,
        "status": "pending",
        "poll_url": f"/expenses/async-process/{job_id}"
    }

@app.get("/expenses/async-process/{job_id}")
def poll_job(job_id: str, db: Session = Depends(get_db)):
    db_job = db.query(AsyncJobModel).filter(AsyncJobModel.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": db_job.job_id,
        "status": db_job.status
    }

# -----------------------------------------------------------------------------
# Location endpoints
# -----------------------------------------------------------------------------
@app.post("/locations", response_model=LocationRead, status_code=201)
def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(LocationModel).filter(LocationModel.name == location.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Location with this name already exists")
    
    now = datetime.utcnow()
    
    db_location = LocationModel(
        id=str(location.id),
        name=location.name,
        street=location.street,
        city=location.city,
        state=location.state,
        postal_code=location.postal_code,
        country=location.country,
        best_drink=location.best_drink,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return location_model_to_read(db_location)

@app.get("/locations", response_model=List[LocationRead])
def list_locations(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    if_none_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    all_locations = db.query(LocationModel).order_by(LocationModel.created_at.desc()).all()
    items = [location_model_to_read(loc) for loc in all_locations]
    
    paged, links = paginate(items, limit, offset)
    etag = generate_etag(paged)
    
    if if_none_match == etag:
        return JSONResponse(status_code=304)
    
    content = [item.model_dump(mode='json') | {"links": links} for item in paged]
    return JSONResponse(content=content, headers={"ETag": etag})

@app.get("/locations/{location_id}", response_model=LocationRead)
def get_location(
    location_id: UUID,
    if_none_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    db_location = db.query(LocationModel).filter(LocationModel.id == str(location_id)).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    item = location_model_to_read(db_location)
    etag = generate_etag([item])
    
    if if_none_match == etag:
        return JSONResponse(status_code=304)
    
    return JSONResponse(content=item.model_dump(mode='json'), headers={"ETag": etag})

@app.patch("/locations/{location_id}", response_model=LocationRead)
def update_location(
    location_id: UUID,
    update: LocationUpdate,
    db: Session = Depends(get_db)
):
    db_location = db.query(LocationModel).filter(LocationModel.id == str(location_id)).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    
    db_location.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_location)
    
    return location_model_to_read(db_location)

@app.delete("/locations/{location_id}", status_code=204)
def delete_location(location_id: UUID, db: Session = Depends(get_db)):
    db_location = db.query(LocationModel).filter(LocationModel.id == str(location_id)).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(db_location)
    db.commit()
    return None

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Welcome to the Matcha Budget API (SQLAlchemy + MySQL). See /docs for OpenAPI UI.",
        "version": "0.2.0"
    }

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)