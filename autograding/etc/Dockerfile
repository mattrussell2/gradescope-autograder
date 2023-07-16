FROM docker.io/tuftscs/gradescope-docker:base

ARG AUTOGRADING_ROOT
ARG REPO_REMOTE
ARG REPO_BRANCH

RUN mkdir /autograder/source
COPY . /autograder/source/

RUN mv /autograder/source/${AUTOGRADING_ROOT}/bin/run_autograder /autograder/
RUN mv /autograder/source/${AUTOGRADING_ROOT}/etc/motd           /etc/motd

RUN cd /autograder/source && \
    git remote set-url origin ${REPO_REMOTE} && \
    git config --unset http.https://gitlab.cs.tufts.edu.sslcainfo && \
    git fetch origin ${REPO_BRANCH} && \
    git checkout -B ${REPO_BRANCH} origin/${REPO_BRANCH}
    
RUN chmod +x  /autograder/run_autograder /autograder/source/${AUTOGRADING_ROOT}/bin/login.sh
RUN chmod 400 /autograder/source/.secrets

RUN echo "session optional pam_exec.so seteuid /autograder/source/${AUTOGRADING_ROOT}/bin/login.sh" >> /etc/pam.d/sshd