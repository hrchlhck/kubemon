IMAGE=vpemfh7/sys-monitor
TAG=latest

docker build -t $IMAGE:$TAG . && docker push $IMAGE:$TAG
