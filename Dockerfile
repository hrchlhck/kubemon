FROM python:3.8-slim

ENV HOME /home/kubemon

RUN apt update -y
RUN groupadd -r kubemon && useradd -ms /bin/bash -rg kubemon kubemon

WORKDIR ${HOME}

STOPSIGNAL SIGINT

COPY setup.py .
COPY entrypoint.sh .
COPY kubemon/ kubemon/

RUN mkdir -p kubemon-data/logs kubemon-data/data && chown -R kubemon:kubemon ${HOME} /usr/local/bin/python 
RUN chmod +x entrypoint.sh

RUN pip install --user .

ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
