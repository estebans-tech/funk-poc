from fastapi import FastAPI, Request, Query, HTTPException, Response, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import os, io, csv

APP_VERSION = "0.1.0"

app = FastAPI(title="funk-poc", version=APP_VERSION)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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
with engine.begin() as conn:
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uniq_policy_number ON policies(number);"))

class PolicyIn(BaseModel):
    number: str = Field(..., min_length=3, max_length=64)
    holder: str = Field(..., min_length=2, max_length=128)
    premium: float = Field(..., ge=0)
    status: str = Field(..., min_length=2, max_length=32)

class PolicyOut(PolicyIn):
    id: int

# ---- Optional API key (enabled when API_KEY env is set) ----
def require_api_key(request: Request):
    expected = os.getenv("API_KEY")
    if not expected:
        return True
    got = (request.headers.get("x-api-key")
           or request.headers.get("x_api_key")
           or request.headers.get("authorization", "").removeprefix("ApiKey ").strip())
    if got == expected:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")

@app.get("/health")
def health():
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status":"degraded","error":str(e)})

@app.get("/version")
def version():
    return {"app": "funk-poc", "version": APP_VERSION}

def apply_search_and_sort(query, q: Optional[str], sort: str, direction: str):
    if q:
        like = f"%{q}%"
        query = query.filter(
            (PolicyDB.number.like(like)) |
            (PolicyDB.holder.like(like)) |
            (PolicyDB.status.like(like))
        )
    # safe sorting: allowlist
    sort_map = {
        "id": PolicyDB.id,
        "number": PolicyDB.number,
        "holder": PolicyDB.holder,
        "premium": PolicyDB.premium,
        "status": PolicyDB.status,
    }
    col = sort_map.get(sort.lower(), PolicyDB.id)
    if direction.lower() == "asc":
        query = query.order_by(col.asc())
    else:
        query = query.order_by(col.desc())
    return query

@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: Optional[str] = None):
    with SessionLocal() as db:
        query = db.query(PolicyDB)
        query = apply_search_and_sort(query, q, sort="id", direction="desc")
        items = query.all()
    return templates.TemplateResponse("index.html", {"request": request, "items": items, "q": q or ""})

@app.get("/policies", response_model=List[PolicyOut])
def list_policies(
    response: Response,
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("id"),
    dir: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    _auth=Depends(require_api_key),
):
    with SessionLocal() as db:
        query = db.query(PolicyDB)
        query = apply_search_and_sort(query, q, sort=sort, direction=dir)
        total = query.count()
        rows = query.offset(offset).limit(limit).all()

    end = min(offset + limit - 1, max(total - 1, 0))
    response.headers["X-Total-Count"] = str(total)
    response.headers["Content-Range"] = f"policies {offset}-{end}/{total}"
    return [PolicyOut(id=r.id, number=r.number, holder=r.holder, premium=r.premium, status=r.status) for r in rows]

@app.get("/policies/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: int, _auth=Depends(require_api_key)):
    with SessionLocal() as db:
        r = db.query(PolicyDB).get(policy_id)
        if not r:
            raise HTTPException(status_code=404, detail="Policy not found")
        return PolicyOut(id=r.id, number=r.number, holder=r.holder, premium=r.premium, status=r.status)

@app.post("/policies", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(p: PolicyIn, _auth=Depends(require_api_key)):
    with SessionLocal() as db:
        row = PolicyDB(**p.model_dump())
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Policy number already exists")
        db.refresh(row)
        return PolicyOut(id=row.id, **p.model_dump())

@app.get("/policies.csv")
def export_policies_csv(
    q: Optional[str] = None,
    sort: str = Query("id"),
    dir: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    _auth=Depends(require_api_key),
):
    with SessionLocal() as db:
        query = db.query(PolicyDB)
        query = apply_search_and_sort(query, q, sort=sort, direction=dir)
        rows = query.all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "number", "holder", "premium", "status"])
    for r in rows:
        writer.writerow([r.id, r.number, r.holder, f"{r.premium:.2f}", r.status])
    buf.seek(0)

    headers = {"Content-Disposition": 'attachment; filename="policies.csv"'}
    return StreamingResponse(buf, media_type="text/csv; charset=utf-8", headers=headers)
