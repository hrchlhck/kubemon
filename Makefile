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

cli:
	docker run \
	--rm \
	--name monitor \
	-it \
	vpemfh7/kubemon:latest \
	-H $(host) \
	-t cli \
	-p 9880 
