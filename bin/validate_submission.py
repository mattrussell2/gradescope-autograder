#!/usr/bin/env python3
"""
validate_submission.py
matt russell
5-23-2023

validates that a provided submission is acceptable; either it's before the due date or token-acceptable, 
and it's submission # <= the max permissible for the course.

uses tokens if required. 

"""
from dateutil    import parser as dateparser
from datetime    import timedelta
from dataclasses import dataclass 
from pathlib     import Path
import json
import os
import toml
import psycopg2

GREEN       = "32m"
MAGENTA     = "35m"
CYAN        = "36m"
START_COLOR = "\033[1;"
RESET_COLOR = "\033[0m"

def COLORIZE(s, color):
    return f"{START_COLOR}{color}{s}{RESET_COLOR}"

def INFORM(s, color): 
    print(COLORIZE(s, color))

INFORM("== Submission Validation ==", CYAN)

def make_token_report():
    assigns = filter(lambda value: value > 0, TOKENDATA)
    report =  "TOKEN USAGE REPORT"
    report += "[assignment]-------[tokens used]"
    for assign, tokens in assigns.items():
        report += f"{assign}: {tokens}"
    return report

def EXIT_FAIL(message):
    message += f"\nIf you have already submitted, you can activate a different submission by clicking the 'Submission History' button below. Whichever submission you activate will be the one that is graded.\n"
    message += make_token_report()
    INFORM(message, MAGENTA)
    with open("/autograder/results/results.json", 'w') as f:
        json.dump( {
                "score": -1, 
                "visibility": "visible",
                "stdout_visibility": "visible"
            }, f)
    try:
        CONN.close()
    except:
        pass
    exit(1)

def EXIT_SUCCESS(message):
    message += f"\nYou have used {len(PREV_SUBMISSIONS) + 1} / {MAX_SUBMISSIONS} submissions for this assignment.\n"
    message += make_token_report()
    with open("/autograder/results/token_results", 'w') as f:
        f.write(message)
    INFORM(message, GREEN) 
    try:
        CONN.close()
    except:
        pass
    exit(0)

CONFIG       = toml.load('/autograder/source/config.toml')
AG_CONFIG    = CONFIG['repo']
TOKEN_CONFIG = CONFIG['tokens']
TESTSET_TOML = toml.load('/autograder/testset.toml')['common']
METADATA     = json.loads(Path('/autograder/submission_metadata.json').read_text())

NAME             = METADATA['users'][0]['name']
PREV_SUBMISSIONS = [submission for submission in METADATA['previous_submissions'] if float(submission['score']) > 0]
ASSIGN_NAME      = METADATA['assignment']['title'].replace(' ', '_')

MAX_SUBMISSIONS  = TESTSET_TOML.get('max_submissions', CONFIG['misc']['SUBMISSIONS_PER_ASSIGN'])
if 'max_submission_exceptions' in TESTSET_TOML and NAME in TESTSET_TOML['max_submission_exceptions']:
    MAX_SUBMISSIONS = TESTSET_TOML['max_submission_exceptions'][NAME]

if 'TEST_USERS' in CONFIG['misc'] and NAME in CONFIG['misc']['TEST_USERS']:
    EXIT_SUCCESS(f"Test user - passing submission validation by default.")

if len(PREV_SUBMISSIONS) >= MAX_SUBMISSIONS: 
    EXIT_FAIL(f"ERROR: Max submissions exceeded for this assignment.")

REQUIRED_FILES  = set(TESTSET_TOML.get('required_files', []))
SUBMITTED_FILES = set(os.listdir('/autograder/submission'))
MISSING_FILES   = REQUIRED_FILES - SUBMITTED_FILES 
if len(MISSING_FILES) > 0:
    EXIT_FAIL(f"ERROR: Required files missing: {MISSING_FILES}")

if not TOKEN_CONFIG['MANAGE_TOKENS']:
    EXIT_SUCCESS("SUCCESS")

GRACE_TIME         = timedelta(minutes=TOKEN_CONFIG["GRACE_TIME"]) 
TOKEN_TIME         = timedelta(minutes=TOKEN_CONFIG["TOKEN_TIME"])
SUBMISSION_TIME    = dateparser.parse(METADATA['created_at']) - GRACE_TIME
DUE_TIME           = dateparser.parse(METADATA['users'][0]['assignment']['due_date'])
ONE_TOKEN_DUE_TIME = DUE_TIME + TOKEN_TIME
TWO_TOKEN_DUE_TIME = DUE_TIME + TOKEN_TIME * 2

if SUBMISSION_TIME > TWO_TOKEN_DUE_TIME:
    EXIT_FAIL("ERROR: After two-token deadline.")

COMMANDS = {
    'get_headers': "SELECT column_name FROM information_schema.columns WHERE table_name = 'tokens';",
    'add_user': f"INSERT INTO tokens(pk) VALUES('{NAME}');",
    'get_tokens': f"SELECT * FROM tokens WHERE pk = '{NAME}';",
    'use_token': f"UPDATE tokens SET \"tokens left\" = \"tokens left\" - 1, \"{ASSIGN_NAME}\" = \"{ASSIGN_NAME}\" + 1 WHERE pk = '{NAME}';", 
    'add_assignment': f"ALTER TABLE tokens ADD COLUMN \"{ASSIGN_NAME}\" INTEGER DEFAULT 0;"
}

CONN   = psycopg2.connect(TOKEN_CONFIG["POSTGRES_REMOTE"])
CURSOR = CONN.cursor()

CURSOR.execute(COMMANDS['get_headers'])
HEADERS = [x[0] for x in CURSOR.fetchall()]

# add the assignment to the db if it not there yet.
if ASSIGN_NAME not in HEADERS:
    CURSOR.execute(COMMANDS['add_assignment'])
    CONN.commit()

    CURSOR.execute(COMMANDS['get_headers'])
    HEADERS = [x[0] for x in CURSOR.fetchall()]


CURSOR.execute(COMMANDS['get_tokens'])
USERDATA = CURSOR.fetchone()
if USERDATA == None:
    CURSOR.execute(COMMANDS['add_user']) 
    CONN.commit()
    CURSOR.execute(COMMANDS['get_tokens']) # adding above provides default # of starting tokens
    USERDATA = CURSOR.fetchone()

TOKENDATA = dict(zip(HEADERS, USERDATA))
TOKENS_LEFT = TOKENDATA['tokens left']
TOKENS_USED = TOKENDATA[ASSIGN_NAME]

# no tokens required!
if SUBMISSION_TIME <= DUE_TIME: 
    EXIT_SUCCESS(f"SUCCESS: Submission arrived before the due date - no tokens required.\nYou have {TOKENS_LEFT} tokens remaining for this semester.")

if SUBMISSION_TIME <= ONE_TOKEN_DUE_TIME:
    
    # already used a token
    if TOKENS_USED == 1:
        EXIT_SUCCESS(f"SUCCESS: Already used one token previously for {ASSIGN_NAME}, so zero tokens used.\nYou have {TOKENS_LEFT} tokens remaining for this semester.")

    # we need to use a token
    if TOKENS_USED == 0:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("ERROR: Tokens needed: 1, tokens available: 0.")

        CURSOR.execute(COMMANDS['use_token'])
        CONN.commit()
        EXIT_SUCCESS(f"SUCCESS: Used one token.\nYou have {TOKENS_LEFT - 1} tokens remaining for the semester.")
    

if SUBMISSION_TIME <= TWO_TOKEN_DUE_TIME:

    if TOKENS_USED == 2: 
        EXIT_SUCCESS(f"SUCCESS: Already used two tokens previously for {ASSIGN_NAME}, so zero tokens used.\nYou have {TOKENS_LEFT} tokens remaining for the semester.")
    
    if TOKENS_USED == 1:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("ERROR: Tokens needed: 2, tokens available: 0.")

        CURSOR.execute(COMMANDS['use_token'])
        CONN.commit()
        EXIT_SUCCESS(f"SUCCESS: Already used one token previously for {ASSIGN_NAME}, but after one token deadline, so one token used.\nYou have {TOKENS_LEFT - 1} tokens remaining for the semester.")
    
    if TOKENS_USED == 0:
        if TOKENS_LEFT < 2:
            EXIT_FAIL(f"ERROR: Tokens needed: 2, tokens available: {TOKENS_LEFT}.")

        CURSOR.execute(COMMANDS['use_token'])
        CURSOR.execute(COMMANDS['use_token'])
        CONN.commit()
        EXIT_SUCCESS(f"SUCCESS: Used two tokens.\nYou have {TOKENS_LEFT - 2} tokens remaining for the semester.")