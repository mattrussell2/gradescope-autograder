#!/bin/bash

# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../
./common_build.sh
cd build

source ../../etc/docker_config.ini

docker build --tag "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}" -f ../dockerbuild/Dockerfile .

echo "${!REGISTRY_PASS_VARNAME}" | docker login "${CONTAINER_REMOTE}" --username "${!REGISTRY_USER_VARNAME}" --password-stdin
docker push "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}"

# clean up 
rm motd run_autograder token_config.ini autograder_config.ini Dockerfile