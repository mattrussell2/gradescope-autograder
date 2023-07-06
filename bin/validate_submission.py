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
from token_management import *

def EXIT_FAIL(message, db=None):
    message = "❌ " + message
    message += f"\nIf you have already submitted, you can activate a different submission by clicking the 'Submission History' button below. Whichever submission you activate will be the one that is graded.\n"
    if db:
        message += db.make_report(NAME)
    message = COLORIZE(message, MAGENTA) + "\n"
    print(message)
    with open("/autograder/results/results.json", 'w') as f:
        json.dump( {
                "score": -1, 
                "visibility": "visible",
                "stdout_visibility": "visible"
            }, f)
    try:
        db.close()
    except:
        pass
    exit(1)

def EXIT_SUCCESS(message, db=None):
    message = "✅ " + message + "\n"
    message += f"✅ You have used {len(PREV_SUBMISSIONS) + 1} / {MAX_SUBMISSIONS} submissions for this assignment.\n"
    if db:
        message += db.make_report(NAME)
    message = COLORIZE(message, GREEN)
    with open("/autograder/results/token_results", 'w') as f:
        f.write(message)
    print(message)
    try:
        db.close()
    except:
        pass
    exit(0)

INFORM("🔑 Submission Validation", BLUE)

CONFIG       = toml.load('/autograder/source/config.toml')
AG_CONFIG    = CONFIG['repo']
TOKEN_CONFIG = CONFIG['tokens']
TESTSET_TOML = toml.load('/autograder/testset.toml')['common']
METADATA     = json.loads(Path('/autograder/submission_metadata.json').read_text())

if len(METADATA['users']) == 0:
    EXIT_FAIL("ERROR: No users in submission metadata - you can only run an active submission.")

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

db = DB(TOKEN_CONFIG["POSTGRES_REMOTE"])

# add the assignment to the db if it not there yet.
if ASSIGN_NAME not in db.HEADERS:
    db.add_assignment(ASSIGN_NAME)

USERDATA = db.get_tokens(NAME)
if USERDATA == None:
    db.add_user(NAME)

TOKENDATA = db.get_report_dict(NAME)
TOKENS_LEFT = TOKENDATA['tokens left']
TOKENS_USED = TOKENDATA[ASSIGN_NAME]

# no tokens required!
if SUBMISSION_TIME <= DUE_TIME: 
    EXIT_SUCCESS(f"Submission arrived before the due date - no tokens required.", db)

if SUBMISSION_TIME <= ONE_TOKEN_DUE_TIME:
    
    # already used a token
    if TOKENS_USED == 1:
        EXIT_SUCCESS(f"Already used one token previously for {ASSIGN_NAME}, so zero tokens used.", db)

    # we need to use a token
    if TOKENS_USED == 0:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("Tokens needed: 1, tokens available: 0.", db)
        db.use_token(NAME, ASSIGN_NAME)
        EXIT_SUCCESS(f"Used one token.", db)
    

if SUBMISSION_TIME <= TWO_TOKEN_DUE_TIME:

    if TOKENS_USED == 2: 
        EXIT_SUCCESS(f"Already used two tokens previously for {ASSIGN_NAME}, so zero tokens used.", db)
    
    if TOKENS_USED == 1:
        if TOKENS_LEFT == 0:
            EXIT_FAIL("Tokens needed: 2, tokens available: 0.", db)

        db.use_token(NAME, ASSIGN_NAME)
        EXIT_SUCCESS(f"Already used one token previously for {ASSIGN_NAME}, but after one token deadline, so one token used.", db)
    
    if TOKENS_USED == 0:
        if TOKENS_LEFT < 2:
            EXIT_FAIL(f"Tokens needed: 2, tokens available: {TOKENS_LEFT}.", db)

        db.use_token(NAME, ASSIGN_NAME)
        db.use_token(NAME, ASSIGN_NAME)
        EXIT_SUCCESS(f"Used two tokens.", db)