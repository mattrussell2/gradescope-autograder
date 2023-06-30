#!/usr/bin/env python3
import os
import json
import ast
from pathlib import Path
from collections import OrderedDict
import toml
import autograde
import style_check

SUBMISSION_METADATA_PATH = "/autograder/submission_metadata.json"
SUBMISSION_FOLDER = "/autograder/submission"

# Result strings
RESULT = "Result:   "
REASON = "Reason:   "
CANON_ERR = "Canonical Error:\n\n"
FAILED = "FAILED!"
PASSED = "PASSED!"
POS_MITIGATE = "Possible Mitigation:\n\n"
COMPILE_LOG = "\nCompile Log:\n\n"

DIFF_STDOUT_RESULT = "Diff Result for stdout:\n"
DIFF_STDERR_RESULT = "Diff Result for stderr:\n"

# Error messages when non UTF-8 characters found in diff files (used by
# get_failure_reason())
DIFF_STDOUT_CONTAINS_BINARY = "Diff Result for stdout contains binary"
DIFF_STDERR_CONTAINS_BINARY = "Diff Result for stderr contains binary"

TESTPASS = f"{RESULT}{PASSED}"

BUILD_FAIL = "Build Failed!\n"
COUT_FAIL = "std::cout did not match the reference\n"
CERR_FAIL = "std::cerr did not match the reference\n"
NO_OFILE_FILE = "Your program is not sending data to a file, but the reference does.\n"
OFILE_FAIL = "The contents of a file output by your program are incorrect\n"
BADEXEC_FAIL = "Makefile Built Incorrect Executable\n"
SEGFAULT = "The program segfaulted during the test\n"
EXIT_FAIL = "The program did not finish successfully (nonzero exit code)\n"
TIMEOUT = "The program timed out during execution\n"
OUTOFMEMORY = "The program exceeded the maximum amount of memory allowed\n"

# Gradescope visibility options
VISIBLE = "visible"               # Used for "public" group
AFTER_PUBLISHED = "after_published"               # Used for "private" group
AFTER_DUE_DATE = "after_due_date"
HIDDEN = "hidden"               # Careful if using this setting! Gradescope
# hides the total score from students if
# ANY test is hidden.... smh....

# todo: put this in a fn
TESTSET = toml.load('testset.toml')

# All the TOML settings used in this file
MAX_VALGRIND_SCORE = 'max_valgrind_score'
VALGRIND_VISIBILITY = 'valgrind_score_visibility'

# Defaults for all the above except MAX_STYLE_SCORE, used
# for loading up TOML_SETTINGS
TOML_DEFAULTS = {
    MAX_VALGRIND_SCORE: 8,
    VALGRIND_VISIBILITY: AFTER_DUE_DATE,
}


def load_common_based_on_defaults():
    """
    Helper function that builds dictionary of common TOML settings, substituting defaults
    where necessary. 

    slamel01
    """

    return {k: (TESTSET['common'][k] if k in TESTSET['common'] else ds) for k, ds in TOML_DEFAULTS.items()}


# Here we actually load up all our settings and add in MAX_STYLE_SCORE
TOML_SETTINGS = load_common_based_on_defaults()


# todo: reinsert canonicalization messages, after considering how canonicalizers
# will be needed in the future
mitigation_map = {
    COUT_FAIL: """
        Check that your output to std::cout EXACTLY matches
        that of the Assignment Spec and/or the reference.
        (Watch out for trailing whitespace!)
    """,
    # For Gerp: Try sorting your STDOUT and the reference STDOUT and then diff them.
               # For Gerp: Are you printing the line twice if there are two instances of a single word in it?
    CERR_FAIL: """
        Your output to std::cerr and/or your Exception Message did not match the expected output.
        Check that your output to std::cerr and/or your Exception Message EXACTLY matches
        that of the Assignment Spec and/or the reference. (Watch out for trailing whitespace!)",
    """,
    OFILE_FAIL: """
        Your output to an output file produced by your program.
        Check that your output to all files produced by your program EXACTLY match
        that of the Assignment Spec and/or the reference. (Watch out for trailing whitespace!)",
    """,
    NO_OFILE_FILE: """
        Produce all necessary output files
    """,
    BUILD_FAIL: """
        Check the compiler output above. Make sure your function names,
        input and output types mSECOND_CHECKED_FILES = {'.c', '.h', '.cpp'}atch the spec EXACTLY!",
    """,
    BADEXEC_FAIL: """
        make must build the same name as the target (i.e. make myprogram must
        build a program named myprogram). Ensure you have `-o yourprogram` in
        the linking command of your Makefile.
    """,
    EXIT_FAIL: """
        Your program must exit successfully. In most cases this means returning
        0 (EXIT_SUCCESS) from main.
    """,
    SEGFAULT: """
        Segfaults usually occur when uninitialized or out-of-bounds memory are accessed.
        Make sure to carefully check variable initialization, use of pointer-variables, and
        that the destructors of your class(es) is/are working as expected.
    """,
    OUTOFMEMORY: """
        There is a limit on the maximum memory allowed for your program. Consult the assignment spec
        for details. Use the command `/usr/bin/time -v ./myprogram` and refer to the 'Maximum
        resident set size' line to see how much memory your program is using.
    """,
    TIMEOUT: """
        Be sure your code is running as efficiently as possible, and has no infinite loops!
    """,
    "OTHER": """
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


def get_valgrind_score():
    try:
        return round(
            sum([x['valgrind_passed'] == True for x in TEST_SUMMARIES if x['valgrind']]) /
            len([x for x in TEST_SUMMARIES if x['valgrind']]) * TOML_SETTINGS[MAX_VALGRIND_SCORE], 2)
    except ZeroDivisionError:
        return 0


# Checks style and collects violations - this had to be moved up here so that get_total_score() can incorporate
# it and is put into the initial save_json() call below
style_checker = style_check.StyleChecker()

def get_total_score():
    # Modified to include style score, handles when style is not graded (get_style_score just returns 0) - slamel01
    return sum([x['max_score'] * x['success'] for x in TEST_SUMMARIES]) + get_valgrind_score() + style_checker.style_score


def get_max_score():
    # Modified to include max style score, handles when style is not graded (max style score is just 0) - slamel01
    return sum([x['max_score'] for x in TEST_SUMMARIES]) + TOML_SETTINGS[MAX_VALGRIND_SCORE] + style_checker.max_style_score


HERE = os.getcwd()
LOG_DIR = os.path.join(HERE, "results", "logs")
TEST_SUMMARIES = load_dicts_from_files(LOG_DIR, '.summary')
RESULTS_JSONPATH = os.path.join(HERE, "results", "results.json")

# dictionary where we'll keep the results
RESULTS = {
    "score": get_total_score(),
    "visibility": VISIBLE if 'lab' in os.environ['ASSIGNMENT_TITLE'] else AFTER_PUBLISHED,
    "stdout_visibility": VISIBLE if 'lab' in os.environ['ASSIGNMENT_TITLE'] else AFTER_PUBLISHED,
    "tests": []
}

# Set defaults for gradescope now, so at least there's the total score if all
# else fails.
save_json(RESULTS_JSONPATH, RESULTS)

# sometimes compile log not created if using manual mode
def get_compile_log(execname):
    if os.path.exists(os.path.join(LOG_DIR, f"{execname}.compile.log")):
        return Path(os.path.join(LOG_DIR, f"{execname}.compile.log")).read_text()
    else:
        return ""

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
    return {"name": name, "visibility": visibility, "score": score, "max_score": max_score, "output": output, "output_format": "ansi"}


# Returns a formatted string with the reason a test failed.
# If a test fails to compile, we grab the contents compileLog for the failed
# test and add it to the returned string
# Format the reason and mitigation into a nice format that looks good on
# Gradescope. Using a dict, we can dynamically pass in any number of
# key->value pairs and return a single formatted string.
def get_failure_reason(test):
    """
    Modified to handle instances of non UTF-8 characters in diff files.
    2/9/23 - slamel01, atanne02
    """

    # use this so we print items in order
    fail = OrderedDict([(RESULT, FAILED)])

    # use == True/False, because defaults are 'None', so not x will return True, even if it is uninitialialized.
    failure_tests = {
        SEGFAULT: test['segfault'] == True,
        TIMEOUT: test['timed_out'] == True,
        NO_OFILE_FILE: test['ofile_file_exists'] == False,
        COUT_FAIL: test['stdout_diff_passed'] == False,
        CERR_FAIL: test['stderr_diff_passed'] == False,
        OFILE_FAIL: wrong_output_program(test['executable']),
        EXIT_FAIL: not (test['exit_status'] == test['exitcodepass']),
        BUILD_FAIL: build_failed(test['executable']),
        OUTOFMEMORY: test['max_ram_exceeded'] == True,
        "OTHER": True
    }
    if failure_tests[BUILD_FAIL]:
        fail[COMPILE_LOG] = get_compile_log(test['executable'])
    else:
        for failtype, res in failure_tests.items():
            if res:
                fail[REASON] = failtype
                if failtype == COUT_FAIL:
                    if not test['ccize_stdout']:
                        fname = f"{test['testname']}.stdout.diff"
                    else:
                        fname = f"{test['testname']}.stdout.ccized.diff"
                    try:
                        fail[DIFF_STDOUT_RESULT] = \
                            Path(os.path.join(HERE, "results",
                                 "output", fname)).read_text()
                    except UnicodeDecodeError:
                        fail[DIFF_STDOUT_RESULT] = DIFF_STDOUT_CONTAINS_BINARY
                elif failtype == CERR_FAIL:
                    if not test['ccize_stderr']:
                        fname = f"{test['testname']}.stderr.diff"
                    else:
                        fname = f"{test['testname']}.stderr.ccized.diff"
                    try:
                        fail[DIFF_STDERR_RESULT] = \
                            Path(os.path.join(HERE, "results",
                                 "output", fname)).read_text()
                    except UnicodeDecodeError:
                        fail[DIFF_STDERR_RESULT] = DIFF_STDERR_CONTAINS_BINARY

                fail[POS_MITIGATE] = mitigation_map[failtype]
                break

    return "\n".join([f"{k}{v}" for k, v in fail.items()])


def make_token_test():
    token_results = Path('/autograder/results/token_results').read_text()
    passed = "SUCCESS" in token_results
    RESULTS["tests"].append(make_test_result(
        name="Submission Validation",
        visibility=VISIBLE,
        score=0,
        max_score=0,
        output=token_results
    ))

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
    name = "Autograder Score"
    info = "This is your autograder score.\n"
    info += "If you are not happy with your current score, and it is before the duedate, you may resubmit.\n\n"\
            "CAUTION: You only have a limited number of submissions (usually 5) per assignment.\n" \
            "Use them wisely!"
    RESULTS["tests"].append(
        make_test_result(name=name, visibility=VISIBLE, score=get_total_score(), max_score=get_max_score(),
                         output=info))


def make_build_test():
    compilation_results = autograde.report_compile_logs(
        type_to_report="failed", output_format="str")
    if compilation_results != "":
        compilation_results = "ERROR: BUILD FAILED\n" + compilation_results
        RESULTS["tests"].append(
            make_test_result(name="Build Fail", visibility=VISIBLE, score=-1, max_score=0,
                             output=compilation_results))


def make_valgrind_test():
    RESULTS["tests"].append(
        make_test_result(name="Valgrind Score",
                         visibility=TOML_SETTINGS[VALGRIND_VISIBILITY],
                         score=get_valgrind_score(),
                         max_score=TOML_SETTINGS[MAX_VALGRIND_SCORE],
                         output="This is your total Valgrind score.\n"))


def make_style_test():
    """
    Adds style test results to JSON. Style violations should be the output
    of check_style and is necessary for score calculation, unlike Valgrind
    score which is calculated from TEST_SUMMARIES
    """
    # It seems like even if the maximum score for style is 0, Gradescope
    # still renders it in the HTML results from the JSON, therefore, not
    # adding this when score is 0 just to avoid student confusion. Note
    # if style_violations is None, then get_style_score and MAX_SCORES[STYLE]
    # will both be 0.
    if style_checker.all_style_violations == None:
        return

    RESULTS["tests"].append(
        make_test_result(name="Style Score",
                         visibility=VISIBLE,
                         score=style_checker.style_score,
                         max_score=style_checker.max_style_score,
                         output=style_checker.style_results))


def make_results():
    make_token_test()
    make_build_test()
    make_test00()
    make_style_test()
    make_valgrind_test()

    for test in TEST_SUMMARIES:
        testname = test['testname']
        max_score = test['max_score']
        score = max_score * test['success']
        reason = TESTPASS if score == max_score else get_failure_reason(test)

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

        RESULTS["tests"].append(
            make_test_result(name=test["description"],
                             visibility=test['visibility'],
                             score=score,
                             max_score=max_score,
                             output=f"{reason}\n\n{vresult}"))

    autograde.INFORM("\n== Style Report ==", color=autograde.CYAN)        
    print(style_checker.style_results)
    save_json(RESULTS_JSONPATH, RESULTS)


if __name__ == "__main__":
    make_results()
