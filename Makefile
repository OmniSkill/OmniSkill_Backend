.PHONY: dev test migrate pipeline-run lint format install docker-up docker-down

install:
	uv sync

dev: docker-up
	uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up -d

docker-down:
	docker compose down

test:
	uv run pytest tests/ -v --cov=packages --cov=apps --cov-report=term-missing

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-e2e:
	uv run pytest tests/e2e/ -v

migrate:
	uv run alembic upgrade head

migrate-new:
	uv run alembic revision --autogenerate -m "$(msg)"

pipeline-run:
	uv run python -m apps.pipelines.main

lint:
	uv run ruff check .
	uv run mypy packages/ apps/

format:
	uv run ruff format .
	uv run ruff check --fix .
