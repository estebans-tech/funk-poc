from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine("sqlite:///./policies.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PolicyDB(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, index=True)
    holder = Column(String, index=True)
    premium = Column(Float)
    status = Column(String, index=True)

Base.metadata.create_all(bind=engine)

class Policy(BaseModel):
    number: str
    holder: str
    premium: float
    status: str

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

@app.post("/policies")
def create_policy(p: Policy):
    db = SessionLocal()
    row = PolicyDB(**p.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
