IP=$(hostname -i)

cd spark/ 
/bin/bash ./bin/spark-submit \
--master spark://spark-master:7077 \
--conf spark.driver.bindAddress=$IP \
--conf spark.driver.host=$IP \
--name sparkpi \
../cpu_test.py 
