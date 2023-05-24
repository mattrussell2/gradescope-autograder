# Gradescope Autograding Setup
Gradescope is great tool for autograding assignments. However, there is still a substantial amount
of infrastructure required to deploy and run an autograder on Gradescope. This document provides 
instructions for setting up an autograder on Gradescope which uses our in-house autograding
framework for `C/C++` code. Setup from start to finish is intended to take roughly 30 minutes.
If you have any questions, please reach out to me at `mrussell@cs.tufts.edu`, or open an issue here. 

# Infrastructure Setup

## Background
Gradescope's autograders rely on Docker containers which are spun up each time 
a submission is graded. However, there are two distinct methods with which you can interface with the containers. You will need to pick one (both are supported here).

* The `.zip` method - this workflow is to manually upload a `.zip` file containing two scripts: `setup.sh`, which installs dependencies (e.g. `Python`, `clang`, etc.), and a shell script named `run_autograder`, which runs the autograder.
* The Docker method - this workflow is to build the Docker container from scratch and upload it to the container registry of your choice.

Fear not! There is lots of starter code to do the bulk of the heavy lifting here, so either way you choose, you will likely not need to do too much setup. However, here are some pros and cons of these approaches:

* The `.zip` method requires slightly more manual work. You have to upload a new `.zip` file each time you want to update the autograder; the Docker container will then need to be built from scratch on Gradescope, which takes time. However, you don't need Docker on your system. If you're not familiar with Docker, this workflow is suggested. 
* The Docker method is more streamlined once it's setup. After uploading the container, for every assignment, you can point Gradescope to the container location - no `.zip` file uploading required. If you already use Docker, will be interested in tweaking the container's build settings (`clang` version, etc.) or are feeling adventurous, go for this option. 

## Autograding git Repo
Regardless of whether you use the `.zip` method or the Docker method you will need to create a git repository for your autograder. This repository will be used by the autograding container; whenever an assignment is autograded, the code from your repository will be pulled, the assignment's autograding files will be copied to right place, and our autograding script will run tests and produce results for Gradescope. So, if you don't currently have a repository related to course material, please make one. 
We suggest using gitlab for this: go to https://gitlab.cs.tufts.edu and 
login with `LDAP` using your Tufts eecs `utln` and password. Then create a new repository from scratch. You do not need a `README`. 
Now, in your terminal:
```
mkdir your-repo-name
cd your-repo-name
git init
git remote add origin git@gitlab.cs.tufts.edu:your_utln/your-repo-name.git
git switch -c main 
```
The repo where you're reading this `README` is the sample repo for you to start with. This repository contains:
* Our `C/C++` autograding framework.
* Files to setup assignments with either the `.zip` or Docker method, such that the autograding framework runs automatically.
* Sample autograding assignments for two different cs-15 assignments.
You can copy these files as follows:
```
git clone git@gitlab.cs.tufts.edu:mrussell/gradescope-autograding
rm -rf gradescope-autograding/.git
mv gradescope-autograding/* .
rm -rf gradescope-autograding
```
Great! Now, you will need an Access Token so your autograder can pull from the repo. To create one, go to gitlab in your browser, and navigate to the course repository you just created. Next, hover over the settings cog on the lower left, and select `Access Tokens`. Create one - this will be used by the Gradescope autograder to pull the most recent version of the autograding files for an assignment. We suggest only providing `read repository` access to the token. Feel free to select whatever you'd like for the name, expiration date, and role, however role must be at least `Developer` in order to be able to pull. Once the token is created, copy the key. 

NOTE on 'secrets': The strategy for handling sensitive data in this repository is to have all of the relevant variables be environment variables on your system. In the configuration files listed below, you will specify the *variable name* (not value), which will then be used during the build process. This enables you maximum flexibility in terms of not having sensitive data in the repo itself.

To that end, you will first need to create an environment variable with the remote path to your autograding repo, including the acess token copied above. 

Now, open your `~/.bashrc` file (or appropriate file for whichever shell you use), and add the following line at the end: 

```
export AUTOGRADING_REPO_REMOTE_PATH="https://REPOSITORY-NAME:ACCESS-TOKEN@gitlab.cs.tufts.edu/path/to/repository.git"
```
Where the appropriate substitions have been made - for example:

```
export AUTOGRADING_REPO_REMOTE_PATH="https://cs-15-2022uc:glpat-Blah8173Blah8023Blah@gitlab.cs.tufts.edu/mrussell/cs-15-2022uc.git"
```
If you don't use BASH, use the `export` variety for your shell. The default variable name in the config file for this variable is `AUTOGRADING_REPO_REMOTE_PATH`, however you can configure the variable name to be whatever you'd like (see next section for details). 

Make sure to run `source ~/.bashrc` or equivalent after editing the file.


## etc/autograder_config.ini
The file `etc/autograder_config.ini` contains various important bits of information toward deploying your autograder. Note that the values in the sample `autograder_config.ini` related to directory structure will work with the directory structure as-is in this repo, but if you change the basic directory structure, they'll be necessary. Options for the `etc/autograder_config.ini` file are as follows:

|     KEY          |        Default       |      Purpose       |
|------------------|----------------------|----------------------|
| `REPO_REMOTE_VARNAME`   |  `AUTOGRADING_REPO_REMOTE_PATH` | Variable name of the environment variable used above  |
| `AUTOGRADING_ROOT` | `""` | Path from repo root which contains `bin/`, `etc/`, `lib/`, and `setup/` |
| `ASSIGN_ROOT`      | `assignments` | Path from `AUTOGRADING_ROOT` where assignment autograding folders live |
| `ASSIGN_AUTOGRADING_SUBFOLDER` | `""` | Path from a given assignment folder which holds the autograding files for that assignment.  |
| `SUBMISSIONS_PER_ASSIGN` | 5 | Default number of submissions per assignment the student can submit; set to a large value to ignore [ NOTE: this is overridable on a per-assignment basis; see the test .toml configuation options section. ] |

NOTE! do not put any spaces around the `=` characters in this file.

Okay! now continue with one of either the `.zip` or Docker methods below.

## .zip method
As mentioned above, with the `.zip` method, you'll need to upload a `.zip` file for each 
assignment (make sure to select `Ubuntu 22.04` for the container type; the Python version, etc. are configured to work with the Jammy Jellyfish defaults). However, there is no other setup required. For the future, if you make changes to any of the files in the `dockerbuild` folder, or to `bin/run_autograder`, make sure to rebuild and re-upload the `Autograder.zip` file. 

### First-time setup with the .zip method 
* `cd setup/zipbuild && ./build_container.sh` - this will produce the necessary `Autograder.zip` file, which will be located in `setup/build/` Note: if you don't change the `setup.sh` or `run_autograder` scripts, you can re-use this file for multiple assigments. However, if you make major changes to the repo, doing a fresh build will put a newer copy into the .zip file.

### For each assignment with the .zip method
* On Gradescope, after creating the programming assignment, upload the `Autograder.zip` file in the `configure autograder' section.
* It should build and be tagged with no errors - if not, check the output of the autograder. 

## Docker method
This method takes a bit more setup in advance. 

0. If you don't have `Docker Desktop`, install it: https://www.docker.com/products/docker-desktop/. 
1. You will need to host your container somewhere. We suggest using the [GitHub container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), however if you have a 'pro' account on Dockerhub, that's also a good option. 
2. If you use the GitHub registry, make sure to share your repo with `gradescope-autograder-servers` after you upload it; if you use Dockerhub, you'll need to add `gradescopeecs` as a private collaborator to your repo.
3. See the file `etc/docker_config.ini`. You'll need to update the values of these variables as needed. Variables are as follows:

|     KEY          |        Default       |        Purpose       |
|------------------|----------------------|----------------------|
| `CONTAINER_REMOTE`   | `ghcr.io` | Which container registry you use (default is GitHub) |
| `CONTAINER_NAME`      | `gradescope-docker` | Name of the package repo that will hold your autograding docker container. |
| `CONTAINER_TAG` | `autograder-autobuild` | Tag of the container which will be used for the course's autograder. One tag will be used per course| 
| `REGISTRY_USER_VARNAME` | `GHUNAME` | Variable name of the environment variable which holds the username to login to the `CONTAINER_REMOTE`. 
| `REGISTRY_PASS_VARNAME` | `GHPAT` | Variable name of the environment variable which holds the password/access token to login to the `CONTAINER_REMOTE` [NB: The PAT needs write:packages permissions]. 

Note that in this case `GHUNAME` and `GHPAT` are the names of environment variables (NOT the values of the variables themselves). So with this example you'd need `export GHUNAME='myghubusername'` in your `~/.bashrc`, etc. Make sure to run `source ~/.bashrc` after editing the file.

### Build and deploy the container
Once you've updated the `etc/autograder_config.ini` and `etc/docker_config.ini` files with the necessary variables, and have put the necessary exports in your `~/.bashrc` file, run:
```
cd setup/dockerbuild
./deploy_container
```
The remote repo will be cloned, and then the container will be built and uploaded to the location you've specified. Note: in rare cases, the Docker build process hangs in the early stages. If this happens to you, run `rm ~/.docker/config.json` and try again. For the future, if you make changes to any of the files in the `dockerbuild` folder, or to `bin/run_autograder`, make sure to re-run this script. 

### For each assignment with the Docker method 

* On Gradescope, after creating the programming assignment, select the 'Manual Docker Configuration' option in the configure autograder' section; place the full remote path to your container (e.g. `ghcr.io/ghubusername/ghubpackageregistry:dockertag`) 
* Note that the container will pull the most recent version of the repo every time it runs...so it's a good idea to rebuild the container if you make massive changes to the repo to keep things snappy.  

That's it! 

## What happens when a student submits code
When a student submits code: 
* The Docker container is fired up on `aws` - again, note that with either method you use above, a Docker container is still used.
* The script located at `bin/run_autograder` is run.  This script (basically):
    * Runs `git pull` to get the most recent version of your autograding tests. 
    * Copies files for the assignment's autograder to `/autograder/` - the initial working directory for Gradescope's autograder.
    * Runs `autograde.py` - our autograding framework [details below]. 
    * Runs `make_gradescope_results.py`, which parses the results files and saves the results at `/autograder/results/results.json` in a form readable by Gradescope. 

**Note! The assignment name for an assignment in the course repository must be the same as the assignment name on Gradescope. An environment variable $ASSIGNMENT_TITLE is provided to our script, and this (along with the paths you specified earlier) is used to find the autograder files. If the names don't match, there will be issues. Update 6-17-2022: You may now use spaces in place of underscores on gradescope; however, the 
other text must match exactly (case sensitive).** 

## Token Management
At Tufts, we have a system for students to be able to manage late submissions with 'tokens'. The token system is flexible and generally works well. The idea is that the students maintain a bank of X tokens, where each token is effectively a 1-day extension on a given assignment. For any assignment, the maximum number of tokens a student can use is usually 2 - so up to 2 days late. 

### Postgres
Although maintaining a file in the repo is at first glance an option, the container needs write permission to the repo, which could get hairy. Likewise, unintended consequences with many students may occur. The solution presented here is Postgres. All of the connection to the server is maintained in the back-end: you only have to setup the server (free) and add a few config variables. Also note that the database URL is not stored in the git repo, and the file which contains the URL is delted in the autograding docker container prior to execution of student's code. 

The way the postgres table will be organized, there will be one row per student, with one column representing the tokens remaining ('tokens left'), and a column per assignment, which will be created automatically. The value of the assignment columns will default to 0, and will increase by 1 for each token the student uses on that assignment. Likewise, the 'tokens left' value will decrement for each token used. 

For even a few hundred students, the free 'TinyTurtle' option at ElephantSQL will work fine. 
1) Create an account at ElephantSQL and a new TinyTurtle database (free) [or, make and host a postgres db somewhere else].
2) Run the following query to build the table. With ElephantSQL you can do this in the browser.  Change the value 5 below to the number of tokens you would like your students to have for the semester. Make sure to copy everything else exactly.
```
CREATE TABLE tokens(pk NAME PRIMARY KEY, 
                    "tokens left" INTEGER DEFAULT 5);
```
3) Copy the URL for the db (in ElephantSQL this is in the details section). Add a line to your `~/.bashrc` as done in previous examples above. The default variable name is `POSTGRES_REMOTE_PATH`, although you may pick another one. The line should look like this:
```
POSTGRES_REMOTE_PATH="postgres://abcdefgh:nSgKEZiD55VdHDlzDXNBT@drona.db.elephantsql.com/abcdefgh"
```
4) Edit the variables in the etc/token_config.ini file. Make sure to set `MANAGE_TOKENS` to `"true"`. 

|     KEY          |        Default       |        Purpose       |
|------------------|----------------------|----------------------|
| `GRACE_TIME`   | `15` | Number of minutes you give the students as 'grace' when they submit |
| `TOKEN_TIME`      | `1440` | Length in minutes that one token provides (default is 24 hours). |
| `STARTING_TOKENS` | `5` | Number of tokens each student has at the start of a semester | 
| `MAX_PER_ASSIGN` | `2` | Maximum number of tokens supported for a given assignment. [NOTE: this must be 2 for now, more/less are not yet supported] | 
| `POSTGRES_REMOTE_VARNAME` | `POSTGRES_REMOTE_PATH` | Variable name of the environment variable which holds the URL of the postgres db. [NOTE!! this variable is substitued with the actual value and put into the container at build time; if you change either the value here, or the actual value of the URL in your `~/.bashrc` file, you will need to rebuild your container. This goes for both Docker and zip build methods.] |
| `MANAGE_TOKENS` | `"false"` | Whether or not to do token management [default of `"false"` will skip tokens entirely]|

Now, every time a student submits, prior to the autograder running, tokens will be checked if the assignment is late. If the token check fails, the autograder will fail immediately. You will want to let students know that in gradescope, if they click 'Submission History' at the bottom of the autograder page, they can 'activate' a different submission. Thus, they can choose which submission they would like to be used for grading. 

## Conclusion
Okay, you are ready to setup an autograder! Continue to the next section to learn about the autograding framework, and for a walkthrough to setup an assignment. 

# Autograding Framework
## Introduction
The autograding framework is designed to have you writing and deploying tests as quickly as possible. 
There are two primary forms of assignment that this autograder supports:
* Tests which are a set of `.cpp` driver files, each with its own `main()`. 
* Tests which build and run a student's completed executable program with different inputs. 

In either case, you can send a file to `stdin` for a test, and `stdout`/`stderr` will both `diff`'d automatically against the output of a reference implementation. Output can be canonicalized before `diff`, and `valgrind` can be run on the programs as well. Limits can be set for memory usage, timeout, etc. See details below.

## `testset.toml` configuration file
The framework depends on a `testset.toml` file (https://toml.io) to specify the testing configuration. `testset.toml` will be configured as follows:
```
[common]
# common test options will go here
# this section can be empty, but is mandatory
# this section must be named "common" 

[set_of_tests] 
# subsequent sections will each contain a group of tests to run
# configuration options placed here will override [common]
# test group names (e.g. [set_of_tests]) can be anything
# tests in a section must be placed in a list named `tests'
# tests = [
      {testname="test0", description="my first test"},
      {testname="test1", description="my second test"},
      ..., 
      {testname="testn", description="my nth test"},
]
# each test must have testname and description fields
# you may add any other option to a given test
# test-specific options override any 'parent' options
```
See the section `test .toml configuration options` for the full details. 

## Setup Files and Directories
These are all of the possible options, but you may not need many of them 
depending on your test configuration.
```
.
|---canonicalizers.py [file with canonicalization function(s)]
|---testrunner.sh     [script that runs `autograde`]
|---submission/       [student submission (provided by gs)]
|---testset/          [everything needed to run tests]
|   |---copy/         [files here will be copied to results/build/]
|   |---cpp/          [.cpp driver files]
|   |---link/         [files here will be symlinked in results/build/]
|   |---makefile/     [contains custom Makefile]
|   |---ref_output/   [output of reference implementation]
|   |---solution/     [solution code]
|   |---stdin/        [files here are sent to stdin]
|---testest.toml      [testing configuration file]
|-
```

## Files/Directories Created by the Autograder
```
.
|--- results/
|   |--- build/      
|   |   |--- [student submission files]
|   |   |--- [files copied from copy/ and symlinked from link/]
|   |   |--- test01   [compiled executables]
|   |   |--- ...
|   |   |--- test21
|   |--- logs/
|   |   |--- status
|   |   |--- test01.compile.log
|   |   |--- test01.summary
|   |   |--- ...
|   |   |--- test21.summary
|   |--- output/
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
|       |--- test21.valgrind
|-
```
## General Notes
* Files in `testset/stdin/` named `<testname>.stdin` (`test01.stdin`) will be sent to `stdin` for that test. 
* The `.diff`, `.ccized`, and `.valgrind` output files for each test will only be created if your configuation requires them.
* This framework supports `diff`ing against any number of output files written to by the program. Such files must be named `<testname>.ANYTHING_HERE.ofile`. The expectation is that the program will receive the name of the file to produce as an input argument. Then, in the `testset.toml` file, you will ensure that the `argv` variable includes `#{testname}.ANYTHING_HERE.ofile` in the `argv` list. See the example configuration #2 below for details. 
* Canonicalization functions which are used by the autograder in `canonicalizers.py` must:
    * Take four parameters:
        1.  A string containing the student's output from whichever stream is to be canonicalized
        2.  A string containing the reference solution's (non-canonicalized) output from whichever stream is to be canonicalized
        3.  A string containing the name of the test (e.g. `test01`)
        4.  A dictionary containing any specific test configuration options (e.g. `{'my_config_var': 10}`)
    * Return a string, which contains the canonicalized output of the student
* The `summary` files contain a dump of the state of the backend `Test` object from the `autograde.py` script - a summary is created upon initialization of the test, and is overwritten after a test finishes. All of the configuration options (e.g. `diff_stdout`, etc.)and results (e.g. `stdout_diff_passed`) are part of the `Test` object, so the `summary` files are very useful for debugging!

### Driver-based testing notes
When deploying a set of tests where each test is a unique driver file:
* Files in `testset/cpp/` named `<testname>.cpp` (`test01.cpp`) are intended to be driver files; each one will contain `main()`, and will be compiled and linked with the student's code.
* You must use a custom `Makefile`, where each test has its own target (i.e. we will run `make test01`). The `Makefile` will be run from the `results/build` directory, and will need to compile and link with the driver files which will live in the relative `../../testset/cpp` directory. See the example: `assignments/sanity_check/testset/makefile/Makefile`.
* Whenever using `our_makefile`, the target to build (e.g. `make target`) must always be named the same as the program to run (e.g. `./target`).

### Student-executable testing notes
When deploying a set of tests where students have produced a fully executable program:
* You do not need files in `testset/cpp/` (the folder is not necessary either).
* You may still choose to have your own custom `Makefile` if you wish (otherwise, be sure to set `our_makefile = false` in `testset.toml`).

## Example configurations 
### Example configuration #1
An example directory/file setup for an assignment with course-staff provided `.cpp` driver files is below

```
.
|---testrunner.sh     [script that runs `autograde`]
|---testset/          [everything needed to run tests]
|   |---cpp/          [.cpp driver files]
|   |---makefile/     [contains custom Makefile]
|   |---ref_output/   [output of reference implementation]
|   |---solution/     [solution code]
|---testest.toml      [testing configuration file]
|-
```
For this assignment, there is no canonicalization required, no input from `stdin`, nothing to copy or link to the build directory. The corresponding `testset.toml` file is as follows:

```
[common]
# using defaults! however, empty 'common' should exist

[tests]
tests = [
    { testname = "test01", description = "size 0 list to string" },
    { testname = "test02", description = "size 1 list to string"},
    { testname = "test03", description = "size 7 list to string" },
    { testname = "test04", description = "isempty test" },
    { testname = "test05", description = "isempty test2" },
    { testname = "test06", description = "clear test on empty list" },
    { testname = "test07", description = "clear test on nonempty list" },
    { testname = "test08", description = "size test"},
    { testname = "test09", description = "size test2"},
    { testname = "test10", description = "check throw on first() with empty list"},
    { testname = "test11", description = "first() test"},
    { testname = "test12", description = "check throw on last() with empty list" },
    { testname = "test13", description = "last() test2"},
    { testname = "test14", description = "elementAt test" },
    { testname = "test15", description = "elementAt test2" },
    { testname = "test16", description = "elementAt test3"},
    { testname = "test17", description = "pushAtBack" },
    { testname = "test18", description = "pushAtBack 2"},
    { testname = "test19", description = "pushAtBack 3" },
    { testname = "test20", description = "pushAtFront" },
    { testname = "test21", description = "pushAtFront2" }
    # ... more tests here ...
]
```
Here the autograder will assume that `testset/cpp/TESTNAME.cpp` contains `main()`, and that there's a target named `TESTNAME` in `testset/makefile/Makefile` which produces an executable named `TESTNAME`; it will run `make TESTNAME`, and then `./TESTNAME`.

### Example configuration #2
This is an example set of required files for an assignment which depends on a student-produced executable file. Also, it illustrates the use of canoncializer functions:
```
.
|---canonicalizers.py [file with canonicalization functions]
|---testrunner.sh     [script that runs `autograde`]
|---testset/          [everything needed to run tests]
|   |---copy/         [files to copy to build/]
|   |---link/         [files to symlink to build/]
|   |---ref_output/   [output of reference implementation]
|   |---solution/     [solution code]
|   |---stdin/        [files to send to `stdin`]
|---testest.toml      [testing configuration file]
|-
```
For this example, let's imagine we want to test the *sorted* output of student code against the *sorted* output of the reference implementation; we would then provide a function in `canonicalizers.py` to do the sorting. 

```
[common]
max_time     = 600             # 10 minutes
max_ram      = 3000            # 3GB
diff_ofiles  = true            # we will diff the output files produced by the program against the reference
ccize_ofiles = true            # canonicalize the output files before diff'ing
ccizer_name  = "sort_lines"    # use 'sort_lines' function in canonicalizers.py
our_makefile = false           # use the student's Makefile
executable   = "myprog"       # all of the tests will run this executable

[set_one]
argv  = ["myDataFile", "#{testname}.ofile"] 
tests = [
    { testname = "test01", description = "my first test },
    { testname = "test02", description = "my second test },
    { testname = "test03", description = "my third test" } 
]

[set_two] 
argv  = ["myOtherDataFile", "#{testname}.ofile"]
tests = [
    { testname = "testXX", description = "myTest", valgrind = true }, 
    { testname = "testYY", description = "myTest2" },
    { testname = "testZZ", description = "myTest3" }
    ...
]

[set_three]
valgrind  = false # for example, if for this set you didn't want to run valgrind
max_score = 2.5   # these tests are weighted more
argv = ["myThirdDataFile", "#{testname}.ofile"]
tests = [
     { testname = "test31", description = "Hello Reader!" },
     { testname = "test32", description = "Happy testing!" },
 ]
```
Notice options for custom timeout, max_ram, etc. Details for each option can be found at the end of this document. Regarding output files, the program that the students would stubmit above is expected to take two command-line arguments - the name of some data file, and the name of an output file to write. For each of the tests, `#{testname}.ofile` will be converted to `test01.ofile`, etc. If your students need to write to an output file, please have them take the name of the file as an input argument, and use this template. They can potentially write to multiple files; in the `testset.toml` file, as long the string contains `#{testname}` and ends with an `.ofile` extension, you're good to go. NOTE! To be clear, the characters "#{testname}" will actually be replaced with the full path for the autograder's output file for that test. For example, if the testname is "test01", and the output file is "test01.ofile", the full path will be something like "/home/autograder/autograder/testset/test01.ofile". This will be determined by the autograder; however, it's worth noting that #{testname} is only intended to be used in the `argv` field to refer to the output file. TODO: change the "#{testname}" to something like"#{testofpath}".

## `autograde.py`
`autograde.py` is the script that does all of the autograding. Here's the basic grading procedure:
* Parse input arguments
* Load the `testset.toml` file and validate configuration
* Create `Test` objects; each `Test` object contains all of the possible configuration variables, either customized, or the defaults. 
* Build directories required to run tests
* Compile the executable(s) specified in the configuration
* Run each test: 
    * Save the initial Test object to `results/logs/testname.summary`
    * Execute the specified command
    * Run any `diff`s required based on the testing configuration; run canonicalization prior to `diff` if specified. 
    * Run `valgrind` if required.
    * Determine whether the test passed or not
    * Save the completed Test object to `results/logs/testname.summary`
* Report the results to `stdout`.

## Testing the Autograder
### Preliminaries
In order to build reference output and test your code easily, first add the `bin/` folder to your `$PATH`. To do this, run the following commands, replacing `REPO_ROOT` with the path to the repository root on your system. 
```
echo -e "export PATH=\$PATH:/REPO_ROOT/bin\n" >> ~/.bashrc
source ~/.bashrc
```
Also, if you don't have `diff-so-fancy` installed on your system and would like to use the `pretty_diff` option then you'll want to add `REPO_ROOT/lib` to your perl library include path (either update `$PERLLIB` in `~/.bashrc` or run `perl -V` to see available locations to copy the file `etc/DiffHighlight.pm` to).

### Building the Reference Output
Once you've configured your tests, run the command 
```
build_ref_output
``` 
from the assignment's autograder directory. The reference code will be run as a submission, and the output of the reference will be placed in the `REPO_ROOT/hwname/testset/ref_output/` directory. If you need to debug your setup, run 
```
build_ref_output -k
```
This will keep the temporary directories used to run the autograder and build the reference output.

### Testing with an Example Submission
After you've produced the reference output, run the command 
```
test_autograder -s SUBMISSION_DIR
```
where `SUBMISSION_DIR` contains the submission code you would like to test. For instance, if you want to test with the solution code, run 
```
test_autograder -s testset/solution
```
This script will create a temporary testing directory named `temp_testing_dir`, copy everything there, and run the tests. You can optionally remove this directory after tests are run with the `-d` option. The `-j` option is also available [see next section]. 

### Parallel Execution of Tests
If you would like to enable parallel execution of tests, instead run 
```
autograde -j NUMCORES
```
where `NUMCORES` is the number of cores you would like to utilize (`-1` will use all available cores). Note that multiple tests may be run on each core concurrently. The default setting is for one core to be used with no tests running concurrently; that is, only one test will be run at a time (no concurrent tests are run). You can also build the reference output with parallelization by running 
```
build_ref_output -j NUMCORES
```
and, similarly, 
```
test_autograder -j NUMCORES
```

### testrunner.sh
In Gradescope's docker container, the usual `run_autograder` script runs the assignment-specific script named `testrunner.sh`, which in turn actually runs `autograde`. The reason for this extra script is to maximize flexibility; any changes made to `run_autograder` would have to both require rebuilding the container and would need to propagate across assignments. This setup, by contrast, allows you to make changes for a given assignment without having to rebuild the container/.zip file. That is to say, feel free to add extra commands before/after tests are run in `testrunner.sh`. For instance, you change the command in that file to include `-j NUMCORES` if you'd like, although on Gradescope there isn't likely much to be gained from this.

## Test .toml Configuration Options
These are the configuration options for a test. You may set any of these in `[common]`,
under a test group, or within a specific test.

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
| `pretty_diff` | `false` | use diff-so-fancy for easy-to-read diffs |
| `max_score` | `1` | maximum points (on Gradescope) for this test |
| `visibility` | `"after_due_date"` | Gradescope visibility setting |
| `argv` | `[ ]` | argv input to the program - Note: all arguments in the list must be represented as strings (e.g. ["1", "abcd"...])|
| `executable` | `(testname)` | executable to build and run |
| `max_valgrind_score` | `8` | `[common]` only setting - maximum valgrind score for this assignment [per-test valgrind score is deduced by default based on this value]. 
| `valgrind_score_visibility` | `"after_due_date"` | `[common]` only setting - visibility of the test which will hold the total valgrind points for the student. 
| `kill_limit` | `750` | `[common]` only setting - test will be killed if it's memory usage exceeds this value (in `MB`) - soft and hard rlimit_data will be set to this value in a preexec function to the subprocess call. NOTE: this parameter is specifically intended to keep the container from crashing, and thus is `[common]` only. Also, if the program exceeds the limit, it will likely receive `SIGSEGV` or `SIGABRT` from the os. Unfortunately, nothing is produced on `stderr` in this case, so while the test will likely fail based on exitcode, it's difficult to 'know' to report an exceeded memory error. However, if `valgrind` is also run and fails to produce a log file (due to also receiving `SIGSEGV`/`SIGABRT`), the test will be assumed to have exceeded max ram...in general, however, this is tricky to debug. In my experience, `valgrind` will fail to allocate memory but still produce a log file at `~50MB` of ram; any lower and no log file will be produced. The default setting of `750` `MB` should be fine for most tests, and will work with the smallest (default) container. |
| `max_submissions` | _ | `[common]` only setting - this value will override the default value of `SUBMISSIONS_PER_ASSIGN` in the `autograder_config.ini`. If not set for an assignment, the default value for this is ignored, and the `SUBMISSIONS_PER_ASSIGN` value is used instead. | 


## Visibility settings in Gradescope
Gradescope allows each test to have a different visiblity setting - the options are `hidden`, `after_due_date`, `after_published`, or `visible`. Note that if any of the options are `hidden`, none of the tests can be visible. For `cs-15`, we usually release some of the tests for the students, and so make these `visible`. However, the default is `after_due_date`. We also decided that we would like to show students their total final autograder score prior to the due date; that is, they could see their 'final score', but only a few of the actual tests. In order to facilitate this, we have added a `test00` in `bin/make_gradescope_results.py` - this is commented out by default, but if you would like to show students their final autograder score without revealing all of the test results then uncomment `#make_test00()` in the `make_results()` function (line ~250).

## Score in Gradescope
Note that if the `max_score` for a test is `0`, then Gradescope will assume that the student passes the test. There's no way around this on our end, so if you want to have 'optional' tests, then just lower the maximum score of the autograder on Gradescope (on gradescope.com - `assignment->settings->AUTOGRADER POINTS`).

# Conclusion
That should be enough to get you up and running! Please feel free to contact me with any questions you have, and/or any bugs, feature requests, etc. you find. Thanks!

# TODOS
* Update the funcationality of `bin/autograde.py` so that if a grader is re-running tests, we don't nuke the entire build folder, but intelligently load the data from alread-run tests. Also, need to verify that the various filter, etc. options work as expected. 

# Changelog
## [2.0.0] - 2023-05-24
After token and security fixes, we're at a distinctly new point - 2.0. 
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
