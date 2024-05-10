#!/usr/bin/env python3
"""
validate_submission.py
matt russell
5-23-2023

validates that a provided submission is acceptable; either it's before the due date or token-acceptable, 
and it's submission # <= the max permissible for the course.

uses tokens if required. 

"""

import os
import json
import toml
from pathlib import Path
from dateutil import parser as dateparser
from datetime import timedelta
from token_manager import DB, INFORM, BLUE


def EXIT_FAIL(message, db=None):
    message = "❌ " + message
    message += f"\nIf you have already submitted, you can activate a different submission by clicking the"
    message +=  "'Submission History' button below. Whichever submission you activate will be the one that is graded.\n"
    print(message)

    if db:
        db.write_report()
        db.close()

    with open(RESULTS_FILE, 'w') as f:
        json.dump( {
                "score": -1, 
                "visibility": "visible",
                "stdout_visibility": "visible"
            }, f)
    exit(1)

def EXIT_SUCCESS(message, db=None):
    if   "by default"       in message: emoji = "🔵"
    if   "zero tokens used" in message: emoji = "🟢"
    elif "one token used"   in message: emoji = "🟡"  
    elif "two tokens used"  in message: emoji = "🟠"
    message = f"{emoji} {message} \n"

    subs_left = MAX_SUB_NUM - CURR_SUB_NUM
    if   subs_left == 0: emoji = "🔴"
    elif subs_left == 1: emoji = "🟠"
    elif subs_left == 2: emoji = "🟡"
    else:                emoji = "🟢"
    message += f"{emoji} This is submission {CURR_SUB_NUM} / {MAX_SUB_NUM} for this assignment.\n"
    print(message)

    with open(TOKEN_RESULTS_FILE, 'w') as f:
        f.write(message)
        if db:
            db.write_report(also_to_file=f)
            db.close()
    exit(0)

def make_dict_case_insensitive(d):
    """
    Chami: 

    Prepares a dictionary for case insensitive queries -- i.e. it makes its
    keys lowercase. If a dictionary has 2 keys which are the same when
    compared case insensitively, an error is raised. 

    Parameters:
        d - dict[str, Any]

    Returns:
        New dictionary matching above (dict[str, Any])

    Usage:
        Convert token, submission exemption dictionaries to enable case insensitive 
        search on email. Again, this is because emails by definition are meant to 
        be case insensitive anyway.

        We raise an error to signify that in either of these cases if there are 2
        different casings of the same email specified in the configuration, that's 
        a problem. 

        Example: we want to inform a staff member if they've done something like 

        { "swaminathan.lamelas@tufts.edu" = 3, "Swaminathan.Lamelas@tufts.edu" = 2 }
    """

    new_dict = dict() 
    for k, v in d.items():
        k_insensitive = k.lower() 
        if k_insensitive in new_dict:
            raise RuntimeError(f"Invalid configuration, have multiple casings of \'{k_insensitive}\', configuration keys = {', '.join(d)}")
        new_dict[k_insensitive] = v 
    return new_dict



INFORM("🔑 Submission Validation", BLUE)

"""
    establish paths
""" 
RESULTS_FILE       = "/autograder/results/results.json"
TOKEN_RESULTS_FILE = "/autograder/results/token_results"
SUBMISSION_DIR     = "/autograder/submission"
SECRETS_PATH       = "/autograder/source/.secrets"
CONFIG_PATH        = "/autograder/source/config.toml"
TESTSET_PATH       = "/autograder/testset.toml"
SUB_META_PATH      = "/autograder/submission_metadata.json"

METADATA      = json.loads(Path(SUB_META_PATH).read_text())
TESTSET_TOML  = toml.load(TESTSET_PATH)['common']
CONFIG        = toml.load(CONFIG_PATH)
SECRETS       = toml.load(SECRETS_PATH)
AG_CONFIG     = CONFIG['repo']
TOKEN_CONFIG  = CONFIG['tokens']
ASSIGN_NAME   = METADATA['assignment']['title']

"""
    extract the email of the user from the metadata file.  
    notes:
        weird case with gradescope - the only submission that has a 'user' field is the active one

    CL: This swapped from 'name' to 'email' to account for the case of multiple students having the same name
    (which would double count tokens for the lack of a better word) or a student sharing a name with a 
    staff member (which could have them bypass the token check)

    Lastly, the use of email is consistent with the CLI hitme system which uses it as a primary key in
    the hitme database. 

    We lowercase the email to enable case insentive email comparison when looking in the various 
    TOML configuration files where users could have entered submission or token exemptions.
""" 
try:
    GRADESCOPE_NAME = METADATA['users'][0]['email'].lower()
    print(f"Submitter: {GRADESCOPE_NAME}")
except:
    EXIT_FAIL("ERROR: You can only run an active submission on gradescope.")


"""
    test set of required files
    Chami: moved this to be before TEST_USER check just so that if a TA submits 
    some code under their name missing a required file then that should be
    reported immediately before they bypass the token and submission limit
    checks that occur below. Otherwise, the autograder tries to run all
    the tests and it takes awhile for them to all fail compilation
"""
REQUIRED_FILES  = set(TESTSET_TOML.get('required_files', []))
SUBMITTED_FILES = set(os.listdir(SUBMISSION_DIR))
MISSING_FILES   = REQUIRED_FILES - SUBMITTED_FILES 
if len(MISSING_FILES) > 0:
    EXIT_FAIL(f"ERROR: Required files missing: {MISSING_FILES} -- this does not count as a submission!")


""" 
    extract the number of current / maximum submissions
    notes:
        if student has an exception for the given assignment, then use that value instead of the course default

    Chami: moved this here because MAX_SUB_NUM and CURR_SUB_NUM must be defined before the first call
    to EXIT_SUCCESS including when test user is passing by default 
"""
PREV_SUBMISSIONS = [submission for submission in METADATA['previous_submissions'] if float(submission['score']) > 0]
CURR_SUB_NUM     = len(PREV_SUBMISSIONS) + 1
try: 
    # chami: convert user specifications in testset.toml for max submission exceptions to enable case insensitive 
    # search by converting all specified emails to lowercase -- this is done here because 'max_submission_exceptions'
    # may not be in common section of testset.toml
    TESTSET_TOML['max_submission_exceptions'] = make_dict_case_insensitive(TESTSET_TOML['max_submission_exceptions'])
    MAX_SUB_NUM  = TESTSET_TOML['max_submission_exceptions'][GRADESCOPE_NAME]
except KeyError: 
    MAX_SUB_NUM  = TESTSET_TOML.get('max_submissions', CONFIG['gradescope']['SUBMISSIONS_PER_ASSIGN'])    


"""
    If the user is a test user, we're done. 

    Chami: We do a case insensitive check here -- GRADESCOPE_NAME has already been
    lowercased, and here we lowercase the user specified test users in config.toml 
"""
try:
    if GRADESCOPE_NAME in { u.lower() for u in CONFIG['gradescope']['TEST_USERS'] }:
        EXIT_SUCCESS("Test user - passing submission validation by default.")
except KeyError:
    pass


"""
    test the max submission number
"""
if CURR_SUB_NUM > MAX_SUB_NUM:
    EXIT_FAIL(f"ERROR: Max submissions exceeded for this assignment.")


# If for this assignment we specified in testset.toml not to manage tokens, exit early 
# Example for gerp medium large
if 'manage_tokens' in TESTSET_TOML and not TESTSET_TOML['manage_tokens']:
    EXIT_SUCCESS(f"not managing tokens for {ASSIGN_NAME} - passed by default")

# If manage_tokens was not specified for this assignment but was turned off course wide,
# exit early (not used for 15 but for compatability) -- note we assume MANAGE_TOKENS is
# always provided in config.toml 
if 'manage_tokens' not in TESTSET_TOML and not TOKEN_CONFIG['MANAGE_TOKENS']:
    EXIT_SUCCESS("not managing tokens for course - passed by default")

# Otherwise, at this point manage_tokens is either set in testset.toml as true or it
# was enabled course wide -- so we move forward to token check

"""
    establish token constants
"""
GRACE_TIME         = timedelta(minutes=TOKEN_CONFIG["GRACE_TIME"]) 
TOKEN_TIME         = timedelta(minutes=TOKEN_CONFIG["TOKEN_TIME"])
SUBMISSION_TIME    = dateparser.parse(METADATA['created_at']) - GRACE_TIME
DUE_TIME           = dateparser.parse(METADATA['users'][0]['assignment']['due_date'])
ONE_TOKEN_DUE_TIME = DUE_TIME + TOKEN_TIME
TWO_TOKEN_DUE_TIME = DUE_TIME + TOKEN_TIME + TOKEN_TIME

"""
    set opening balance of the user
    notes: 
        if they are an 'excepted' user then use that value, otherwise choose course default
"""
try:
    # chami: convert user specifications in config.toml for token exceptions to enable case insensitive 
    # search by converting all specified emails to lowercase -- this is done here because 'exceptions'
    # may not be in token section of config.toml
    TOKEN_CONFIG['EXCEPTIONS'] = make_dict_case_insensitive(TOKEN_CONFIG['EXCEPTIONS'])
    OPENING_BALANCE = TOKEN_CONFIG['EXCEPTIONS'][GRADESCOPE_NAME]
except KeyError:
    OPENING_BALANCE = TOKEN_CONFIG['STARTING_TOKENS']
    
"""
    establish db session and determine token usage for the current assignment
    notes: 
        the db session is specific to the assignment and the student. 
        assignment and student will be added to the db if needed. 
"""
db = DB(ASSIGN_NAME, GRADESCOPE_NAME, OPENING_BALANCE, SECRETS, CONFIG)
TOKENS_LEFT, ASSIGN_TOKENS_USED = db.get_tokens_left_and_assign_usage()

"""
    early or late
"""
if SUBMISSION_TIME <= DUE_TIME: 
    EXIT_SUCCESS(f"Submission arrived before the due date - so zero tokens used.", db=db)

if SUBMISSION_TIME > TWO_TOKEN_DUE_TIME:
    EXIT_FAIL("ERROR: After two-token deadline.", db=db)

"""
    before one token deadline
"""
if SUBMISSION_TIME <= ONE_TOKEN_DUE_TIME:
    if ASSIGN_TOKENS_USED  == 1:
        EXIT_SUCCESS(f"Already used one token previously for {ASSIGN_NAME}, so zero tokens used.", db=db)

    if ASSIGN_TOKENS_USED  == 0:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("Tokens needed: 1, tokens available: 0.", db=db)
        
        db.use_token()
        EXIT_SUCCESS(f"Before one token deadline, and no tokens yet used, so one token used.", db=db)

    EXIT_SUCCESS(f"Already used more than one token, but before one-token deadline, so zero tokens used.", db=db)
    
"""
    before two token deadline
"""
if SUBMISSION_TIME <= TWO_TOKEN_DUE_TIME:

    if ASSIGN_TOKENS_USED == 2: 
        EXIT_SUCCESS(f"Already used two tokens previously for {ASSIGN_NAME}, so zero tokens used.", db=db)
    
    if ASSIGN_TOKENS_USED == 1:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("Tokens needed: 2, tokens available: 0.", db=db)

        db.use_token()
        EXIT_SUCCESS(f"Already used one token for {ASSIGN_NAME}; after one token deadline, so one token used.", db=db)
    
    if ASSIGN_TOKENS_USED == 0:
        if TOKENS_LEFT < 2:
            EXIT_FAIL(f"Tokens needed: 2, tokens available: {TOKENS_LEFT}.", db=db)

        db.use_token()
        db.use_token()
        EXIT_SUCCESS(f"Before the two token deadline, and haven't used any tokens yet, so two tokens used.", db=db)
    
    EXIT_SUCCESS(f"Already used more than two tokens, but before two-token deadline, so zero tokens used.", db=db)