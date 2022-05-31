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

# update message of the day
cp /autograder/source/etc/motd /etc/motd

# copy DiffHighlight.pm so diff-so-fancy can view it
cp /autograder/source/lib/DiffHighlight.pm /usr/share/perl5/

# this script needs to be placed in /autograder in order for the autograder to work right. 
cp /autograder/source/bin/run_autograder /autograder/

# pretty bash terminal header
printf 'export PS1=\"\\u@gs:\\W\\$ \"\n' >> ~/.bashrc

# load the config vars so we have access to $REPO_REMOTE_PATH
source /autograder/source/autograder_config.ini

#REPO_REMOTE_PATH=$(cat /autograder/source/autograder_config.ini | grep REPO_REMOTE_PATH | cut -d '=' -f 2)

# clone the course repo
cd /autograder/source && git clone $REPO_REMOTE_PATH course-repo