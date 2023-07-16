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
SUBMISSION_FOLDER        = "/autograder/submission"

# Gradescope visibility options
VISIBLE         = "visible"                 # Used for "public" group
AFTER_PUBLISHED = "after_published"         # Used for "private" group
AFTER_DUE_DATE  = "after_due_date"
HIDDEN          = "hidden"                  # Careful if using this setting! Gradescope
                                            # hides the total score from students if
                                            # ANY test is hidden.... smh....

TESTSET = toml.load('testset.toml')

# All the TOML settings used in this file
MAX_VALGRIND_SCORE  = 'max_valgrind_score'
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


HERE             = os.getcwd()
LOG_DIR          = os.path.join(HERE, "results", "logs")
OUTPUT_DIR       = os.path.join(HERE, "results", "output")
TEST_SUMMARIES   = load_dicts_from_files(LOG_DIR, '.summary')
RESULTS_DIR      = os.path.join(HERE, "results")
RESULTS_JSONPATH = os.path.join(RESULTS_DIR, "results.json")

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
    return {"name": name, "visibility": visibility, "score": score, "max_score": max_score,
            "output": output, "output_format": "ansi"}

def make_test_output(test):
#     """
#     Modified to handle instances of non UTF-8 characters in diff files.
#     2/9/23 - slamel01, atanne02
#     """
    failstr = ""
    if wrong_output_program(test['executable']) or test['compiled'] == False:
        return f"{test['testname']} failed to build. See log below.\n{get_compile_log(test['executable'])}"

    diff_fpaths = [x for x in os.listdir(OUTPUT_DIR) if x.startswith(test['testname']) and x.endswith(f".diff")]
    for f in diff_fpaths:
        try:
            diff_text = Path(os.path.join(OUTPUT_DIR, f)).read_text()
            if diff_text != "":
                failstr += f"{f}\n{diff_text}\n"
        except UnicodeDecodeError:
            failstr += f"{f} contains non UTF-8 characters. This indicates that binary is in student output\n"
    return failstr

def make_token_test():
    if not os.path.exists('/autograder/results/token_results'):
        print("No token results file found. Token test was skipped.")
        return
    RESULTS["tests"].append(make_test_result(
        name       = "Submission Validation",
        visibility = VISIBLE,
        score      = 0,
        max_score  = 0,
        output     = Path('/autograder/results/token_results').read_text()
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
    #stdout is already visible, so don't show output 2x
    if RESULTS['stdout_visibility'] == VISIBLE:
        return 
    visible_results_path = f"{RESULTS_DIR}/visible_results_output.txt"
    if not os.path.exists(visible_results_path): return

    info = "This is your total autograder score.\n"
    info += "A limited set of tests are shown below. You must determine what the hidden tests are.\n"
    info += Path(visible_results_path).read_text()
    
    RESULTS["tests"].append(
        make_test_result(name       = "Autograder Score", 
                         visibility = VISIBLE,
                         score      = get_total_score(), 
                         max_score  = get_max_score(),
                         output     = info))

def make_build_test():
    compilation_results = autograde.report_compile_logs(type_to_report="failed", output_format="str")
    if compilation_results == "": return
    RESULTS["tests"].append(
        make_test_result(name       = "Build Fail", 
                         visibility = VISIBLE, 
                         score      = -1,
                         max_score  = 0,
                         output     = compilation_results))


def make_valgrind_test():
    RESULTS["tests"].append(
        make_test_result(name       = "Valgrind Score",
                         visibility = TOML_SETTINGS[VALGRIND_VISIBILITY],
                         score      = get_valgrind_score(),
                         max_score  = TOML_SETTINGS[MAX_VALGRIND_SCORE],
                         output     = "This is your total Valgrind score.\n"))


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

    if TESTSET['common'].get('check style', False):
        autograde.INFORM('\n' + "🕶️ Style Report", color=autograde.BLUE)        
        print(style_checker.style_results)

    RESULTS["tests"].append(
        make_test_result(name       = "Style Score",
                         visibility = VISIBLE,
                         score      = style_checker.style_score,
                         max_score  = style_checker.max_style_score,
                         output     = style_checker.style_results))


def make_results():
    make_token_test()
    make_build_test()
    make_test00()
    make_valgrind_test()
    make_style_test()

    for test in TEST_SUMMARIES:
        RESULTS["tests"].append(
            make_test_result(name       = test["description"],
                             visibility = test['visibility'],
                             score      = test['max_score'] * test['success'],
                             max_score  = test['max_score'],
                             output     = make_test_output(test)))
    
    save_json(RESULTS_JSONPATH, RESULTS)

if __name__ == "__main__":
    make_results()