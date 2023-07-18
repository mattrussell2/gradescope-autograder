#!/usr/bin/env python3
"""
token_manager.py
matt russell
5-23-2023

A token management system. 

"""
import os
import paramiko
import re
import time 
import io
from rich.console import Console
from rich.table import Table, Column
from rich import print as rprint
from rich import box
import sys
sys.path.append(os.path.dirname(__file__))
from autograde import COLORIZE, INFORM, GREEN, MAGENTA, CYAN, BLUE

def replaceNonAlphaNum(s, c='_'):
    return re.sub('[^0-9a-zA-Z]+', c, s)

class DB: 
    def __init__(self, ASSIGN, STUDENT, OPENING_BALANCE, SECRETS):

        self.ASSIGN          = replaceNonAlphaNum(ASSIGN).lower()
        self.STUDENT         = replaceNonAlphaNum(STUDENT).lower()
        self.OPENING_BALANCE = OPENING_BALANCE

        self.TOKENS_HOST     = SECRETS['TOKENS_HOST']
        self.TOKENS_UTLN     = SECRETS['TOKENS_UTLN']
        self.TOKENS_PASS     = SECRETS['TOKENS_PASS']
        self.MYSQL_USER      = SECRETS['MYSQL_USER']
        self.MYSQL_PASS      = SECRETS['MYSQL_PASS']
        self.MYSQL_DBNAME    = SECRETS['MYSQL_DBNAME']
        self.MYSQL_LOC       = SECRETS['MYSQL_LOC']
        self.TABLE           = replaceNonAlphaNum(SECRETS['COURSE_SLUG']).lower()

        self.COMMANDS = {
            'create_table'   : f"CREATE TABLE {self.TABLE}(pk VARCHAR(255) PRIMARY KEY);",
            'describe_table' : f"DESCRIBE {self.TABLE};",
            'get_headers'    : f"SELECT column_name FROM information_schema.columns WHERE table_name = '{self.TABLE}';",
            'add_student'    : f"INSERT INTO {self.TABLE}(pk) VALUES('{self.STUDENT}');",
            'get_tokens'     : f"SELECT * FROM {self.TABLE} WHERE pk = '{self.STUDENT}';",
            'use_token'      : f"UPDATE {self.TABLE} SET {self.ASSIGN} = {self.ASSIGN} + 1 WHERE pk = '{self.STUDENT}';",
            'add_assignment' : f"ALTER TABLE {self.TABLE} ADD COLUMN {self.ASSIGN} INTEGER DEFAULT 0;"
        }

        self.ERRORS = {
            'no_table': "ERROR 1146"
        }

        self.create_db_conn()
        self.register_sql_login()
        self.create_table_if_needed()
        self.get_db_colnames()
        self.add_assignment_if_needed()
        self.add_student_if_needed()
        
    def create_db_conn(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname = self.TOKENS_HOST, username = self.TOKENS_UTLN, password = self.TOKENS_PASS)

    def register_sql_login(self):
        register_cmd = f"mysql_config_editor set "    + \
                       f"--login-path=eecs_token_db " + \
                       f"--host={self.MYSQL_LOC} "    + \
                       f"--user={self.MYSQL_USER} "   + \
                        "--skip-warn --password"
        stdin, stdout, stderr = self.ssh.exec_command(register_cmd)
        stdin.write(f"{self.MYSQL_PASS}\n")
        stdin.flush()
        
    def run_db_cmd(self, command):
        return self.ssh.exec_command(f"mysql --login-path=eecs_token_db -D {self.MYSQL_DBNAME} -e \"{command}\"") 
    
    def create_table_if_needed(self):
        stdin, stdout, stderr = self.run_db_cmd(self.COMMANDS['describe_table'])
        if self.ERRORS['no_table'] in str(stderr.read()):
            print("Course doesn't yet exist in db. Creating table named {self.TABLE}...}")
            _, stdout, stderr = self.run_db_cmd(self.COMMANDS['create_table'])

    def get_db_colnames(self):
        _, stdout, _ = self.run_db_cmd(self.COMMANDS['get_headers'])
        self.HEADERS = stdout.read().decode().split('\n')[1:-1] 

    def get_user_tokens(self):
        _, stdout, _ = self.run_db_cmd(self.COMMANDS['get_tokens'])
        output = stdout.read().decode().strip()
        return None if output == '' else output
        
    def add_assignment_if_needed(self):
        if self.ASSIGN not in self.HEADERS:
            _, stdout, _ = self.run_db_cmd(self.COMMANDS['add_assignment'])
            self.get_db_colnames()
    
    def add_student_if_needed(self):
        USERDATA = self.get_user_tokens()
        if USERDATA == None:
            _, stdout, stderr = self.run_db_cmd(self.COMMANDS['add_student'])

    def use_token(self):
        self.run_db_cmd(self.COMMANDS['use_token'])

    def get_report_dict(self):
        """
            NOTE: "tokens_left" used to be a column in the db for alpha testing, but is no longer used. 
                  the skip of it will be necessary until the end of summer 2023, when the 15-2023ucm1 table is no longer necessary.
        """

        USERDATA = self.get_user_tokens()
        lines    = USERDATA.split('\n')
        assigns  = lines[0].split('\t')
        values   = [int(x) if i != 0 else x for i, x in enumerate(lines[1].split('\t'))]
        data     = [ [assign, value] for assign, value in zip(assigns, values) if assign not in ['pk', 'tokens_left'] and value > 0 ]
        balance  = self.OPENING_BALANCE - sum([value for assign, value in data])
        return data, balance

    def get_tokens_left_and_assign_usage(self):
        data, balance = self.get_report_dict()
        try:
            assign_usage = [ value for assign, value in data if assign == self.ASSIGN ][0]
        except:
            assign_usage = 0
        return balance, assign_usage

    def write_report(self, also_to_file=None):
        usage, balance = self.get_report_dict()
        
        report = Table(Column("Assignment", "[bold]Opening Balance\nRemaining Balance[/]"),
                       Column("Tokens Used", f"[bold]{self.OPENING_BALANCE}\n{balance}[/]", 
                              justify = "center"),
                       title         = "💰 [bold][blue]Token Report[/]",
                       title_justify = "left",
                       show_footer   = True, 
                       show_header   = False,
                       box           = box.HORIZONTALS)

        for assign_name, tokens_used in usage:
            report.add_row(assign_name.replace('_', ' '), str(tokens_used))
         
        # always write report to stdout
        console = Console(force_terminal=True)
        console.print(report)
        console.print(' ') # only way to add a single newline

        # in this case, also write to the file
        if also_to_file:
            console = Console(file=also_to_file, force_terminal=True)
            console.print(report)
            console.print(' ')

    def close(self):
        self.ssh.close()