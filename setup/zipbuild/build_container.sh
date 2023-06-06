#!/bin/bash
# build_container.sh
# builds the autograding .zip file for gradescope
# by matt russell
# see README.md for details

cd ../../bin
python3 container_prep.py

cd ../setup/build

cp ../zipbuild/setup.sh .

zip -r Autograder.zip .

rm config.toml # contains secrets so remove it. 