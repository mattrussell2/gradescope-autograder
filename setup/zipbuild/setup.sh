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
                postgresql-client \
                jq \
                clang-12 -y

ln -s /usr/bin/clang++-12 /usr/bin/clang++

# install pip packages
python3 -m pip install --upgrade pip
python3 -m pip install toml dataclasses tqdm filelock python_dateutil psycopg2-binary yq icdiff

# update message of the day
cp "/autograder/source/motd" /etc/motd

# this script needs to be placed in /autograder in order for the autograder to work right. 
cp /autograder/source/run_autograder /autograder/

# pretty bash terminal header
printf 'export PS1=\"\\u@gs:\\W\\$ \"\n' >> ~/.bashrc

adduser student --no-create-home --disabled-password --gecos ""