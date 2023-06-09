# Gradescope Autograding 
Gradescope is great tool for autograding assignments. Nevertheless, there is still a substantial amount
of infrastructure required to deploy and run an autograder on Gradescope. This document provides 
instructions for setting up an autograder on Gradescope which uses our in-house autograding
framework code. Setup from start to finish is intended to take roughly 30 minutes.
If you have any questions, please reach out to me at `mrussell@cs.tufts.edu`, or open an issue here. 

# Infrastructure Setup

## Background
As a high-level overview, each time a submission is provided to gradescope, or a ta re-runs tests:
* A Docker container based on your build is spun up by Gradescope.
* `git pull` gets the most recent version of your autograder and tests. 
*  The submission is checked re: lateness and number of submissions to see if it is acceptable [optional]
* Student's code is run and `diff`ed vs. reference output
* The results are parsed to produce a `results.json` formatted for Gradescope. 

## Create Your Autograding Git Repo
Before we begin, you will need a git repository for your autograder. If you don't currently have a repository related to course material, please make one. We suggest using gitlab for this: go to https://gitlab.cs.tufts.edu and login with `LDAP` using your Tufts eecs `utln` and password. Then create a new repository from scratch [don't add a README]. Then, clone this repo to get the relevant files. 
```shell
git clone git@gitlab.cs.tufts.edu:mrussell/gradescope-autograding
mv gradescope-autograding YOUR_REPO_FOLDER_NAME
cd YOUR_REPO_FOLDER NAME
git remote set-url origin git@gitlab.cs.tufts.edu:YOUR_UTLN/YOUR_REPO_NAME.git
git push
```
Great! You will need an Access Token to provide the autograder container with permissions to the repo. To create one, go to gitlab in your browser, and navigate to the course repository you just created. Next, hover over the settings cog on the lower left, and select `Access Tokens`. Create one. We suggest only providing `read repository` access to the token. Feel free to select whatever you'd like for the name, expiration date, and role, however role must be at least `Developer` in order to be able to pull. Once the token is created, copy the key. 

A note on 'secrets': The strategy for handling sensitive data in this repository (like your access token) is to have all of the relevant data be stored in enviornment variables on your system. The first example of this will be an environment variable with the remote path to your autograding repo, including the acess token copied above. Open your `~/.bashrc` file (or appropriate file for whichever shell you use), and add the following line (or the appropriate `export` for your shell): 

```shell
export AUTOGRADING_REPO_REMOTE_PATH="https://REPOSITORY-NAME:ACCESS-TOKEN@gitlab.cs.tufts.edu/path/to/repository.git"
```
Where the appropriate substitions have been made - for example:

```shell
export AUTOGRADING_REPO_REMOTE_PATH="https://cs-15-2022uc:glpat-Blah8173Blah8023Blah@gitlab.cs.tufts.edu/mrussell/cs-15-2022uc.git"
```

Make sure `source ~/.bashrc` (or equivalent) after editing the file.

Note that in the configuration files listed below, you will sometimes specify the *variable name* (not value), which will then be used during the build process. This is for situations with secrets, and enables you maximum flexibility in terms of not having sensitive data in the repo itself. You can rename these variables to whatever you'd like - we suggest adding identifiers associated with your course, in case you use the framework multiple times: for example, the variable above might be named `AG_REPO_REMOTE_CS15_SUMMER_2023`; in this case, change the value of the variable `REPO_REMOTE_VARNAME` below to match (i.e. so replace `"AUTOGRADING_REPO_REMOTE_PATH"` with `"AG_REPO_REMOTE_CS15_SUMMER_2023"`, etc.) . 

## Configure Your Autograding Repo
The file `etc/config.toml` contains various important bits of information related to your autograder configuration.
```toml
[repo]
REPO_REMOTE_VARNAME = "AUTOGRADING_REPO_REMOTE_PATH"
REPO_BRANCH = "main"
ASSIGN_ROOT = "assignments"
ASSIGN_AUTOGRADING_SUBFOLDER = ""
AUTOGRADING_ROOT = ""

[tokens]
GRACE_TIME = 15   # 15 minutes
TOKEN_TIME = 1440 # 24 hours
STARTING_TOKENS = 5
MAX_PER_ASSIGN = 2
MANAGE_TOKENS = false
POSTGRES_REMOTE_VARNAME = "POSTGRES_REMOTE_PATH"

[docker]
CONTAINER_REGISTRY = "ghcr.io"
CONTAINER_NAME = "gradescope-docker"
CONTAINER_TAG = "autograder-autobuild"
REGISTRY_USER_VARNAME = "GHUNAME"
REGISTRY_PASS_VARNAME = "GHPAT"

[misc]
SUBMISSIONS_PER_ASSIGN = 5
TEST_USERS = ["Matthew Russell"]
```
### [repo]
Items in the `[repo]` section relate to the course repository location and structure. Options are
|   Key | Default | Purpose |
|-------|---------|---------|
| `REPO_REMOTE_VARNAME`   |  `"AUTOGRADING_REPO_REMOTE_PATH"` | Variable name of the environment variable used to hold the remote path of your autograding repo.  |
| `REPO_BRANCH` | `"main"` | Specific branch of the repo to use for your autograder. This will be the only branch pulled from for the autograding container. |
| `AUTOGRADING_ROOT` | `""` | Path from repo root which contains the `bin/`, `etc/`, and `setup/` folders |
| `ASSIGN_ROOT`      | `"assignments"` | Path from `AUTOGRADING_ROOT` where the assignment folders are |
| `ASSIGN_AUTOGRADING_SUBFOLDER` | `""` | Path from a given assignment folder which holds the autograding files for that assignment.  |

Here is a visualization of the default directory tree and options 
```
.
|--- assignments/               # ASSIGN_ROOT - "assignments" - path from repo root that holds the assignment folders themselves
|   |--- my_first_assignment            
|       |--- testrunner.sh      # ASSIGN_AUTOGRADING_SUBFOLDER - "" - specifies path where autograding files for an assignment  
|       |--- testset.toml.      # are relative to the directory for that assignment -- THIS MUST BE THE SAME FOR ALL ASSIGNMENTS.
|       |--- testset/
|   |--- ...
|   |--- assignment_n
|       |--- testrunner.sh 
|       |--- testset.toml. 
|       |--- testset/            
|--- bin/                       # AUTOGRADING_ROOT - "" - holds path to folder that holds bin/, etc/, and setup/ folders 
|--- etc/
|--- setup/
|-
```
With this example repo it doesn't make much sense to get more complicated than this, but here is another example
```
.
|--- my_random_folder               # ASSIGN_ROOT - "my_random_folder/assignments"
|    |--- assignments/               
|       |--- my_first_assignment            
|           |--- autograder         # ASSIGN_AUTOGRADING_SUBFOLDER - "autograder" -- THIS MUST BE THE SAME FOR ALL ASSIGNMENTS
|               |--- testrunner.sh 
|               |--- testset.toml. 
|               |--- testset/
|       |--- ...
|       |--- assignment_n 
|           |--- autograder
|               |--- testrunner.sh 
|               |--- testset.toml. 
|               |--- testset/
|--- autograding_framework           # AUTOGRADING_ROOT - "autograding_framework"
|   |--- bin/                      
|   |--- etc/
|   |--- setup/
|-
```
**Note! The assignment name for an assignment in the `assignments/` folder must have the same name as the assignment name on Gradescope. An environment variable $ASSIGNMENT_TITLE is provided to the container by Gradescope, and this is used to find the autograder files. If the names don't match, there will be issues. One caveat is that you may use spaces in place of underscores on gradescope; however, the other text must match exactly (case sensitive).**

### [tokens]
At Tufts, we have a system for students to be able to manage late submissions with 'tokens'. The token system is flexible and generally works well. The idea is that the students maintain a bank of X tokens, where each token is effectively a 1-day extension on a given assignment. For any assignment, the maximum number of tokens a student can use is usually 2 - so up to 2 days late. If you would like to use this system, see the tokens section below; otherwise simply ignore it. 

### [docker]
These are settings specific to the docker-build process. If you woud like to manually build your container, you will need them. See the `Docker method` section below for details; likewise simply ignore this section if you don't want to use docker manually.

### [misc]
Other miscellaneous information. The currently available options are
|   Key | Default | Purpose |
|-------|---------|---------|
| `SUBMISSIONS_PER_ASSIGN`   |  `5` | Allows you to set a cap on the number of submissions a student can send to the autograder per assignment. Change this to a large value to ignore.  |
| `TEST_USERS` | `["Matthew Russell"]` | Specify any names of users (names on Gradescope) who are to be exempted from `SUBMISSIONS_PER_ASSIGN` for testing purposes. |


## Build Your Autograding Docker Container

### Prereqs
Prior to building the container, you will need
1) python3 
2) `toml` library for python: `python3 -m pip install toml`

### Intro
There are two methods by which you can build the autograding Docker container for Gradescope
1) The `.zip` method - for each assignment, this workflow is to manually upload a `.zip` file to Gradescope that contains two scripts: `setup.sh`, which installs dependencies, and a shell script named `run_autograder`, which runs the autograder. Gradescope then builds a docker container that is adapted based on your setup.sh script. This will work fine if you don't want to get into Docker yourself.
2) The Docker method - this workflow is to build the Docker container from scratch and upload it to the container registry of your choice. Then for each assignment you simply point gradescope to use your container. If you already use Docker, or are feeling adventurous, go for this option. 

### .zip: first time setup
* run `cd setup/zipbuild && ./build_container.sh` to produce `Autograder.zip` file, which will be located in `setup/build/`. You'll want to keep this `.zip` file around, as you can re-use it on subsequent assignments. 

### .zip: per-assignment todo
* On Gradescope, after creating the programming assignment:
    * Go to the `configure autograder` section.
    * Select `Ubuntu 22.04` for the container type.
    * Upload the `Autograder.zip` file
* It should build and be tagged with no errors - this will take ~5 minutes.

### Docker: first-time setup
0. Install Docker Desktop https://www.docker.com/products/docker-desktop/. 
1. You will need to host your container somewhere. We suggest using the [GitHub container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), but a Dockerhub 'pro' (paid) account will also work.
2. For either registry, you will need a username and password/access token for that registry.
3. See the [docker] section of `etc/config.toml`. You'll need to update the values of these variables as needed. Note that in this case `GHUNAME` and `GHPAT` are the names of environment variables (NOT the values of the variables themselves). So with this example you'd need `export GHUNAME='myghubusername'` in your `~/.bashrc`, etc. Run `source ~/.bashrc` after editing the file.

|     KEY          |        Default       |        Purpose       |
|------------------|----------------------|----------------------|
| `CONTAINER_REMOTE`  | `ghcr.io` | Which container registry you use (default is GitHub) |
| `CONTAINER_NAME` | `gradescope-docker` | Name of the package repo that will hold your autograding docker container. |
| `CONTAINER_TAG` | `autograder-autobuild` | Tag of the container which will be used for the course's autograder. One tag will be used per course| 
| `REGISTRY_USER_VARNAME` | `GHUNAME` | Variable name of the environment variable which holds the username to login to the `CONTAINER_REMOTE`. 
| `REGISTRY_PASS_VARNAME` | `GHPAT` | Variable name of the environment variable which holds the password/access token to login to the `CONTAINER_REMOTE` [NB: The PAT needs write:packages permissions]. 

4. Build and deploy the container. 
```shell
cd setup/dockerbuild
python3 deploy_container.py
```
5. For either registry, after uploading your container [keep it private!], you will need to share it with gradescope's relevant account - this will only have to be done once.
* from github: `gradescope-autograder-servers` 
* from dockerhub: `gradescopeecs`

### Docker - per-assignment todos
Select the `Manual Docker Configuration` option in the `configure autograder` section of the assignment; place the full remote path to your container (e.g. `ghcr.io/ghubusername/ghubpackageregistry:dockertag`). Gradescope will then immediately be able to use your container.

### When to Rebuild the Container
In general, you will only need to build `Autograder.zip` or to deploy your docker container once. However, notable exceptions include
* Changes to the variables in the `etc/config.toml` file
* Changes to the values of any of the environment variables referenced to by the `etc.toml` file
* Changes to any of the files in the `dockerbuild` or `zipbuild` folders
* Changes to the `bin/run_autograder` script
* If you make major changes to the repo, such that the time taken to `git pull` is becoming more than you'd like.

## Token Management
At Tufts, we have a system for students to be able to manage late submissions with 'tokens'. The token system is flexible and generally works well. The idea is that the students maintain a bank of X tokens, where each token is effectively a 1-day extension on a given assignment. For any assignment, the maximum number of tokens a student can use is usually 2 - so up to 2 days late. If you don't want to use tokens, just skip this section.

### Postgres
The solution presented here to manage tokens is Postgres. All of the connection to the server is maintained in the back-end of the scripts here: you only have to setup the server (free), create one environment variable on your system, and tweak a few options in `etc/config.toml`.

The way the postgres table will be organized, there will be one row per student, with one column representing the tokens remaining ('tokens left'), and one column per assignment. These will be created automatically. The value of the assignment columns will default to 0, and will increase by 1 for each token the student uses on that assignment. Likewise, the 'tokens left' value will decrement for each token used. 

For even a few hundred students, the free 'TinyTurtle' option at ElephantSQL should work fine. 
1) Create an account at ElephantSQL and a new TinyTurtle database (free) [or, make and host a postgres db somewhere else].
2) Run the following query to build the table. With ElephantSQL you can do this in the browser.  Change the value 5 below to the number of tokens you would like your students to have for the semester. Make sure to copy everything else exactly.
```sql
CREATE TABLE tokens(pk NAME PRIMARY KEY, 
                    "tokens left" INTEGER DEFAULT 5);
```
3) Copy the URL for the db (in ElephantSQL this is in the details section). Add a line to your `~/.bashrc` as done in previous examples above. The default variable name is `POSTGRES_REMOTE_PATH`, although you may pick another one. The line should look like this:
```shell
export POSTGRES_REMOTE_PATH="postgres://abcdefgh:nSgKEZiD55VdHDlzDXNBT@drona.db.elephantsql.com/abcdefgh"
```
4) Update the variables in the `[tokens]` section of the `etc/config.toml` file. Make sure to set `MANAGE_TOKENS` to `true`. 

|     KEY          |        Default       |        Purpose       |
|------------------|----------------------|----------------------|
| `GRACE_TIME`   | `15` | Number of minutes you give the students as 'grace' when they submit |
| `TOKEN_TIME`      | `1440` | Length in minutes that one token provides (default is 24 hours). |
| `STARTING_TOKENS` | `5` | Number of tokens each student has at the start of a semester | 
| `MAX_PER_ASSIGN` | `2` | Maximum number of tokens supported for a given assignment. [NOTE: this must be 2 for now, more/less are not yet supported] | 
| `MANAGE_TOKENS` | `false` | Whether or not to do token management [default of `false` skips tokens entirely] |
| `POSTGRES_REMOTE_VARNAME` | `"POSTGRES_REMOTE_PATH"` | Variable name of the environment variable which holds the URL of the postgres db. [NOTE!! this variable is substitued with the actual value and put into the container at build time; if you change either the value here, or the actual value of the URL in your `~/.bashrc` file, you will need to rebuild your container. This goes for both Docker and zip build methods.] |

Now, every time a student submits, prior to the autograder running, tokens will be checked if the assignment is late. If the token check fails, the autograder will fail immediately. You will want to let students know that in Gradescope, if they click 'Submission History' at the bottom of the autograder page, they can 'activate' a different submission. Thus, they can choose which submission they would like to be used for grading. 

Note also that students rows and assignment columns will be added the database automatically by the autograder. 

## Security
Security concerns have been raised re: Gradescope's containers by a number of people over the years. Our approach to maximizing security is as follows:
* A non-root user is created (named `student`) during the container build process. 
* Prior to running any element of a student's submitted code, all of the files of the repository and configuration files created during the build process are chmodded such that they are not visible to `student`.
* All subprocess calls which interact with student code in any way [e.g. via `make`, or executing files produced by `make`], are run as the user `student`. 
This ensures that any time student's code is run, they should not be able to see any of the back-end autograding files. 

## Conclusion
Continue to the next section to learn about the autograding framework, and for a walkthrough to setup an assignment. 

# Autograding Framework

## Introduction
The autograding framework is designed to have you writing and deploying tests as quickly as possible. 
There are two methods of testing a student's submission that this autograder supports

1) Tests which are a set of `.cpp` driver files, each with their own `main()`. 
2) Tests which send different input files to a student's executable program. 

In either case, `stdout`/`stderr` can be `diff`'d automatically against the output of a reference implementation, you can send a file to `stdin` for a test, output can be canonicalized before `diff`, and `valgrind` can be run on the programs as well. Limits can be set for memory usage, timeout, etc. See details below.

## `autograde.py`
Before getting into the details, here is a summary of the procedure run by `bin/autograde.py`, which is the script that does the autograding. 
* Parse input arguments
* Load `testset.toml` file and validate configuration
* Create `Test` objects, each of which contains all possible configuration variables.
* Build directories required to run tests
* Compile the executable(s) specified in the configuration, and save compilation logs in `results/logs/testname.compile.log`
* Run each test: 
    * Save a dump of the initial Test object to `results/logs/testname.summary`
    * Execute the specified command
    * Run any `diff`s required based on the testing configuration; run canonicalization prior to `diff` if specified. 
    * Run `valgrind` if required.
    * Determine whether the test passed or not
    * Save a dump of the completed Test object to `results/logs/testname.summary`
* Report the results to `stdout`.

## Files/Directories Created by the Autograder
After the autograder runs, here is an example of the various files that are created. Note that various `.ofile`, `.diff`, `.ccized`, etc. files may not be created depending on your configuration. 
```
.
|--- results/
|   |--- build/      
|   |   |--- [student submission files]
|   |   |--- [files copied from copy/ and symlinks that symlink to files in link/]
|   |   |--- test01   [compiled executables]
|   |   |--- ...
|   |   |--- testnn
|   |--- logs/
|   |   |--- status
|   |   |--- test01.compile.log
|   |   |--- test01.summary
|   |   |--- ...
|   |   |--- testnn.summary
|   |--- output/
|       |--- test01.memtime
|       |--- test01.ofile
|       |--- test01.ofile.diff
|       |--- test01.ofile.ccized
|       |--- test01.ofile.ccized.diff
|       |--- test01.stderr
|       |--- test01.stderr.diff
|       |--- test01.stderr.ccized
|       |--- test01.stderr.ccized.diff 
|       |--- test01.stdout
|       |--- test01.stdout.diff
|       |--- test01.stdout.ccized
|       |--- test01.stdout.ccized.diff
|       |--- test01.valgrind
|       |--- ...
|       |--- testnn.valgrind
|-
```
### build/
Inside the `build` directory are all of the students submitted files, and any course-staff-provided files which need to be copied over [see `copy` and `link` directories below]. Also there are the executables produced during the compilation step. 

### logs/
A set of compilation logs and summary files for each test. **Each `testname.summary` file in the `logs/` directory contains a dump of the state of a given test. This is literally a dump of the backend `Test` object from the `autograde.py` script, which contains all of the values of the various configuration options (e.g. `diff_stdout`, etc.) and results (e.g. `stdout_diff_passed`). A first summary is created upon initialization of the test, and it is overwritten after a test finishes with the updated results. `summary` files are very useful for debugging!**

### output/
Output of each test. There are output files created for `stdout`, `stderr`, output files produced by the program (marked with the `.ofile` extension) and `valgrind`. `diff` files contain the result of `diff`ing the given output against the reference output are also here. If any of the output streams are to-be canonicalized prior to `diff`, then the `.ccized` file is created for that output stream [e.g. `testname.stdout.ccized`], along with the `.ccized.diff`, indicating that the files `diff`'d are the canoncialized outputs. Also here is a `.memtime` file, which contains the result of running `/usr/bin/time -v %M %S %U` on the given program. This file is only produced in the case where memory limits are set in the configuration.

## `testset.toml` configuration file
The framework depends on a `testset.toml` file (https://toml.io) to specify the testing configuration. `testset.toml` must be configured as follows
```toml
[common]
# common test options go here
# this section can be empty, but is mandatory
# this section must be named "common" 

[set_of_tests] 
# subsequent sections in the .toml file contain a group of tests to run
# configuration options placed under this section here will override the settings in [common] for these tests
# test group names (e.g. [set_of_tests]) can be anything
# tests in a section must be placed in a list named `tests'
tests = [
      { testname = "test0", description = "my first test" },
      { testname = "test1", description = "my second test" },
      ..., 
      { testname = "testn", description = "my nth test" },
]
# each test **must** have testname and description fields
# you may add any other option to a given test
# test-specific options override any 'parent' options
```
See the section `test .toml configuration options` for the full details. 

## Example #1: Staff-Provided Driver Test Configuration [Default]
An assignment with course-staff provided `.cpp` driver files is the default behavior for the autograder. Using the `testset.toml` file above, for example, here is one possible configuration of a corresponding (bare-bones) directory structure 
```
.
|---testrunner.sh     [one-line script that runs the command `autograde`]
|---testset/          
|   |---cpp/          [contains .cpp driver files]
|   |---makefile/     [contains custom Makefile]
|   |---ref_output/   [contains output of reference implementation]
|---testest.toml      [testing configuration file]
|-
```
For this simple grading configuration, the autograder assumes that each testname [e.g. `test01` above] corresponds to a file `testset/cpp/testname.cpp` which contains its own `main()`, and that there is a target named `testname` in `testset/makefile/Makefile` which produces an executable named `testname`; it will run `make testname`, and then `./testname`. Then, the default behavior will be to `diff` the output of the student's provided submission with the output in `ref_output`. Reference output can be generated automatically [see `Testing the Autograder` section below].


### testrunner.sh
Note the file `testrunner.sh`. This is an exteremely simple, one-line script which tyipically just calls `autograde`. Why is it here, you ask? Great question. It's useful to have a unique script used by each autograding assignment which is separate from `run_autograder`. This is so that if you need to make any assignment-specific tweaks - prepping any unusual directories or files, or installing anything special programs, etc., you can simply make the relevant updates in this file and `git push`, without having to rebuild the whole autograding container.  

### Course-Staff-Provided Makefile
Here is an example of a corresponding `Makefile`, which would be in the directory `testset/makefile/`. Note that the `make` program will be run from the directory `results/build`. This example produces a target for each of `test01 ... test59`. Also, note that with this particular `Makefile`, the target to build (e.g. `make target`) must always be named the same as the program to run (e.g. `./target`).
```shell
# Testing Makefile
TESTSETDIR=../../testset
TESTSOURCEDIR=${TESTSETDIR}/cpp

CXX = clang++
CXXFLAGS = -Wall -Wextra -std=c++11 -I .

MYTESTS = $(shell bash -c "echo test{01..59}")

${MYTESTS}: StudentFile.o
	${CXX} ${CXXFLAGS} -o $@ $^ ${TESTSOURCEDIR}/$@.cpp

%.o: %.cpp $(shell echo *.h)
	${CXX} ${CXXFLAGS} -c $<

clean:
	rm -rf test?? *.o *.dSYM
```

## Example 2: Student Executable Test Configuration
Let's now assume that a student has written code to produce an executable program. A `testset.toml` file for such an assignment might look like this
```toml
[common]
our_makefile = false           # NOT DEFAULT -- use the student's Makefile to compile their program
executable   = "myprog"        # all of the tests will use this executable

[set_one]
tests = [
    { testname = "test01", description = "my first test },
    { testname = "test02", description = "my second test },
    { testname = "test03", description = "my third test" } 
]
```
And the corresponding (bare-bones) directory structure
```
.
|---testrunner.sh     [script that runs `autograde`]
|---testset/          [everything needed to run tests]
|   |---ref_output/   [output of reference implementation]
|   |---stdin/        [files to send as stdin to the tests]
|---testest.toml      [testing configuration file]
|-
```
Note that the default behavior of the autograder, regardless of testing format, is for Any file in `testset/stdin/` that is named `<testname>.stdin` will be sent to `stdin` for a test with the testname `<testname>`. Also here we do not need a `makefile` folder - it is assumed we will be using the student's `Makefile` instead. 

## Command-Line Arguments
For any test, you may specify a variable `argv` which is a list of command-line arguments to send to the executable. This is doable with either style of assignment-testing demonstrated above. Note all `arvg` arguments must be written as strings, however they will be passed without quotes to the executable. To add `"` characters, escape them in the `argv` list. For example, the following test will be run as `./test0 1 2 "3"`.  
```toml
{ testname = "test0", description = "my first test", argv = ["1", "2", "\"3\""] }
```
You may specify an `argv` value for a set of tests as well
```toml
...
[my_group_of_tests]
argv = ["hello", "world!"] # for each test in tests[] below, will have this list sent as its command-line arguments
tests = [
    { testname = "test01", description = "my first test },
    { testname = "test02", description = "my second test },
    { testname = "test03", description = "my third test" } 
]functionality
...
```

## `diff`ing Output Files
In addition to `diff`ing student's `stdout` and `stderr` against a reference output, this framework supports `diff`ing against any number of output files created by the student's program. Specifically
1) Such output files must be named `<testname>.ANYTHING_HERE.ofile`
2) Such output files must be placed in `results/output/`

In order to make this happen
1) The expectation is that the executable will receive the name of the file to produce as a command-line argument to the program.
2) In the `testset.toml` file, you can use a special customizable string that will contain the correct output path,including the directory and beginning of the file name: `"${test_ofile_path}`". 

So, in practice, your test object might look like this
```toml
{ testname = "test0", description = "my first test", argv = [ "${test_ofile_path}.one.ofile", "${test_ofile_path}.two.ofile" ] }
```
You can generalize this functionality to multiple tests as well. In the following example, all of the tests in the group [set_of_tests] will have these two argv arguments specified, whereby the string `"${test_ofile_path}"` will be replaced with the full path to the output file (e.g. `/autograder/results/output/test01`). 
```toml
[set_of_tests]
argv = [ "${test_ofile_path}.cookies.ofile", "${test_ofile_path}.candy.ofile" ]
tests = [ { testname = "test0", description = "my first test" }
         ... 
]
```

## Canonicalization Prior to `diff`
The autograder supports canonicalization of either of `stderr`, `stdout`, or any output files generated by the program prior to `diff`ing against the reference. Functions which are used by the autograder in this capacity must be in a file `canonicalizers.py`, at the root of the assignment's autograder. Such functions must:
* Take five parameters (which will be provided by the autograder)
    1.  A string which will contain the student's output from whichever stream is to be canonicalized
    2.  A string which will contain the reference solution's (non-canonicalized) output from whichever stream is to be canonicalized
    3.  A string which will contain the name of the test (e.g. `test01`)
    4.  A string which will contain the name of the stream to be canonicalized [`stdout`, `stderr`, or the output filename in the `argv` list (e.g. `test0.one.ofile` or `test0.two.ofile` in the fist example above)]
    5.  A dictionary which will contain any specific configuration options for a test or set of tests (e.g. `{'my_config_var': 10}`)
* Return a string, which contains the canonicalized output of the student's program
Here's an example `testset.toml` file will which canonicalizes of all the possible output streams [ not sure why anyone would actually need to do this :) ]
```toml
[common]
ccize_stdout = true
ccize_stderr = true
ccize_ofiles = true            # canonicalize the output files before diff'ing
ccizer_name  = "sort_lines"    # use 'sort_lines' function in canonicalizers.py
ccizer_args  = { "random_variable": 10 }
our_makefile = false           # use the student's Makefile
executable   = "studProg"      # all of the tests will run this executable

[the_tests]
argv  = ["myDataFile", "${test_ofile_path}.one.ofile", "${test_ofile_path}.two.ofile"] 
tests = [
    { testname = "test01", description = "my first test },
    ...
]
```
And here's a dummy example for `canonicalizers.py` which sorts in order if the stream is `stdout/stderr`, but in reverse order if the output is an ofile. 

```python
# canonicalizers.py
def sort_lines(student_unccd_output, reference_unccd_output, testname, streamname, params):
    if streamname in ['stdout', 'stderr']:
        student_ccd = sort(student_unccd_output) 
    else:
        student_ccd = sort(student_unccd_output, reverse=True)
    return student_ccd
```

## Copying / Linking Files and Folders to Build/
Often you will want to give the executable program access to certain folders and/or files provided by the course staff. 
* Any files or folders in an optional `testset/copy` directory will be copied to the `build` directory prior to running tests. 
* Similarly, any files in an optional `testset/link` directory will be symlinked-to from the `build` directory. Symlinking is convenient if you have a particularly large set of directories to work with.

## Test Time and Memory Limits
Options exist to limit time and memory usage of student programs. See the test configuration options section below for details. 

## All Possible Files and Directories for an Assignment's Autograder
As expressed above with the simple examples, you will likely not need all of these for a given assignment. Items marked with a * are mandatory in all cases. 
```
.
|---canonicalizers.py [file with canonicalization function(s)]
|---testrunner.sh     *[script that runs `autograde`]
|---submission/       *[student submission (provided by gradescope, so doesn't need to be in the repo)]
|---testset/          *[everything needed to run tests]
|   |---copy/         [files here will be copied to results/build/]
|   |---cpp/          [.cpp driver files]
|   |---link/         [files here will be symlinked in results/build/]
|   |---makefile/     [contains custom Makefile]
|   |---ref_output/   *[output of reference implementation]
|   |---solution/     [solution code - this location is the default, but can be anywhere]
|   |---stdin/        [files here are sent to stdin]
|---testest.toml      *[testing configuration file]
|-
```

## All`testset.toml` Test Configuration Options
These are the configuration options for a test. You may set any of these in `[common]`, under a test group, or within a specific test.

| option | default | pupose | 
|---|---|---|
| `max_time` | `10` | maximum time (in seconds) for a test [a test foo is run as `timeout max_time ./foo`]|
| `max_ram` | `-1` (unlimited) | maximum ram (in MB) usage for a test to be considered successful [`/usr/bin/time -f %M` value is compared with max_ram * 1024] |
| `valgrind` | `true` | run an additional test with valgrind [valgrind tests ignore `max_ram`] |
| `diff_stdout` | `true` | test diff of student vs. reference stdout |
| `diff_stderr` | `true` | test diff of student vs. reference stderr |
| `diff_ofiles` | `true` | test diff of student vs. reference output files |
| `ccize_stdout` | `false` | diff canonicalized stdout instead of stdout |
| `ccize_stderr` | `false` | diff canonicalized stderr instead of stderr |
| `ccize_ofiles` | `false` | diff canonicalized ofiles instead of ofiles |
| `ccizer_name` | `""` | name of canonicalization function to use |
| `ccizer_args` | `{}` | arguments to pass to canonicalization function |
| `our_makefile` | `true` | use `testset/makefile/Makefile` to build tests |
| `exitcodepass` | `0` | return code considered successful by the autograder|
| `pretty_diff` | `true` | use `icdiff` for easy-to-read diffs |
| `max_score` | `1` | maximum points (on Gradescope) for this test |
| `visibility` | `"after_due_date"` | Gradescope visibility setting |
| `argv` | `[ ]` | argv input to the program - Note: all arguments in the list must be represented as strings (e.g. ["1", "abcd"...])|
| `executable` | `(testname)` | executable to build and run |
| `max_valgrind_score` | `8` | `[common]` only setting - maximum valgrind score for this assignment [per-test valgrind score is deduced by default based on this value]. 
| `valgrind_score_visibility` | `"after_due_date"` | `[common]` only setting - visibility of the test which will hold the total valgrind points for the student. | 
| `kill_limit` | `750` | `[common]` only setting - test will be killed if it's memory usage exceeds this value (in `MB`) - soft and hard rlimit_data will be set to this value in a preexec function to the subprocess call. NOTE: this parameter is specifically intended to keep the container from crashing, and thus is `[common]` only. Also, if the program exceeds the limit, it will likely receive `SIGSEGV` or `SIGABRT` from the os. Unfortunately, nothing is produced on `stderr` in this case, so while the test will likely fail based on exitcode, it's difficult to 'know' to report an exceeded memory error. However, if `valgrind` is also run and fails to produce a log file (due to also receiving `SIGSEGV`/`SIGABRT`), the test will be assumed to have exceeded max ram...in general, however, this is tricky to debug. In my experience, `valgrind` will fail to allocate memory but still produce a log file at `~50MB` of ram; any lower and no log file will be produced. The default setting of `750` `MB` should be fine for most tests, and will work with the smallest (default) container. |
| `max_submissions` | _ | `[common]` only setting - this value will override the default value of `SUBMISSIONS_PER_ASSIGN` in the `etc/config.toml`. If not set for an assignment, the default value for this is ignored, and the `SUBMISSIONS_PER_ASSIGN` value is used instead. |
| `exec_command` | `""` | Enables 'manual mode' for a given test. In this mode, specify the specific command to-be-run [e.g. `python3 my_file.py`]. Automatic management of `stdin/stdout/stderr/ofiles` will work as usual; also `kill_limit`, `max_ram`, and `timeout` limits work as normal. Canonicalization will likewise work. Make sure to set `valgrind` to `false` if you don't want it to run for these tests. If `exec_command` is used, the `executable` argument will be ignored. | 

<!-- | `style_score_visbility` | `"after_due_date"` | `[common]` only setting - visibilitiy of the test which will hold the total style points for the student. | -->
<!-- | `cols_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code has over `style_max_columns` columns. If all `_style_weight` options are set to `0` (as by default), a style check will not be performed. |
| `tabs_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code contains tabs. |
| `todos_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code contains TODOs. |
| `symbol_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code contains symbols (`&&`, `\|\|`, `!`) instead of keywords (`and`, `or`, `not`). Note `!=` is not considered a violation. |
| `break_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code contains `break`. |
| `boolean_style_weight` | `0` | `[common]` only setting - number of points to take off if a student's code contains boolean style violations (i.e. comparing a boolean variable via `==` or `!=` with `True` or `False` instead of `if (x)` or `if (not x)`). |
| `non_code_style_checkset` | `["README", ".h", ".cpp"]` | `[common]` only setting - specifies the set of files which will be checked for non-code style violations. Non-code style violations are having more than `style_max_columns` columns, having tabs, or having TODO statements. There are two ways to specify files in the check set. The first is to provide a direct filename such as `"README"`. This means any file in the student's submission which *case-insensitive* matches `"README"` will be checked. The second group of strings in this setting are file extensions. For example, specifying `".cpp"` means any `.cpp` file in the student's submission will be checked. |
| `code_style_checkset` | `[".h", ".cpp"]` | `[common]` only setting - specifies the set of files which will be checked for code style violations. Code style violations are using symbols instead of keywords, break statements, or not practicing boolean zen. The two ways you can specify files in this checkset are the same as the two ways for `non_code_style_checklist`. |
| `style_max_columns` | `80` | `[common]` only setting - the number of columns that is considered too many for a single line. | -->


## Building Reference Output and Testing the Autograder

### Preliminaries
NOTE: Building reference output does not work well on OSX. This is for a number of reasons, including:
1) valgrind doesn't work on OSX
2) defaults for various gnu programs such as `/usr/bin/time` and `timeout` used in standard Linux systems aren't available on OSX, and are a pain to get working. 

Therefore, it is highly suggested to build your reference output and test your autograder on a Linux machine. You can use the `remote-containers` extension in `VSCode` to work within an `Ubuntu` container quite easily: https://code.visualstudio.com/docs/devcontainers/containers

In order to build reference output and test your code easily, first add the `bin/` folder of the autograding repo to your `$PATH`. To do this, run the following commands, replacing `REPO_ROOT` with the path to the repository root on your system. 
```shell
echo -e "export PATH=\$PATH:/REPO_ROOT/bin\n" >> ~/.bashrc
source ~/.bashrc
```
Also, if you don't have `icdiff` installed on your system and would like to use the `pretty_diff` option you'll need to install it (`brew/apt-get icdiff`).

### Building the Reference Output
Once you've configured your tests, from the assignment's autograder directory [when you run `ls` from here you should see `testset.toml`, `testset`, etc.], run the command
```shell
build_ref_output -s SOLUTION_PATH
``` 
where `SOLUTION_PATH` is the path to a folder with the reference solution. The reference code will be run *as a submission*, and the output of the reference will be placed in the `REPO_ROOT/hwname/testset/ref_output/` directory. The default behavior of `build_ref_output` is to keep the temporary `temp_ref_build_dir` directory created to run the autograder and build the reference output. The files in `temp_ref_build_dir/results/` can be invaluable if you have tests which aren't functioning right - `cd`-ing into `temp_ref_build_dir/results/logs` or `temp_ref_build_dir/results/output` can be very helpful! You can optionally remove this directory after the reference output is created run with the `-d` option.

### Testing with an Example Submission
After you've produced the reference output, if you'd like to test a given folder against the produced reference output, run
```shell
test_autograder -s SUBMISSION_PATH
```
where `SUBMISSION_PATH` contains the path to a folder with the submission code you would like to test. This script will create a temporary testing directory named `temp_testing_dir`, copy everything there, and run the tests. You can optionally remove this directory after tests are run with the `-d` option.

### Parallel Execution of Tests
The `autograde` program supports parallel execution of tests with the `-j` option
```shell
autograde -j NUMCORES
```
where `NUMCORES` is the number of cores you would like to utilize (`-1` will use all available cores). Note that multiple tests may be run on each core concurrently. The default setting is equivalent to `-j 1`, which runs tests without parallelization enabled. You can also supply the `-j NUMCORES` option to the `build_ref_output` or `test_autograder` scripts.

Note! Given resource limits on gradescope use you should be careful with enabling multiple cores for Gradescope! This is most likely useful when building reference output on your local system. 

## Gradescope Results
After running the autograder, our program produces results for Gradescope. A few notes on this:

### Visibility settings
Gradescope allows each test to have a different visiblity setting - the options are `hidden`, `after_due_date`, `after_published`, or `visible`. Their systems are setup such that if any of the options are `hidden`, all of the tests will be hidden. The default setting is therefore `after_due_date`, which is usable with tests that are also `visible`. We often like to show some tests but not others, and this generally works well. 

We also decided that we would like to show students their total final autograder score prior to the due date; that is, they could see their 'final score', but only a few of the actual tests. This is not doable by default. In order to facilitate this, added a `test00` in `bin/make_gradescope_results.py` which shows the student's final autograder score. This code is commented out by default, but if you would like to show students their final autograder score without revealing all of the test results then uncomment `#make_test00()` in the `make_results()` function (line ~250) of `bin/make_gradescope_results.py`.

## Score in Gradescope
Note that if the `max_score` for a test is `0`, then Gradescope assumes that the student passes the test. There's no way around this on our end, so if you want to have 'optional' tests, then just lower the maximum score of the autograder on Gradescope (on gradescope.com - `assignment->settings->AUTOGRADER POINTS`).

# Conclusion
That should be enough to get you up and running! Please feel free to contact me with any questions you have, and/or any bugs, feature requests, etc. you find. Thanks!

# TODOS
* Update the functionality of `bin/autograde.py` so that if a grader is re-running tests, we don't nuke the entire build folder, but intelligently load the data from alread-run tests. Also, need to verify that the various filter, etc. options work as expected. 
* Since we've removed course code from the repo, we need more examples in `assignments/`.

# Changelog
## [2.1.2] - 2023-06-09 -
Update canonicalizer function arguments to take in bytes instead of utf8-decoded text. Now keep multiple ofile results as variables. Refactor massive report results fn. Changed `icdiff` command to `python3 -m icdiff` for halligan compatibility. Requires rebuild. 

## [2.1.2] - 2023-06-08 - 
Configure container prep to work properly with MANAGE_TOKENS=false

## [2.1.2] - 2023-06-08 - b5338d47
Bug fix re: mistaken earlier changes with adding `./` where appropriate to executable name. TODO: fix up this logic. 

## [2.1.1] - 2023-06-08 - 043ceaea
Dump log if `git pull` fails.  

## [2.1.0] - 2023-06-06 - 0fdbc91f
Updated backend functionality to make use of `.toml` config file properly instead of sourcing forced `.ini` files. Added functionality for selecting repo branch, and for adding users exempt from submission number checks. Updated section names in config to be better [paths->repo, and other->misc]. Dropping file-specific changes from README logs; instead will tag repo commit that has the major changes. 

## [2.0.3] - 2023-06-02
README updates, and moved from "#{testname}" -> "${test_ofile_path}". Documentation is much clearer on this as well. 
* Changed
    * `autograde.py`
    * `README`

## [2.0.2] - 2023-06-01
Merged Chami's branch. 
## [2.0.1] - 2023-05-28
README.md updates

## [2.0.0] - 2023-05-27
Pythonified build process, and merged all config files into one `.toml` file. 
After the new, improved, simplified build process, token management system, and security fixes, we're at version 2.0 [!]
* Added
    * `etc/config.toml` - how holds all config options from the old `.ini` files
    * `bin/container_prep.py` - does the logic of common_build.sh; returns the 'secret' config
    * `setup/dockerbuild/deploy_container.py` - does the logic of `deploy_container.sh`
* Removed
    * `etc/autograder_config.ini`
    * `etc/token_config.ini`
    * `etc/docker_config.ini`
    * `setup/dockerbuild/deploy_container.sh`
* Changed
    * `bin/validate_submission.py` - minor update to work with new config
    * `bin/run_autograder` - remove python3.6 workarounds
    * `setup/dockerbuild/Dockerfile` - update to work with new python build process
    * `setup/zipbuild/build_container.sh` - update to work with new python build process
    * `README.md` - significan README clarifications

## [1.4.6] - 2023-05-27
Merged most of the two build scripts into one - `common_build.sh`, which is now called by both of the `deploy_container.sh`(dockerbuild) and `build_container.sh` (zipbuild) scripts. 
* Added
    * `setup/common_build.sh` - does most of the setup for both container styles. 
* Changed
    * `setup/dockerbuild/deploy_container.sh`
    * `setup/zipbuild/build_container.sh`
## [1.4.5] - 2023-05-26
Switch from `diff-so-fancy` to `icdiff` for `pretty_diff` option; used the `ansi` option for gs output for the tests so colorized output works; removed `diff-so-fancy`, and the `lib` dir
* Changed
    * `setup/dockerbuild/deploy_container.sh` - remove references to `lib`
    * `setup/dockerbuild/Dockerfile` - remove references to `lib`; add `icdiff` to `apt-get` list
    * `setup/zipbuild/setup.sh` - remove references to `lib`; add `icdiff` to `apt-get` list
    * `setup/run_autograder.sh` - remove references to `lib`
    * `bin/make_gradescope_results.py` - use `ansi` option for gradescope test output for color output [!]
    * `bin/autograde.py` - simplify `diff` logic (`icdiff` returns nonzero exit code on different files as expected)
* Removed
    * `bin/diff-so-fancy`
    * `lib/DiffHighlight.pm` - used by `diff-so-fancy`
    * `lib/` - no longer needed.
## [1.4.4] - 2023-05-26
* Changed
    * `setup/dockerbuild/deploy_container.sh` - update build dir to setup/build
    * `setup/zipbuild/build_container.sh` - update with all recent fixes for version 2.0; also fixed issue where default python version in 22.04 container is 3.10
    * `setup/zipbuild/setup.sh` - update with all recent fixes for version 2.0
## [1.4.3] - 2023-05-24
* Changed
    * `bin/build_ref_output.py` - add argument to autograde to not use 'student' user if building reference output
    * `bin/autograde.py` - support arugment for not using `student` user. Also wrapped preexec fn in lambda - this was
                           a latent bug! The preexec fn was being run globally rather than as a preexec. This still worked to limit the container's ram usage, but was functioning slightly differently than we thought. 
## [1.4.2] - 2023-05-24
* Changed
    * `bin/run_autograder` - chmod directories for security
    * `bin/autograde.py` - add user argument to subprocess calls that run student code; pass "student" to those calls, 
                         - also makes any non-student-facing files (solution, repo, etc.) 770.
    * `setup/dockerbuild/Dockerfile` - add command to create 'student' user without elevated permissions
    * `README.md` - remove security TODO

## [1.4.1] - 2023-05-24
* Changed
    * `bin/run_autograder` - delete the file that contains the postgres URL prior to executing the autograder. 
    * `README.md` - added more security TODOs. 

## [1.4.0] - 2023-05-24
* Added
    * `etc/token_config.ini` - token management configuration
    * `bin/validate_submision.py` - do #submission validation and token validation
    * `bin/validate_submission` - symlink to validate.py
* Changed
    * `setup/dockerbuild/deploy_container.sh` - reorganized logic to use build/ directory; clone repo and keep local copy to use for faster building of the container. 
    * `setup/zipbuild/build_container.sh` - reorganized logic to use build/ directory; also clone repo and keep copy locally to use, so no deploy key in the container itself.  
    * `.gitignore` - add `**/setup/build` so the repo clone won't be copied to itself!
    * `etc/autograder_config.ini` - added `SUBMISSIONS_PER_ASSSIGN` argument
    * `bin/autograde.py`- add a default argument for max_submissions, which is ignored unless specified [`SUBMISSIONS_PER_ASSIGN` in `etc/autograder_config.ini` is used by default]. 
    * `run_autograder` - always call `validate_submission`. If it fails, quit.

## [1.3.7] - 2023-05-23
* Changed
    * `setup/dockerbuild/deploy_container.sh` - clone repo before docker build; no more ARG with deploy key; delete after build
    * `setup/dockerbuild/Dockerfile` - use `COPY` to move the repo files over
## [1.3.6] - 2023-02-08
* Changed
    * `bin/autograde.py` - autograder's output fixed to show all results for all tests (last test with an odd number was being dropped)    
## [1.3.5] - 2022-10-26
* Changed 
    * `bin/autograde.py` - updated default `kill_limit` setting to 750. 
## [1.3.4] - 2022-9-30
* Changed
    * `bin/autograde.py` - updated autograde to be interoperable with `our_makefile=true` for some tests and `false` for others. Note that a global setting for either will break; just set the relevant setting within the test subgroup if using both for one assignment. 
## [1.3.3] - 2022-9-13
* Changed
    * `bin/autograde.py` - unicodedecodeerror fix crashing issue when student ccized / stderr has non-utf-8-decodeable text in their output. 
## [1.3.2] - 2022-9-12
* Removed
    * `assignments/` - everything removed here except for `assignments/sanity_check`
* Changed
    * `README.md` - update docs to not discuss tufts-course-specific items. 

## [1.3.1] - 2022-9-7
* Changed
    * `bin/autograde.py` - Minor updates to print more info in test summary.
* Added
    * `assignments/sanity_check` - A 'sanity check' assignment with checks for expected passing and failure cases. Good for future deployments. Put more tests here! This is of the 'arraylist' variety - perhaps add a sanity check for the 'gerp' variety of testset as well.
## [1.3.0] - 2022-9-7
* Changed
    * `bin/autograde.py` - Refactored code to not use the `capture_output=True` param of subprocess module. Problem was that if the max rlimit is passed due to a bunch of output (for instance with an infinite loop printing to cout), than the captured stream's bytes exceedes the rlimit and the autograder crashes. Instead, refactored RUN() to call subprocess.run() with stdin/stderr params; these are /dev/null if not otherwise specified. For 'regular' tests, they'll always be the default (`output/testname.stdout`, `output/testname.stderr`), and valgrind is called with `--logfile=...`, so the valgrind tests send their logs to the logfile as usual. Minor assumption here that `valgrind` tests aren't going to be checked for their `stdout` content, but based on the other structure here this is natural. This should finally fix the kerfuffle with max_ram/kill_limit being overrun. 

## [1.2.2] - 2022-9-7
* Changed 
    * `bin/autograde.py` - remove any student files that are also in the link directory prior
to symlinking. 
* Changed
    * `bin/autograde.py` - update rlimit code to limit BOTH the soft and hard limits. Should avoid crashing the autograder from now on. Fixed bug with `self.max_ram_exceeded` value being incorrectly deduced.
    * `README.md` - Minor updates.
## [1.2.1] - 2022-9-7
* Changed 
    * `README.md` - `Guest` permissions for the Gitlab PAT can't pull!
    * `setup/dockerbuild/deploy_container.sh` - fixed incorrect tag during dockerbuild step.
## [1.2.0] - 2022-8-23
* Changed
    * `setup/dockerbuild/deploy_container.sh` - updated local tag to include username and reponame; this fixes error where container wouldn't be found when trying to push to dockerhub. 
## [1.1.9] - 2022-8-21
* Changed
    * `README` - indicate that `Ubuntu 22.04` should be used in zip builds.
    * `setup/zipbuild/setup.sh` - changed clang version to clang-12; this avoids known compatibility issues with most recent clang and valgrind versions.
    * `setup/zipbuild/build_container.sh` - remove any currently existing `Autograder.zip` file, without this, every time the script runs, the size of the zip file will increase. 
## [1.1.8] - 2022-8-7
* Changed 
    * `bin/autograde.py` - set `max_ram` to be in `MB` in the `testset.toml` files to be consistent with `kill_limit` form.
    * `bin/autograde.py` - lower `max_time` to `10` seconds.
## [1.1.7] - 2022-8-1
* 'Breaking Change' related to canonicalization.
* Changed
    * `bin/autograde.py` - added `testset.toml` config variable `ccizer_args` - this is a dictionary of arguments to pass to the canonicalization function. 
    * `bin/autograde.py` - canonicalization function now takes 4 arguments instead of 1 - arguments now include:
      * student output
      * reference output
      * test name
      * canonicalizer options
These arguments will be provided by default to the canonicalization function. For backwards compatibility, change the paramters of your canonicalization function to include `*args`.
    
## [1.1.6] - 2022-7-28
* Changed 
  * `bin/autograde.py` - `autograde.py` now correctly handles the case where  `"#{testname}"` is provided as the value of the `executable` variable in the `testset.toml` file for a test.

## [1.1.5] - 2022-7-12
Substantial revision of setup configuration - updated configuation to manage secret keeping better by using environment variables for Docker configuration - some configuration variables now hold name of the environnment variable, rather than the data itself. Updated default to not use Dockerhub anymore, but rather GitHub Container registry; this avoid sketchy sharing of private info (dockercreds), and makes the docker setup more generalized (can login to any container registry with new setup).
* Created
    - `etc/docker_config.ini` - Placed docker-only configuration here
* Changed
    - `etc/autograder_config.ini` - Updated variable names, separated out docker-only variables
    - `setup/dockerbuild/deploy_container.sh` - use better secret keeping
    - `setup/zipbuild/build_container.sh` and `.../setup.sh` - use better secret keeping

## [1.1.4] - 2022-7-9
* Changed 
    - `bin/make_gradescope_results.py` - Don't crash when `diff_stderr=False` 
## [1.1.3] - 2022-6-27
* Changed
    - `bin/make_gradescope_results.py` - Don't crash when no valgrind tests. 

## [1.1.2] - 2022-6-23
* Changed 
    - `bin/autograde.py` - Changed `MAX_V_MEMORY` to `kill_limit`, which is now a configurable parameter for tests; default value is `500` `MB`; updated the preexec function setting the limit to take a parameter.
    - `bin/autograde.py` - Added `max_valgrind_score` and `valgrind_score_visibility` `[common]` only parameters. 
    - `bin/autograde.py` - Added `valg_out_of_mem` test result, which will fire if the test file is not created; this way, the autograder won't crash on valgrind being killed b/c out of ram do not producing a log file. 
    - `bin/autograde.py` - Changed reporting mechanism to output # of failed tests, and to display only failures (# segfaults, etc.) when there are any; added `Exceeded Max Ram` and `V. Exceeded Max Ram`.
    - `bin/make_gradescope_results.py` - added the valgrind test; loads the global data from the `testset.toml` file; note that the defaults for these (8, `"after_due_date"`) are set in this file - [TODO] refactor to set defaults in `autograde.py` and load them from any given test in this file?

## [1.1.1] - 2022-6-20
* Changed
    - `bin/autograde.py` - added `--errors-for-leak-kinds=none` to `valgrind` args - this will prevent
leaks from being shown as errors. Refactored scoring logic to deduce valgrind failure from combination
of no leaks/errors (no longer checking exit code).
    - `bin/autograde.py` - reformatted output to two columns for easier viewing. Added optional arg `-l`
which forces single-column output. Generally cleaned up logic of test reporting for easy add-ons later.

## [1.1.0] - 2022-6-17
* Changed
    - `bin/run_autograder` - now will replace any spaces in `$ASSIGNMENT_TITLE` with underscores. This 
will allow spaces in the gradescope title. Note that upgrading to this version requires rebuilding the container.
    - `bin/autograde.py` - negative returncode values are now handled correctly.
    - `bin/autograde.py` - fix bug where stdout/stderr diffs are attempted even though `diff_stdout` and `diff_stderr` are `false`
## [1.0.9] - 2022-6-16
* Changed
    - `bin/autograde.py` - updated default max memory usage per proc to `1GB` - valgrind was crashing at the `100MB` cap during `CalcYouLater` testing!
## [1.0.8] - 2022-6-14
* Changed
    - `bin/autograde.py` - first draft of an enforced max memory usage; separate from the `max_ram` param used for 'correctness' purposes. 
    - `README.md` - added `[TODO]` section above.

## [1.0.7] - 2022-6-13
* Changed 
    - `bin/make_gradescope_results.py` - updated code to correctly display canonicalized `stdout`/`stderr` if required.

## [1.0.6] - 2022-6-9
* Changed
    - `bin/autograde.py` - added `compiled` variable to `Test` class, and added logic to not run 
test on compilation failure. 
    - `bin/autograde.py` - changed output to compilation log files to be `utf-8` encoded strings; 
will also write binary if output from `make` is not `utf-8` encodable for whatever reason.
    - `bin/make_gradescope_results.py` - work correctly with tests that didn't compile - instead of failing, 
show the compilation log.

## [1.0.5] - 2022-6-6
* Changed
    - `bin/autograde.py` - automatically remove any `.o` files and any executables needed for testing.
    - `bin/autograde.py` - removed header comments, added [TODO] related to `Test` var which notes compilation failure - needed if we're going to try to run tests even if some didn't compile!   

## [1.0.4] - 2022-6-2
* Changed
    - `README.md` - max points note
    - `README.md` - changed arrangement of Changelog to be most recent first. 

## [1.0.3] - 2022-6-1
* Changed
    - `/bin/autograde.py` - refactored multi-processed `tqdm` with `-j 1` (default behavior) to manually run a loop instead of `process_map` with a lock - on @Marty's Mac, for whatever reason the call to `process_map` was not working correctly, and this fixes the issue.

## [1.0.2] - 2022-5-31
* Changed
    - `bin/autograde.py` - change `RUN` command option `universal_newlines=True` to `universal_newlines=False`; this will produce binary output for `result.stdout` and `result.stderr`, so changed `Path(STDOUTPATH/STDERRPATH).write_text(result.stdout/result.stderr)` to `write_bytes`. This will mean that student code which is invalid binary output will not crash program; also, `read_bytes` and decode with `utf-8` before sending to canonicalizer; write fail message to `.diff` if cannot be decoded. Note that regular `diff` on 'binary' files will work fine; as long as the text is `utf-8` encodable, 
    `diff` will function as normal; otherwise, will get 'binary files differ' message, which is good. 

## [1.0.1] - 2022-5-30
* Changed
    - `README.md` - `after-due-date` -> `after_due_date`; added discussion of `after_published`
    - `bin/autograde.py` - `after-due-date` -> `after_due_date`

## [1.0.0] - 2022-5-29
* Changed
  - `README.md`        - added changelog; fixed perl library include path instructions; clarified that `bin/`, `etc/`, `lib/` and `setup/` all `AUTOGRADING_ROOT` in the `setup/config.ini` file
  - `bin/autograde.py` - diffs now correctly save to a file [diffs were being done and incorrect output was being caught, but `.diff` files weren't being written to]; make `pretty_diff` false by default
  - `setup/dockerbuild/deploy_container.sh` - update `grep -v` instruction to exclude `REPO_REMOTE_PATH`
  - `setup/dockerbuild/Dockerfile` - copy `lib/DiffHighlight.pm` to `/usr/share/perl5`
  - `setup/zipbuild/setup.sh`      - copy `lib/DiffHighlight.pm` to `/usr/share/perl5`
  - Added `tokens` branch with token setup [currently in alpha, will use for cs-15 summer if prof. biswas wants.]
