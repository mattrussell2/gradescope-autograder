#!/bin/bash

# initial apt stuff
apt-get update -y && apt-get upgrade -y
apt-get install software-properties-common \
                lsb-release \
                build-essential \
                wget \
                git \
                clang-format \
                valgrind \
                ssh \                
                time \
                clang -y

# install python3.9 - the default is 3.6.9; autograder needs >= 3.8
add-apt-repository ppa:deadsnakes/ppa -y
apt update -y
apt install python3.9 python3.9-distutils -y

# install pip packages
python3.9 -m pip install --upgrade pip
python3.9 -m pip install toml dataclasses tqdm filelock python_dateutil

# copy the config file
cp /autograder/source/setup/config.ini /autograder/source/config.ini

# update message of the day
cp /autograder/source/lib/motd /etc/motd

# this script needs to be placed in /autograder in order for the autograder to work right. 
cp /autograder/source/bin/run_autograder /autograder/

# pretty bash terminal header
printf 'export PS1=\"\\u@gs:\\W\\$ \"\n' >> ~/.bashrc

# load the config vars so we have access to $REPO_REMOTE_PATH
source /autograder/source/config.ini

# clone the course repo
cd /autograder/source && git clone $REPO_REMOTE_PATH course-repo