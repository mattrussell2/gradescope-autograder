#!/usr/bin/env python3
"""
validate_submission.py
matt russell
5-23-2023

A token management system. 
"""
from dateutil    import parser as dateparser
from datetime    import timedelta
from dataclasses import dataclass 
from pathlib     import Path
import json
import os
import toml
import psycopg2
import pprint

pp = pprint.PrettyPrinter(indent=4)

GREEN       = "32m"
MAGENTA     = "35m"
CYAN        = "36m"
START_COLOR = "\033[1;"
RESET_COLOR = "\033[0m"

def COLORIZE(s, color):
    return f"{START_COLOR}{color}{s}{RESET_COLOR}"

def INFORM(s, color): 
    print(COLORIZE(s, color))

class DB: 
    def __init__(self, remote):
        self.COMMANDS = {
            'get_headers'    : "SELECT column_name FROM information_schema.columns WHERE table_name = 'tokens';",
            'add_user'       : lambda NAME: f"INSERT INTO tokens(pk) VALUES('{NAME}');",
            'get_tokens'     : lambda NAME: f"SELECT * FROM tokens WHERE pk = '{NAME}';",
            'add_token'      : lambda NAME: f"UPDATE tokens SET \"tokens left\" = \"tokens left\" + 1 WHERE pk = '{NAME}';",
            'subtract_token' : lambda NAME: f"UPDATE tokens SET \"tokens left\" = \"tokens left\" - 1 WHERE pk = '{NAME}';",
            'use_token'      : lambda NAME, ASSIGN_NAME: f"UPDATE tokens SET \"tokens left\" = \"tokens left\" - 1, \"{ASSIGN_NAME}\" = \"{ASSIGN_NAME}\" + 1 WHERE pk = '{NAME}';", 
            'unuse_token'    : lambda NAME, ASSIGN_NAME: f"UPDATE tokens SET \"tokens left\" = \"tokens left\" + 1, \"{ASSIGN_NAME}\" = \"{ASSIGN_NAME}\" - 1 WHERE pk = '{NAME}';",
            'add_assignment' : lambda ASSIGN_NAME: f"ALTER TABLE tokens ADD COLUMN \"{ASSIGN_NAME}\" INTEGER DEFAULT 0;",
            'get_db'         : "SELECT * FROM tokens;"
        }

        self.create_db_conn(remote)
        self.get_db_colnames()

    def create_db_conn(self, remote):
        self.CONN   = psycopg2.connect(remote)
        self.CURSOR = self.CONN.cursor()
    
    def get_db_colnames(self):
        self.CURSOR.execute(self.COMMANDS['get_headers'])
        self.HEADERS = [x[0] for x in self.CURSOR.fetchall()]

    def get_tokens(self, student_name):
        self.CURSOR.execute(self.COMMANDS['get_tokens'](student_name))
        return self.CURSOR.fetchone()

    def run_db_cmd(self, cmd):
        self.CURSOR.execute(cmd)
        self.CONN.commit()

    def add_assignment(self, assign_name):
        self.run_db_cmd(self.COMMANDS['add_assignment'](assign_name))

    def add_user(self, student_name):
        self.run_db_cmd(self.COMMANDS['add_user'](student_name))

    def add_token(self, student_name):
        self.run_db_cmd(self.COMMANDS['add_token'](student_name))

    def subtract_token(self, student_name):
        self.run_db_cmd(self.COMMANDS['subtract_token'](student_name))

    def use_token(self, student_name, assign_name):
        self.run_db_cmd(self.COMMANDS['use_token'](student_name, assign_name))

    def unuse_token(self, student_name, assign_name):
        self.run_db_cmd(self.COMMANDS['unuse_token'](student_name, assign_name))

    def get_report_dict(self, student_name):
        USERDATA = self.get_tokens(student_name)
        USERTOKENDATA = dict(zip(self.HEADERS, USERDATA))
        return USERTOKENDATA

    def make_report(self, student_name):
        USERTOKENDATA = self.get_report_dict(student_name)
        
        assigns = {key:value for key,value in USERTOKENDATA.items() if key != 'pk' and int(value) > 0}
        report =  "\nTOKEN REPORT\n"
        max_width = max([len(key) for key in assigns.keys()]) + 2
        report += "-" * (max_width + 1) + "\n"
        for assign, tokens in assigns.items():
            report += f"{f'{assign}': <{max_width}}{tokens}\n"
        
        return report

    def print_report(self, student_name):
        report = self.make_report(student_name)
        print(report)

    def close(self):
        self.CONN.close()


if __name__ == "__main__":
    FPATH = os.path.dirname(__file__)
    CONFIG = toml.load(f"{FPATH}/../etc/config.toml")
    
    try:
        db = DB(os.environ[CONFIG['tokens']["POSTGRES_REMOTE_VARNAME"]])
    except:
        print("ERROR! Could not connect to the database. Check your environment variables. You need to set the following:")
        print(f"  {CONFIG['tokens']['POSTGRES_REMOTE_VARNAME']}")
        print("To be clear, you need an environment variable that has the key of the value of the above variable in your etc/config.toml file")
        exit()

    print("Token Management")
    print("NOTE! This program allows you to make any token updates for a student.")
    print("      It is up to you to maintain a valid configuration - be careful!")

    NAME = input("\nEnter the student's full name as it is on gradescope, spaces and capitalization included (e.g. Matthew P. Russell): ")

    USERDATA = db.get_tokens(NAME)
    if USERDATA == None:
        toADD = input(f"There is no user in the database named: {NAME} - do you want to add them? (y/n): ")
        if toADD == 'y':
            db.add_user(NAME)
        else:
            print("exiting...")
            db.close()
            exit()

    report = db.make_report(NAME)

    print(report)
    print("What would you like to do? Options are") 
    print("  1. add a token to the total tokens left")
    print("  2. subtract a token from the total tokens left")
    print("  3. 'unuse' a token for an assignment")
    print("  4. use a token for an assignment")
    print("  5. see complete token report")

    opt = input("\nEnter a number: ")
    while (opt not in ['1', '2', '3', '4', '5']):
        opt = input("Enter a number: ")

    if opt == '1':
        db.add_token(NAME)
        db.print_report(NAME)
    elif opt == '2':
        db.subtract_token(NAME)
        db.print_report(NAME)
    else:
        TOKENDATA = db.get_report_dict(NAME)
        max_width = max([len(key) for key in TOKENDATA.keys()]) + 2
        print(f"\n{'       ASSIGNMENT ':-<{max_width}} TOKENS USED")
        print("\n".join([f"  {i+1:02}. {assign:-<{max_width}} {tokens}" for i, (assign, tokens) in enumerate(TOKENDATA.items()) if assign != 'pk' and assign != 'tokens left']))

        if opt == '5': 
            db.close()
            exit()
        if opt == '3': 
            word = "unuse"
        else:
            word = "use"

        op = f"{word}_token"

        ASSIGN_NUM = input(f"\nEnter the number of the assignment you would like to '{word}' a token for: ")
        while (not ASSIGN_NUM.isdigit() or int(ASSIGN_NUM) > len(TOKENDATA.items()) - 2):
            ASSIGN_NUM = input(f"Enter the number of the assignment you would like to '{word}' a token for: ")
        ASSIGN_NAME = list(TOKENDATA.keys())[int(ASSIGN_NUM) - 1]
        
        if word == "use":
            db.use_token(NAME, ASSIGN_NAME)
        else:
            db.unuse_token(NAME, ASSIGN_NAME)

        db.print_report(NAME)

    db.close()