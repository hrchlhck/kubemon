FROM python:3.8

WORKDIR /opt/

STOPSIGNAL SIGINT

ADD setup.py .
ADD kubemon/ kubemon/
ADD kubemon.py .

RUN pip install . \
    && chmod +x kubemon.py

ENTRYPOINT ["python3", "kubemon.py"]
