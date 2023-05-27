#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../../ 

# make build directory if it doesn't exist
if [ ! -d "setup/build" ]; then
    mkdir setup/build
fi

cp -r bin/ setup/build/bin
cp -r etc/ setup/build/etc


source etc/autograder_config.ini

# these two files need to be in the root dir
cp setup/zipbuild/setup.sh setup/build/
cp bin/run_autograder setup/build/

cd setup/build

if [ ! -d "course-repo" ]; then
    echo "cloning course repo with deploy token"
    echo ${!REPO_REMOTE_VARNAME}
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