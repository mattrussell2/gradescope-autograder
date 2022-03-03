#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

CONFIG = None


# Get current working directory. This is /autograder on Gradescope and
# /tmp/autograder-XXXXXX  on Halligan
cwd = os.getcwd()

# The paths we need for dummy_results.json and results.json
source_path   = os.path.join(cwd, "source")
dummy_results = os.path.join(source_path, "dummy_results.json")
result_path   = os.path.join(cwd, "results")
result_json   = os.path.join(result_path, "results.json")

# Executable python script update_results.py
update_results_prog = os.path.join(source_path, "update_results.py")



"""
                            Main
"""

def main(tests, filters=[], action=None):
    """Runs tests

    Args:
        tests (list[str]): list of test nam
        filters ([type], optional): [description]. Defaults to None.
        action ([type], optional): [description]. Defaults to None.
    """
    # Change umask so all created files + directories are group rwx
    os.umask(0o007)

    filteredtestset = getSelectedTests(CONFIG.testset, tests, filters)

    if not filteredtestset["tests"]:
        return

    dispatchTable = {
        None: [setup, ensureCompiled, run_tests, report_tests],
        "--status": [printStatuses],
        "--diff": [printDiffs],
        "--valgrind": [printValgrindLogs],
        "--compileLog": [printCompileLogs],
        "--compileCMD": [printMakeCommands]
    }

    # Run all steps in order
    for func in dispatchTable[action]:
        func(filteredtestset)

    # Copy dummy_results.json to /cwd/results/results.json
    shutil.copy(dummy_results, result_json)

    # Run update_results.py to generate results.json for Gradescope
    subprocess.run(update_results_prog)


def setup(testset):
    # Assert that necessary directories exist
    for x in CONFIG.toMkdir():
        Path(x).mkdir(exist_ok=True, parents=True, mode=0o770)

    # Clone directories into staging area
    for source, destination in CONFIG.toClone():
        clone(source, destination)

    # Dump a filtered json into the temptestsetdir.
    # Allows TAs to specify which tests to run
    with (CONFIG.temptestsetdir / "testset.json").open('w') as f:
        json.dump(testset, f, indent=4)


def make_args(target):
    args = [target, '-C', str(CONFIG.stagingdir)]
    if target not in CONFIG.studentexecutables:
        # Use staff makefile instead
        args += ['-f', str(CONFIG.makefile)]
    return args


def ensureCompiled(testset):
    allExec = {x["program"] for x in testset["tests"]}
    if CONFIG.studentexecutables and not CONFIG.makefile:
        raise AssertionError(
            "Must specify a makefile for executables not built by student"
        )

    # Arguments for make
    cmds = [
        args for args in (make_args(e) for e in allExec) if not isMade(*args)
    ]
    if len(cmds) == 0:
        return

    sectionHeader("Compiling {0} executable", len(cmds))

    pbarFormat = 'Compiled: {n_fmt}/{total_fmt} |{bar}| {elapsed}'
    with tqdm(total=len(cmds), bar_format=pbarFormat, file=sys.stdout) as pbar:
        for args in cmds:
            didCompile = make(*args)
            pbar.update(didCompile)

    warnings = sum(
        compileLogHasWarnings(CONFIG.programCompileLog(x))
        for x in set(t["program"] for t in testset["tests"])
    )

    if warnings:
        print("\n" + str(warnings) + " executable(s) compiled with warnings")

    # Race conditions if multiple make invocations build the same dependency
    # Would use make's "-j" option, but then can't output to log file
    # with ThreadPoolExecutor() as executor:
    #     futures = {executor.submit(make, *x[0], **x[1]) for x in args}
    #     for future in tqdm(as_completed(futures), total=len(args)):
    #         try:
    #             future.result()
    #         except AssertionError as e:
    #             print(e)
    #             sys.exit(1)

    print()


def run_tests(testset):
    sectionHeader("Running {0} test", len(testset["tests"]))

    def initNumFinished():
        lastModified = lambda x: x.stat().st_mtime_ns if x.exists() else -1
        summary = CONFIG.testSummary
        running = {
            summary(x): lastModified(summary(x))
            for x in testset["tests"]
        }
        # Framework writes a summary for each test. A modified summary ==
        # test is done
        return lambda: sum(
            bool(running.pop(k)) for k in list(running)
            if running[k] != lastModified(k)
        )

    numFinished = initNumFinished()

    progressbar = tqdm(
        total=len(testset["tests"]),
        bar_format='Completed: {n_fmt}/{total_fmt} |{bar}| {elapsed}',
        file=sys.stdout
    )

    cmd = [
        str(x) for x in (
            "python3", CONFIG.testframeworkroot / "run_tests.py",
            CONFIG.temptestsetdir, CONFIG.stagingdir, "-nproc", cpu_count()
        )
    ]
    # halligan has a newer version of valgrind in /usr/bin,
    # newer versions of valgrind don't report the 72,704.
    # Which lets noah's framework correctly show that there's no errors
    valgrindENV = dict(os.environ, PATH="/usr/bin:" + os.environ["PATH"])
    framework = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=valgrindENV
    )

    # Run the tests
    with framework, progressbar:
        # Spinlock while tests are running
        while framework.poll() is None:
            progressbar.update(numFinished())
        # Make sure tests ran successfully
        if framework.returncode != 0:
            print("Error: \n" + framework.communicate()[0].decode())
            sys.exit(1)

    print()


def check_style():
    def studentFiles(*predicates):
        yield from (
            f for f in CONFIG.studentroot.iterdir()
            if f.is_file() and all(p(f) for p in predicates)
        )

    notHidden = lambda path: path.name[0] != "."
    notTxt    = lambda path: not path.name.lower().endswith('.txt')
    notObjectFile = lambda path: path.name[-2:] != ".o"
    notExec = lambda path: path.name not in CONFIG.studentexecutables

    def notOneOf(*filenames):
        return lambda path: path.name not in filenames

    def maxCols(path):
        proc = subprocess.run(
            ["wc", "-L", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        return int(proc.stdout.decode().split(maxsplit=1)[0])

    over80 = {
        file: cols
        for file, cols in ((f, maxCols(f)) for f in studentFiles(notHidden,
                                                                 notObjectFile,
                                                                 notExec,
                                                                 notTxt))
        if cols > 80
    }

    hasTabs = {
        file
        for file in studentFiles(notHidden, notExec, notOneOf("Makefile"))
        if subprocess.run(["grep", "-qP", "\t", str(file)]).returncode == 0
    }

    runTODO = lambda x: subprocess.run(
        ["grep", "-n", "TODO", str(x)], stdout=subprocess.PIPE
    )
    hasTodo = {
        file: proc.stdout.decode()
        for file, proc in ((f, runTODO(f)) for f in studentFiles(notHidden))
        if proc.returncode == 0
    }

    numProblems = sum(bool(b) for b in [over80, hasTabs, hasTodo])
    if numProblems != 0:
        sectionHeader("Potential Style Issue", numProblems)

    if over80:
        print("\n    Files over 80 cols: ")
        for file, cols in over80.items():
            print("            {0}: {1}".format(file.name, cols))

    if hasTabs:
        print("\n    Tabs found in: ")
        for file in hasTabs:
            print("            " + file.name)

    if hasTodo:
        print("\n    TODO found in: ")
        for file, output in hasTodo.items():
            print("            {0}:".format(file.name))
            for line in output.splitlines():
                print("                    " + line)


def report_tests(testset):
    """Reports the outcome of the tests

    Args:
        testset (dict): The testset that was run
    """
    #    print("== Results ==")

    subprocess.run(
        map(
            str, [
                "python3", CONFIG.testframeworkroot / "report_results.py",
                "-format", "comp40",
                *[CONFIG.testSummary(x) for x in testset["tests"]]
            ]
        )
    )
    check_style()


def testsetIterator(func):
    def toReturn(testset):
        for test in testset["tests"]:
            func(test)

    return toReturn


def printStatuses(testset):
    outcomes = {}

    for test in testset["tests"]:
        testname = (test["name"] + "(" + test["description"] + ")")
        key = " has not been run."
        if CONFIG.testSummary(test).exists():
            with CONFIG.testSummary(test).open() as f:
                s = json.load(f)
                key = "PASSED" if s["success"] == "PASSED" else s["reason"]
        outcomes.setdefault(key, []).append(testname)

    for key in sorted(outcomes):
        for testname in outcomes[key]:
            print(key, "<->", testname)


@testsetIterator
def printDiffs(test):
    glob = test["name"] + ".*"
    ref = CONFIG.temptestsetdir
    results = CONFIG.resultsdir
    commonfiles = set(f.name for f in ref.glob(glob)).intersection(
        f.name for f in set(results.glob(glob))
    )
    cmdOptions = [["code", "-d", "--wait"], ["icdiff", "-N"], ["diff"]]
    # cmdOptions = [['vimdiff', '+colorscheme apprentice']]

    # Get first available option
    cmd = next((c for c in cmdOptions if shutil.which(c[0])), None)

    print((test["name"] + "(" + test["description"] + ")"))
    for file in sorted(commonfiles):
        import filecmp
        if filecmp.cmp(str(ref / file), str(results / file)):
            continue
        if cmd[0] == "code":
            print(file, "| Close file to continue")
        subprocess.run([*cmd, str(ref / file), str(results / file)])
        if cmd[0] != "code":
            input("Press enter to continue")
            print()
    print()


@testsetIterator
def printCompileLogs(test):
    print((test["name"] + "(" + test["description"] + ")"), end=None)
    if not CONFIG.compileLog(test).exists():
        return print(" has not been compiled.")
    with CONFIG.compileLog(test).open() as f:
        return print("\n\n" + f.read(), end="\n\n")


@testsetIterator
def printValgrindLogs(test):
    print((test["name"] + "(" + test["description"] + ")"), end=None)
    if not CONFIG.valgrindLog(test).exists():
        return print(" has not been run with valgrind.")
    with CONFIG.valgrindLog(test).open() as f:
        return print("\n\n" + f.read(), end="\n\n")


@testsetIterator
def printMakeCommands(test):
    print(
        "{0} -> make {1}".format(
            test["name"], ' '.join(make_args(test["program"]))
        )
    )


"""
                            Utils
"""


def clone(src: Path, dest: Path):
    """Recursively clones src to dest, preserving metadata
       Assumes that there exist no cycles

    Args:
        src (Path): The source directory
        dest (Path): The destination directory
    """
    src = Path(src)
    dest = Path(dest)
    if src.is_dir():
        dest.mkdir(exist_ok=True)
        for child in src.iterdir():
            clone(child, (dest / child.name))
    else:
        # Copy metadata so speed up compilation (make detects no change)
        shutil.copy2(*map(str, [src, dest]), follow_symlinks=True)


def make_cmd(func=None, *, defaultargs=[]):
    """
        Decorator to generate specialized make commands

        Args:
            func ((mkTarget, mkCmd, mkExitCode, mkOutput) -> T):
                A function which accepts the target, command, exit code, and
                output of make
            defaultargs (list[str]): Arguments that are always forwarded to make
        Returns:
            function ((mkTarget, *args) -> T): 
                A function  which accepts the make target and variadic number 
                of arguments, and returns the result of applying `func`
    """
    def specializedDecorator(f):
        def inner(target, *args):
            """
                Invokes `make` for specified target and arguments, and 
                forwards info to decorated function

                Args:
                    target: make target
                    *args (str): Arguments to forward to the make command
                Returns
                    Result of applying decorated function to the 
                    make target, command, exit code, and output
            """
            cmd = map(str, ["make", target, *args, *defaultargs])
            cp = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            return f(target, cmd, cp.returncode, cp.stdout.decode())

        return inner

    return specializedDecorator if func == None else specializedDecorator(func)


@make_cmd(defaultargs=["-q"])
def isMade(target, cmd, exitcode, stdouterr):
    """Checks if target is made

    Returns:
        bool: True if make terminated succesfully, false otherwise
    """
    return exitcode == 0


@make_cmd
def make(target, cmd, exitcode, stdouterr):
    """Runs `make target`,

    Args:
        target (str): The rule's target
        cmd (list[str]): The original make command
        exitcode (int): Make's exit code
        stdouterr (str): Merged stdout and stderr of make

    Returns:
        bool: True if make was successful
    """
    # log make output
    with CONFIG.programCompileLog(target).open("w") as logfile:
        print(stdouterr, file=logfile)

    return exitcode == 0


def failed(test):
    if not CONFIG.testSummary(test).exists():
        return False

    with CONFIG.testSummary(test).open() as f:
        return json.load(f)["success"] != "PASSED"


def getSelectedTests(testset, testnames, filters):
    testnames = set(testnames)
    isNamed = lambda x: len(testnames) == 0 or x["name"] in testnames

    filtersFn = {
        "failed": failed,
        "cmpwarning": compiledWithWarnings,
        "cmperror": compiledWithErrors,
        "memerror": hasMemoryError,
        "memleak": hasMemoryLeak,
    }

    predicates = [filtersFn[x] for x in filters if x in filtersFn] + [isNamed]
    return dict(
        testset,
        tests=[t for t in testset["tests"] if all(p(t) for p in predicates)]
    )


def compileLogHasWarnings(compilelog):
    if not compilelog.exists():
        return False
    with compilelog.open() as f:
        return any(re.match(r".+:\d+:\d+: warning:", line) for line in f)


def compileLogHasErrors(compilelog):
    if not compilelog.exists():
        return False
    with compilelog.open() as f:
        return any(re.match(r".+:\d+:\d+: error:", line) for line in f)


def compiledWithWarnings(test):
    return compileLogHasWarnings(CONFIG.compileLog(test))


def compiledWithErrors(test):
    return compileLogHasErrors(CONFIG.compileLog(test))


def hasMemoryLeak(test):
    if not CONFIG.valgrindJson(test).exists():
        return False
    with CONFIG.valgrindJson(test).open() as f:
        return any(
            value != 0
            for key, value in json.load(f).items() if key != "Errors"
        )


def hasMemoryError(test):
    if not CONFIG.valgrindJson(test).exists():
        return False
    with CONFIG.valgrindJson(test).open() as f:
        return json.load(f)["Errors"] != 0


def sectionHeader(formatstring, num):
    print("== " + formatstring.format(num) + "s =="[num == 1:])


def parseArgs(args=None):
    """Parses program's arguments

    Returns:
        argparse.Namespace: parsed args
    """
    args = sys.argv[1:] if args is None else args
    tests = [test["name"] for test in CONFIG.testset["tests"]]
    action = {
        "--status": "Show the success status",
        "--valgrind": "Shows the valgrind output",
        "--diff": "Shows diff between output and reference",
        "--compileLog": "Shows the compile logs",
        "--compileCMD": "Shows the command used to compile test"
    }

    parser = argparse.ArgumentParser()
    actions = parser.add_argument_group("Actions", "--action can be one of")
    xorGroup = actions.add_mutually_exclusive_group(required=False)

    for a, helpmsg in action.items():
        xorGroup.add_argument(
            a, dest="action", help=helpmsg, action="store_const", const=a
        )

    parser.add_argument(
        "--filter",
        dest="filters",
        action="append",
        default=[],
        choices=["failed", "cmpwarning", "cmperror", "memerror", "memleak"]
    )
    # nargs="*" + choices is broken, must specify no args is OK despite "*"
    parser.add_argument(
        "tests", nargs="*", choices=[*tests, []], metavar="testname"
    )

    def desugar(args):
        """ De-sugars each occurence of
                "--action:FILTER" into  "--action --filter FILTER"
        """
        for arg in args:
            argSplit = arg.split(":", 1)
            if len(argSplit) == 1 or not argSplit[0] in action:
                yield arg
            else:
                yield from (argSplit[0], "--filter", argSplit[1])
    return parser.parse_args(list(desugar(args)))


def config(
    *,
    testingroot,
    testframeworkroot,
    testsetdir,
    studentroot,
    studentexecutables,
    makefile=None
):
    """Configures nmtestrunner with paths to required resources. Must be called
       before running

    Args:
        testingroot (Path): Directory to that will house all testing output
        testframeworkroot (Path): Path to noah mendelsohn's framework
        testsetdir (Path): Path to testset for framework
        studentroot (Path): Path to student's code
        studentexecutables (Path): Executables the student is responsible for (assumes a makefile in studentroot)
        makefile (Path): Staff makefile that builds executables student isn't responsible for 
    """
    global CONFIG
    CONFIG = Config(**locals())


class Config:
    def __init__(
        self, testingroot, testframeworkroot, testsetdir, studentroot,
        studentexecutables, makefile
    ):
        self.testingroot = Path(testingroot)
        self.testframeworkroot = Path(testframeworkroot)
        self.testsetdir = Path(testsetdir)
        self.studentroot = Path(studentroot)
        self.makefile = None if makefile is None else Path(makefile).absolute()
        self.studentexecutables = set(
            studentexecutables if studentexecutables else []
        )
        #
        # Computed properties
        #
        with (self.testsetdir / "testset.json").open() as f:
            self.testset = json.load(f)

        self.compilelogdir = self.testingroot / "compileLogs"
        # Where all executables will be located
        self.stagingdir = self.testingroot / "student.1"
        # Copy of testset dir with a replaced testset.json
        self.temptestsetdir = self.testingroot / self.testsetdir.name
        # Where the framework puts all the testing results
        # (stdout, stderr, exitcodes, valgrind, etc...)
        self.resultsdir = Path(
            str(self.stagingdir) + '.test_results'
        ) / self.testsetdir.name
        # Where the framework puts all the testing summaries
        # (stdout, stderr, exitcodes, valgrind, etc...)
        self.summarydir = Path(
            str(self.stagingdir) + '.test_summaries'
        ) / self.testsetdir.name

    def programCompileLog(self, programName):
        return self.compilelogdir / (programName + ".log")

    def compileLog(self, test):
        return self.programCompileLog(test["program"])

    def testSummary(self, test):
        return self.summarydir / (test["name"] + '.summary.json')

    def valgrindJson(self, test):
        return self.resultsdir / (test["name"] + '.valgrind.json')

    def valgrindLog(self, test):
        return self.resultsdir / (test["name"] + '.valgrindlog')

    def toMkdir(self):
        yield self.testingroot
        yield self.compilelogdir
        yield self.stagingdir
        yield self.temptestsetdir

    def toClone(self):
        yield (self.studentroot, self.stagingdir)
        yield (self.testsetdir, self.temptestsetdir)


# """
#                     Main
# """

# if __name__ == "__main__":
#     main(**vars(parseArgs()))
