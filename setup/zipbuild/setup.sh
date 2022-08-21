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
                clang-12 -y

ln -s /usr/bin/clang++-12 /usr/bin/clang++

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

# clone the course repo
cd /autograder/source && git clone "${REPO_REMOTE_PATH}" course-repo
