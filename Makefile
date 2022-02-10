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

server:
	sudo -b su -c "venv/bin/python -m kubemon -t collector >> collector.out 2>&1 &"

stop_collector:
	docker kill $(shell docker ps | grep collector | awk '{print $$1}')

daemon:
	sudo -b su -c "venv/bin/python -m kubemon -t daemon -H $(host) >> daemon.out 2>&1 &"

kill:
	sudo kill -9 $(shell ps aux | grep kubemon | awk {'print $$2'})

cli:
	sudo venv/bin/python -m kubemon -t cli -H $(host)