import tempfile, os
from fastapi.testclient import TestClient
import main
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def client():
    # Se till att auth är AV i standardtester
    os.environ.pop("API_KEY", None)

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
    for i, prem in [("A-1", 5.0), ("B-2", 3.0), ("C-3", 7.5)]:
        c.post("/policies", json={"number":i,"holder":"Ho","premium":prem,"status":"active"})
    r = c.get("/policies.csv?sort=premium&dir=asc")
    assert r.status_code == 200
    assert r.headers.get("content-type","").startswith("text/csv")
    text_lines = r.text.strip().splitlines()
    assert text_lines[0].startswith("id,number,holder,premium,status")
    assert any(",3.00," in line for line in text_lines[1:])

def test_delete_policy():
    c = client()
    r = c.post("/policies", json={"number":"DEL-1","holder":"Ha","premium":1,"status":"active"})
    assert r.status_code == 201
    pid = r.json()["id"]
    r2 = c.delete(f"/policies/{pid}")
    assert r2.status_code == 204
    r3 = c.get(f"/policies/{pid}")
    assert r3.status_code == 404

def test_auth_optional_api_key():
    # Aktivera auth för just detta test
    os.environ["API_KEY"] = "k"
    c = client()  # client() poppar API_KEY, så sätt efter instansiering:
    os.environ["API_KEY"] = "k"
    r = c.get("/policies?limit=1")
    assert r.status_code == 401
    r2 = c.get("/policies?limit=1", headers={"X-API-Key":"k"})
    assert r2.status_code == 200
    os.environ.pop("API_KEY", None)
