FROM python:3.8-slim

ENV HOME /home/kubemon
ENV WITHIN_DOCKER yes

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
