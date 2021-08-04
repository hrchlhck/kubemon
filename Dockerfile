FROM python:3.8

WORKDIR /opt/

STOPSIGNAL SIGINT

ADD setup.py .
ADD kubemon/ kubemon/

RUN pip install . 

ENTRYPOINT ["python3", "-m", "kubemon"]
