#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../../ 

# make build directory if it doesn't exist
if [ ! -d "build" ]; then
    mkdir build
fi

cp -r bin/ build/bin
cp -r etc/ build/etc

# these two files need to be in the root dir
cp setup/zipbuild/setup.sh build/
cp bin/run_autograder .

cd build

if [ ! -d "course-repo" ]; then
    echo "cloning course repo with deploy token"
    git clone ${!REPO_REMOTE_VARNAME} course-repo 
else 
    echo "course-repo already exists, pulling latest"
    cd course-repo
    git pull
    cd ..
fi

source etc/token_config.ini

gsed -i "s|POSTGRES_REMOTE_VARNAME|PG_REM_PATH|g" etc/token_config.ini
gsed -i "s|${POSTGRES_REMOTE_VARNAME}|${POSTGRES_REMOTE_PATH}|g" etc/token_config.ini

cp etc/token_config.ini .
cp etc/autograder_config.ini .

rm -rf bin etc

zip -r Autograder.zip .

rm -f setup.sh run_autograder