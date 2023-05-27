# deploy_container.py
# builds and deploys the autograding docker container for gradescope
# by matt russell 
# see README.md for details
import os
import toml
import subprocess
import sys

sys.path.append('../../bin') # needed for import from relative path [chdir isn't enough]
import container_prep

os.chdir('../../bin')

config = container_prep.prep_build()

CONTAINER_REGISTRY = config['docker']['CONTAINER_REGISTRY']
CONTAINER_NAME     = config['docker']['CONTAINER_NAME']
CONTAINER_TAG      = config['docker']['CONTAINER_TAG']
REGISTRY_USER      = config['docker']['REGISTRY_USER']
REGISTRY_PASS      = config['docker']['REGISTRY_PASS']

REMOTE_TAG = f'{CONTAINER_REGISTRY}/{REGISTRY_USER}/{CONTAINER_NAME}:{CONTAINER_TAG}'
LOGIN_CMD  = f'echo {REGISTRY_PASS} | docker login {CONTAINER_REGISTRY} --username {REGISTRY_USER} --password-stdin'
PUSH_CMD   = f'docker push {REMOTE_TAG}'

os.chdir('../setup/build')

subprocess.run(f'docker build --tag {REMOTE_TAG} -f ../dockerbuild/Dockerfile .', shell=True)
subprocess.run(f'{LOGIN_CMD} && {PUSH_CMD}', shell=True)

os.remove('token_config.ini') # file contains secrets