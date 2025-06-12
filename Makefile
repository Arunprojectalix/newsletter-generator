DOCKER_COMPOSE=docker compose -f docker-compose.yml

.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: dev
dev:
	${DOCKER_COMPOSE} down -v &&$(DOCKER_COMPOSE) up --build