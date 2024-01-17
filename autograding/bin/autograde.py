#!/usr/bin/env python3
"""
autograde.py 
matt russell
5-17-2022
"""

import os
import pwd
import grp
import sys
import subprocess
import argparse
import shutil
import traceback
import toml as tml
from pathlib import Path
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Callable
from pprint import pprint
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from multiprocessing import cpu_count, Lock
from filelock import FileLock
import traceback
from functools import reduce, partial
import resource
from rich.console import Console
from rich.table import Table, Column
from rich import print as rprint
from rich import box
from collections.abc import Iterable
if 'canonicalizers.py' in os.listdir():
    sys.path.append(os.getcwd())
    import canonicalizers

# colors for printing to terminal
RED         = "31m"
GREEN       = "32m"
YELLOW      = "33m"
BLUE        = "34m"
CYAN        = "36m"
MAGENTA     = "35m"
LGRAY       = "37m"
START_COLOR = "\033[1;"
RESET_COLOR = "\033[0m"

CWD = os.path.abspath(".")

SUBMISSION_DIR = f"{CWD}/submission"
RESULTS_DIR    = f"{CWD}/results"
TESTSET_DIR    = f"{CWD}/testset"

REF_OUTPUT_DIR = f"{TESTSET_DIR}/ref_output"
TEST_CPP_DIR   = f"{TESTSET_DIR}/cpp"
LINK_DIR       = f"{TESTSET_DIR}/link"
COPY_DIR       = f"{TESTSET_DIR}/copy"
LINK_DIR       = f"{TESTSET_DIR}/link"
STDIN_DIR      = f"{TESTSET_DIR}/stdin"

BUILD_DIR      = f"{RESULTS_DIR}/build"
LOG_DIR        = f"{RESULTS_DIR}/logs"
OUTPUT_DIR     = f"{RESULTS_DIR}/output"

MAKEFILE_PATH  = f"{TESTSET_DIR}/makefile/Makefile"

MEMLEAK_PASS   = "All heap blocks were freed -- no leaks are possible"
MEMERR_PASS    = "ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)"
VALG_NO_MEM    = "Valgrind's memory management: out of memory"


def COLORIZE(s, color):
    return f"{START_COLOR}{color}{s}{RESET_COLOR}"


def INFORMF(s, stream, color):
    stream.write(COLORIZE(s, color))
    stream.flush()


def INFORM(s, color):
    print(COLORIZE(s, color))


def RUN(cmd_ary,
        timeout=5,
        stdin=None,
        input=None,
        cwd=".",
        capture_output=False,
        universal_newlines=False,
        preexec_fn=None,
        stdout=None,
        stderr=None,
        user=None, 
        group=None, 
        extra_groups=None):
    """
        Runs the subprocess module on the given command and returns the result.

        Parameters:
            cmd_ary (list) : list of command and options to run
            timeout (int)  : timeout in seconds
            stdin (string) : file to send to stdin, or None
            input (string) : any text to send to stdin [use this xor stdin]
            cwd   (string) : current working directory for the command

        Returns:
            (completedProcess) : the result of the completed subprocess module

        Notes:
            Always capture output; universal newlines = False so binary output okay.
            Always add a timeout argument - this is adjustable in the .toml file
            Subprocess module when setting user will NOT set the group information!
    """
    # Set group information (used for student user)
    if user is not None:                
        gname = pwd.getpwnam(user).pw_name
        group = grp.getgrnam(gname).gr_gid
        extra_groups = []

    return subprocess.run(["timeout", str(timeout)] + cmd_ary,
                          stdin=stdin,
                          capture_output=capture_output,
                          universal_newlines=universal_newlines,
                          cwd=cwd,
                          input=input,
                          preexec_fn=preexec_fn,
                          stdout=stdout,
                          stderr=stderr,
                          user=user,
                          group=group, 
                          extra_groups=extra_groups)

def FAIL(s):
    INFORM(s, color=RED)
    exit(1)


@dataclass
class TestConfig:
    max_time: int = 10
    max_ram: int = -1
    max_score: int = 1

    ccize_stdout: bool = False
    ccize_stderr: bool = False
    ccize_ofiles: bool = False
    ccizer_name: str = ""
    ccizer_args: dict = field(default_factory=dict)

    diff_stdout: bool = True
    diff_stderr: bool = True
    diff_ofiles: bool = True

    valgrind: bool = True
    pretty_diff: bool = True
    our_makefile: bool = True
    exitcodepass: int = 0
    visibility: str = "after_due_date"               # gradescope setting
    argv: List[str] = field(default_factory=list)

    # assignment-widfe ([common]) settings - note that all besides kill_limit are not even
    # referenced in this file, however they still must be listed here. If they
    # are not, a TypeError is raised indicating that the TestConfig __init__
    # fails when any of these fields are specified in the TOML - 2/25/2023 slamel01
    kill_limit: int = 5900
    max_valgrind_score: int = 8
    valgrind_score_visibility: str = "after_due_date"
    style_check: bool = False

    max_submissions: int = 1
    # default = [...] doesn't work, need to use default_factory that just has a lambda return some specified [...]
    max_submission_exceptions: dict = field(default_factory=dict)
    required_files: List[str] = field(default_factory=list)

    # only used for manual mode
    exec_command: str = ""

    # These will be assigned to a test by the time it finshes execution
    # could keep these as part of the 'Test' class, but it's easier
    # to load a test from file by throwing all the variables into the config.
    compiled:            bool = None
    success:             bool = None
    valgrind_passed:     bool = None
    ofile_file_exists:   bool = None
    stdout_diff_passed:  bool = None
    stderr_diff_passed:  bool = None
    fout_diffs_passed:   bool = None
    timed_out:           bool = None
    memory_errors:       bool = None
    memory_leaks:        bool = None
    valg_out_of_mem:     bool = None
    segfault:            bool = None
    max_ram_exceeded:    bool = None
    kill_limit_exceeded: bool = None
    exit_status:         int = None
    description:         str = None
    testname:            str = None
    executable:          str = None
    fpaths:              dict = field(default_factory=dict)

    # this is set as the function with the name provided in the .toml file
    # it must:
    #   * live in the 'canonicalizers.py' file
    #   * take one argument, which is the filename of a test output
    #   * return a string, which is the result of canonicalization
    canonicalizer: Callable[[str], str] = None

    def update(self, **kwargs):
        """
            Purpose:
                Updates values of myself with the key-value pairs in kwargs
        """
        for (key, value) in kwargs.items():
            setattr(self, key, value)
        return self

    def mergecopy(self, **kwargs):
        """
            Purpose: 
                Returns a deep copy of myself, updated with the parmeters provided.
            Parameters: 
                kwargs (key-value pairs) : a list of key-value pairs to update              
            Returns: 
                The updated copy
        """
        return deepcopy(self).update(**kwargs)


class Test:

    # when our servers have python 10, we'll use inheritance with dataclasses...
    # this works for now.
    def __init__(self, config):
        for (key, value) in vars(config).items():
            if key != "tests":               # a 'Test' shouldn't contain any information about other Tests.
                setattr(self, key, value)

        # note: output files dealt with at runtime
        self.fpaths = {
            "stdin"       : f"{STDIN_DIR}/{self.testname}.stdin",
            "stdout"      : f"{OUTPUT_DIR}/{self.testname}.stdout",
            "stderr"      : f"{OUTPUT_DIR}/{self.testname}.stderr",
            "stdout.diff" : f"{OUTPUT_DIR}/{self.testname}.stdout.diff",
            "stderr.diff" : f"{OUTPUT_DIR}/{self.testname}.stderr.diff",
            "valgrind"    : f"{OUTPUT_DIR}/{self.testname}.valgrind",
            "memtime"     : f"{OUTPUT_DIR}/{self.testname}.memtime",
            "ref_stdout"  : f"{REF_OUTPUT_DIR}/{self.testname}.stdout",
            "ref_stderr"  : f"{REF_OUTPUT_DIR}/{self.testname}.stderr",
        }

        # B -> MB;  setrlimit uses Bytes
        self.kill_limit = self.kill_limit * 1024 * 1024

        # KB -> MB; /usr/bin/time -o %M uses KB
        if self.max_ram != -1:
            self.max_ram *= 1024

        # can only get here if the test has compiled, so True by default
        # however, if exec_command is set, we want manual mode, so compilation is irrelevant
        self.compiled = True if not self.exec_command else None

        # chami fix
        if not self.exec_command:
            self.executable = './' + (self.executable if self.executable else self.testname)

        self.replace_placeholders_in_self()

        if vars(config)["ccizer_name"] != "":
            self.canonicalizer = getattr(canonicalizers, vars(config)["ccizer_name"])

    def replace_placeholders(self, value_s):
        """
            Purpose:
                Given either a list of values, or a value from the .toml file
                make any necessary substitutions of `.toml variables`.                 
                This supports lists of lists of lists....but not dictionaries
            Note: 
                #{name} shouldn't be used anymore, but keeping it for backwards compatibility
        """
        replacements = {
            "${test_ofile_path}" : f"{OUTPUT_DIR}/{self.testname}",
            "${testname}"        : self.testname,

            # these are legacy
            "#{testname}"        : f"{OUTPUT_DIR}/{self.testname}",
            "#{name}"            : f"{OUTPUT_DIR}/{self.testname}",
        }
        if isinstance(value_s, str):
            for replacement_k, replacement_v in replacements.items():
                value_s = value_s.replace(replacement_k, replacement_v)
        elif isinstance(value_s, Iterable) and not isinstance(value_s, dict):
            value_s = [self.replace_placeholders(v) for v in value_s]
        return value_s

    def replace_placeholders_in_self(self):
        """
            Purpose:
                Replaces all placeholders from the .toml file (e.g. ${testname} ) with the correct stuff.
            Note!
                Assumes no dictionaries in .toml.
        """
        for (key, value) in vars(self).items():
            if isinstance(value, Iterable) and \
               not isinstance(value, dict) and \
               not isinstance(value, str):
                value = [self.replace_placeholders(v) for v in value]
            else:
                value = self.replace_placeholders(value)
            setattr(self, key, value)

    def __repr__(self):
        return (repr(vars(self)))

    def save_status(self, finished=False):
        """
            Purpose:
                saves
                    1) the status of a test to the status file. 
                    2) the variables of the test in a summary file.
            Notes:
                The status file may be concurrently written to by multiple procs, so use a lockfile.
                Replaces the actual canonicalizer function with its name so the function isn't 
                attempted to be loaded if the data is read from the file
        """
        logfile  = f"{LOG_DIR}/status"
        lockfile = f"{LOG_DIR}/status.lock"

        testid = f"{self.testname} - {self.description}"
        if finished:
            if self.success:
                line = COLORIZE(f"passed {testid}", color=GREEN)
            else:
                line = COLORIZE(f"failed {testid}", color=RED)
        else:
            line = COLORIZE(f"not run {testid}", color=CYAN)

        with FileLock(lockfile):
            lines = Path(logfile).read_text().split('\n')
            found = [i for i, line in enumerate(lines) if testid in line]

            if not found:
                lines.append(line)
            else:
                lines[found[0]] = line

            lines.sort()
            Path(logfile).write_text('\n'.join(lines))

        with open(f"{LOG_DIR}/{self.testname}.summary", 'w') as f:
            tmpvars                  = deepcopy(vars(self))
            tmpvars['canonicalizer'] = f"function: [{self.ccizer_name}]"
            pprint(tmpvars, stream=f)

    def limit_virtual_memory(self):
        resource.setrlimit(resource.RLIMIT_DATA, (self.kill_limit, self.kill_limit))

    def run_exec(self, exec_prepend=None, STDOUTPATH=None, STDERRPATH=None, user="student"):
        """
            Purpose: 
                Run self.executable from BUILD_DIR; send output streams to STDOUTPATH and STDERRPATH
            Parameters (all optional):
                exec_prepend (string) : prepend this string to the executable list [e.g. valgrind]
                STDOUTPATH   (string) : path to stdout file
                STDERRPATH   (string) : path to stderr file
            Returns: 
                Exit code of the process run
            Note:  
                If there is a testname.stdin file then it is used as stdin.                
        """
        if self.exec_command:
            exec_cmds = self.exec_command.split()
        else:
            exec_cmds = [self.executable] + self.argv

        if exec_prepend:
            exec_cmds = exec_prepend + exec_cmds

        stdin = open(self.fpaths['stdin'], 'r') if os.path.exists(self.fpaths['stdin']) else None
        
        if STDOUTPATH:
            stdout = open(STDOUTPATH, 'wb')
            stderr = open(STDERRPATH, 'wb')
        else:
            stdout = open('/dev/null', 'wb')
            stderr = open('/dev/null', 'wb')

        result = RUN(exec_cmds,
                     timeout=self.max_time,
                     stdin=stdin,
                     cwd=BUILD_DIR,
                     preexec_fn=self.limit_virtual_memory if user == "student" else None,
                     stdout=stdout,
                     stderr=stderr,
                     user=user)

        for f in [stdin, stdout, stderr]:
            if f != None:
                f.close()

        return result.returncode

    def run_test(self, user="student"):
        """
            Purpose: 
                Runs the 'standard' test and sets variables associated with pass / failure
            Notes:
                add ../../ to memtime file because we'll be running from testset/build/ directory and 
                valgrind writes to a local path. 
        """
        # always produce a memtime file - helpful for debugging. 
        prepend = ['/usr/bin/time', '-o', self.fpaths['memtime'], '-f', '%M %S %U']
        
        test_rcode = self.run_exec(exec_prepend=prepend,
                                   STDOUTPATH=self.fpaths['stdout'],
                                   STDERRPATH=self.fpaths['stderr'],
                                   user=user)

        test_rcode       = abs(test_rcode)               # returns negative value if killed by signal
        self.exit_status = test_rcode
        self.timed_out   = test_rcode == 124
        self.segfault    = test_rcode in [11, 139]

        # exitcode 134 is 'interrupted by exit code 6'
        if self.exit_status in [6, 134] and self.exitcodepass in [6, 134]:
            self.exit_status = self.exitcodepass

        self.max_ram_exceeded    = False
        self.kill_limit_exceeded = False

        # ISSUE: if process is killed, no memtime output file is produced; then we need to rely on valgrind results
        if os.path.exists(self.fpaths['memtime']):
            memdata = Path(self.fpaths['memtime']).read_text()
            if memdata != '':               # this might happen if timeout kills program
                memlines = memdata.splitlines()

                # sometimes with errors (see below), max_rss info won't be first line; guaranteed to be last line in file
                max_rss = int(memlines[-1].split()[0])  
                self.max_ram_exceeded = (self.max_ram != -1 and max_rss > self.max_ram)

                # TODO: REFACTOR THIS. Potentially add a new failure condition of uncaught exception, assuming 
                #       that the kill_limit isn't breached. 
                # signal 6 is SIGABRT; usually this is sent when kill limit is exceeded, 
                # however sometimes a program will terminate by throwing an uncaught exception, which produces SIGABRT
                # we attempt to deal with this by checking if the max_ram value is exceeded and that the program doesn't
                # expect a return code of 6; if not it's likely that
                # it's just an uncaught exception; if so, we assume kill limit is exceeded.  
                if "Command terminated by signal 6" in memlines[0] and self.exitcodepass != 6 and self.max_ram_exceeded:
                    self.kill_limit_exceeded = True

                elif "Command terminated by signal 9" in memlines[0]:
                    print("Please share the following note with a TA")
                    print("This is NOT a usual kill_limit_exceeded occurrence. If you see this, odds are that the ")
                    print("kill limit for the assignment is less than that of the container. Sometimes you just forgot ")
                    print("to up the value for a memory-heavy assignment, but other times things actually do bug out ")
                    print("on gradescope's side and the container's actual RAM value isn't what it seems. Saving an ")
                    print("'incorrect' value in the gs web interface for the assignment settings, and then saving the ")
                    print("correct value after that should fix the issue.")
                    self.kill_limit_exceeded = True
                

        # Checking for std::bad_alloc is a bit bittle.
        if not self.kill_limit_exceeded and os.path.exists(self.fpaths['stderr']):
            try:
                stderrdata = Path(self.fpaths['stderr']).read_bytes().decode('utf-8')
            except (TypeError, UnicodeDecodeError):
                stderrdata = "ERROR: non-utf-8 decodable text in student result"
            if "std::bad_alloc" in stderrdata:
                self.kill_limit_exceeded = True

    def run_valgrind(self, user="student"):
        """
            Purpose: 
                Runs the valgrind test and sets variables associated with valgrind pass / failur
            Note: 
                Valgrind will be killed by the os if memory usage exceeds kill_limit; 
                in practice, this usually only happens if the 'main' test has the same issue; 
                the 'main' test should show a segfault; here, we will set max_ram_exceeded to true
        """
        if self.valgrind:
            valgrind_command = [
                "/usr/bin/valgrind",                # doesn't have 72,704 bug
                "--show-leak-kinds=all",            # gimme all the leaks
                "--leak-check=full",                # catch all kinds of leaks
                "--errors-for-leak-kinds=none",     # separate errors from leaks
                "--error-exitcode=1",               # errors return 1
                f"--log-file={self.fpaths['valgrind']}"
            ]
            self.valgrind_rcode = self.run_exec(valgrind_command, user=user)
            if not os.path.exists(self.fpaths['valgrind']):
                self.valgrind_passed     = False
                self.memory_leaks        = False
                self.memory_errors       = True
                self.kill_limit_exceeded = True     # valgrind killed so no output file produced
                self.valg_out_of_mem     = True
            else:
                valgrind_output      = Path(self.fpaths['valgrind']).read_text()
                self.memory_leaks    = MEMLEAK_PASS not in valgrind_output
                self.memory_errors   = MEMERR_PASS not in valgrind_output
                self.valg_out_of_mem = VALG_NO_MEM in valgrind_output
                
                # if kill limit exceeded in test valgrind fails, but it can't throw errors :/
                self.valgrind_passed = not self.memory_leaks and not self.memory_errors and not self.valg_out_of_mem and not self.kill_limit_exceeded

    def run_diff(self, filea, fileb, filec, stream=None, canonicalize=False):
        """
            Purpose:
                Run diff on filea and fileb, and write the output to filec
                if 'canonicalize', run diff on canonicalized output from filea and fileb                
            Precondition: 
                Assumes filea and fileb both exist.
            Inputs:
                filea        (str)  : student output filename
                fileb        (str)  : reference output filename
                filec        (str)  : file to write diff output to
                stream       (str)  : which output stream is being diff'd 
                canonicalize (bool) : whether or not to run diff on canonicalized output.
            Returns: 
                (int) the return code of the diff.
            Notes:                
                I like pretty diffs, so icdiff is an option. :) 
                Am doing diffs with subprocess shell=True. Otherwise will have 
                problems with any non-utf8 output [encountered with largeGutenberg in gerp]. 
                [TODO] refactor to use RUN?                        
        """
        if not os.path.exists(filea):
            return 2               # diff's non-existing file return code
        
        if not os.path.exists(fileb):
            INFORM(f"reference output missing for: {self.testname} " + "- ignore if building reference output",
                   color=MAGENTA)
        
        if canonicalize:
            student_bytes = Path(filea).read_bytes()
            solution_bytes = Path(fileb).read_bytes() if os.path.exists(fileb) else None
            try:
                ccized = self.canonicalizer(student_bytes, solution_bytes, self.testname, stream, self.ccizer_args)
            except Exception as e:
                ccized = f"ERROR: canonicalizer failed - {repr(e)}\n{traceback.format_exc()}"
            if ccized == None:
                INFORM(f"canonicalizer for test {self.testname} does not return a string with the" +
                       "result - defaulting to empty string", color=MAGENTA)
                ccized = ""

            Path(f"{filea}.ccized").write_text(ccized)
            filea = f"{filea}.ccized"
            fileb = f"{fileb}.ccized"
            filec = f"{filea}.diff"               # => will be original 'filea'.ccized.diff

        # icdiff doesn't always return 1 when we expect!
        diff_result  = subprocess.run(f"diff {filea} {fileb} > {filec} 2> /dev/null", shell=True)
        diff_retcode = diff_result.returncode

        if self.pretty_diff:
            # for some wacky reason, icdiff hangs sometimes; we've opened a github issue:
            # https://github.com/jeffkaufman/icdiff/issues/213
            try:
                diff_result = subprocess.run(f"python3 -m icdiff {filea} {fileb} > {filec} 2> /dev/null", shell=True, timeout=5)
            except subprocess.TimeoutExpired:
                diff_result = subprocess.run(f"diff {filea} {fileb} > {filec} 2> /dev/null", shell=True)

        return diff_retcode


    def run_diffs(self):
        """
            Purpose:
                Runs diff tests for stdout, stderr, and any number of other output files            
            ** NOTE ** 
                Any 'other' output files must of the form: 'testname.ofile'
                These files will be written to by the student's program        
                Design here requires that student's program reads in the filename to write to 
        """
        if self.timed_out:
            return

        if self.diff_stdout:
            self.stdout_diff_passed = self.run_diff(self.fpaths['stdout'], self.fpaths['ref_stdout'],
                                                    self.fpaths['stdout.diff'], 'stdout', self.ccize_stdout) == 0

        if self.diff_stderr:
            self.stderr_diff_passed = self.run_diff(
                self.fpaths['stderr'],
                self.fpaths['ref_stderr'],
                self.fpaths['stderr.diff'],
                'stderr',
                self.ccize_stderr,
            ) == 0

        if self.diff_ofiles:
            self.fout_diffs_passed = True
            created_files          = os.listdir(REF_OUTPUT_DIR) if os.path.exists(REF_OUTPUT_DIR) else []
            created_files          = list(set(created_files + os.listdir(OUTPUT_DIR)))
            self.produced_ofiles   = [x for x in created_files if self.testname in x and x.endswith(".ofile")]
            for ofilename in self.produced_ofiles:
                retcode = self.run_diff(f"{OUTPUT_DIR}/{ofilename}", f"{REF_OUTPUT_DIR}/{ofilename}",
                                        f"{OUTPUT_DIR}/{ofilename}.diff", ofilename, self.ccize_ofiles)
                if retcode == 2:
                    setattr(self, f"{ofilename}_file_exists", False)

                setattr(self, f"{ofilename}_diff_passed", retcode == 0)
                if not retcode == 0:
                    self.fout_diffs_passed = False

    def determine_success(self):
        """
            Purpose:
                Determine whether the test passed or failed
            NOTE: 
                Valgrind failure does not count as a failure here.        
        """
        if (self.exit_status != self.exitcodepass) or \
           (self.diff_stdout and not self.stdout_diff_passed) or \
           (self.diff_stderr and not self.stderr_diff_passed) or \
           (self.diff_ofiles and not self.fout_diffs_passed) or \
           (self.max_ram_exceeded) or \
           (self.kill_limit_exceeded):
            self.success = False
        else:
            self.success = True


# def pad_emoji(text, width):
#     return text + ' ' * (width - wcswidth(text))

def report_results(TESTS, console=None):
    """
        Purpose:
            Print test results to the terminal                 
    """
    report = {
        "segfault"    : { 'test': lambda test: test.segfault,                                    'symbol': "💥", 'mitigation': "See course reference page on debugging segfaults" },
        "timeout"     : { 'test': lambda test: test.timed_out,                                   'symbol': "⏰", 'mitigation': "Infinite loop, or inefficient code" },
        "ofile diff"  : { 'test': lambda test: test.diff_ofiles and not test.fout_diffs_passed,  'symbol': "📝", 'mitigation': "Check your file output (including spaces!)" }, 
        "stdout diff" : { 'test': lambda test: test.diff_stdout and not test.stdout_diff_passed, 'symbol': "💬", 'mitigation': "Check your std::cout output (including spaces!)" },
        "stderr diff" : { 'test': lambda test: test.diff_stderr and not test.stderr_diff_passed, 'symbol': "🧯", 'mitigation': "Check your std::cerr output (including spaces!)" },
        "exit code"   : { 'test': lambda test: test.exit_status != test.exitcodepass,            'symbol': "🚪", 'mitigation': "Exit code mismatch. Usually should be EXIT_SUCCESS" },
        "max ram"     : { 'test': lambda test: test.max_ram_exceeded,                            'symbol': "💾", 'mitigation': "Program's memory usage exceeds specified limit" },
        "kill limit"  : { 'test': lambda test: test.kill_limit_exceeded,                         'symbol': "💀", 'mitigation': "Program was killed for excessive memory usage" },
        "build"       : { 'test': lambda test: not test.compiled,                                'symbol': "🔨", 'mitigation': "Unsuccessful build, or wrong executable produced" }
    } 
    FAIL_COLOR = "red"
    CHECK = "[green]:white_heavy_check_mark:[/]"
    EX    = f"[bold][{FAIL_COLOR}]:x:[/]"
    CNCL  = f"[{FAIL_COLOR}]:no_entry_sign:[/]"
    DASH  = "[bold][grey]:heavy_minus_sign:[/]"
    mitigation_table = {}
    table = Table("Test Description", 
                  Column("Result", justify="center"),
                  Column("Valgrind", justify="center"),
                  Column("Errors", justify="left"),
                  title="🧪 [blue]Test Results[/]", title_justify="left", box=box.HORIZONTALS)
    
    # Jumbo easter egg on all tests passed & passed valgrind
    if all([test.success and (test.valgrind_passed or not test.valgrind) for test in TESTS.values()]):
        CHECK = "🐘"
    
    for testname, test in TESTS.items():
        if test.success and test.valgrind_passed:
            table.add_row(f"{test.description}", CHECK, CHECK, "")
        elif test.success and not test.valgrind:
            table.add_row(f"{test.description}", CHECK, DASH if CHECK != "🐘" else "🐘", "")
        elif test.success and not test.valgrind_passed:
            if test.memory_leaks and test.memory_errors:
                table.add_row( f"{test.description}", CHECK, f":water_wave::thinking_face:", "")
            elif test.memory_leaks:
                table.add_row( f"{test.description}", CHECK, f":water_wave:", "")
            elif test.memory_errors:
                table.add_row( f"{test.description}", CHECK, f":thinking_face:", "")
        else:
            symbols = ""
            for testtype, test_mitigation_obj in report.items():
                if test_mitigation_obj['test'](test):
                    symbols += test_mitigation_obj['symbol']
            table.add_row(f"{test.description}", EX, CNCL if test.valgrind else DASH, symbols)
    
    if not console:
        console = Console(force_terminal=True)
    
    console.print(table)

    mitigation = Table(Column("Symbol", justify="center"),
                       Column("Failure Code", justify="left"), 
                       Column("Details", justify="left"),
                       box=box.HORIZONTALS)
    if CHECK == "🐘":
        mitigation.add_row("🐘", "", "You crushed it! All tests passed!")
    else:
        mitigation.add_row("✅", "Test Pass", "Nice work! Test passed")
        mitigation.add_row("❌", "Test Fail", "Test failed")
        mitigation.add_row("🚫", "No Valgrind", "Test failed, so no valgrind run [counted as valgrind fail]")
        mitigation.add_row("➖", "No Valgrind", "No valgrind for this test [not counted as valgrind fail]")
        for k, v in report.items():
            mitigation.add_row(v['symbol'], k, v['mitigation'])
        mitigation.add_row(":water_wave:", "Memory Leak", "Memory leak detected")
        mitigation.add_row(":thinking_face:", "Memory Error", "Memory error detected")
    console.print(mitigation)

def run_full_test(tup):
    test = tup[0]
    user = tup[1]
    test.save_status(finished=False)
    if not test.exec_command and not os.path.exists(os.path.join(BUILD_DIR, test.executable)):
        test.success  = False
        test.compiled = False
        test.save_status(finished=True)
    else:
        test.run_test(user=user)
        test.run_diffs()
        test.run_valgrind(user=user)
        test.determine_success()
        test.save_status(finished=True)
    return test

def run_tests(TESTS, OPTS):
    """
        Purpose:
            Runs all tests in the testset.
        Returns: 
            List of finished tests
        Notes: 
            Tests are run in parallel, on per process       
            Make sure to store result as list before returning
    """
    INFORM(f"🕐 Running {len(TESTS)} test{'s' if len(TESTS) > 1 else ''}", color=BLUE)
    user = None if OPTS["no_user"] else "student"
    if OPTS['jobs'] == 1:
        return {test.testname: run_full_test((test, user)) for test in TESTS.values()}
    else:
        result = process_map(run_full_test, [(x, user) for x in TESTS.values()], ncols=60, max_workers=OPTS['jobs'])
        return {test.testname: test for test in result}

def compile_exec(target, OPTS):
    """
        Purpose:    
            compile the target executable in BUILD_DIR    
        Parameters: 
            target to build
        Effects:    
            writes result of compilation to the right place 
        Returns:    
            whether or not the compilation was successful
    """
    if not target:
        return 0

    # if student provides executable, remove it.
    if os.path.exists(os.path.join(BUILD_DIR, target)):
        os.remove(os.path.join(BUILD_DIR, target))

    if target[:2] == './':
        target = target[2:]               # remove the './' prefix

    # REFACTOR LOGIC HERE - testname replacement should be something else after path is there.
    # if testname is the target and has been replaced, extract the name from the path
    if '/' in target or '\\' in target:
        if '/' in target: schar = '/'
        else: schar             = '\\'
        target                  = target.split(schar)[-1]

    user = None if OPTS["no_user"] else "student"

    with open(f"{LOG_DIR}/{target}.compile.log", "w") as f:
        INFORMF(f"🔨 running make {target}\n", stream=f, color=BLUE)
        compilation_proc    = RUN(["make", target], cwd=BUILD_DIR, stdout=f, stderr=subprocess.STDOUT, user=user)
        compilation_success = compilation_proc.returncode == 0
        compilation_color   = GREEN if compilation_success else RED

        if not compilation_success:
            INFORMF(f"❌ build failed\n", stream=f, color=RED)
        elif target not in os.listdir(BUILD_DIR):
            INFORMF(f"  \n'make {target}' must build a program named {target}", stream=f, color=RED)
            compilation_success = False
        else:
            INFORMF("✅ build completed successfully\n", stream=f, color=GREEN)
            RUN(["chmod", "a+x", target], cwd=BUILD_DIR, user=user)      # g++ doesn't always play nice, so chmod it

    return compilation_success


def compile_execs(TOML, TESTS, OPTS):
    """
        Purpose:
            compile the the tests    
        Parameters: 
            dictionary of Tests; testing options
        Effects:    
            runs compile_exec for each test, 
            which logs result of compilation to the right place 
        Returns:    
            True iff all of the compilations succeeded
        Notes:      
            Will copy the custom Makefile to build/ if it exists. Ignore if using exec_command [test.executable == None].
    """
    execs_to_compile     = { test.executable: test.our_makefile for test in TESTS.values() if test.executable != None }
    our_makefile_tests   = [ test for test in execs_to_compile if execs_to_compile[test] ]
    their_makefile_tests = [ test for test in execs_to_compile if not execs_to_compile[test] ]

    compiled_list = []
    num_execs     = len(execs_to_compile)
    if their_makefile_tests:
        INFORM(
            f"🔨 Building {len(their_makefile_tests)} executable{'s' if len(their_makefile_tests) >= 1 else ''} with the student's makefile",
            color=BLUE)
        compiled_list = [compile_exec(x, OPTS) for x in their_makefile_tests]

    if our_makefile_tests:
        INFORM(
            f"🔨 Building {len(our_makefile_tests)} executable{'s' if len(our_makefile_tests) >= 1 else ''} with our makefile",
            color=BLUE)
        if not os.path.exists(MAKEFILE_PATH):
            print("our_makefile option requires a custom Makefile in testset/makefile/")
        else:
            shutil.copyfile(MAKEFILE_PATH, 'results/build/Makefile')
        compiled_list += [compile_exec(x, OPTS) for x in our_makefile_tests]

    if sum(compiled_list) != num_execs:
        INFORM("❌ Some Tests Failed to Build!\n", color=RED)
        report_compile_logs(type_to_report="fail")
    else:
        print("🟢 Build successful\n")

def chmod_dir(d, permissions):
    """
        Purpose:
            chmod the testset with the provided permissions
        Notes:
            This is used so the student code doesn't overwrite read-only files
    """
    if os.path.exists(d):
        subprocess.run([f"chmod -R {permissions} {d}"], shell=True)


def build_testing_directories():
    """
        Purpose:
            Builds directories required to run tests.
        Notes: 
            These directories are hard-coded in this file - 
            there should be no need to change them.
            don't remove results_dir directly because gradescope puts the 'stdout' file there
    """
    if os.path.exists(RESULTS_DIR):
        for fldr in BUILD_DIR, LOG_DIR, OUTPUT_DIR:
            if os.path.exists(fldr):
                shutil.rmtree(fldr)

    for fldr in [RESULTS_DIR, BUILD_DIR, LOG_DIR, OUTPUT_DIR]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)

    # if submission dir doesn't have +w, we won't be able to copy anything after first copytree()
    chmod_dir(SUBMISSION_DIR, "770")

    # remove any student-provided .o files
    for f in os.listdir(SUBMISSION_DIR):
        if f.endswith('.o') or os.path.exists(os.path.join(LINK_DIR, f)):
            os.remove(os.path.join(SUBMISSION_DIR, f))

    shutil.copytree(SUBMISSION_DIR, BUILD_DIR, dirs_exist_ok=True)
    if os.path.exists(COPY_DIR):
        shutil.copytree(COPY_DIR, BUILD_DIR, dirs_exist_ok=True)
    
    if os.path.exists(LINK_DIR):
        for f in os.listdir(LINK_DIR):
            os.symlink(os.path.join('..', '..', LINK_DIR, f), os.path.join(BUILD_DIR, f))

    Path(f'{LOG_DIR}/status.lock').write_text("Lockfile for status reporting")
    Path(f'{LOG_DIR}/status').write_text("")

    # students need read access to link/stdin/cpp dirs
    chmod_dir(TESTSET_DIR, "551") 
    chmod_dir(LINK_DIR, "775")   
    chmod_dir(STDIN_DIR, "775")
    chmod_dir(TEST_CPP_DIR, "775")    
    
    # students need write access to the output/log/build dirs
    chmod_dir(OUTPUT_DIR, "777")
    chmod_dir(LOG_DIR, "777")
    chmod_dir(BUILD_DIR, "777")    


class CustomFormatter(argparse.HelpFormatter):
    """
        Argparse is great, but it's formatting options are bleh. 
        SO to the rescue - https://stackoverflow.com/a/23941599/8742968
    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return self._metavar_formatter(action, action.dest)(1)[0]
        else:
            # keep -s, --long as is
            if action.nargs == 0:
                parts = action.option_strings

            # from -s ARGS, --long ARGS
            # to   -s, --long ARGS
            else:
                parts      = [f'{opt_str}' for opt_str in action.option_strings]
                parts[-1] += f' {self._format_args(action, action.dest.upper())}'

            return ', '.join(parts)


def filter_tests(TESTS, OPTS):
    """
    Purpose:
        filter the testset to only include those provided by user, if any
    """
    if OPTS['tests']:
        TESTS = {testname: TESTS[testname] for testname in OPTS['tests']}

    if OPTS['diff'] == []:
        OPTS['diff'] = ['.stdout.diff', '.stderr.diff', '.ofile.diff']

    elif OPTS['diff'] != None:
        OPTS['diff'] = [f".{x}.diff" for x in OPTS['diff']]

    if OPTS['filter']:
        OPTS['filter'] = OPTS['filter'][0]
        get_test_var   = lambda test: test.valgrind_passed if OPTS['valgrind'] else test.success
        TESTS          = {
             name: test for name, test in TESTS.items() if \
                            get_test_var(test) and OPTS['filter'] == "passed" or \
                        not get_test_var(test) and OPTS['filter'] == "failed"
        }
    return TESTS


def validate_opt(valid_opts, OPTS, config_type, failure_string):
    """
        Purpose:
            Validates the the provided configutation options
        Effects:
            Quits with failure string if any of the options are invalid               
    """
    if not OPTS[config_type]:
        return

    for opt in OPTS[config_type]:
        if opt not in valid_opts:
            FAIL(f"{failure_string}: {opt}\nvalid options are: {valid_opts}")


def validate_opts(TESTS, OPTS):
    """
        Purpose:
            Validate input options from the user        
    """
    """
        note: argparser is weird about this; format the list
        start  -> {... 'filter': ['0,12411'],   'diff': ['21,', '1241'],'tests': ['23542,12412']}
        finish -> {... 'filter': ['0', '12411'],'diff': ['21', '1241'], 'tests': ['23542', '12412']}
    """
    for arg in OPTS:
        if type(OPTS[arg]) == list:
            OPTS[arg] = [x for y in [s.replace(',', ' ').split() for s in OPTS[arg]] for x in y]

    VALID_TEST_NAMES  = TESTS.keys()
    VALID_FILTER_OPTS = ["passed", "failed"]
    VALID_DIFF_OPTS   = ["stdout", "stderr", "ofile", " or none (all are run by default)"]

    validate_opt(VALID_TEST_NAMES, OPTS, "tests", "Invalid test name")
    validate_opt(VALID_FILTER_OPTS, OPTS, "filter", "Invalid filter option")
    validate_opt(VALID_DIFF_OPTS, OPTS, "diff", "Invalid diff option")

    return OPTS


def load_tests(TOML):
    """
        Purpose:
            Loads tests from the TOML file 
        Returns:
            A dictionary of { testname : Test }
        Notes: 
            Each test is initialized with global, group, and test-specific configuration, where any
            of the parameters in the 'narrower' configuration overrides the corresponding config
            of the 'broader' category. i.e. the test-specific config overrides the group config,
            and group config overrides the global config.
    """
    COMMON_CONFIG = TestConfig(**TOML['common'])
    TESTS         = {}
    for group in [TOML[group_name] for group_name in TOML if group_name != "common"]:
        GROUP_CONFIG = COMMON_CONFIG.mergecopy(**group)
        for tinfo in group['tests']:
            TEST_CONFIG              = GROUP_CONFIG.mergecopy(**tinfo)
            TESTS[tinfo['testname']] = Test(TEST_CONFIG)
    return TESTS


def parse_args(argv):
    """
        Purpose:
            Loads .toml file parse provided configuation options, and returns lists of Tests to run
        Notes:             
            usage: diff_test [-h] [-s] [-v] [-c] [-j jobs]  [-f [filteropt [filteropt ...]]]
                                                            [-d [diffopt [diffopt ...]]]
                                                            [-t [testXX [testXX ...]]]

            optional arguments:
            -h, --help          show this help message and exit
            -s, --status        show the success status
            -v, --valgrind      show valgrind output
            -c, --compile-logs  show the compilation logs and commands
            -j, --jobs jobs     number of parallel jobs; default=1; -1=number of available cores
            -f, --filter [filteropt [filteropt ...]]
                          one or more filters to apply: failed, cmpwarning, cmperr, memerr, memleak
            -d, --diff [diffopt [diffopt ...]]
                          show diff of one or more output streams: stdout, stderr, outfiles
            -t, --tests [testXX [testXX ...]]
                          one or more tests to run
            -n, --no-user do not run tests in group 'student' [used to build container on local system]
                        
            These args are passed in here 'as expected' i.e. flags are bools, 
            and 'filter', 'diff', and 'tests' are all lists of strings. 
    """
    HELP = {
        's' : "show the success status",
        'v' : "show valgrind output",
        'c' : "show the compilation logs and commands",
        'j' : "number of parallel jobs; default=1; -1=number of available cores",
        'f' : "one or more filters to apply: (f)ailed, (p)assed",
        'd' : "one or more diffs to show: stdout, stderr, and ofile",
        't' : "one or more tests to run",
        'l' : "show output in one column",
        'n' : "runs tests without running as student user. Used to build container on local system"
    }
    ap = argparse.ArgumentParser(formatter_class=CustomFormatter)
    ap.add_argument('-s', '--status', action='store_true', help=HELP['s'])
    ap.add_argument('-v', '--valgrind', action='store_true', help=HELP['v'])
    ap.add_argument('-c', '--compile-logs', action='store_true', help=HELP['c'])
    ap.add_argument('-l', '--lengthy-output', action='store_true', help=HELP['l'])
    ap.add_argument('-j', '--jobs', default=1, metavar="jobs", type=int, help=HELP['j'])
    ap.add_argument('-d', '--diff', nargs='*', metavar="diffopt", type=str, help=HELP['d'])
    ap.add_argument('-f', '--filter', nargs='*', metavar="filteropt", type=str, help=HELP['f'])
    ap.add_argument('-t', '--tests', nargs='*', metavar="testXX", type=str, help=HELP['t'])
    ap.add_argument('-n', '--no-user', action='store_true', help=HELP['n'])

    args = vars(ap.parse_args(argv))
    if args['jobs'] == -1:
        args['jobs'] = cpu_count()
    return args


def report_compile_logs(exitcode=None, type_to_report=None, tests=None, output_format="stdout"):
    """
        Purpose:
            Prints all of the compilation logs. Will filter by
        Args: 
            exitcode       (int)          : if provided, exit with this code
            type_to_report (string)       : [passed/failed] - will only print these logs
            tests          (list[string]) : will only print the results of compiling these execs
    """

    compile_pass = "build completed successfully"
    compile_fail = "build failed"
    build_logs   = find_logs(['.compile.log'], os.listdir(LOG_DIR), directory=LOG_DIR)

    if type_to_report:
        type_to_report = compile_pass if type_to_report == "passed" else compile_fail
        build_logs     = {f: log for f, log in build_logs.items() if type_to_report in log}

    if tests:
        build_logs = {f: log for f, log in build_logs.items() if f.split('compile.log')[0] in tests}

    build_pass_fn = lambda x: True if compile_pass in x else False
    logs = report_log(build_logs, build_pass_fn, print_header=True, output_format=output_format)
    if exitcode != None:
        exit(exitcode)
    return logs


def report_log(data_dict, success_fn, print_header=True, output_format="stdout"):
    """
        Purpose: 
            Prints a log to to the terminal 
        Args: 
            data_dict (dictionary[string,string]) : dict of the form {filename: filedata}
            success_fn (lambda x => [true,false]) : function to apply to each value of the dict 
                                                    which determines if the test passed or failed
            print_header (bool)                   : if True, print the keys of the dict. 
    """
    output_str = ""
    for header in sorted(data_dict.keys()):
        data    = data_dict[header]
        success = success_fn(data)
        if header and data and print_header:
            output_str += COLORIZE(header, color=CYAN) + '\n'
            output_str += COLORIZE(data, color=GREEN if success_fn(data) else RED) + '\n'
        elif header and not data:               # .diff files are empty == success
            output_str += COLORIZE(header, color=GREEN if success_fn(data) else RED) + '\n'
        else:
            output_str += COLORIZE(data, color=GREEN if success_fn(data) else RED) + '\n'

    if output_format == "stdout":
        print(output_str)
    else:
        return output_str


def find_logs(exts, tests_to_report, directory=OUTPUT_DIR):
    """
        Purpose: 
            Given a file extension and a subset of tests to report, return a dictionary of 
            { filename: filedata }, where filedata is the loaded text of the file.
    """
    logs = {}
    for f in os.listdir(directory):
        if any([f.endswith(ext) for ext in exts]) and any([t in f for t in tests_to_report]):
            logs[f] = Path(os.path.join(directory, f)).read_text()
    return logs


def cleanup():
    pass
    #chmod_dir(TESTSET_DIR, "770")


def run_autograder(argv):
    OPTS = parse_args(argv)

    if not os.path.exists('testset.toml'):
        FAIL("testset.toml must be in the current directory")

    TOML = tml.load('testset.toml')

    TESTS = load_tests(TOML)

    # make sure user called program correctly
    OPTS = validate_opts(TESTS, OPTS)

    # filters tests based on user options (i.e. passed/failed, -t test01, etc.)
    TESTS = filter_tests(TESTS, OPTS)

    try:
        build_testing_directories()
        compile_execs(TOML, TESTS, OPTS)
        TESTS = run_tests(TESTS, OPTS)
        print("🟢 Tests ran successfully\n")

        if OPTS['status']:
            statusfile    = Path(f"{LOG_DIR}/status").read_text().splitlines()
            filteredlines = list(filter(lambda l: any([t in l for t in TESTS]), statusfile))
            line_pass     = lambda x: True if "passed" in x else False if "failed" in x else None
            report_log({i: l for i, l in enumerate(filteredlines)}, line_pass, print_header=False)

        elif OPTS['diff']:
            dtests = find_logs(OPTS['diff'], TESTS.keys())
            report_log(dtests, lambda x: x == '')

        elif OPTS['compile_logs']:
            report_compile_logs(exitcode=0, type_to_report=OPTS['filter'], tests=TESTS.keys())

        elif OPTS['valgrind']:
            vtests     = find_logs(['.valgrind'], TESTS.keys())
            vtest_pass = lambda x: MEMERR_PASS in x and MEMLEAK_PASS in x
            report_log(vtests, vtest_pass)
        else:
            report_results(TESTS)
            visible_tests = {k: v for k, v in TESTS.items() if v.visibility == "visible"}
            out_file = f"{RESULTS_DIR}/visible_results_output.txt"
            with open(out_file, "w") as f:
                console = Console(file=f)
                report_results(visible_tests, console=console)

    except Exception as e:
        print("🔴 Error while running tests!\n")
        print(traceback.format_exc())

    finally:
        cleanup()


if __name__ == '__main__':
    run_autograder(sys.argv[1:])
