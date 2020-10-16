FROM python:3.8

WORKDIR /opt/

STOPSIGNAL SIGINT

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY sys_monitor/ sys_monitor/
COPY static/ static/
COPY main.py .

ENTRYPOINT ["python3", "main.py"]