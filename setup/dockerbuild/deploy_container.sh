#!/bin/bash
# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../../

source setup/config.ini 
grep -v "DOCKER_CREDS\|DOCKER_TAG\|REPO_PATH" setup/config.ini > config.tmp
docker build --tag $DOCKER_TAG --build-arg REPO_REMOTE_PATH=$REPO_REMOTE_PATH -f setup/dockerbuild/Dockerfile .
rm config.tmp

docker push $DOCKER_TAG
if [ $? != 0 ]; then
    echo "need to login to docker -- username is: tuftscs"
    echo $DOCKER_CREDS | docker login --username tuftscs --password-stdin
    docker push $DOCKER_TAG
fi