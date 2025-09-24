.PHONY: run seed test fmt

run:
\tuvicorn main:app --reload

seed:
\tpython seed.py

test:
\tpytest -q

fmt:
\tpython -m pip install -q black && black .

