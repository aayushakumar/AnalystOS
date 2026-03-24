.PHONY: setup dev-backend dev-frontend dev seed-db eval test lint clean

CONDA_ACTIVATE = eval "$$(conda shell.bash hook)" && conda activate analystos

setup: setup-conda setup-frontend seed-db

setup-conda:
	conda create -n analystos python=3.11 -y
	$(CONDA_ACTIVATE) && cd backend && pip install -e ".[dev]"

setup-frontend:
	cd frontend && npm install

dev-backend:
	$(CONDA_ACTIVATE) && cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

seed-db:
	$(CONDA_ACTIVATE) && cd backend && python -m app.db.seed

eval:
	$(CONDA_ACTIVATE) && cd backend && python -m app.eval.runner

test:
	$(CONDA_ACTIVATE) && cd backend && pytest -v

lint:
	$(CONDA_ACTIVATE) && cd backend && ruff check . && ruff format --check .

clean:
	rm -f backend/data/analystos.duckdb backend/data/traces.db
