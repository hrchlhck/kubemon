ifeq ($(OS),Windows_NT)
	ROOT_DIR:=$(shell cd)
else
	ROOT_DIR:=$(shell pwd)
endif


all: clean build_docker

test: build_test run_test

build_docker:
	docker build -t vpemfh7/sys-monitor:latest .

build_test:
	docker build -f Dockerfile.test -t vpemfh7/sys-monitor:latest-test .

run_test:
	docker run -it --rm -v $(ROOT_DIR)/tests:/opt/tests/ vpemfh7/sys-monitor:latest-test

clean:
	venv/bin/python cleanup.py

collector:
	@clear
	@docker run -v /tmp/data:/tmp/data --rm --name collector  -it vpemfh7/sys-monitor:latest -t collector
