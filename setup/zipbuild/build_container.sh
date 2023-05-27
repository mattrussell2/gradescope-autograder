#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../
./common_build.sh
cd build

cp ../zipbuild/setup.sh .

zip -r Autograder.zip .

rm motd run_autograder token_config.ini autograder_config.ini 