#!/bin/bash 

cd ../

source etc/autograder_config.ini 
source etc/token_config.ini

# make build directory if it doesn't exist
if [ ! -d "setup/build" ]; then
    mkdir setup/build
fi

cp bin/run_autograder setup/build/

cp etc/autograder_config.ini setup/build/
cp etc/token_config.ini setup/build/
cp etc/motd setup/build/

# move the dockerfile to the build directory
cp setup/dockerbuild/Dockerfile setup/build/

gsed -i "s|POSTGRES_REMOTE_VARNAME|PG_REM_PATH|g" setup/build/token_config.ini
gsed -i "s|${POSTGRES_REMOTE_VARNAME}|${POSTGRES_REMOTE_PATH}|g" setup/build/token_config.ini

if [ ! -d "setup/build/course-repo" ]; then
    echo "cloning course repo with deploy token"
    git clone ${!REPO_REMOTE_VARNAME} setup/build/course-repo 
else 
    echo "course-repo already exists, pulling latest"
    cd setup/build/course-repo
    git pull
    cd ../../../
fi

cd setup