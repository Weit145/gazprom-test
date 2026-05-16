POETRY ?= poetry
DOCKER_COMPOSE ?= docker compose

LOCUST_HOST ?= http://localhost:8000
LOCUST_USERS ?= 20
LOCUST_SPAWN_RATE ?= 5
LOCUST_RUN_TIME ?= 1m

.PHONY: help test docker-up docker-down docker-clean docker-logs locust locust-ui

help:
	@echo "Available targets:"
	@echo "  make test          Run pytest"
	@echo "  make docker-up     Build and start Docker Compose services"
	@echo "  make docker-down   Stop Docker Compose services"
	@echo "  make docker-clean  Stop services and remove volumes"
	@echo "  make docker-logs   Follow Docker Compose logs"
	@echo "  make locust        Run headless Locust load test"
	@echo "  make locust-ui     Run Locust web UI"

test:
	$(POETRY) run pytest

docker-up:
	$(DOCKER_COMPOSE) up --build -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans

docker-logs:
	$(DOCKER_COMPOSE) logs -f

locust:
	$(POETRY) run locust -f locustfile.py --headless -u $(LOCUST_USERS) -r $(LOCUST_SPAWN_RATE) -t $(LOCUST_RUN_TIME) --host $(LOCUST_HOST) --only-summary

locust-ui:
	$(POETRY) run locust -f locustfile.py --host $(LOCUST_HOST)
