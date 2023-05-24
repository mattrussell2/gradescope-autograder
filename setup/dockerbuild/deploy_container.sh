#!/bin/bash

# deploy_container.sh
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details

cd ../../

source etc/autograder_config.ini 
source etc/docker_config.ini
source etc/token_config.ini

# make build directory if it doesn't exist
if [ ! -d "build" ]; then
    mkdir build
fi

cp -r bin/ build/bin
cp -r etc/ build/etc
cp -r lib/ build/lib

cp setup/dockerbuild/Dockerfile build/

cd build

gsed -i "s|POSTGRES_REMOTE_VARNAME|PG_REM_PATH|g" etc/token_config.ini
gsed -i "s|${POSTGRES_REMOTE_VARNAME}|${POSTGRES_REMOTE_PATH}|g" etc/token_config.ini

if [ ! -d "course-repo" ]; then
    echo "cloning course repo with deploy token"
    git clone ${!REPO_REMOTE_VARNAME} course-repo 
else 
    echo "course-repo already exists, pulling latest"
    cd course-repo
    git pull
    cd ..
fi

docker build --tag "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}" -f Dockerfile .

echo "${!REGISTRY_PASS_VARNAME}" | docker login "${CONTAINER_REMOTE}" --username "${!REGISTRY_USER_VARNAME}" --password-stdin
docker push "${CONTAINER_REMOTE}/${!REGISTRY_USER_VARNAME}/${CONTAINER_NAME}:${CONTAINER_TAG}"

rm -rf bin etc lib