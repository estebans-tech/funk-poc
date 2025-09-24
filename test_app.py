import tempfile
from fastapi.testclient import TestClient
import main
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def client():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    test_engine = create_engine(f"sqlite:///{tmp.name}", connect_args={"check_same_thread": False})
    main.engine = test_engine
    main.SessionLocal = sessionmaker(bind=test_engine)
    main.Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as conn:
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uniq_policy_number ON policies(number);"))
    return TestClient(main.app)

def test_create_and_duplicate():
    c = client()
    r1 = c.post("/policies", json={"number":"T-1","holder":"Al","premium":10,"status":"active"})
    assert r1.status_code == 201
    r2 = c.post("/policies", json={"number":"T-1","holder":"Al","premium":10,"status":"active"})
    assert r2.status_code == 409

def test_pagination_headers():
    c = client()
    for i in range(3):
        c.post("/policies", json={"number":f"P-{i}","holder":"Ha","premium":i,"status":"active"})
    r = c.get("/policies?limit=2&offset=0")
    assert r.status_code == 200
    assert r.headers.get("X-Total-Count") == "3"
    assert r.headers.get("Content-Range", "").startswith("policies 0-1/3")

def test_csv_export_and_sorting():
    c = client()
    # seed
    for i, prem in [("A-1", 5.0), ("B-2", 3.0), ("C-3", 7.5)]:
        c.post("/policies", json={"number":i,"holder":"Ho","premium":prem,"status":"active"})
    r = c.get("/policies.csv?sort=premium&dir=asc")
    assert r.status_code == 200
    assert r.headers.get("content-type","").startswith("text/csv")
    text = r.text.strip().splitlines()
    # header + 3 rows, and first data row should be premium=3.00
    assert text[0].startswith("id,number,holder,premium,status")
    assert any(",3.00," in line for line in text[1:])

