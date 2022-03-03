#!/usr/bin/env python3



# Tried to be cool and print passed and failed in colors on Gradescope, but
# they wrap everything in a <pre> tag that is pre-formatted
# class htmlclr:
#     OK   = "#008000"    # Green
#     FAIL = "#FF0000"    # Red
# HTML_FAIL = "<H1><FONT COLOR=\"{}\">FAILED!</H1>".format(htmlclr.FAIL)
# HTML_PASS = "<H1><FONT COLOR=\"{}\">PASSED!</H1>".format(htmlclr.OK)

import os
import json
from datetime import datetime, timezone
from webbrowser import get

# We need dateutil on Gradescope, but not on Halligan. This library does not
# exist locally, so we simply pass when running locally.
try:
    from dateutil import parser
except:
    pass

# For printing in pretty colors : )
class termclr:
    OK        = '\033[92m'   # Green
    WARN      = '\033[93m'   # Yellow
    FAIL      = '\033[91m'   # Red
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKCYAN    = '\033[96m'
    ENDC      = '\033[0m'    # Stop colors
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

# Error and warning in color. 
ERROR = "{}Error:{}".format(termclr.FAIL, termclr.ENDC)
WARN  = "{}Warning:{}".format(termclr.WARN, termclr.ENDC)


### Set up paths we need.  ###

# Path to this file
here = os.path.dirname(os.path.abspath(__file__))

# Path to student testXX.summary.json files
student_test_summaries = os.path.join(
    here,
    "..",
    "testing", 
    "student.1.test_summaries",
    "testset"
)

# Path to Compile Logs
compile_log_path = os.path.join(here, "..", "testing", "compileLogs")

# Path to ~/results directory needed by Gradescope  
results_path = os.path.join(here, "..", "results")

# Path to results.json file we populate with test results. Also required by
# Gradescope to properly show test results to students
results_json = os.path.join(results_path, "results.json")

# Path to our testset.json file we provide. Holds information for Noah's
# Framework to run the autograder. We also use it to populate results.json
testset_json_path = os.path.join(here, "testset", "testset.json")

# This file is created by Gradescope, and so, does not exist on Halligan.
# We use it to dynamically pull the duedate in order to properly set the 
# tentative_autograder_test visibility
metadata_path = os.path.join("/autograder", "submission_metadata.json")


# Gradescope visibility options
visible         = "visible"         # Used for "public" group
after_published = "after_published" # Used for "private" group
after_due_date  = "after_due_date"  
hidden          = "hidden"          # Careful if using this setting! Gradescope
                                    # hides the total score from students if 
                                    # ANY test is hidden.... smh....

# Result strings
RESULT      = "Result:   "
REASON      = "Reason:   "
FAILED      = "FAILED!"
PASSED      = "PASSED!"
POS_MITGATE = "Possible Mitigation:\n\n"
COMPILE_LOG = "\nCompile Log:\n\n"
NOT_FOUND   = "Executable Not Found!"

# score setting
SINGLE_TEST_SCORE = 1

mitigation_map = {
    "Contents of results file stdout are incorrect": "\tYour output to Standard Out did not match the expected output.\n"\
                                                     "\tCheck that your output to Standard Out EXACTLY matches\n"\
                                                     "\tthat of the Assignment Spec and/or the reference. (Watch out for trailing whitespace!)",

    "Contents of results file stderr are incorrect": "\tYour output to Standard Error and/or your Exception Message did not match the expected output.\n"\
                                                     "\tCheck that your output to Standard Error and/or your Exception Message EXACTLY matches\n"\
                                                     "\tthat of the Assignment Spec and/or the reference. (Watch out for trailing whitespace!)",

    "Program executable not found": "\tThere was a problem compiling the executable for this test.\n"\
                                    "\tCheck the compiler output above. Make sure your function names,\n"\
                                    "\tinput and output types match the spec EXACTLY!",

    "Results file stdout not found": "\tYour program terminated before it produced anything to Standard Out!\n"\
                                     "\tPossible reasons include Segfaults, Illegal Instructions or other 'fatal' errors'"
}

def get_mitigation(key):
    if key in mitigation_map:
        return mitigation_map[key]
    else:
        return "No standard mitigation suggestion is available!"


def main(): 
    # Gradescope requires a root level folder called /results to hold 
    # results.json.
    # We create this locally from launch_autograder.py, and on the Gradescope
    # end from setup.sh. Here we just ensure the file exists.
    if not os.path.exists(results_json):
        print("{}\n{} does not exist!\nGradescope and this "\
              "script require this file to run properly. Exiting...".format(ERROR, results_json))
        exit(1)

    # We do one pass to set the top level attributes for results.json. The 
    # rational being that even if all else fails, at least we will have set the
    # total autograder score, and top level visibility setting correctly.
    set_top_level_attributes()

    # Since Gradescope is dumb and won't release the Autograder score until you
    # publish the entire assignment's grades, we have to do a workaround to 
    # show the students their tentative final score in a separeate test. By 
    # convention this test is named 'test00' and is made hidden once the 
    # due_date for the assignment has passed.
    set_tentative_autograder_score()

    # Now, for each test in our testset.json file, we create a corresponding 
    # test result in results.json in the format that Gradescope expects
    add_student_test_results_to_results_json()


def set_top_level_attributes():
    num_passed = get_num_passed() # Get Top-level score for entire assignment
    
    with open(results_json, "r") as f:
        results_data = json.load(f)
        results_data["score"] = num_passed
        results_data["visibility"] = after_published
        results_data["stdout_visibility"] = after_published

    with open(results_json, "w") as f:
        json.dump(results_data, f, indent = 4)


# Add the tentative final autograder score as the first test, namely 'test00'.
# We now leave this test as "visible" at all times, but change the name of 
# the test to 'Final Autograder Score' once the date today is past the 
# due_date. If it is before the due_date, we title it 'Tentative Autograder 
# Score'. 
def set_tentative_autograder_score():
    with open(results_json, "r") as f:
        results_data = json.load(f)
        name, output = set_name_and_output()
        results_data["tests"].append(make_single_test_result(
                name       = name,
                # visibility = set_tentative_autograder_visibility(),
                visibility = visible,
                score      = get_num_passed(),
                max_score  = get_autograder_max_score(),
                output     = output
            )
        )
    # Save the results back to results.json
    with open(results_json, "w") as f:
        json.dump(results_data, f, indent = 4)


# If we are testing on Halligan, the 'metadata_path' will not exist, since
# this file is created by Gradescope. We essentially ignore this and
# return 'visible' since it doesn't really matter what we return here as 
# the results.json file is not used by any of our grading programs locally.
#
# If we are running on Gradescope however, this function determines if the 
# tentative autograder score should be visible, or if it should be hidden by
# comparing the date today with the due_date for the assignment. We get the 
# due_date from the metadata.json that Gradescope makes.
def set_tentative_autograder_visibility():
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

            due_date = parser.parse(metadata["assignment"]["due_date"])
            today    = datetime.now(timezone.utc)

            return visible if today <= due_date else hidden
    except:
        return visible

# Some BullS*&%t we had to do because Gradescope does not display the top-level
# Autograder score, even if you set visibility to "visible" and set the score
# manually.... so dumb...
# Gradescope will hide the final autograder score if ANY of your individual
# tests are set with the visibility == 'hidden'
def set_name_and_output():

    before_duedate_title = "test00 - Tentative Final Autograder Score"
    before_duedate_msg   = "This is your TENTATIVE final autograder score.\n" \
                        "Your actual final score will be displayed here and in " \
                        "the upper right-hand corner\nonce we release "    \
                        "final grades for this assignment.\n\n"              \
                        "If you are not happy with it, you may resubmit.\n\n"\
                        "CAUTION: You have 5 submissions per assignment. " \
                        "Use them wisely! : )"

    after_due_date_title = "test00 - Final Autograder Score"
    after_due_date_msg   = "This is your Final Autograder Score"

    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

            due_date = parser.parse(metadata["assignment"]["due_date"])
            today    = datetime.now(timezone.utc)

            if today <= due_date:
                return before_duedate_title, before_duedate_msg
            else:
                return after_due_date_title, after_due_date_msg
    except:
        return "test00", "You are running this on Halligan. FYI this file is "\
                         "only important to Gradescope."

# Get the max autograder score for the assignment. Currently, every test is
# weighted exactly the same, i.e. 1 test == 1 point, so we can simply return
# the length of the list of tests.
def get_autograder_max_score():
    # Make sure ~/source/testset/testset.json exists
    try:
        with open(testset_json_path, "r") as testset_f:
            testset_json = json.load(testset_f)
    except Exception as e:
        print(e)
        print("{} was not able to be opened! Check that the file exists.".format(testset_json_path))
        exit(1)

    return len(testset_json["tests"])

    
# Returns a dictionary for a testcase in a form that Gradescope can understand.
# We append dictionaries returned by this function to the results.json["tests"]
# list.
def make_single_test_result(name, visibility, score, max_score, output):
    test_result = {
        "name": name,
        "visibility": visibility,
        "score": score,
        "max_score": max_score,
        "output": output
    }
    return test_result


def get_num_passed():
    # Make sure ~/testing/testset/student.1.test
    if not os.path.exists(student_test_summaries):
        print("Error:")
        print("\t{} does not exist.".format(student_test_summaries))
        exit(1)

    num_passed = 0
    for root, dirs, files in os.walk(student_test_summaries):
        for file in files:
            with open(os.path.join(student_test_summaries, file), "r") as f:
                json_data = json.load(f)
                if json_data['success'] == "PASSED":
                    num_passed += 1
    
    return num_passed



def add_student_test_results_to_results_json():
    # Make sure ~/source/testset/testset.json exists
    try:
        with open(testset_json_path, "r") as testset_f:
            testset_json = json.load(testset_f)
    except Exception as e:
        print(e)
        print("{} was not able to be opened! Check that the file exists.".format(testset_json_path))
        exit(1)

    # If we got this far we know results.json exists, so no need to check.
    #
    # Iterate through our testset.json file to create a single entry for each
    # test, regardless of if that test was successfully run by nmtestrunner.py
    # or not.
    with open(results_json, "r") as f:
        results_data = json.load(f)
        for test in testset_json["tests"]:

            testname = test["name"]
            score, reason, valgrind_results = get_student_test_result(get_summary_path(testname), testname)

            test_result_dict = make_single_test_result(test["description"],
                                                       determine_visibility(test),
                                                       score,
                                                       SINGLE_TEST_SCORE,
                                                       "{}\n\n{}".format(reason, valgrind_results)
                                                       )

            results_data["tests"].append(test_result_dict)

    # Save the results back to results.json
    with open(results_json, "w") as f:
        json.dump(results_data, f, indent = 4)



# Returns the score as an integer, Reason for passing or failing a test, and
# the results of valgrind for that test, if valgrind was run for this test.
#
# Takes the path to the testXX.summary.json file created by nmtestrunner.py
# and Noah's Framework. 
def get_student_test_result(test_summary_path, testname):
    not_run = "Valgrind: Valgrind was intentionally not run on this test."
    not_run_because_no_test = "Valgrind: Could not be run because the test failed to run!"
    if not os.path.exists(test_summary_path):
        # If the testXX.summary.json does not exist, this means that 
        # Noah's framework failed to create it. Most likely this is because 
        # the executable did not build.
        return  0,                                                           \
                "Test failed to run. Possible reasons: "                     \
                "\n\tExecutable failed to compile,\n\tIllegal Instructions," \
                "\n\tSegfaults, and other 'fatal' errors.",  \
                not_run_because_no_test
    else:
        with open(test_summary_path, "r") as f:
            summary_data = json.load(f)

            # First, make sure executable was found. If not, return the proper
            # error result.
            if executable_not_found(summary_data):
                return  0, \
                        get_failure_reason_and_mitigation(summary_data["reason"], exec_not_found=True, testname=testname), \
                        not_run_because_no_test

            # Check if passed, if so, return 1 and a happy response,
            # if not, get reason why. Get Valgrind results as well.
            if summary_data["success"] == "PASSED":
                return 1,                                                   \
                       "{}{}".format(RESULT, PASSED),                       \
                       not_run if "valgrind" not in summary_data else       \
                            get_valgrind_result(summary_data["valgrind"])    
            else:
                return  0,                                                          \
                        get_failure_reason_and_mitigation(summary_data["reason"]),  \
                        not_run if "valgrind" not in summary_data else              \
                            get_valgrind_result(summary_data["valgrind"])    

# Returns a formatted string with the reason a test failed, taken verbatim 
# from testXX.summary.json, and possible mitigation. We use the failure 
# reason as the key to a dictionary of possible mitigations.
# If a test fails to compile, we grab the contents compileLog for the failed
# test and add it to the returned string
def get_failure_reason_and_mitigation(reason, exec_not_found=False, testname=None):
    
    if exec_not_found:
        return format_reason_and_mitigation(
            {
                RESULT:      FAILED,
                REASON:      NOT_FOUND,
                COMPILE_LOG: get_compile_log(testname),
                POS_MITGATE: get_mitigation("Program executable not found")
            }
        )
    else:
        return  format_reason_and_mitigation(
            {
                RESULT:      FAILED,
                REASON:      reason,
                POS_MITGATE: get_mitigation(reason)
            }
        )

# Format the reason and mitigation into a nice format that looks good on 
# Gradescope. Using a dict, we can dynamically pass in any number of
# key->value pairs and return a single formatted string.
def format_reason_and_mitigation(reason_dict):
    formatted_output = ""
    for k, v in reason_dict.items():
        output_item = "{}{}\n".format(k, v)
        formatted_output += output_item
    return formatted_output


def get_compile_log(testname):
    log_path = get_log_path(testname)
    parsed_log_output = ""

    try:
        with open(log_path, "r") as f:
            log_output = f.readlines()
            for line in log_output:
                if not line.startswith("make: Entering") and not line.startswith("make: Leaving"):
                    parsed_log_output += line
    except:
        parsed_log_output = "There was a problem generating the compilation log"\
            " for this test! Please contact the course staff."
        

    return parsed_log_output


def get_log_path(testname):
    executable_name = get_executable_name(testname)
    return os.path.join(compile_log_path, executable_name + ".log")

def get_executable_name(testname):
    with open(testset_json_path, "r") as f:
        testset = json.load(f)
        for test in testset["tests"]:
            if test["name"] == testname:
                return test["program"]


# super ugly but working code to determine if a test's executable failed to
# compile
def executable_not_found(summary_data):
    if "executionsummary" in summary_data:
        if "execution_failed" in summary_data["executionsummary"]:
            if "executablenotfound" in summary_data["executionsummary"]["execution_failed"]:
                return True
    return False

# Extracts the valgrind result from a dictionary of results we grab from each
# test.summary.json.  We return a formatted string that looks nice when 
# displayed on Gradescope
def get_valgrind_result(valgrind_data):
    positive_result = "Valgrind: PASSED! No Memory Leaks or Errors."
    negative_result = "Valgrind: FAILED!\n\tReason(s): "
    any_failed      = False
    for k, v in valgrind_data.items():
        if int(v) != 0:
            any_failed = True
            negative_result += "\n\t    Memory {}: {} ".format(k, v) if k == "Errors" else \
            "\n\t    Memory Leak - {}: {}".format(k, v)
    
    return positive_result if not any_failed else negative_result
 
# Returns path to a single student testXX.summay.json file
def get_summary_path(testname): 
    return os.path.join(student_test_summaries, "{}.summary.json".format(testname))

# Returns visibility setting, based on the category we set in out testset.json
# for each test.
def determine_visibility(test):
    return visible if test["category"] == "public" else after_published

if __name__ == "__main__":
    main()

