#!/usr/bin/env python3
"""
autograde.py 
matt russell
5-17-2022

[TODO] be more intelligent in terms of when to re-run tests - now am re-running every time
"""
import os
import sys
import subprocess
import argparse
import shutil
import ast
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
from collections.abc import Iterable
if 'canonicalizers.py' in os.listdir():   
    sys.path.append(os.getcwd())
    import canonicalizers

# colors for printing to terminal
RED            = "31m"
GREEN          = "32m"
YELLOW         = "33m"
CYAN           = "36m"
MAGENTA        = "35m"
LGRAY          = "37m"
START_COLOR    = "\033[1;"
RESET_COLOR    = "\033[0m"

CWD            = os.path.abspath(".")

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

def COLORIZE(s, color):
    return f"{START_COLOR}{color}{s}{RESET_COLOR}"

def INFORMF(s, stream, color):    
    stream.write(COLORIZE(s, color))

def INFORM(s, color):
    print(COLORIZE(s, color))
    
def RUN(cmd_ary, timeout=30, stdin=None, input=None, cwd=".", 
        capture_output=True,  universal_newlines=False):
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
            Always capture output and use universal newlines.
            Always add a timeout argument - this is adjustable in the .toml file
    """    
    return subprocess.run(["timeout", str(timeout)] + cmd_ary, 
                          stdin=stdin, 
                          capture_output=capture_output,                          
                          universal_newlines=universal_newlines,
                          cwd=cwd,
                          input=input)
    
def FAIL(s):
    INFORM(s, color=RED)
    exit(1)

@dataclass
class TestConfig:    
    # These are configuation options for the test
    max_time:      int  = 30 
    max_ram:       int  = -1 
    max_score:     int  = 1
        
    ccize_stdout:  bool = False
    ccize_stderr:  bool = False
    ccize_ofiles:  bool = False
    ccizer_name:   str  = ""

    diff_stdout:   bool = True
    diff_stderr:   bool = True 
    diff_ofiles:   bool = True    
    
    valgrind:      bool = True
    pretty_diff:   bool = False
    our_makefile:  bool = True        
    exitcodepass:  int  = 0
    visibility:    str  = "after_due_date" # gradescope setting    
    argv:          List[str] = field(default_factory=list)  
    
    # These will be assigned to a test by the time it finshes execution    
    # could keep these as part of the 'Test' class, but it's easier 
    # to load a test from file by throwing all the variables into the config.
    compiled:           bool = None
    success:            bool = None 
    valgrind_passed:    bool = None
    stdout_diff_passed: bool = None
    stderr_diff_passed: bool = None
    fout_diffs_passed:  bool = None
    timed_out:          bool = None
    memory_errors:      bool = None
    memory_leaks:       bool = None 
    segfault:           bool = None   
    max_ram_exceeded:   bool = None
    exit_status:        int  = None            
    description:        str  = None
    testname:           str  = None
    executable:         str  = None    
    fpaths:             dict = field(default_factory=dict)    
    
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

    def mergecopy(self, drop=None, **kwargs):
        """
            Purpose: 
                Returns a deep copy of myself, updated with the parmeters provided.
            Parameters: 
                drop (List[str])        : A list of keys to drop
                kwards (key-value pairs : a list of key-value pairs to update              
            Returns: 
                The updated copy
        """
        return deepcopy(self).update(**kwargs)

class Test:
    
    # when halligan has python 10, we'll use inheritance with dataclasses...
    # this is good for now
    def __init__(self, config):
        for (key, value) in vars(config).items():            
            if key != "tests":  # a 'Test' shouldn't contain any information about other Tests.
                setattr(self, key, value)
        
        # note: output files dealt with at runtime
        self.fpaths   = {            
            "stdin":       f"{STDIN_DIR}/{self.testname}.stdin",
            "stdout":      f"{OUTPUT_DIR}/{self.testname}.stdout",
            "stderr":      f"{OUTPUT_DIR}/{self.testname}.stderr",            
            "stdout.diff": f"{OUTPUT_DIR}/{self.testname}.stdout.diff",
            "stderr.diff": f"{OUTPUT_DIR}/{self.testname}.stderr.diff",            
            "valgrind":    f"{OUTPUT_DIR}/{self.testname}.valgrind",   
            "memory":      f"{OUTPUT_DIR}/{self.testname}.memory",     
            "ref_stdout":  f"{REF_OUTPUT_DIR}/{self.testname}.stdout",
            "ref_stderr":  f"{REF_OUTPUT_DIR}/{self.testname}.stderr",                                    
        }
       
        # can only get here if the test has compiled
        self.compiled = True 

        if self.executable == None:
            self.executable = self.testname
      
        if self.executable[0] != '/':
            self.executable = './' + self.executable

        self.replace_placeholders_in_self()

        if vars(config)["ccizer_name"] != "":
            setattr(self, "canonicalizer", getattr(canonicalizers, vars(config)["ccizer_name"]))        

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
            "#{testname}": f"{OUTPUT_DIR}/{self.testname}", 
            "#{name}":     f"{OUTPUT_DIR}/{self.testname}",
        }
        if isinstance(value_s, str):
            for replacement_k, replacement_v in replacements.items():
                value_s = value_s.replace(replacement_k, replacement_v) 
        elif isinstance(value_s, Iterable) and not isinstance(value_s, dict):
            value_s = [get_replacement_s(v) for v in value_s]
        return value_s

    def replace_placeholders_in_self(self):
        """
            Purpose:
                Replaces all placeholders from the .toml file [#{testname}] with the correct stuff.
            Note!
                Assumes no dictionaries from .toml.
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
            tmpvars = deepcopy(vars(self))            
            tmpvars['canonicalizer'] = f"function: [{self.ccizer_name}]"
            pprint(tmpvars, stream=f)

    def run_exec(self, exec_prepend=None, STDOUTPATH=None, STDERRPATH=None):
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
        exec_cmds = [self.executable] + self.argv
        if exec_prepend:
            exec_cmds = exec_prepend + exec_cmds

        if os.path.exists(self.fpaths['stdin']):            
            with open(self.fpaths['stdin'], "r") as stdin:
                result = RUN(exec_cmds, timeout=self.max_time, stdin=stdin, cwd=BUILD_DIR)
        else:
            result = RUN(exec_cmds, timeout=self.max_time, cwd=BUILD_DIR)
                
        if STDOUTPATH: Path(STDOUTPATH).write_bytes(result.stdout)
        if STDERRPATH: Path(STDERRPATH).write_bytes(result.stderr)

        return result.returncode

    def run_test(self):   
        """
            Purpose: 
                Runs the 'standard' test and sets variables associated with pass / failure
            Notes:
                add ../../ to memory file because we'll be running from the build directory
        """      
        if self.max_ram != -1:
            prepend  = ['/usr/bin/time', '-o', os.path.join('..','..',self.fpaths['memory']), '-f', '%M']
        else:
            prepend  = []

        test_rcode       = self.run_exec(exec_prepend=prepend, 
                                         STDOUTPATH=self.fpaths['stdout'], 
                                         STDERRPATH=self.fpaths['stderr'])
        self.exit_status = test_rcode
        self.timed_out   = test_rcode == 124        
        self.segfault    = test_rcode in [11, 139]
        
        self.max_ram_exceeded = False
        if os.path.exists(self.fpaths['memory']):
            memdata = Path(self.fpaths['memory']).read_text()
            if memdata != '': # this might happen if timeout kills program
                max_rss = int(memdata.splitlines()[-1]) # if segfault, last line has max_rss info
                self.max_ram_exceeded = max_rss > self.max_ram                  
      
    def run_valgrind(self):  
        """
            Purpose: 
                Runs the valgrind test and sets variables associated with valgrind pass / failure
        """         
        valgrind_command = [
            "/usr/bin/valgrind",                      # doesn't have 72,704 bug
            "--show-leak-kinds=all",                  # gimme all the leaks
            "--leak-check=full",                      # leaks -> errors
            "--error-exitcode=1",                     # errors return 1
            f"--log-file={self.fpaths['valgrind']}"
        ]
        if self.valgrind:
            self.valgrind_passed = self.run_exec(valgrind_command) == 0
            valgrind_output      = Path(self.fpaths['valgrind']).read_text()       
            self.memory_leaks    = MEMLEAK_PASS not in valgrind_output
            self.memory_errors   = MEMERR_PASS not in valgrind_output
        
    def run_diff(self, filea, fileb, filec, canonicalize=False):
        """
            Purpose:
                Run diff on filea and fileb, and write the output to filec
                if 'canoniczliaze', run diff on canonicalized output from filea and fileb                
            Precondition: 
                Assumes filea and fileb both exist.
            Inputs:
                filea        (str)  : student output filename
                fileb        (str)  : reference output filename
                filec        (str)  : file to write diff output to
                canonicalize (bool) : whether or not to run diff on canonicalized output.
            Returns: 
                (bool) Whether or not the diff succeeds
            Notes:                
                I like pretty diffs, so diff-so-fancy is an option. :) 
                Am doing diffs with subprocess shell=True. Otherwise will have 
                problems with any non-utf8 output [encountered with largeGutenberg in gerp]. 
                [TODO] refactor to use RUN?                        
        """        
        if not os.path.exists(filea):
            Path(f"{filea}.diff").write_text(f"diff: {ofilename} not found!")
            return False
        elif not os.path.exists(fileb): 
            INFORM(f"reference output missing for: {self.testname} " + 
                    "- ignore if building reference output", color=RED)

        if canonicalize:
            bytes = Path(filea).read_bytes()
            try:
                text   = bytes.decode('utf-8')                     
            except TypeError:
                ccized = "ERROR: binary output in student result"
            else:
                try:
                    ccized = self.canonicalizer(text)
                except: 
                    ccized = "ERROR: canonicalizer failed"

            Path(f"{filea}.ccized").write_text(ccized)
            filea = f"{filea}.ccized"
            fileb = f"{fileb}.ccized"
            filec = f"{filea}.diff"   # => will be original 'filea'.ccized.diff
                           
        diff_result  = subprocess.run(f"diff {filea} {fileb} > {filec}", shell=True)        
        diff_retcode = diff_result.returncode # diff-so-fancy returns 0 on failure, always use this!
       
        # diff-so-fancy requires output of [diff -u ...] as its input
        if self.pretty_diff:
            subprocess.run(f"diff -u {filea} {fileb} | diff-so-fancy > {filec}", shell=True)                            
        
        return diff_retcode == 0
    
    def run_diffs(self):
        """
            Purpose:
                Runs diff tests for stdout, stderr, and any number of other output files            
            ** NOTE ** 
                Any 'other' output files must of the form: 'testname.ofile'
                These files will be written to by the student's program        
                Design here requires that student's program reads in the filename to write to 
        """
        self.stdout_diff_passed = self.run_diff(self.fpaths['stdout'], 
                                                self.fpaths['ref_stdout'],
                                                self.fpaths['stdout.diff'], 
                                                self.ccize_stdout)
        
        self.stderr_diff_passed = self.run_diff(self.fpaths['stderr'],  
                                                self.fpaths['ref_stderr'],
                                                self.fpaths['stderr.diff'],
                                                self.ccize_stderr)
        
        self.fout_diffs_passed = True
        created_files = os.listdir(REF_OUTPUT_DIR) if os.path.exists(REF_OUTPUT_DIR) else []
        created_files = list(set(created_files + os.listdir(OUTPUT_DIR))) 
        ofilenames = [x for x in created_files if self.testname in x and x.endswith(".ofile")]                 
        for ofilename in ofilenames:
            if not self.run_diff(f"{OUTPUT_DIR}/{ofilename}", 
                                 f"{REF_OUTPUT_DIR}/{ofilename}", 
                                 f"{OUTPUT_DIR}/{ofilename}.diff",
                                 self.ccize_ofiles):
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
           (self.max_ram_exceeded):
            self.success = False
        else:
            self.success = True    

def report_testgroup(header, group, color):
    groupstr = '\n\t\t      '.join(group)
    INFORM(f"{header}: {groupstr}\n", color=color)   

def report_results(TESTS, OPTS): 
    INFORM(f"\n== Test Report ==", color=CYAN)  

    # obviously not so efficient, but easy to read.
    report = {
        "passed":          [f"{name} - {t.description}" for name,t in TESTS.items() if t.success],
        "failed":          [f"{name} - {t.description}" for name,t in TESTS.items() if not t.success],
        "passed_valgrind": [f"{name} - {t.description}" for name,t in TESTS.items() if t.valgrind and t.valgrind_passed],
        "failed_valgrind": [f"{name} - {t.description}" for name,t in TESTS.items() if t.valgrind and not t.valgrind_passed],
        "timed_out":       [f"{name} - {t.description}" for name,t in TESTS.items() if t.timed_out]
    }    
    num_valgrind = len(report['passed_valgrind']) + len(report['failed_valgrind'])
    nums = { key: f"{len(report[key]):02} / {len(TESTS) if 'valgrind' not in key else num_valgrind}" for key in report }
                
    passclr   = COLORIZE(f"Passed    {nums['passed']}",    color=GREEN)   
    failclr   = COLORIZE(f"Failed    {nums['failed']}",    color=RED)         
    tmoutclr  = COLORIZE(f"Timed Out {nums['timed_out']}", color=MAGENTA)

    print(f"{passclr}\n{failclr}\n{tmoutclr}\n")
    report_testgroup("\tPassed tests", report["passed"],    GREEN)    
    report_testgroup("\tFailed tests", report["failed"],    RED)    
    report_testgroup("\t   Timed Out", report['timed_out'], MAGENTA)

    INFORM(f"\n== Valgrind Report ==", color=CYAN)  
    passvclr = COLORIZE(f"Passed Valgrind: {nums['passed_valgrind']}", color=GREEN)
    failvclr = COLORIZE(f"Failed Valgrind: {nums['failed_valgrind']}", color=RED)
    print(f"{passvclr}\n{failvclr}\n") 
    report_testgroup("     Passed Valgrind", report['passed_valgrind'], GREEN)
    report_testgroup("     Failed Valgrind", report['failed_valgrind'], RED)

def run_full_test(test):
    test.save_status(finished=False)
    if not os.path.exists(os.path.join(BUILD_DIR, test.executable)):
        test.success  = False
        test.compiled = False
        test.save_status(finished=True)
    else:
        test.run_test()        
        test.run_diffs()    
        test.run_valgrind()    
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
    INFORM(f"\n== Running {len(TESTS)} test{'s' if len(TESTS) > 1 else ''} ==", color=CYAN)        
    if OPTS['jobs'] == 1:
        return { test.testname: run_full_test(test) for test in TESTS.values() }
    else: 
        result = process_map(run_full_test, TESTS.values(), 
                             ncols=60, max_workers=OPTS['jobs'])
        
        return { test.testname: test for test in result }
   
def compile_exec(target):
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
    # if student provides executable, remove it. 
    if os.path.exists(os.path.join(BUILD_DIR, target)):
        os.remove(os.path.join(BUILD_DIR, target))

    target = target[2:] # remove the './' prefix
    with open(f"{LOG_DIR}/{target}.compile.log", "w") as f:
        INFORMF(f"== running make {target} ==\n", f, color=CYAN)
        compilation_proc    = RUN(["make", target], cwd=BUILD_DIR)
        compilation_success = compilation_proc.returncode == 0   
        compilation_color   = GREEN if compilation_success else RED 
        
        for stream in [compilation_proc.stdout, compilation_proc.stderr]:            
            try:            
                INFORMF(stream.decode('utf-8'), stream=f, color=compilation_color) 
            except:
                INFORMF(stream, stream=f, color=compilation_color)
            
        if not compilation_success:
            INFORMF(f"\ncompilation failed\n", stream=f, color=RED)                
        elif target not in os.listdir(BUILD_DIR):
            INFORMF(f"\n'make {target}' must build a program named {target}", stream=f, color=RED)
            compilation_success = False
        else:
            INFORMF("\nbuild completed successfully\n", stream=f, color=GREEN)    
            RUN(["chmod", "u+x", target], cwd=BUILD_DIR) # g++ doesn't always play nice, so chmod it
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
            Will copy the custom Makefile to build/ if it exists.
    """ 
    execs_to_compile =    { test.executable   for test in TESTS.values() }
    our_makefile     = any([test.our_makefile for test in TESTS.values()])
    
    if our_makefile:
        if not os.path.exists(MAKEFILE_PATH):
            print("our_makefile option requires a custom Makefile in testset/makefile/")
        else:
            shutil.copyfile(MAKEFILE_PATH, 'results/build/Makefile')

    num_execs = len(execs_to_compile)
    INFORM(f"== Compiling {num_execs} executable{'s' if num_execs >= 1 else ''} ==", color=CYAN)
    if OPTS['jobs'] == 1:
        compiled_list = [compile_exec(x) for x in execs_to_compile]
    else:    
        compiled_list = process_map(compile_exec, execs_to_compile, ncols=60, max_workers=OPTS['jobs'])    

    if sum(compiled_list) != num_execs:
        INFORM(f"== Compilation Failed! ==\n", color=RED)
        report_compile_logs()                          

def chmod_dir(d, permissions):    
    """
        Purpose:
            chmod the testset with the provided permissions
        Notes:
            This is used so the student code doesn't overwrite read-only files
    """
    subprocess.run([f"chmod -R {permissions} {d}"], shell=True)       

def build_testing_directories():  
    """
        Purpose:
            Builds directories required to run tests.
        Notes: 
            These directories are hard-coded in this file - 
            there should be no need to change them.
    """ 
    # don't remove results_dir directly because gradescope puts the 'stdout' file there
    # this should be refactored.
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
        if f.endswith('.o'):
            os.remove(os.path.join(SUBMISSION_DIR, f))
            
    shutil.copytree(SUBMISSION_DIR, BUILD_DIR, dirs_exist_ok=True)
    if os.path.exists(COPY_DIR):
        shutil.copytree(COPY_DIR, BUILD_DIR, dirs_exist_ok=True)
    if os.path.exists(LINK_DIR):
        for f in os.listdir(LINK_DIR):
            os.symlink(os.path.join('..','..',LINK_DIR, f), os.path.join(BUILD_DIR, f))

    Path(f'{LOG_DIR}/status.lock').write_text("Lockfile for status reporting")
    Path(f'{LOG_DIR}/status').write_text("")
    
    # don't allow student code to write to the testset!
    chmod_dir(TESTSET_DIR, "550")

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
        TESTS = { testname: TESTS[testname] for testname in OPTS['tests'] }
    
    if OPTS['diff'] == []:        
        OPTS['diff'] = ['.stdout.diff', '.stderr.diff', '.ofile.diff']

    elif OPTS['diff'] != None:
        OPTS['diff'] = [f".{x}.diff" for x in OPTS['diff']]
    
    if OPTS['filter']: 
        OPTS['filter'] = OPTS['filter'][0]        
        get_test_var = lambda test: test.valgrind_passed if OPTS['valgrind'] else test.success
        TESTS = {
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
            OPTS[arg] = [x for y in [s.replace(',',' ').split() for s in OPTS[arg]] for x in y]
    
    VALID_TEST_NAMES  = TESTS.keys()
    VALID_FILTER_OPTS = ["passed", "failed"]
    VALID_DIFF_OPTS   = ["stdout", "stderr", "ofile", " or none (all are run by default)"]
    
    validate_opt(VALID_TEST_NAMES,  OPTS, "tests",  "Invalid test name")
    validate_opt(VALID_FILTER_OPTS, OPTS, "filter", "Invalid filter option")
    validate_opt(VALID_DIFF_OPTS,   OPTS, "diff",   "Invalid diff option")          

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
            TEST_CONFIG = GROUP_CONFIG.mergecopy(**tinfo)
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
                        
            These args are passed in here 'as expected' i.e. flags are bools, 
            and 'filter', 'diff', and 'tests' are all lists of strings. 
    """        
    HELP = {
        's': "show the success status",
        'v': "show valgrind output",
        'c': "show the compilation logs and commands",
        'j': "number of parallel jobs; default=1; -1=number of available cores",
        'f': "one or more filters to apply: (f)ailed, (p)assed",   
        'd': "one or more diffs to show: stdout, stderr, and ofile",
        't': "one or more tests to run"
    }    
    ap = argparse.ArgumentParser(formatter_class=CustomFormatter)      
    ap.add_argument('-s', '--status',       action='store_true', help=HELP['s'])
    ap.add_argument('-v', '--valgrind',     action='store_true', help=HELP['v'])
    ap.add_argument('-c', '--compile-logs', action='store_true', help=HELP['c']) 
    ap.add_argument('-j', '--jobs',     default=1, metavar="jobs",       type=int, help=HELP['j'])
    ap.add_argument('-d', '--diff',     nargs='*', metavar="diffopt",    type=str, help=HELP['d'])
    ap.add_argument('-f', '--filter',   nargs='*', metavar="filteropt",  type=str, help=HELP['f'])    
    ap.add_argument('-t', '--tests',    nargs='*', metavar="testXX",     type=str, help=HELP['t'])         

    args = vars(ap.parse_args(argv))
    if args['jobs'] == -1:
        args['jobs'] = cpu_count()
    return args
              
def report_compile_logs(exitcode=None, type_to_report=None, tests=None):
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
        build_logs = { f:log for f,log in build_logs.items() if type_to_report in log }            
    
    if tests:
        build_logs = { f:log for f, log in build_logs.items() if f.split('compile.log')[0] in tests }

    build_pass_fn  = lambda x: True if compile_pass in x else False
    report_log(build_logs, build_pass_fn, print_header=True)
    if exitcode != None:
        exit(exitcode)
    
def report_log(data_dict, success_fn, print_header=True):
    """
        Purpose: 
            Prints a log to to the terminal 
        Args: 
            data_dict (dictionary[string,string]) : dict of the form {filename: filedata}
            success_fn (lambda x => [true,false]) : function to apply to each value of the dict 
                                                    which determines if the test passed or failed
            print_header (bool)                   : if True, print the keys of the dict. 
    """
    for header in sorted(data_dict.keys()):
        data    = data_dict[header]
        success = success_fn(data)                                 
        if header and data and print_header:                
            INFORM(header, color=CYAN)  
            INFORM(data,   color=GREEN if success_fn(data) else RED)                                                                   
        elif header and not data: # .diff files are empty == success
            INFORM(header, color=GREEN if success_fn(data) else RED)
        else:
            INFORM(data,   color=GREEN if success_fn(data) else RED)
               
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
    chmod_dir(TESTSET_DIR, "770")

def run_autograder(argv):
    OPTS = parse_args(argv)

    if not os.path.exists('testset.toml'):
        FAIL("testset.toml must be in the current directory")

    TOML = tml.load('testset.toml') 
    
    #[TODO] make below feature 'work' as-expected.
    # if we've run tests already, load them in from the log files; otherwise build fresh tests
    # gradescope makes a file /autograder/results/stdout
    # if os.path.exists("results") and os.listdir("results") not in [[], ['stdout']]:
        
    #     TESTS = {}
    #     for f in [x for x in os.listdir(LOG_DIR) if x.endswith(".summary")]:
    #         fdata = Path(os.path.join(LOG_DIR, f)).read_text()             
    #         TESTS[f.split('.summary')[0]] = Test(TestConfig(**ast.literal_eval(fdata)))            
    # else:    
    TESTS = load_tests(TOML)
        
    # make sure user called program correctly    
    OPTS  = validate_opts(TESTS, OPTS)

    # filters tests based on user options (i.e. passed/failed, -t test01, etc.)
    TESTS = filter_tests(TESTS, OPTS)

    try:       
        build_testing_directories()  
        compile_execs(TOML, TESTS, OPTS)
        TESTS = run_tests(TESTS, OPTS)    
            
        if OPTS['status']:       
            statusfile    = Path(f"{LOG_DIR}/status").read_text().splitlines()        
            filteredlines = list(filter(lambda l: any([t in l for t in TESTS]), statusfile))                     
            line_pass     = lambda x: True if "passed" in x else False if "failed" in x else None
            report_log({i:l for i,l in enumerate(filteredlines)}, line_pass, print_header=False)
                
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
            report_results(TESTS, OPTS)

    except Exception as e:
        print("ERROR WHILE RUNNING TESTS")
        print(traceback.format_exc())

    finally:
        cleanup()

if __name__ == '__main__':
    run_autograder(sys.argv[1:])
