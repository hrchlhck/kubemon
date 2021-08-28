FROM python:3.8-slim

WORKDIR /home/user/

STOPSIGNAL SIGINT

COPY setup.py .
COPY kubemon/ kubemon/

RUN pip install --user .

ENTRYPOINT ["python", "-m", "kubemon"]
