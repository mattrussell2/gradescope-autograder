# need to use gradescope's image as base
FROM gradescope/auto-builds:ubuntu-22.04

# initial apt stuff
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install software-properties-common \
                    lsb-release \
                    build-essential \
                    wget \
                    git \
                    clang-format \
                    valgrind \
                    ssh \                    
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
COPY autograder_config.ini /autograder/source/autograder_config.ini

# message of the day
COPY etc/motd /etc/motd

# DiffHighlight.pm needs to be on the perl path for diff-so-fancy
COPY lib/DiffHighlight.pm /usr/share/perl5/

# pretty bash terminal header
RUN printf "export PS1=\"\\u@gs:\\W\\$ \"\n" >> ~/.bashrc

# clone the course repository
ARG REPO_REMOTE_PATH
RUN cd /autograder/source/ && git clone $REPO_REMOTE_PATH course-repo