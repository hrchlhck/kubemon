set -e

TAG=latest

function build() {
    NAME=$1
    IMAGE=vpemfh7/spark-$NAME:$TAG
    cd $([ -z "$2" ] && echo "./$NAME" || echo "$2")
    echo '--------------------------' building $IMAGE in $(pwd)
    docker build -t $IMAGE . && docker push $IMAGE
    cd -
}

build master
build worker
