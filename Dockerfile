FROM python:3.8

WORKDIR /opt/

STOPSIGNAL SIGINT

ADD setup.py .
ADD sys_monitor/ sys_monitor/
ADD main.py .

RUN python setup.py install \
    && chmod +x main.py

ENTRYPOINT ["python3", "main.py"]
