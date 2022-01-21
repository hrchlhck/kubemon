HOST_DIR=~/Documents/kubemon-data

all: clean build

build:
	docker build -t vpemfh7/kubemon:latest .

clean:
	rm -rf $(shell find . -name __pycache__)

collector:
	docker run \
	-p 9822:9822/tcp \
	-p 9880:9880/udp \
	-v $(HOST_DIR):/home/kubemon/kubemon-data \
	--rm \
	--name collector \
	-d \
	vpemfh7/kubemon:latest \
	-t collector

stop_collector:
	docker kill $(shell docker ps | grep collector | awk '{print $$1}')

daemon:
	sudo -b su -c "venv/bin/python -m kubemon -t daemon -H $(host) > /dev/null 2>&1 &"