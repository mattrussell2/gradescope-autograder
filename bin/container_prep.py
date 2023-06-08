import os
import toml
import subprocess
import shutil


def prep_build():

    config = toml.load('../etc/config.toml')

    # load the environment variables from the config file
    VARNAME_STR = '_VARNAME'
    for vartype in config:
        for varname in [var for var in config[vartype] if var.endswith(VARNAME_STR)]:
            if varname == "POSTGRES_REMOTE_VARNAME" and not config['TOKENS']['MANAGE_TOKENS']:
                continue
            config[vartype][varname[:-len(VARNAME_STR)]] = os.environ[config[vartype][varname]]
            del config[vartype][varname]

    BUILD_DIR = os.path.join('..', 'setup', 'build')
    if not os.path.isdir(BUILD_DIR):
        os.mkdir(BUILD_DIR)

    shutil.copyfile('run_autograder', os.path.join(BUILD_DIR, 'run_autograder'))
    shutil.copyfile(os.path.join('..', 'etc', 'motd'), os.path.join(BUILD_DIR, 'motd'))

    LOCAL_REPO_PATH = os.path.join(BUILD_DIR, 'course-repo')
    if not os.path.isdir(LOCAL_REPO_PATH):
        subprocess.run(
            ['git', 'clone', '--branch', config['repo']["REPO_BRANCH"], config['repo']['REPO_REMOTE'], 'course-repo'],
            cwd=BUILD_DIR)
    else:
        subprocess.run(['git', 'pull'], cwd=LOCAL_REPO_PATH)

    del config['repo']['REPO_REMOTE']

    with open(os.path.join(BUILD_DIR, 'config.toml'), 'w') as f:
        toml.dump(config, f)

    return config

if __name__ == '__main__':
    prep_build()