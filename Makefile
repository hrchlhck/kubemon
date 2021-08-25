all: clean build

build:
	docker build -t vpemfh7/kubemon:latest .

clean:
	rm -rf $(shell find . -name __pycache__)

collector:
	@clear
	@docker run -p 9822:9822 -p 9880:9880/udp -v /tmp/data:/tmp/data --rm --name collector -it vpemfh7/kubemon:latest -t collector -H 0.0.0.0 -p 9822
