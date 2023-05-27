# need to use gradescope's image as base
FROM gradescope/auto-builds:ubuntu-22.04

# initial apt stuff
RUN apt-get update --fix-missing -y && apt-get upgrade -y
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
                    icdiff \
                    clang-12 -y

# use clang++
RUN ln -s /usr/bin/clang++-12 /usr/bin/clang++

# install python packages
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install toml dataclasses tqdm filelock python_dateutil psycopg2-binary

# pretty bash terminal header
RUN printf "export PS1=\"\\u@gs:\\W\\$ \"\n" >> ~/.bashrc

# use this user to run components of the autograder that run student code
RUN adduser student --no-create-home --disabled-password --gecos ""

COPY autograder_config.ini /autograder/source/autograder_config.ini
COPY token_config.ini      /autograder/source/token_config.ini
COPY run_autograder        /autograder/run_autograder
COPY course-repo/          /autograder/source/course-repo/
COPY motd                  /etc/motd

RUN chmod +x /autograder/run_autograder