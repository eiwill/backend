all: run-frontend

env:
	bash ./setup.sh

main-deps: env
	env/bin/pip install -r requirements.txt

run-frontend: main-deps
	@bash -c "env/bin/python frontend.py"

run-worker: main-deps
	@bash -c "env/bin/python worker.py $(WORKER_PARAMS)"

clean:
	rm -rf env && find ./ -name "*.pyc" | xargs rm

.PHONY: run

test: main-deps
	@bash -c "env/bin/python test_frontend.py -v"

build-docker-base:
	@bash -c "docker build -t test/base -f docker/Dockerfile ."

build-docker-frontend: build-docker-base
	@bash -c "docker build -t test/frontend -f docker/Dockerfile_frontend ."

build-docker-worker: build-docker-base
	@bash -c "docker build -t test/worker -f docker/Dockerfile_worker ."