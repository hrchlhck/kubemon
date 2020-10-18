FROM openjdk:8

WORKDIR /opt/

STOPSIGNAL SIGINT

RUN wget http://mirror.nbtelecom.com.br/apache/spark/spark-3.0.1/spark-3.0.1-bin-hadoop3.2.tgz
RUN tar xvf spark-3.0.1-bin-hadoop3.2.tgz
RUN mv spark-3.0.1-bin-hadoop3.2 /usr/local/spark

ENV PATH=$PATH:/usr/local/spark/bin

RUN apt update
RUN apt install build-essential \
                zlib1g-dev \
                libncurses5-dev \
                libgdbm-dev \
                libnss3-dev \
                libssl-dev \
                libreadline-dev \
                libffi-dev \
                libsqlite3-dev \
                wget \
                libbz2-dev -y
RUN wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
RUN tar -xf Python-3.8.0.tgz

WORKDIR Python-3.8.0

RUN ./configure
RUN make -j 8
RUN make altinstall

WORKDIR /opt/

COPY cpu_test.py .
COPY bible.txt .
COPY requirements.txt .

RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install -r requirements.txt

ENV PYSPARK_PYTHON=/usr/local/bin/python3.8

CMD ["python3.8", "cpu_test.py", "bible.txt"]