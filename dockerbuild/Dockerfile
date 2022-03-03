FROM gradescope/auto-builds:ubuntu-18.04

COPY . build

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install software-properties-common -y

RUN add-apt-repository ppa:apt-fast/stable
RUN apt-get update
RUN echo debconf apt-fast/maxdownloads string 16 | debconf-set-selections
RUN echo debconf apt-fast/dlflag boolean true | debconf-set-selections
RUN echo debconf apt-fast/aptmanager string apt-get | debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive apt-get install apt-fast -y 

RUN apt-get install lsb-release \
                    build-essential \
                    wget \
                    git \
                    clang-format-10 \
                    valgrind \
                    ssh \
                    sudo \
                    python3.7 \
                    python3-pip -y

RUN chmod +x ./build/install_clang
RUN bash ./build/install_clang 8
RUN ln -s /usr/bin/clang-8 /usr/bin/clang++
RUN ln -s /usr/bin/clang-format-10 /usr/bin/clang-format

RUN bash ./build/update_motd.sh

RUN printf "export PS1=\"\\u@gs:\\W\\$ \"" >> ~/.bashrc

RUN python3 -m pip install ./build/autograder-base/nmtestrunner/
RUN python3 -m pip install git+https://github.com/jeffkaufman/icdiff.git

RUN cp ./build/run_autograder /autograder/run_autograder
RUN chmod +x /autograder/run_autograder