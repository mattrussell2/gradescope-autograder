"""
Library of functions for doing style checking in make_gradescope_results.py

Chami Lamelas
Spring - Summer 2023
"""

import re
import toml
from pathlib import Path
import os
import autograde

SUBMISSION_FOLDER = "/autograder/submission"
TESTSET_TOML_PATH = "testset.toml"
CONFIG_TOML_PATH = "/autograder/source/config.toml"


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
    "COLUMNS_STYLE_WEIGHT": [VIOL_COLS],
    "TABS_STYLE_WEIGHT": [VIOL_TABS],
    "TODOS_STYLE_WEIGHT": [VIOL_TODO],
    "SYMBOL_STYLE_WEIGHT": [VIOL_AND, VIOL_OR, VIOL_NOT],
    "BREAK_STYLE_WEIGHT": [VIOL_BREAK],
    "BOOLEAN_STYLE_WEIGHT": [VIOL_BOOL_ZEN]
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


def should_check(filename, check_files_set):
    """
    Determines whether a file should be checked. A file will be checked if:
    1. It's not a hidden file
    2. It ends with an extension in check_files_set or matches case insensitive to a 
    member of check_files_set
    """

    return filename[0] != '.' and any([((check_file[0] == '.' and filename.endswith(check_file)) or
                                        (check_file[0] != '.' and filename.upper() == check_file))
                                       for check_file in check_files_set])


def clean_contents(contents, regex, repl):
    # Returns contents of an assumed C/C++ source file with all matches on given regex
    # replaced with repl
    return re.sub(regex, repl, contents)


def regex_match_in_code(code, regex):
    # Determines whether code has a match for a certain regex
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
    # Performs file cleaning for code checked files (removing comments, string, character literals)
    return clean_contents(clean_contents(contents, COMMENTED_REGEX, "\n"), STRING_LITERAL_REGEX, "")


def report_filelines(filelines, violation, line_print):
    """
    Informs the user of the files and lines where violation occurred - helper to report_style_violations
    filelines - dict from filename (str) -> list with lines where violations occurred
    violation - name of the violation
    line_print - function that a line is passed to for each line in filelines lists
    """
    result = ""
    if filelines:
        result += autograde.COLORIZE(f"    {violation}:\n", color=autograde.RED)
        for file, lines in filelines.items():
            result += autograde.COLORIZE("        " + file + ": \n", color=autograde.RED)
            for line_info in lines[:MAX_VIOLATIONS_TO_SHOW]:
                result += autograde.COLORIZE("            " +
                                 line_print(line_info) + '\n', color=autograde.RED)
            if len(lines) > MAX_VIOLATIONS_TO_SHOW:
                result += autograde.COLORIZE(
                    f"            {len(lines) - MAX_VIOLATIONS_TO_SHOW} more violations were found, but were not printed!\n", color=autograde.RED)
    return result


class StyleChecker:
    def __init__(self):
        self.testset_common = toml.load(TESTSET_TOML_PATH)["common"]
        self.config = toml.load(CONFIG_TOML_PATH)["style"]
        self.style_results = ""
        
        if "style_check" in self.testset_common and self.testset_common["style_check"]:
            self.calculate_max_style_score()
            self.collect_all_style_violations()
            self.calculate_style_score()
            self.generate_report()
        else:
            self.max_style_score = 0
            self.all_style_violations = None
            self.style_score = 0

    def calculate_max_style_score(self):
        self.max_style_score = sum(
            self.config[k] for k in STYLE_WEIGHTS_VIOLATIONS)

    def collect_all_style_violations(self):
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
        """

        # Collect names, paths of files to check for style
        # Using should_check() with 2 different file sets, construct 2 lists
        # 1st list - files to check for columns, tabs, and TODOs
        # 2nd list - files to check for break, &&, ||, !
        first_files_to_check = list()
        second_files_to_check = list()
        for entry in os.scandir(SUBMISSION_FOLDER):
            if entry.is_file():
                if should_check(entry.name, self.config["NON_CODE_STYLE_CHECKSET"]):
                    first_files_to_check.append((entry.name, entry.path))
                if should_check(entry.name, self.config["CODE_STYLE_CHECKSET"]):
                    second_files_to_check.append((entry.name, entry.path))

        # Construct violations dictionary using helper functions
        self.all_style_violations = {
            VIOL_COLS: collect_violations(first_files_to_check, None, lambda line: len(line.rstrip('\n')) > self.config["MAX_COLUMNS"]),
            VIOL_TABS: collect_violations(first_files_to_check, None, lambda line: '\t' in line),
            VIOL_TODO: collect_violations(first_files_to_check, lambda contents: clean_contents(contents, STRING_LITERAL_REGEX, ""), lambda line: 'TODO' in line),
            VIOL_AND: collect_violations(second_files_to_check, code_clean, lambda line: '&&' in line),
            VIOL_OR: collect_violations(second_files_to_check, code_clean, lambda line: '||' in line),
            VIOL_BREAK: collect_violations(second_files_to_check, lambda contents: clean_contents(code_clean(contents), SWITCH_CASE_REGEX, ""), lambda line: 'break;' in line),
            VIOL_NOT: collect_violations(second_files_to_check, lambda contents: clean_contents(code_clean(contents), CHARACTER_LITERAL_REGEX, ""), lambda line: regex_match_in_code(line, NOT_BUT_NOT_EQ_REGEX)),
            VIOL_BOOL_ZEN: collect_violations(
                second_files_to_check, code_clean, lambda line: regex_match_in_code(line, BOOLEAN_ZEN_REGEX))
        }

    def calculate_style_score(self):
        """
        Gets the student's style score as follows
        """

        # Writing out because 1-liner is somewhat hard to read
        deductions = 0
        for weight, violations in STYLE_WEIGHTS_VIOLATIONS.items():
            # Deduct testset_common[weight] points if any of the violations occurred that the
            # weight corresponds to
            deductions += self.config[weight] * \
                any(self.all_style_violations[v] for v in violations)
        self.style_score = self.max_style_score - deductions

    def default_line_print(self, line_info):
        # Default function for returning string for when a violation line is printed
        return (line_info[0][:self.config["MAX_COLUMNS"]] + " < line cut off >") if len(line_info[0]) > self.config["MAX_COLUMNS"] else line_info[0]

    def generate_report(self):
        """
        Reports the style violations from check_style() - i.e. actually prints them to the autograder results
        """
        if self.all_style_violations is None:
            # Adding this print statement just for nicety to whoever is setting up autograder/grader
            message = autograde.COLORIZE("Style check was not run!\n", autograde.CYAN)
            return message

        message = ""

        if not any(self.all_style_violations.values()):
            message += autograde.COLORIZE("\nStyle check passed, good work!\n", color=autograde.GREEN)
        else:
            # Define here a dict mapping violation -> how lines with that violation should be printed
            line_printers = dict()

            # When maximum number of cols are violated, since line numbers are accurate to the original file, we print
            # the line and the line number
            line_printers[VIOL_COLS] = lambda line_info: f"line {line_info[1]}: " + self.default_line_print(line_info)

            # For tabs, it is possible for students to have a line with just a tab that's otherwise blank, which is
            # visually a little confusing - therefore we have that if the line is empty besides whitespace, we will print
            # the substitute instead
            line_printers[VIOL_TABS] = lambda line_info: f"line {line_info[1]}: " + (
                self.default_line_print(line_info) if len(line_info[0].strip()) > 0 else EMPTY_LINE_SUBSTITUTE)

            # For all the remaining violations, we just print the line without the number due to cleaning making the line
            # numbers not make sense (see check_style/collect_violations)
            line_printers.update(dict.fromkeys(
                [VIOL_TODO, VIOL_AND, VIOL_OR, VIOL_BREAK, VIOL_NOT, VIOL_BOOL_ZEN], self.default_line_print))

            for viol, printer in line_printers.items():
                message += report_filelines(
                    self.all_style_violations[viol], f"{viol} found in", printer)

        self.style_results = message
