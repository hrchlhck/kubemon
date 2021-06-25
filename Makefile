ifeq ($(OS),Windows_NT)
	ROOT_DIR:=$(shell cd)
else
	ROOT_DIR:=$(shell pwd)
endif


all: clean build_docker

build_docker:
	docker build -t vpemfh7/kubemon:latest .

clean:
	venv/bin/python cleanup.py

collector:
	@clear
	@docker run -p 9822:9822 -p 9880:9880/udp -v /tmp/data:/tmp/data --rm --name collector -it vpemfh7/kubemon:latest -t collector -H 0.0.0.0 -p 9822
