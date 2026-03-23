.PHONY: setup setup-backend dev backend frontend build test smoke package-release

setup:
	npm run setup

setup-backend:
	npm run setup:backend

dev:
	npm run dev

backend:
	npm run backend

frontend:
	npm run frontend

build:
	npm run build

test:
	npm run test:backend

smoke:
	npm run smoke:backend

package-release:
	npm run package:release
