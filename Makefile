DOCKER_COMPOSE=docker compose -f docker-compose.yml
DOCKER_COMPOSE_DEV=docker compose -f docker-compose.dev.yml

.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: dev
dev:
	${DOCKER_COMPOSE_DEV} down -v && $(DOCKER_COMPOSE_DEV) up --build