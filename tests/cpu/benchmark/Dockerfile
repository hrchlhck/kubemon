FROM ubuntu:14.04

RUN apt-get update && apt-get -y install p7zip-full

# Runs a benchmark on a single core
CMD while true; do 7z b -mmt1; done