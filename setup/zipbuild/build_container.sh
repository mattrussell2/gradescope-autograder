#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../../ 
cp setup/zipbuild/setup.sh .
cp etc/autograder_config.ini autograder_config.ini 
source autograder_config.ini
echo -e "\nREPO_REMOTE_PATH=${!REPO_REMOTE_VARNAME}\n" >> autograder_config.ini
cp bin/run_autograder .
zip -r setup/zipbuild/Autograder.zip .
rm setup.sh
rm run_autograder
rm autograder_config.ini 