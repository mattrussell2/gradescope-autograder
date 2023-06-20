#!/usr/bin/env python3
import os
import json
from datetime import datetime, timezone
import ast
from pathlib import Path
from collections import OrderedDict
import toml
import autograde
import re

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
MAX_STYLE_SCORE = 'max_style_score'
STYLE_VISIBILITY = 'style_visibility'
COLS_STYLE_WEIGHT = 'cols_style_weight'
TABS_STYLE_WEIGHT = 'tabs_style_weight'
TODOS_STYLE_WEIGHT = 'todos_style_weight'
SYMBOL_STYLE_WEIGHT = 'symbol_style_weight'
BREAK_STYLE_WEIGHT = 'break_style_weight'
BOOLEAN_STYLE_WEIGHT = 'boolean_style_weight'
NON_CODE_STYLE_CHECKSET = 'non_code_style_checkset'
CODE_STYLE_CHECKSET = 'code_style_checkset'
STYLE_MAX_COLUMNS = 'style_max_columns'

# Defaults for all the above except MAX_STYLE_SCORE, used
# for loading up TOML_SETTINGS
TOML_DEFAULTS = {
    MAX_VALGRIND_SCORE: 8,
    VALGRIND_VISIBILITY: AFTER_DUE_DATE,
    STYLE_VISIBILITY: AFTER_DUE_DATE,
    COLS_STYLE_WEIGHT: 0,
    TABS_STYLE_WEIGHT: 0,
    TODOS_STYLE_WEIGHT: 0,
    SYMBOL_STYLE_WEIGHT: 0,
    BREAK_STYLE_WEIGHT: 0,
    BOOLEAN_STYLE_WEIGHT: 0,
    NON_CODE_STYLE_CHECKSET: autograde.DEFAULT_NON_CODE_STYLE_CHECKSET,
    CODE_STYLE_CHECKSET: autograde.DEFAULT_CODE_STYLE_CHECKLIST,
    STYLE_MAX_COLUMNS: autograde.DEFAULT_MAX_COLUMNS
}

# Violation keys used in dictionary returned by check_style as well as in the
# definition of VIOL_SYMBOL. These are also the names of the violations that
# appear when style violations are printed in the autograder output in
# report_style_violations.
VIOL_COLS = "Lines with too many columns"
VIOL_TABS = "Tabs"
VIOL_TODO = "TODOs"
VIOL_AND = "&&"
VIOL_OR = "||"
VIOL_BREAK = "break"
VIOL_NOT = "!"
VIOL_BOOL_ZEN = "boolean style violations (e.g. x == true should be x, y == false should be not y)"

# Map TOML weight settings to the violations they correspond to for
# get_style_score( ), this also collects all the weights to compute
# TOML_SETTINGS[MAX_STYLE_SCORE]
STYLE_WEIGHTS_VIOLATIONS = {
    COLS_STYLE_WEIGHT: [VIOL_COLS],
    TABS_STYLE_WEIGHT: [VIOL_TABS],
    TODOS_STYLE_WEIGHT: [VIOL_TODO],
    SYMBOL_STYLE_WEIGHT: [VIOL_AND, VIOL_OR, VIOL_NOT],
    BREAK_STYLE_WEIGHT: [VIOL_BREAK],
    BOOLEAN_STYLE_WEIGHT: [VIOL_BOOL_ZEN]
}

# Regexes for identifying comments (block, line inc. EOL comments), ! but not !=,
# boolean zen violations, C++ string literals, identifying switch() {} statements
# All used by check_style()
COMMENTED_REGEX = r"\/\*([\s\S]*?)\*\/\s*|\s*\/\/.*\n*"
NOT_BUT_NOT_EQ_REGEX = r"![^=]"

# I had to add [^A-Za-z_] because we don't want to falsely penalize students who
# may say name variables starting with true, for example if they do x == true_datum
# We only want to deduct if they do (x == true) or (x == true&& ...) or y = x == true;
BOOLEAN_ZEN_REGEX = r"(=|!)=\s*(true|false)[^A-Za-z_]"

# This handles when there's a \" inside " "
STRING_LITERAL_REGEX = r"\"(?:\\\"|[^\"])*?\""

# Came up with this using regex101
CHARACTER_LITERAL_REGEX = r"'([^\\]|\\.)'"

# I had to add this because students are allowed to use break; inside of switch {...}.
# This does not balance { } (as this can't be done with regex, see:
# https://stackoverflow.com/questions/546433/regular-expression-to-match-balanced-parentheses)
# Therefore, it will not identify instances where students put like an if statement or
# a loop inside the switch { }.
SWITCH_CASE_REGEX = r"switch\s*\(\s*[A-Za-z_]+\s*\)\s*\{(\n|[^\}])+\}"

# Control violation reporting - how many to show per file, and what should be
# substituted in the event of an empty violation line (e.g. a line containing just a tab)
MAX_VIOLATIONS_TO_SHOW = 5
EMPTY_LINE_SUBSTITUTE = "< whitespace only line >"


def load_common_based_on_defaults():
    """
    Helper function that builds dictionary of common TOML settings, substituting defaults
    where necessary. 

    slamel01
    """

    return {k: (TESTSET['common'][k] if k in TESTSET['common'] else ds) for k, ds in TOML_DEFAULTS.items()}


# Here we actually load up all our settings and add in MAX_STYLE_SCORE
TOML_SETTINGS = load_common_based_on_defaults()
TOML_SETTINGS[MAX_STYLE_SCORE] = sum(
    TOML_SETTINGS[k] for k in STYLE_WEIGHTS_VIOLATIONS)

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

# check_style helper functions ...


def should_check(filename, check_files_set):
    """
    Determines whether a file should be checked. A file will be checked if:
    1. It's not a hidden file
    2. It ends with an extension in check_files_set or matches case insensitive to a member of check_files_set
    2/11/23 - slamel01
    """

    return filename[0] != '.' and any([((check_file[0] == '.' and filename.endswith(check_file)) or
                                        (check_file[0] != '.' and filename.upper() == check_file))
                                       for check_file in check_files_set])


def clean_contents(contents, regex, repl):
    # Returns contents of an assumed C/C++ source file with all matches on given regex replaced with repl - 2/11/23, slamel01
    return re.sub(regex, repl, contents)


def regex_match_in_code(code, regex):
    # Determines whether code has a match for a certain regex - 2/9/23, slamel01, atanne02
    return re.compile(regex).search(code)


def collect_violations(check_files, clean, predicate):
    """
    Helper function that collects violations of a particular kind over a file check set.
    check_files - (filename, filepath) list of 2-tuples
    clean - clean function to apply to the contents of a file (str) and returns cleaned str (can be None)
    predicate - each line is passed into this predicate, predicate(line) == True => violation on that line
    Returns dictionary of filename (str) -> list of 2-tuples of (violation line, violation line number)
    Note that these violation line numbers are in the context of the cleaned lines, so if clean != None, then
    those line numbers will not be the line numbers of the input file.

    Note: clean should be designed in a way that clean(contents of a file).split("\n") yields lines of a file
    to be checked

    slamel01 - 3/1/23
    """

    violations = dict()
    for filename, filepath in check_files:
        if clean is None:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [(line.rstrip('\n'), i + 1)
                         for i, line in enumerate(f)]
        else:
            # The read_text().split() is slightly iffy - it depends to some extent how clean() works - this may
            # not yield lines in the way the caller intends
            lines = [(line, i + 1)
                     for i, line in enumerate(clean(Path(filepath).read_text()).split("\n"))]

        # Each element of lines list is (line, line number) - hence predicate should only be applied to line component
        lines = list(filter(lambda line_info: predicate(line_info[0]), lines))

        # Obtain violations and if any exist, add into output dict
        if len(lines) > 0:
            violations[filename] = lines
    return violations


def code_clean(contents):
    # Performs file cleaning for code checked files (removing comments, string, character literals) - 4/21/23, slamel01
    return clean_contents(clean_contents(contents, COMMENTED_REGEX, "\n"), STRING_LITERAL_REGEX, "")


def check_style():
    """
    Checks student style and constructions dictionary of violations:
    "cols" -> dict of files:lines with > MAX_COLUMNS columns
    "tabs" -> dict of files:lines with tabs
    "TODOs" -> list of files with TODOs in code not in string literals
    "&&" -> && in code not in comments or string literals
    "||" -> || in code not in comments or string literals
    "break" -> break in code not in comments or string literals
    "!" -> ! in code not in comments or string literals (!= ok)

    None is returned in the event that the max style score is 0 which
    means style is not being autograded. This is done in the hope that
    this will trigger apparent crashes in any function that uses the
    dict of style violations. It does not signify that there are no
    style violations which would be indicated by empty dicts/lists above

    2/11/23 - slamel01
    """

    if TOML_SETTINGS[MAX_STYLE_SCORE] == 0:
        return None

    # Collect names, paths of files to check for style
    # Using should_check() with 2 different file sets, construct 2 lists
    # 1st list - files to check for columns, tabs, and TODOs
    # 2nd list - files to check for break, &&, ||, !
    first_files_to_check = list()
    second_files_to_check = list()
    for entry in os.scandir(SUBMISSION_FOLDER):
        if entry.is_file():
            if should_check(entry.name, TOML_SETTINGS[NON_CODE_STYLE_CHECKSET]):
                first_files_to_check.append((entry.name, entry.path))
            if should_check(entry.name, TOML_SETTINGS[CODE_STYLE_CHECKSET]):
                second_files_to_check.append((entry.name, entry.path))

    # Construct violations dictionary using helper functions
    return {
        VIOL_COLS: collect_violations(first_files_to_check, None, lambda line: len(line.rstrip('\n')) > TOML_SETTINGS[STYLE_MAX_COLUMNS]),
        VIOL_TABS: collect_violations(first_files_to_check, None, lambda line: '\t' in line),
        VIOL_TODO: collect_violations(first_files_to_check, lambda contents: clean_contents(contents, STRING_LITERAL_REGEX, ""), lambda line: 'TODO' in line),
        VIOL_AND: collect_violations(second_files_to_check, code_clean, lambda line: '&&' in line),
        VIOL_OR: collect_violations(second_files_to_check, code_clean, lambda line: '||' in line),
        VIOL_BREAK: collect_violations(second_files_to_check, lambda contents: clean_contents(code_clean(contents), SWITCH_CASE_REGEX, ""), lambda line: 'break;' in line),
        VIOL_NOT: collect_violations(second_files_to_check, lambda contents: clean_contents(code_clean(contents), CHARACTER_LITERAL_REGEX, ""), lambda line: regex_match_in_code(line, NOT_BUT_NOT_EQ_REGEX)),
        VIOL_BOOL_ZEN: collect_violations(
            second_files_to_check, code_clean, lambda line: regex_match_in_code(line, BOOLEAN_ZEN_REGEX))
    }


def get_style_score(style_violations):
    """
    Gets the student's style score as follows (out of MAX_STYLE_SCORE): 
    2/11/23 - slamel01
    """

    if style_violations is None:
        return 0

    # Writing out because 1-liner is somewhat hard to read
    deductions = 0
    for weight, violations in STYLE_WEIGHTS_VIOLATIONS.items():
        # Deduct TOML_SETTINGS[weight] points if any of the violations occurred that the
        # weight corresponds to
        deductions += TOML_SETTINGS[weight] * \
            any(style_violations[v] for v in violations)
    return TOML_SETTINGS[MAX_STYLE_SCORE] - deductions


# Checks style and collects violations - this had to be moved up here so that get_total_score() can incorporate
# it and is put into the initial save_json() call below
style_violations = check_style()


def get_total_score():
    # Modified to include style score, handles when style is not graded (get_style_score just returns 0) - slamel01
    return sum([x['max_score'] * x['success'] for x in TEST_SUMMARIES]) + get_valgrind_score() + get_style_score(style_violations)


def get_max_score():
    # Modified to include max style score, handles when style is not graded (max style score is just 0) - slamel01
    return sum([x['max_score'] for x in TEST_SUMMARIES]) + TOML_SETTINGS[MAX_VALGRIND_SCORE] + TOML_SETTINGS[MAX_STYLE_SCORE]


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


# def before_duedate():
#     metadata = load_json(SUBMISSION_METADATA_PATH)
#     due_date = parser.parse(metadata["assignment"]["due_date"])
#     today = datetime.now(timezone.utc)
#     return today < due_date


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
        name = "Submission Validation",
        visibility = VISIBLE,
        score = 0,
        max_score = 0,
        output = token_results
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
# Edited by slamel01 on 2/28/2023 to take the currently identified style
# violations so that the style score could be calculated inside upon request
# from Milod so that students can see their style score specifically before
# the deadline
def make_test00(style_violations):
    #if before_duedate():
    name = "Autograder Score"
    info = "This is your autograder score.\n"
    RESULTS["tests"].append(
        make_test_result(name=name, visibility=VISIBLE, score=get_total_score(), max_score=get_max_score(),
                         output=info))
    # if style_violations is not None:
    #     info += f"Note that your current autograded style score is {get_style_score(style_violations)}/{TOML_SETTINGS[MAX_STYLE_SCORE]}.\n"
    # info += "If you are not happy with your current score, and it is before the duedate, you may resubmit.\n\n"\
    #     "CAUTION: You only have a limited number of submissions (usually 5) per assignment.\n" \
    #     "Use them wisely!"
    # else:
    #     name = "Final Autograder Score"
    #     info = "This is your Final Autograder Score"

def make_build_test():
    compilation_results = autograde.report_compile_logs(type_to_report="failed", output_format="str")
    if compilation_results != "":
        compilation_results = "ERROR: BUILD FAILED\n" + compilation_results
        RESULTS["tests"].append(
            make_test_result(name="Build Fail", visibility=VISIBLE, score=-1, max_score=0,
                            output=compilation_results))


# helper functions for report_style_violations ..


def report_filelines(filelines, violation, line_print):
    """
    Informs the user of the files and lines where violation occurred - helper to report_style_violations
    filelines - dict from filename (str) -> list with lines where violations occurred
    violation - name of the violation
    line_print - function that a line is passed to for each line in filelines lists

    slamel01 - 3/1/23
    """
    if filelines:
        autograde.INFORM(f"\n    {violation}:", color=autograde.RED)
        for file, lines in filelines.items():
            autograde.INFORM("        " + file + ": ", color=autograde.RED)
            for line_info in lines[:MAX_VIOLATIONS_TO_SHOW]:
                autograde.INFORM("            " +
                                 line_print(line_info), color=autograde.RED)
            if len(lines) > MAX_VIOLATIONS_TO_SHOW:
                autograde.INFORM(
                    f"            {len(lines) - MAX_VIOLATIONS_TO_SHOW} more violations were found, but were not printed!", color=autograde.RED)


def default_line_print(line_info):
    # Default function for returning string for when a violation line is printed - slamel01, 3/1/23
    return (line_info[0][:TOML_SETTINGS[STYLE_MAX_COLUMNS]] + " < line cut off >") if len(line_info[0]) > TOML_SETTINGS[STYLE_MAX_COLUMNS] else line_info[0]


def report_style_violations(violations):
    """
    Reports the style violations from check_style() - i.e. actually prints them to the autograder results
    3/1/23 - slamel01
    """

    if violations is None:
        # Adding this print statement just for nicety to whoever is setting up autograder/grader
        # this runs all the time? connect with slamel01 on this. 
        #autograde.INFORM("\nStyle check was not run!", color=autograde.CYAN)
        return

    autograde.INFORM("\n== Style Report ==", color=autograde.CYAN)
    if not any(violations.values()):
        autograde.INFORM("\nStyle check passed, good work!",
                         color=autograde.GREEN)
    else:
        # Define here a dict mapping violation -> how lines with that violation should be printed
        line_printers = dict()

        # When maximum number of cols are violated, since line numbers are accurate to the original file, we print
        # the line and the line number
        line_printers[VIOL_COLS] = lambda line_info: f"line {line_info[1]}: " + default_line_print(
            line_info)

        # For tabs, it is possible for students to have a line with just a tab that's otherwise blank, which is
        # visually a little confusing - therefore we have that if the line is empty besides whitespace, we will print
        # the substitute instead
        line_printers[VIOL_TABS] = lambda line_info: f"line {line_info[1]}: " + (
            default_line_print(line_info) if len(line_info[0].strip()) > 0 else EMPTY_LINE_SUBSTITUTE)

        # For all the remaining violations, we just print the line without the number due to cleaning making the line
        # numbers not make sense (see check_style/collect_violations)
        line_printers.update(dict.fromkeys(
            [VIOL_TODO, VIOL_AND, VIOL_OR, VIOL_BREAK, VIOL_NOT, VIOL_BOOL_ZEN], default_line_print))

        for viol, printer in line_printers.items():
            report_filelines(violations[viol], f"\n{viol} found in", printer)


def make_style_test(style_violations):
    """
    Adds style test results to JSON. Style violations should be the output
    of check_style and is necessary for score calculation, unlike Valgrind
    score which is calculated from TEST_SUMMARIES
    2/24/23 - slamel01
    """

    # It seems like even if the maximum score for style is 0, Gradescope
    # still renders it in the HTML results from the JSON, therefore, not
    # adding this when score is 0 just to avoid student confusion. Note
    # if style_violations is None, then get_style_score and MAX_SCORES[STYLE]
    # will both be 0.
    if style_violations is None:
        return

    RESULTS["tests"].append(
        make_test_result(name="Style Score",
                         visibility=TOML_SETTINGS[STYLE_VISIBILITY],
                         score=get_style_score(style_violations),
                         max_score=TOML_SETTINGS[MAX_STYLE_SCORE],
                         output="This is your total autograded style score.\n"))


def make_valgrind_test():
    RESULTS["tests"].append(
        make_test_result(name="Valgrind Score",
                         visibility=TOML_SETTINGS[VALGRIND_VISIBILITY],
                         score=get_valgrind_score(),
                         max_score=TOML_SETTINGS[MAX_VALGRIND_SCORE],
                         output="This is your total Valgrind score.\n"))


def make_results():
    make_token_test()
    make_build_test()
    #make_test00(style_violations)
    #make_style_test(style_violations)
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

    report_style_violations(style_violations)
    save_json(RESULTS_JSONPATH, RESULTS)


if __name__ == "__main__":
    make_results()
