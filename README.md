# Gradescope Autograding Setup
Gradescope is great tool for autograding assignments. However, there is still a substantial amount
of infrastructure required to deploy and run an autograder on gradescope. This document provides 
instructions for setting up an autograder on Gradescope which uses our in-house autograding
framework for `C/C++` code. Setup from start to finish is intended to take roughly 30 minutes.
If you have any questions, please reach out to me at `mrussell@cs.tufts.edu`

# Infrastructure Setup

## Background
Gradescope's autograders rely on `Docker` containers which are spun up each time 
a submission is graded. The default container runs a variant of `Ubuntu 18.04` which contains
the bare-bones infrastructure to make Gradescope's systems function. Before diving into autograding, you will need to set up a method to integrate with Gradescope's systems. This document presents two options: 

* The `.zip` method - this workflow is to manually upload a `.zip` file 
      containing two scripts `setup.sh`, which installs dependencies (e.g. `Python`, 
      `clang`, etc.), and a shell script named `run_autograder`, which runs the autograder.
* The `Docker` method - this workflow is to build the `Docker` container from scratch and upload it to `Dockerhub`.

Fear not! There is lots of starter code to do the bulk of the heavy lifting here, so either way you choose, you will likely not need to do too much setup. However, here are some pros and cons of these approaches:

* The `.zip` method requires more manual work. You have to upload a new `.zip` file each time you want to update the autograder; the `Docker` container will then need to be built from scratch on Gradescope, which takes time. However, you don't need `Docker` on your system. If you're not familiar with `Docker`, this workflow is suggested. 
* The `Docker` method is more streamlined once it's setup. After uploading the container, for every assignment, you can point Gradescope to the container on `Dockerhub` - no `.zip` file uploading required. And, if you make minor changes to the setup script, usually rebuilding the container is very fast. All of the steps to do the building and deploying of the container are done in a script for you. If you already use `Docker`, will be interested in tweaking the `Docker` container's build settings (`clang` version, etc.) or are feeling adventurous, go for this option. 
* Gradescope's default container runs `Ubuntu 18.04`; we manually install `Python 3.9` in the container in the `setup.sh` file; the `Docker` setup we have builds `Ubuntu 22.04`, which comes with `Python 3.10` by default.

## Autograding `.git` Repo
Regardless of whether you use the `.zip` method or the `Docker` method, you will need to create a `git` repository for your autograder. This repository will be used by the autograding container; whenever an assignment is autograded, the code from your repository will be pulled, the assignment's autograding files will be copied to right place, and our autograding script will do run the tests and produce the results for Gradescope. So, if you don't currently have a repository related to course material, please make one. 
We suggest using `gitlab` for this: go to https://gitlab.cs.tufts.edu and 
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
Create one - this will be used by the Gradescope autograder to pull the most recent version of the autograding files for an assignment. We suggest only providing `read repository` access to the token. Feel free to select whatever you'd like for the name, expiration date, and role. Once the token is created, copy the key. Now, return to your repo, and open the `autograder_config.ini` file - `REPO_ROOT/etc/autograder_config.ini` and update the `REPO_REMOTE_PATH` variable as follows:

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
| `DOCKER_CREDS`     | Credentials to login to docker. [`Docker` only - see `Docker method` section for details]      |
| `DOCKER_TAG`       |  `tuftscs/gradescope-docker:YOURTAGNAME` [`Docker` only - see `Docker method` section for details] |
| `REPO_REMOTE_PATH` | `https` path to your repository |
| `ASSIGN_ROOT`      | where assignment autograding folders are relative to repo root (so if you use the structure `REPO_ROOT/assignments/(your assignments here)` then `assignments` would be placed as the value here)|
| `ASSIGN_AUTOGRADING_SUBFOLDER` | for assignments, if you put the autograder in a subfolder of the assignment folder, put the intermediate path here (so if you use the structure `REPO_ROOT/assignments/hw1_ArrayLists/autograder/(autograding files)` then `autograder` would be placed as the value here) |
| `AUTOGRADING_ROOT` | path from repo root which contains bin/ setup/ and lib/ |

NOTE! do not put any spaces around the `=` characters in this file.

The values in the sample `autograder_config.ini` will work with the directory structure as-is in this repo.
Feel free to customize the paths - for instance, if you'd like to place your assignments in the root directory of your grading repo, then update the value of `ASSIGN_ROOT` to be "". 

Okay! Assuming you've updated the `config` with the paths you'd like, and have added the `REPO_REMOTE_PATH`, continue with one of either the `.zip` or `Docker` methods below.

## .zip method
As mentioned above, with the `.zip` method, you'll need to upload a `.zip` file for each 
assignment. However, there is no other setup required. For the future, if you make changes to any of the files in the `dockerbuild` folder, or to `bin/run_autograder`, make sure to rebuild and re-upload the `Autograder.zip` file.

### For each assignment with the .zip method: 
* `cd setup/zipbuild && ./build_container.sh` - this will produce the necessary `Autograder.zip` file. Note: if you don't change the `setup.sh` or `run_autograder` scripts, you can re-use this file for multiple assigments.  
* On gradescope, after creating the programming assignment, upload the `Autograder.zip` file in the `configure autograder' section.
* It should build and be tagged with no errors - if not, check the output of the autograder. 
* Contact me if you run into trouble!

## `Docker` method
If you don't have `Docker Desktop`, install it: https://www.docker.com/products/docker-desktop/
Then, open back up the `etc/autograder_config.ini` file.
You will need to add two more things here. 

### DOCKERTAG
Update the `PUT_YOUR_TAG_HERE` in
```
tuftscs/gradescope-docker:PUT_YOUR_TAG_HERE     
```
to reflect something related to your course for the tag name (e.g. `cs-11-2022summer`).
Note that `tuftscs/gradescope-docker:` is required at the start of the value. This will be the tag that is uploaded to `Dockerhub`; Gradescope will need it to know where to find the `Docker` container to run the autograder.

### DOCKERCREDS
If you have a 'pro' account on `Dockerhub`, create your own access token and put it here - note that you'll need to add `gradescopeecs` as a private collaborator to the repository on `Dockerhub`. If you don't have a `pro` account, reach out to me at `mrussell@cs.tufts.edu`, and I'll send you the DOCKERCREDS. 
Note!! This access token must be kept private; to that end, please keep your course autograding
repository private.

### Build and upload the container to Dockerhub
Once you've updated the `autograder_config.ini` with the necessary variables, run:
```
cd dockerbuild
./deploy_container
```
The container will be built and uploaded to Dockerhub with the tag you specified. Note: in rare cases, the `Docker` build process hangs in the early stages. If this happens to you, run `rm ~/.docker/config.json` and try again. For the future, if you make changes to any of the files in the `dockerbuild` folder, or to `bin/run_autograder`, make sure to re-run this script. 

### For each assignment with the `Docker` method 

* On gradescope, after creating the programming assignment, select the 'Manual Docker Configuration' option in the configure autograder' section; place the contents of the `DOCKERTAG` variable in the box (e.g. `tuftscs/gradescope-docker:cs-11-2022summer`).

That's it! 

## What happens when a student submits code
When a student submits code: 
* The `Docker` container is fired up on `aws` - again, note that with either method you use above, a `Docker` container is still used.
* The script located at `bin/run_autograder` is run.  This script (basically):
* * Runs `git pull` to get the most recent version of your autograding tests. 
* * Copies files related to the assignment's autograder.
* * Runs our autograding framework [details below]. 
* * Saves the results at `/autograder/results/results.json` in a form readable by Gradescope. 

**Note! The assignment name for an assignment in the course repository must be the same as the assignment name on gradescope. An environment variable $ASSIGNMENT_TITLE is provided to our script, and this (along with the paths you specified earlier) is used to find the autograder files. If the names don't match, there will be issues.** 

## Conclusion
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

## Example configurations 
### Example configuration for hw1_ArrayLists
The hw1_ArrayLists assignment requires students to write an `ArrayList` class - thus, we want our autograding setup to be a set of `.cpp` files, each with `main()`. The example `testset` directory in  `assignments/hw1_ArrayLists/` is structured as follows:

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
For this assignmnent, there is no canonicalization required, no input from `stdin`, nothing to copy or link to the build directory. The corresponding `testset.toml` file is as follows:

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
]
```
Here the autograder will assume that `testset/cpp/TESTNAME.cpp` contains `main()`, and that there's a target named `TESTNAME` in `testset/makefile/Makefile` which produces an executable named `TESTNAME`; it will run `make TESTNAME`, and then `./TESTNAME`.

### Example configuration for gerp
This assignment requires students to build a program named `gerp`, which mirrors a subset of functionality from `grep`. The students provide their own implementations and `Makefile`. For this assignment, the example `testset` directory in  `assignments/gerp` is structured as follows:
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
For this assignmnent, we want to test the *sorted* output of student code against the *sorted* output of the reference implementation; thus, there is a function named `sort_lines` in `canonicalizers.py` which is used by the autograder. Also, there are library files which the students will need that are in `copy/`. There is a large set of directories which it's easier to link, so those are in `link/`. For each test, there will need to be a unique input to `stdin`, so those files are in `stdin/` (named `testname.stdin`). The corresponding `testset.toml` file is as follows:

```
[common]
max_time     = 600             # 10 minutes
max_ram      = 8000000         # 8GB
diff_ofiles  = true            # we will diff the output files produced by the program against the reference
ccize_ofiles = true            # canonicalize the output files before diff'ing
ccizer_name  = "sort_lines"    # use 'sort_lines' function in canonicalizers.py
our_makefile = false           # use the student's Makefile
executable   = "gerp"          # all of the tests will run this executable

[tiny]
argv  = ["tinyData", "#{testname}.ofile"] 
tests = [
    { testname = "test01", description = "Tiny Sensitive - we", visibility = "visible"},
    { testname = "test02", description = "Tiny Sensitive - COMP15" },
    { testname = "test03", description = "Tiny Insensitive - @i remember", visibility = "visible" },
    { testname = "test04", description = "Tiny Insensitive - @i i" },          
    { testname = "test05", description = "Tiny Insensitive - @i pretty" }, 
    { testname = "test06", description = "Tiny Insensitive - @i gibberish" },
    { testname = "test07", description = "Tiny Tricky - grep!", visibility = "visible" },
    { testname = "test08", description = "Tiny Tricky - 40?" },
    { testname = "test09", description = """Tiny Tricky - \u0022Tree-Mendous""" },
    { testname = "test10", description = """Tiny Tricky - @i don\u0027t""" }
]

[small] 
argv  = ["smallGutenberg", "#{testname}.ofile"]
tests = [
    { testname = "test11", description = "Small Gutenberg Sensitive - student", valgrind = true }, 
    { testname = "test12", description = "Small Gutenberg Sensitive - Jumbo", visibility = "visible"},
    { testname = "test13", description = "Small Gutenberg Sensitive - Easier" },    
    { testname = "test14", description = "Small Gutenberg Sensitive - texts" },
    { testname = "test15", description = "Small Gutenberg Sensitive - Civilization" },
    { testname = "test16", description = "Small Gutenberg Sensitive - bachelor" },
    { testname = "test17", description = "Small Gutenberg Insensitive - @i zoological" },
    { testname = "test18", description = "Small Gutenberg Insensitive - @i intelligent" },
    { testname = "test19", description = "Small Gutenberg Insensitive - @i parents" },
    { testname = "test20", description = "Small Gutenberg Insensitive - @i insensitive diana" },
    { testname = "test21", description = "Small Gutenberg Tricky - [*]" },
    { testname = "test22", description = "Small Gutenberg Tricky - computer\u0027s" },
    { testname = "test23", description = """Small Gutenberg Tricky - \u0022\u0027Joke!\u0027""" }, 
    { testname = "test24", description = "Small Gutenberg Tricky - A--little-bit--wild?" },
    { testname = "test25", description = "Small Gutenberg Tricky - @i {....." },
    { testname = "test26", description = "Small Gutenberg Tricky - @i www.gutenberg.org" },
    { testname = "test27", description = "Small Gutenberg Tricky - @i cometh?" },
    { testname = "test28", description = "Small Gutenberg Tricky - @i deal!" },
    { testname = "test29", description = """Small Gutenberg Tricky - @i \u0022\u0027""" },
    { testname = "test30", description = """Small Gutenberg Tricky - @i \"yours?\u0022""" }
]

[medium]
valgrind  = false # would take too long
max_score = 2.5   # these tests are weighted more
argv = ["mediumGutenberg", "#{testname}.ofile"]
tests = [
     { testname = "test31", description = "Medium Gutenberg - Time and Memory Complexity" },
     { testname = "test32", description = "Medium Gutenberg with Queries" },
 ]
```
Notice options for custom timeout, max_ram, etc. Details for each option can be found at the end of this document. Regarding output files, `gerp` expects two command-line arguments - the name of the directory to index, and a file to write output to. For each of the tests, `#{testname}.ofile` will be converted to `test01.ofile`, etc. If your students need to write to an output file, please have them take the name of the file as an input argument, and use this template. They can potentially write to multiple files; in the `testset.toml` file, as long the string contains `#{testname}` and ends with an `.ofile` extension, you're good to go.

## Testing the Autograder
### Preliminaries
In order to build reference output and test your code easily, first add the `bin/` folder to your `$PATH`. To do this, run the following commands, replacing `REPO_ROOT` with the path to the repository root on your system. 
```
echo -e "export PATH=\$PATH:/REPO_ROOT/bin\n" >> ~/.bashrc
source ~/.bashrc
```
### Building the Reference Output
Once you've configured your tests, run the command `build_ref_output` from the assignment's autograder directory. The reference code will be run as a submission, and the output of the reference will be placed in the `REPO_ROOT/hwname/testset/ref_output/` directory. If you need to debug your setup, run 
```
build_ref_output -k
```
This will keep the temporary directories used to run the autograder and build the reference output.

### Testing with an Example Submission
After you've produced the reference output, copy potential submission code to a directory named 
`submission` in the root of the homework's autograding folder (`REPO_ROOT/hwname/submission/`). Then run the command `autograde`. Results should be shown, and a `results` folder will be created. Make sure to remove `submission` and `results` before doing `git push`. [TODO write a script to run all this in a temporary directory]

### Parallel Compilation and Parallel Execution
If you would like to enable parallel compilation and parallel execution of tests, instead run 
```
autograde -j NUMCORES
```
where `NUMCORES` is the number of cores you would like to utilize (`-1` will use all available cores). Note that multiple tests may be run on each core concurrently. The default setting is for one core to be used with no tests running concurrently; that is, only one test will be run at a time (no concurrent tests are run). You can also build the reference output with parallelization by running 
```
build_ref_output.py -j NUMCORES
```
Note that on gradescope the file `testrunner.sh` is what actually runs the autograder. This is so you can have some flexibility around running the autograder without having to rebuild the container/.zip file - `run_autograder` will call this script, so feel free to add extra bash commands before/after tests are run. You change the command in that file to include `-j NUMCORES` if you'd like, although on gradescope there isn't likely much to be gained from this.

## Test .toml Configuration Options
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
| `executable` | `(testname)` | executable to build and run |

# Conclusion
That should be enough to get you up and running! Please feel free to contact me with any questions you have, and/or any bugs, feature requests, etc. you find. Thanks!
