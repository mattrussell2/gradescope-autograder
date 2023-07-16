#!/bin/bash
#
# if we're in an ssh login session, delete the secrets files
#

if [ "$PAM_TYPE" != "close_session" ]; then 
    rm /autograder/source/.secrets
fi