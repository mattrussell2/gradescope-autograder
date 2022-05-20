#!/bin/bash

# builds the autograding docker container for gradescope

# prereqs:
# there are three files you must have in the cwd (note they all start with .):
#   1) .dockercreds file -> should be supplied for you; has creds to login to dockerhub
#   2) .dockertag        -> variant of the repo you're using
#                       format: tuftscs/gradescope-docker:WHATEVERYOUWANTHERE
#   3) .repopath         -> path to the course repo, including deploy token - of the form: 
#                       format: https://reponame:deploytoken@gitlab.cs.tufts.edu/path/to/repo.git

DOCKERTAG=$(cat .dockertag)
export DOCKER_BUILDKIT=1 # required for docker secrets

cd ../

docker build --secret id=REPOPATH,src=dockerbuild/.repopath --tag $DOCKERTAG -f dockerbuild/Dockerfile .

docker push $DOCKERTAG
if [ $? != 0 ]; then
    echo "need to login to docker -- username is: tuftscs"
    docker login --username tuftscs --password-stdin < dockerbuild/.dockercreds
    docker push $DOCKERTAG
fi