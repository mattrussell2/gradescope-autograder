# need to use gradescope's image as base
FROM gradescope/auto-builds:ubuntu-22.04

# initial apt stuff
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install software-properties-common -y

# install necessary packages
RUN apt-get install lsb-release \
                    build-essential \
                    wget \
                    git \
                    clang-format \
                    valgrind \
                    ssh \
                    sudo \                    
                    time \
                    clang-12 -y

# use clang++
RUN ln -s /usr/bin/clang++-12 /usr/bin/clang++

# install python packages
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install toml dataclasses tqdm filelock python_dateutil

# run_autograder has to be in /autograder/ or gradescope fails to run
COPY bin/run_autograder /autograder/run_autograder

# mkdir to move setup scripts and copy necessary files
RUN mkdir /autograder/source/

# copy configuration file
COPY config.tmp /autograder/source/config.ini

# message of the day
COPY lib/motd /etc/motd

# pretty bash terminal header
RUN printf "export PS1=\"\\u@gs:\\W\\$ \"\n" >> ~/.bashrc

ARG REPO_REMOTE_PATH

# clone the course repository
RUN cd /autograder/source/ && git clone $REPO_REMOTE_PATH course-repo