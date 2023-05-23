#!/bin/bash

# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../../

source etc/autograder_config.ini 
source etc/docker_config.ini

echo "cloning course repo with deploy token"
git clone ${!REPO_REMOTE_VARNAME} course-repo 

cp etc/autograder_config.ini .

docker build --tag "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}" -f setup/dockerbuild/Dockerfile .

rm -rf course-repo
rm autograder_config.ini 

echo "${!REGISTRY_PASS_VARNAME}" | docker login "${CONTAINER_REMOTE}" --username "${!REGISTRY_USER_VARNAME}" --password-stdin
docker push "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}"
