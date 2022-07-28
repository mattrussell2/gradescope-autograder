#!/bin/bash

# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../../

source etc/autograder_config.ini 
source etc/docker_config.ini

cp etc/autograder_config.ini .

docker build --tag $CONTAINER_TAG --build-arg REPO_REMOTE_PATH="${!REPO_REMOTE_VARNAME}" -f setup/dockerbuild/Dockerfile .

rm autograder_config.ini 

echo "${!REGISTRY_PASS_VARNAME}" | docker login "${CONTAINER_REMOTE}" --username "${!REGISTRY_USER_VARNAME}" --password-stdin
docker push "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}"
