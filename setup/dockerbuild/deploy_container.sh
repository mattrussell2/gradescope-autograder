#!/bin/bash
# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../../

source etc/autograder_config.ini 
grep -v "DOCKER_CREDS\|DOCKER_TAG\|REPO_PATH" etc/autograder_config.ini > autograder_config.ini 
docker build --tag $DOCKER_TAG --build-arg REPO_REMOTE_PATH=$REPO_REMOTE_PATH -f setup/dockerbuild/Dockerfile .
rm autograder_config.ini 

echo $DOCKER_CREDS | docker login --username tuftscs --password-stdin
docker push $DOCKER_TAG
