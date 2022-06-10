#!/usr/bin/env python3
import os
import json
from datetime import datetime, timezone
from webbrowser import get
import ast
from pathlib import Path
from collections import OrderedDict 

# We need dateutil on Gradescope, but not on Halligan. This library does not
# exist locally, so we simply pass when running locally.
try:
    from dateutil import parser
    HALLIGAN = False
    # file made by gs; has useful info like duedatetime of assignment
    SUBMISSION_METADATA_PATH = "/autograder/submission_metadata.json" 
except:
    HALLIGAN = True

# Result strings
RESULT       = "Result:   "
REASON       = "Reason:   "
CANON_ERR    = "Canonical Error:\n\n"
FAILED       = "FAILED!"
PASSED       = "PASSED!"
POS_MITIGATE = "Possible Mitigation:\n\n"
COMPILE_LOG  = "\nCompile Log:\n\n"

TESTPASS     = f"{RESULT}{PASSED}"

BUILD_FAIL   = "Compilation Failed!\n"
COUT_FAIL    = "std::cout did not match the reference\n"
CERR_FAIL    = "std::cerr did not match the reference\n"
OFILE_FAIL   = "The contents of a file output by your program are incorrect\n"
BADEXEC_FAIL = "Makefile Built Incorrect Executable\n"
SEGFAULT     = "The program segfaulted during the test\n"
EXIT_FAIL    = "The program did not finish successfully (nonzero exit code)\n"
TIMEOUT      = "The program timed out during execution\n"
OUTOFMEMORY  = "The program exceeded the maximum amount of memory allowed\n"

# Gradescope visibility options
VISIBLE         = "visible"         # Used for "public" group
AFTER_PUBLISHED = "after_published" # Used for "private" group
AFTER_DUE_DATE  = "after_due_date"  
HIDDEN          = "hidden"          # Careful if using this setting! Gradescope
                                    # hides the total score from students if 
                                    # ANY test is hidden.... smh....

# todo: reinsert canonicalization messages, after considering how canonicalizers
# will be needed in the future
mitigation_map = {
    COUT_FAIL: 
    """
        Check that your output to std::cout EXACTLY matches
        that of the Assignment Spec and/or the reference. 
        (Watch out for trailing whitespace!)
    """,
    #For Gerp: Try sorting your STDOUT and the reference STDOUT and then diff them.
    #For Gerp: Are you printing the line twice if there are two instances of a single word in it?

    CERR_FAIL:  
    """
        Your output to std::cerr and/or your Exception Message did not match the expected output.
        Check that your output to std::cerr and/or your Exception Message EXACTLY matches
        that of the Assignment Spec and/or the reference. (Watch out for trailing whitespace!)",
    """,

    BUILD_FAIL:
    """
        Check the compiler output above. Make sure your function names,
        input and output types match the spec EXACTLY!",
    """,

    BADEXEC_FAIL:
    """
        make must build the same name as the target (i.e. make myprogram must 
        build a program named myprogram). Ensure you have `-o yourprogram` in 
        the linking command of your Makefile.
    """,

    EXIT_FAIL: 
    """
        Your program must exit successfully. In most cases this means returning 
        0 (EXIT_SUCCESS) from main.
    """,
    
    SEGFAULT: 
    """
        Segfaults usually occur when uninitialized or out-of-bounds memory are accessed. 
        Make sure to carefully check variable initialization, use of pointer-variables, and
        that the destructors of your class(es) is/are working as expected. 
    """,
    OUTOFMEMORY:
    """
        There is a limit on the maximum memory allowed for your program. Consult the assignment spec
        for details. Use the command `/usr/bin/time -v ./myprogram` and refer to the 'Maximum 
        resident set size' line to see how much memory your program is using.
    """,
    TIMEOUT: 
    """
        Be sure your code is running as efficiently as possible, and has no infinite loops!
    """,

    "OTHER": 
    """
        No standard mitigation suggestion is available!
    """
}

# helper functions for file loading/saving, etc.
def load_dict_from_file(d, fname):    
    return ast.literal_eval(Path(os.path.join(d, fname)).read_text())

def load_dicts_from_files(d, extension):
    files = [f for f in os.listdir(d) if f.endswith(extension)]
    return [load_dict_from_file(d, f) for f in files]

def load_json(fullpath):
    with open(fullpath, 'r') as f:
        jsondata = json.load(f)
    return jsondata

def save_json(fname, data, d=None):
    savepath = fname if not d else os.path.join(d, fname)
    with open(savepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_total_score():
    return sum([x['max_score'] * x['success'] for x in TEST_SUMMARIES])

def get_max_score():
    return sum([x['max_score'] for x in TEST_SUMMARIES])    

HERE           = os.getcwd()

# Path to student testXX.summary files and compilation logs
LOG_DIR        = os.path.join(HERE, "results", "logs")

# loads the summaries - one per test - as dictionaries
TEST_SUMMARIES = load_dicts_from_files(LOG_DIR, '.summary')

#if not os.path.exists('results'):
#    os.mkdir('results')
RESULTS_JSONPATH  = os.path.join(HERE, "results", "results.json")

# dictionary where we'll keep the results
RESULTS = {
    "score":             get_total_score(),
    "visibility":        VISIBLE if 'lab' in os.environ['ASSIGNMENT_TITLE'] else AFTER_PUBLISHED,
    "stdout_visibility": VISIBLE if 'lab' in os.environ['ASSIGNMENT_TITLE'] else AFTER_PUBLISHED,
    "tests":             []
}

# Set defaults for gradescope now, so at least there's the total score if all 
# else fails.    
save_json(RESULTS_JSONPATH, RESULTS)

def before_duedate():
    if HALLIGAN: return True # Halligan doesn't care 
    try:
        metadata = load_json(SUBMISSION_METADATA_PATH)
        due_date = parser.parse(metadata["assignment"]["due_date"])
        today    = datetime.now(timezone.utc)
        return today < due_date
    except:
        return False # HACK for hallian, which seems to recognize the library

def get_autograder_visibility():
    return HIDDEN if before_duedate() else VISIBLE

def get_compile_log(execname):
    return Path(os.path.join(LOG_DIR, f"{execname}.compile.log")).read_text()

def get_compile_logs():
    return [x for x in LOG_DIR if x.endswith(".compile.log")]

def test_compiled(execname):
    return "build completed successfully" in get_compile_log(execname)

def build_failed(execname):
    return not test_compiled(execname)

def wrong_output_program(execname):
    incorrect_exec = f"make {execname}' must build a program named {execname}"
    return incorrect_exec in get_compile_log(execname)

# Returns a dictionary for a testcase in a form that Gradescope requires.
# We append dictionaries returned by this function to the results.json["tests"]
# list.
def make_test_result(name, visibility, score, max_score, output):
    return { 
        "name":       name,
        "visibility": visibility,
        "score":      score,
        "max_score":  max_score,
        "output":     output
    }
  
# Returns a formatted string with the reason a test failed.
# If a test fails to compile, we grab the contents compileLog for the failed
# test and add it to the returned string
# Format the reason and mitigation into a nice format that looks good on 
# Gradescope. Using a dict, we can dynamically pass in any number of
# key->value pairs and return a single formatted string.
def get_failure_reason(test):
    fail = OrderedDict([(RESULT, FAILED)]) # use this so we print items in order
    
    failure_tests = {
        SEGFAULT:    lambda test: test['segfault'] == True,
        TIMEOUT:     lambda test: test['timed_out'] == True,
        COUT_FAIL:   lambda test: not test['stdout_diff_passed'],
        CERR_FAIL:   lambda test: not test['stderr_diff_passed'],
        OFILE_FAIL:  lambda test: wrong_output_program(test['executable']),
        EXIT_FAIL:   lambda test: not (test['exit_status'] == test['exitcodepass']),
        BUILD_FAIL:  lambda test: build_failed(test['executable']),
        OUTOFMEMORY: lambda test: test['max_ram_exceeded'] == True,
        "OTHER":     lambda test: True
    }
    if failure_tests[BUILD_FAIL](test):
        fail[COMPILE_LOG] = get_compile_log(test['executable']) 
    else:    
        for failtype, func in failure_tests.items():
            if func(test):
                fail[REASON] = failtype                
                if failtype == COUT_FAIL:
                    fail['Diff Result for stdout\n'] = Path(f"/autograder/results/output/{test['testname']}.stdout.diff").read_text()
                elif failtype == CERR_FAIL:
                    fail['Diff Result for stderr\n'] = Path(f"/autograder/results/output/{test['testname']}.stderr.diff").read_text()
                fail[POS_MITIGATE] = mitigation_map[failtype]
                break
    return "\n".join([f"{k}{v}" for k, v in fail.items()])


# Some BullS*&%t we had to do because Gradescope does not display the top-level
# Autograder score, even if you set visibility to "VISIBLE" and set the score
# manually.... so dumb...
# Gradescope will hide the final autograder score if ANY of your individual
# tests are set with the visibility == 'hidden'
# So, add the tentative final autograder score as the first test, namely 'test00'.
# We now leave this test as "visible" at all times, but change the name of 
# the test to 'Final Autograder Score' once the date today is past the 
# due_date. If it is before the due_date, we title it 'Tentative Autograder 
# Score'. 
def make_test00():
    if before_duedate():
        name = "test00 - Tentative Final Autograder Score"
        info = "This is your TENTATIVE final autograder score.\n" \
                "The final score will be posted here after the duedate\n"\
                "If you are not happy with your tentative score, you may resubmit.\n\n"\
                "CAUTION: You only have 5 submissions per assignment. " \
                "Use them wisely! : )"
    else:
        name = "test00 - Final Autograder Score"
        info = "This is your Final Autograder Score"
    
    RESULTS["tests"].append(make_test_result(
            name       = name,
            visibility = VISIBLE,
            score      = get_total_score(),
            max_score  = get_max_score(),
            output     = info
        )
    )

def make_results():
   # make_test00()

    # maybe necessary? not sure. i think the program exits immediately if compilation fails, so yes.
    # compile_logfiles = get_compile_logs()
    # if any([build_failed(log.split('.compile.log')[0]) for log in compile_logfiles]) and \
    #    len(TEST_SUMMARIES) == 0:
    #     testname = "compilation failed"
    #     max_score = 0
    #     score = 0
    #     reason = "Your program

    for test in TEST_SUMMARIES:
        testname  = test['testname']
        max_score = test['max_score']
        score     = max_score * test['success']
        reason    = TESTPASS if score == max_score else get_failure_reason(test)
        
        vresult = "Valgrind: "
        if not test['valgrind']:
            vresult += "Valgrind was intentionally not run on this test."
        elif test['exit_status'] != test['exitcodepass']:
            vresult += "Valgrind could not be run because the test failed."
        elif test['valgrind_passed']:
            vresult += "Valgrind Passed!"
        elif test['memory_leaks']:
            vresult += "Valgrind reported memory leaks."
        elif test['memory_errors']:
            vresult += "Valgrind reported memory errors."

        RESULTS["tests"].append(make_test_result(
            name        = test["description"],
            visibility  = test['visibility'],
            score       = score,
            max_score   = max_score,
            output      = f"{reason}\n\n{vresult}"
        ))

    save_json(RESULTS_JSONPATH, RESULTS)

if __name__ == "__main__":
    make_results()
