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
                    postgresql-client \
                    jq \
                    clang-12 -y

# use clang++
RUN ln -s /usr/bin/clang++-12 /usr/bin/clang++

# install python packages
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install toml dataclasses tqdm filelock python_dateutil psycopg2-binary

# run_autograder has to be in /autograder/ or gradescope fails to run
COPY bin/run_autograder /autograder/run_autograder

# message of the day
COPY etc/motd /etc/motd

# DiffHighlight.pm needs to be on the perl path for diff-so-fancy
COPY lib/DiffHighlight.pm /usr/share/perl5/

# pretty bash terminal header
RUN printf "export PS1=\"\\u@gs:\\W\\$ \"\n" >> ~/.bashrc

# use this user to run components of the autograder that run student code
RUN adduser student --no-create-home --disabled-password --gecos ""

# copy configuration files
COPY etc/autograder_config.ini /autograder/source/autograder_config.ini
COPY etc/token_config.ini /autograder/source/token_config.ini

# clone the course repository
COPY course-repo/ /autograder/source/course-repo/
