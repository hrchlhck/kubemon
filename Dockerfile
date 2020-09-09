FROM python:3.8

WORKDIR /opt/

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY sys_monitor/ sys_monitor/
COPY static/ .
COPY main.py .

CMD ["python3", "main.py"]