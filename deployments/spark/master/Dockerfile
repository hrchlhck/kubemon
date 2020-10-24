FROM bde2020/spark-base:latest

COPY master.sh /
COPY start.sh / 
COPY cpu_test.py /
COPY bible.txt /

ENV SPARK_MASTER_PORT 7077
ENV SPARK_MASTER_WEBUI_PORT 8080
ENV SPARK_MASTER_LOG /spark/logs
ENV PYSPARK_PYTHON /usr/bin/python3

EXPOSE 8080 7077 6066 4040

RUN pip3 install pyspark

CMD ["/bin/bash", "/master.sh"]
