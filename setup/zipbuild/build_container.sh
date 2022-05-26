#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../../ 
cp setup/zipbuild/setup.sh .
grep -v "DOCKER_CREDS\|DOCKER_TAG\|REPO_PATH" etc/autograder_config.ini  > autograder_config.ini 
cp bin/run_autograder .
zip -r setup/zipbuild/Autograder.zip .
rm setup.sh
rm run_autograder
rm autograder_config.ini 