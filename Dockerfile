FROM python:3.8-slim

ENV HOME /home/kubemon
ENV WITHIN_DOCKER yes
ENV SERVICE_NAME "monitor"
ENV NUM_DAEMONS "1"
ENV COLLECT_INTERVAL "5"
ENV MONITOR_PORT "80"
ENV OUTPUT_DIR "output"
ENV NAMESPACES "k8s-bigdata testbed"
ENV FROM_K8S "true"

RUN apt update -y
RUN groupadd -r kubemon && useradd -ms /bin/bash -rg kubemon kubemon

WORKDIR ${HOME}

STOPSIGNAL SIGINT

COPY setup.py .
COPY entrypoint.sh .
COPY kubemon/ kubemon/
COPY README.md .

RUN chown -R kubemon:kubemon ${HOME} /usr/local/bin/python 
RUN chmod +x entrypoint.sh

RUN pip install --user .

ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
