.PHONY: install test test-automation test-middleware build dev docker-up

install:
	npm install
	cd middleware && npm install
	cd frontend && npm install
	cd automation && pip install -r requirements.txt -r requirements-dev.txt
	cd agent && pip install -r requirements.txt

test: test-middleware test-automation

test-middleware:
	npm --prefix middleware test

test-automation:
	python -m pytest automation/tests -q

build:
	npm --prefix frontend run build

docker-up:
	docker compose up --build
