ifeq ($(OS),Windows_NT)
	ROOT_DIR:=$(shell cd)
else
	ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
endif


all: clean build

test: build_test run_test

build:
	docker build -t vpemfh7/sys-monitor:latest .

build_test:
	docker build -f Dockerfile.test -t vpemfh7/sys-monitor:latest-test .

run_test:
	docker run -it --rm -v $(ROOT_DIR)/tests:/opt/tests/ vpemfh7/sys-monitor:latest-test

clean:
	python cleanup.py