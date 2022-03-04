HOST_DIR=~/Documents/kubemon-data

all: clean build

build:
	docker build -t vpemfh7/kubemon:latest .

clean:
	sudo rm -rf $(shell find . -name __pycache__)

collector:
	docker run \
	-p 9822:9822/tcp \
	-p 9880:9880/udp \
	-v $(HOST_DIR):/home/kubemon/output \
	-e MONITOR=monitor \
	--rm \
	--name collector \
	-it \
	vpemfh7/kubemon:latest \
	-t collector \
	-H $(host)

monitor:
	docker run \
	-p 9822:9822/tcp \
	-v /proc:/procfs:ro \
	-v /sys:/sys:ro \
	-v /var/lib/docker:/var/lib/docker:ro \
	-v /var/run/docker.sock:/var/run/docker.sock \
	-v /etc/hostname:/etc/host_hostname:ro \
	--privileged \
	--rm \
	--name monitor \
	-it \
	vpemfh7/kubemon:latest \
	-H $(host) \
	-t daemon \
	-n 1 \

server:
	sudo su -c "venv/bin/python -m kubemon -t collector -H 192.168.15.9 -n 1 >> collector.out 2>&1 &"

stop_collector:
	docker kill $(shell docker ps | grep collector | awk '{print $$1}')

daemon:
	sudo -b su -c "venv/bin/python -m kubemon -t daemon -H $(host) >> daemon.out 2>&1 &"

kill:
	sudo kill -9 $(shell ps aux | grep kubemon | awk {'print $$2'})

cli:
	sudo venv/bin/python -m kubemon -t cli -p 9880 -H $(host)
