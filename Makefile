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
	@docker run -p 9822:9822 -p 9880:9880/udp -v /tmp/data:/tmp/data --rm --name collector -it vpemfh7/sys-monitor:latest -t collector -H 0.0.0.0 -p 9822
