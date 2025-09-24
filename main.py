from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine("sqlite:///./policies.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PolicyDB(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True)
    holder = Column(String, index=True)
    premium = Column(Float)
    status = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# säkerställ unikt index (om gammal db saknar det)
with engine.begin() as conn:
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uniq_policy_number ON policies(number);"))

class PolicyIn(BaseModel):
    number: str = Field(..., min_length=3, max_length=64)
    holder: str = Field(..., min_length=2, max_length=128)
    premium: float = Field(..., ge=0)
    status: str = Field(..., min_length=2, max_length=32)

class PolicyOut(PolicyIn):
    id: int

@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: Optional[str] = None):
    db = SessionLocal()
    query = db.query(PolicyDB)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (PolicyDB.number.like(like)) |
            (PolicyDB.holder.like(like)) |
            (PolicyDB.status.like(like))
        )
    items = query.order_by(PolicyDB.id.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "items": items, "q": q or ""})

@app.get("/policies", response_model=List[PolicyOut])
def list_policies(
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = SessionLocal()
    query = db.query(PolicyDB)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (PolicyDB.number.like(like)) |
            (PolicyDB.holder.like(like)) |
            (PolicyDB.status.like(like))
        )
    rows = query.order_by(PolicyDB.id.desc()).offset(offset).limit(limit).all()
    return [PolicyOut(id=r.id, number=r.number, holder=r.holder, premium=r.premium, status=r.status) for r in rows]

@app.post("/policies", response_model=PolicyOut)
def create_policy(p: PolicyIn):
    db = SessionLocal()
    row = PolicyDB(**p.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return PolicyOut(id=row.id, **p.model_dump())
