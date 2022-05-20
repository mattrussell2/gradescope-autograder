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

# install python packages
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install toml dataclasses tqdm filelock python_dateutil

# install diff-so-fancy
COPY dockerbuild/diff-so-fancy    /bin/
COPY dockerbuild/DiffHighlight.pm /bin/

# pretty bash terminal header
RUN printf "export PS1=\"\\u@gs:\\W\\$ \"\n" >> ~/.bashrc

RUN ln -s /usr/bin/clang++-12 /usr/bin/clang++

# mkdir to move setup scripts and copy necessary files
RUN mkdir /build

# update the message of the day
COPY dockerbuild/update_motd.sh   /build/
RUN bash /build/update_motd.sh 

COPY dockerbuild/update_results.py /autograder/update_results.py
COPY dockerbuild/run_autograder    /autograder/run_autograder
RUN chmod +x /autograder/run_autograder 

# Do these last because the layers are going to change depending on what's going on.
# clone the course repository
RUN --mount=type=secret,id=REPOPATH cd /build && git clone $(cat /run/secrets/REPOPATH) course-repo 