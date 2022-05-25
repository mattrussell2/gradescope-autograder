`# gradescope autograding setup
Gradescope is great tool for autograding assignments. However, there is still a substantial amount
of infrastructure required to deploy and run an autograder on gradescope. This document provides 
instructions for setting up an autograder on Gradescope which usesour in-house autograding
framework for `C/C++` code. Setup from start to finish is intended to take roughly 30 minutes.
If you have any questions, please reach out to me at `mrussell@cs.tufts.edu`

# infrastructure setup

## background
Gradescope's autograders rely on `Docker` containers which are spun up each time 
a submission is graded. The default container runs a variant of `Ubuntu 18.04` which contains
the bare-bones infrastructure to make Gradescope's systems function. Before diving into autograding, you will need to set up a method to integrate with Gradescope's systems. This document presents two options: 

* The `.zip` method - this workflow is to manually upload a `.zip` file 
      containing two scripts `setup.sh`, which installs dependencies (e.g. `Python`, 
      `clang`, etc.), and a shell script named `run_autograder`, which runs the autograder.
* The `Docker` method - this workflow is to build the `Docker` container from scratch and upload it to `Dockerhub`.

Fear not! There is lots of starter code to do the bulk of the heavy lifting here, so either way you choose, you will likely not need to do too much setup. However, here are some pros and cons of these approaches:

* The `.zip` method requires more manual work. You have to upload
      a new `.zip` file each time you want to update the autograder; the `Docker` container 
      will then need to be built from scratch on Gradescope, which takes time. However, you don't need 
      `Docker` on your system. If you're not familiar with `Docker`, this workflow is suggested. 
* The `Docker` method is more streamlined once it's setup. After uploading the container, for every assignment, you can point Gradescope to the container on `Dockerhub` - no `.zip` file uploading required. And, if you make minor changes to the setup script, usually rebuilding the container is very fast. All of the steps to do the building and deploying of the container are done in a script for you. If you already use `Docker`, will be interested in tweaking the `Docker` container's build settings (`clang` version, etc.) or are feeling adventurous, go for this option. 

## autograding `.git` repo
Regardless of whether you use the `.zip` method or the `Docker` method, you will need to create a `git` repository for your autograder. This repository will be used by the autograding container; each time a code is autograded, the code from your repository will be pulled, the assignment's autograding files will be copied to right place, and our autograding script will do the bulk of the work running the tests and producing results. So, if you don't currently have a repository related to course material, please make one. 
We suggest using `gitlab` for this: go to https://gitlab.cs.tufts.edu, and 
login with `LDAP`, using your Tufts eecs `utln` and password. Then create a new repository from scratch. You do not need a `README`. 
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
* Files to setup assignments with either the `.zip` or `Docker` method, such that the autograding framework runs automatically.
* Sample autograding assignments for two different `cs-15` assignments.
You can copy these files as follows:
```
git clone git@gitlab.cs.tufts.edu:mrussell/gradescope-autograding
rm -rf gradescope-autograding/.git
mv gradescope-autograding/* .
rm -rf gradescope-autograding
```
Great! Now, you will need an Access Token so your autograder can pull from the repo. To create one, go to `gitlab` in your browser, and navigate to the course repository you just created. Next, hover over the settings cog on the lower left, and select `Access Tokens`.
Create one - this will be used by the Gradescope autograder to pull the most recent version of the autograding files for an assignment. We suggest only providing `read repository` access to the token. Feel free to select whatever you'd like for the name, expiration date, and role. Once the token is created, copy the key. Now, return to your repo, and open the `config.ini` file - `REPO_ROOT/setup/config.ini` and update the `REPO_REMOTE_PATH` variable as follows:

```
https://REPOSITORY-NAME:ACCESS-TOKEN@gitlab.cs.tufts.edu/path/to/repository.git
```
For example:
```
REPO_REMOTE_PATH="https://cs-15-2022uc:glpat-Blah8173Blah8023Blah@gitlab.cs.tufts.edu/mrussell/cs-15-2022uc.git"
```
Note that this path has your access token inside of it, so if you set it to have `write` permissions (not recommended) please keep your repository private!

Before we continue, let's go over the other options for this file: 

|     KEY          |        Purpose       |
|------------------|----------------------|
| `DOCKER_CREDS`     | Credentials to login to docker. [Docker only]      |
| `DOCKER_TAG`       |  `tuftscs/gradescope-docker:YOURTAGNAME` [Docker only] |
| `REPO_REMOTE_PATH` | `https` path to your repository |
| `ASSIGN_ROOT`      | where assignments autograding folders are relative to repo root |
| `ASSIGN_AUTOGRADING_SUBFOLDER` | for assignments, if you put the autograder in a subfolder of the assignment folder, put the intermediate path here (e.g. if you use the structure `REPO_ROOT/assignments/hw1_ArrayLists/autograder/(autograding files)`, then `autograder` would be placed as the value here) |
| `AUTOGRADING_ROOT` | path from repo root which contains bin/ setup/ and lib/ |

NOTE! do not put any spaces around the `=` characters in this file.

More information on the Docker options are below - as for the other options, if you plan to put only autograding material in this repo, then the defaults will likely be fine; the options may come in handy if you'd like to customize things.

For instance, if you'd like to place your assignments in the root directory of your grading repo, then update the value of `ASSIGN_ROOT` to be "". The values in the sample `config.ini` will work with the directory structure as-is in this repo.

Okay! Assuming you've updated the `config` with the paths you'd like, and have added the `REPO_REMOTE_PATH`, continue with one of either the `.zip` or `Docker` methods below.

## .zip method
As mentioned above, with the `.zip` method, you'll need to upload a `.zip` file for each 
assignment. However, there is no other setup required. 

### for each assignment with the .zip method: 
* `cd setup/zipbuild && ./build_container.sh` - this will produce the necessary `Autograder.zip` file. Note: if you don't change the `setup.sh` or `run_autograder` scripts, you can re-use this file for multiple assigments.  
* On gradescope, after creating the programming assignment, upload the `Autograder.zip` file in the `configure autograder' section.
* It should build and be tagged with no errors - if not, check the output of the autograder. 
* Contact me if you run into trouble!

## `Docker` method
If you don't have `Docker Desktop`, install it: https://www.docker.com/products/docker-desktop/
Then, open back up the `setup/config.ini` file.
You will need to add two more things here. 

### DOCKERTAG
Update the `PUT_YOUR_TAG_HERE` in
```
tuftscs/gradescope-docker:PUT_YOUR_TAG_HERE     
```
to reflect something related to your course for the tag name (e.g. `cs-11-2022summer`).
Note that `tuftscs/gradescope-docker:` is required at the start of the value. This will be the tag that is uploaded to `Dockerhub`; gradescope will need it to know where to find the `Docker` container to run the autograder.

### DOCKERCREDS
If you have a 'pro' account on `Dockerhub` ($50/yr), feel free to simply create your own access token and put it here - note that you'll need to add `gradescopeecs` as a private collaborator to the repository on `Dockerhub`. If you don't have this, reach out to 
me at `mrussell@cs.tufts.edu`, and I'll send you the file ASAP. 
Note!! This access token must be kept private; to that end, please keep your course autograding
repository private.

### build and upload the container to Dockerhub
Once you've updated the `config.ini` with the necessary variables, run:
```
cd dockerbuild
./deploy_container
```
The container will be built and uploaded to Dockerhub with the tag you specified. Note: in rare cases, the `Docker` build process hangs in the early stages. If this happens to you, run `rm ~/.docker/config.json` and try again. For the future, if you make changes to any of the files in the `dockerbuild` folder, or to `bin/run_autograder`, make sure to re-run this script. 

### to-dos per assignment with the `Docker` method 

* On gradescope, after creating the programming assignment, select the 'Manual Docker Configuration' option in the configure autograder' section; place the contents of the `.dockertag` file in the box (e.g. `tuftscs/gradescope-docker:cs-11-2022summer`).

That's it! 

## what happens when a student submits code
When a student submits code: 
* The `Docker` container is fired up on `aws`
* The script located in the repo at `bin/run_autograder` is run.  This script (basically):
* * Runs `git pull` to get the most recent version of your autograding tests. 
* * Copies files related to the assignment's autograder.
* * Runs our autograding framework [details below]. 
* * Saves the results at `/autograder/results/results.json` in a form readable by Gradescope. 

**Note! The assignment name for your autograder for an assignment in the course repository must be the same as the assignment name on gradescope. An environment variable $ASSIGNMENT_TITLE is provided to our script, and this (along with the paths you specified earlier) is used to find the autograder files. If the names don't match, there will be issues.** 

### Conclusion
Okay, you are ready to setup an autograder! Continue to the next section to learn 
about the autograding framework, and for a walkthrough to setup an assignment. 

# Autograding Framework
## Introduction
The autograding framework is designed to have you writing and deploying tests as quickly as possible. 
There are two primary forms of assignment that this autograder supports:
* Tests which are a set of `.cpp` files, each with `main()`. 
* Tests which test a student's executable program. 
In either case, you can send a file to `stdin` for a test; `stdout` and `stderr` will be `diff`'d automatically against the output of a reference implementation. Output can be canonicalized before `diff`, and `valgrind` can be run on the programs as well. More details will follow. 

## testset.toml configuration file
The framework depends on a `testset.toml` file (https://toml.io/en/) to specify the testing configuration. `testset.toml` will be configured as follows:
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
|---testrunner.sh     [script that runs this file]
|---submission/       [student submission (provided by gs)]
|---testset/          [everything needed to run tests]
|   |---copy/         [files here will be copied to results/build/]
|   |---cpp/          [.cpp driver files]
|   |---link/         [files here will be symlinked in results/build/]
|   |---makefile/     [contains custom Makefile]
|   |---ref_output/   [output of reference implementation]
|   |---solution/     [solution code]
|   |---stdin/        [files here are sent to stdin]
|---testest.toml       [testing configuration file]
|-
```

## Files/Directories Created by the Autograder
```
.
|--- results/
|   |--- build/      
|   |   |--- File.cpp [student submission files]
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
## Important Notes
* Files in `stdin/` named `<testname>.stdin` (`test01.stdin`) will be sent via `stdin` for that test. 
* Files in `.cpp/` named `<testname>.cpp` (`test01.cpp`) will each contain `main()`, and will be compiled and linked with the student's code.
* If you plan to use files in `.cpp`, you must use a custom `Makefile` - see the example: `assignments/hw1_ArrayLists/testset/makefile/Makefile`.
* If the students are writing programs which have their own `main()`, then you do not need files in `.cpp` - you may still choose to have your own custom `Makefile` if you wish (otherwise, be sure to set `our_makefile = false` in `testset.toml`). 
* The target to build (e.g. `make target`) must be named the same as the program to run (e.g. `./target`).
* Canonicalization functions which are used by the autograder in `canonicalizers.py` must:
* * take a single parameter - this will be a string containing the student's output from whichever stream is to be canonicalized
* * return a string, which contains the canonicalized output 
* The `.diff`, `.ccized`, and `.valgrind` output files for each test will only be created if your configuation requires them.
* This framework supports `diff`ing against any number of output files written to by the program. Such files must be named `<testname>.ANYTHING_HERE.ofile`. The expectation is that the program will receive the name of the file to produce as an input argument. Then, in the `testset.toml` file, you will ensure that the `argv` variable includes `#{testname}.ANYTHING_HERE.ofile` in the `argv` list. See the `gerp` example: `assignments/gerp/testset.toml`. 
* The `summary` files are a dump of the state of a Test object - a summary is created upon initialization of the test, and is overwritten after a test completes with all the information about the test. All of the configuration options are there for a given test, so this is very useful for debugging!


## How to Build Reference Output
Once you've configured your tests, you can build the reference output as follows:
```
cd path/to/repo/root/bin
python3 build_ref_output.py -p path/to/assignment/autograder/
```
The reference code will be run as a submission, and the output of the reference will be placed in 
the `REPO_ROOT/hwname/testset/ref_output/` directory. If you need to debug your setup, run 
```
python3 build_ref_output.py -p path/to/assignment/autograder/ -k
```
This will keep the temporary directories used to run the autograder. 

[TODO] - make this smoother.

### Testing an Autograder Locally
After you've produced the reference output, copy a potential submission code to a directory named 
`submission` in the autograder folder (`REPO_ROOT/hwname/submission/`). Then run 
```
python3 path/to/repo/root/bin/autograde.py
```

### Parallel Compilation and Parallel Execution
If you would like to enable parallel compilation and parallel execution of tests, instead run 
```
python3 path/to/repo/root/bin/autograde.py -j NUMCORES
```
where `NUMCORES` is the number of cores 
you would like to utilize (`-1` will use all available cores). Note that multiple tests may be 
run on each core concurrently. The default setting is for one core to be used with no tests running 
concurrently; that is, only one test will be run at a time (no concurrent tests are run). You can
also build the reference output with parallelization by running 
```
python3 build_ref_output.py -p path/to/assignment/autograder/ -j NUMCORES
```
Note that on gradescope the file `testrunner.sh` is what actually runs the autograder. This is so you can have some flexibility around running the autograder without having to rebuild the container/zip file - `run_autograder` will call this script, so feel free to add extra bash commands before/after tests are run. You 
change the command in that file to include `-j NUMCORES` if you'd like, although on 
gradescope there isn't likely much to be gained from this.  

### Test .toml Configuration Options
These are the configuration options for a test. You may set any of these in `[common]`,
under a test group, or within a specific test.

| option | default | pupose | 
|---|---|---|
| `max_time` | `30` | maximum time (in seconds) for a test |
| `max_ram` | `-1` (unlimited) | maximum ram (in kb) for a test |
| `valgrind` | `true` | run an additional test with valgrind |
| `diff_stdout` | `true` | test diff of student vs. reference stdout |
| `diff_stderr` | `true` | test diff of student vs. reference stderr |
| `diff_ofiles` | `true` | test diff of student vs. reference output files |
| `ccize_stdout` | `false` | diff canonicalized stdout instead of stdout |
| `ccize_stderr` | `false` | diff canonicalized stderr instead of stderr |
| `ccize_ofiles` | `false` | diff canonicalized ofiles instead of ofiles |
| `ccizer_name` | `""` | name of canonicalization function to use |
| `our_makefile` | `true` | use testset/makefile/Makefile to build tests |
| `pretty_diff` | `true` | use diff-so-pretty for easy-to-ready diffs |
| `max_score` | `1` | maximum points (on gradescope) for this test |
| `visibility` | `"after-due-date"` | gradescope visibility setting |
| `argv` | `[ ]` | argv input to the program |
| `executable` | `None` | executable to build and run |

# Conclusion
That should be enough to get you up and running! Please feel free to contact me with any questions you have, and/or any bugs, feature requests, etc. you find. Thanks!
