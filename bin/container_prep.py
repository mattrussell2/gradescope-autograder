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
            config[vartype][varname[:-len(VARNAME_STR)]] = os.environ[config[vartype][varname]]
            del config[vartype][varname]

    BUILD_DIR = os.path.join('..', 'setup', 'build')
    if not os.path.isdir(BUILD_DIR):
        os.mkdir(BUILD_DIR)

    shutil.copyfile('run_autograder',                  os.path.join(BUILD_DIR, 'run_autograder'))
    shutil.copyfile(os.path.join('..', 'etc', 'motd'), os.path.join(BUILD_DIR, 'motd'))

    # on the back-end, autograder expects two config files (for now)
    # these are sourced by bash scripts so export them as .ini files
    for config_fname, config_type in zip(['autograder_config.ini', 'token_config.ini'], ['paths', 'tokens']):
        with open(os.path.join(BUILD_DIR, config_fname), 'w') as f:
            for key in config[config_type]:
                if isinstance(config[config_type][key], str):
                    f.write(f'{key}="{config[config_type][key]}"\n')
                else:
                    f.write(f'{key}={config[config_type][key]}\n')

            if config_type == 'paths':
                f.write(f'SUBMISSIONS_PER_ASSIGN={config["other"]["SUBMISSIONS_PER_ASSIGN"]}\n')

    if not os.path.isdir(os.path.join(BUILD_DIR, 'course-repo')):
        subprocess.run(['git', 'clone', config['paths']['REPO_REMOTE'], 'course-repo'], cwd=BUILD_DIR)
    else:
        subprocess.run(['git', 'pull'], cwd=os.path.join(BUILD_DIR, 'course-repo'))

    del config['paths']['REPO_REMOTE']

    return config

if __name__ == '__main__':
    prep_build()