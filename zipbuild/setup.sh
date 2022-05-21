#!/bin/bash

REPOPATH="https://gradescope-autograding:glpat-kxknPc_tMsb3rkBvG7Us@gitlab.cs.tufts.edu/mrussell/gradescope-autograding.git"

# initial apt stuff
apt-get update -y && apt-get upgrade -y
apt-get install software-properties-common -y

# install necessary packages
apt-get install lsb-release \
                build-essential \
                wget \
                git \
                clang-format \
                valgrind \
                ssh \
                sudo \
                time \
                clang -y

add-apt-repository ppa:deadsnakes/ppa -y

apt update -y

apt install python3.9 python3.9-distutils -y

# install python packages
python3.9 -m pip install --upgrade pip
python3.9 -m pip install toml dataclasses tqdm filelock python_dateutil

# pretty bash terminal header
printf 'export PS1=\"\\u@gs:\\W\\$ \"\n' >> ~/.bashrc

# update message of the day
/autograder/source/update_motd.sh

cp /autograder/source/run_autograder    /autograder/
cp /autograder/source/update_results.py /autograder/

mkdir /build && cd /build
git clone $REPOPATH course-repo 

printf 'export PATH=\"/autograder/source:$PATH\"\n' >> ~/.bashrc