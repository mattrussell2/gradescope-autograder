#!/bin/env python3

import re
import os
from pathlib import Path
import sys
from random import random

def process_output(student_stdout, solution_stdout, testname, ccizer_args):      
    graph           = initGraph(ccizer_args['artists_file'])
    ccized_results  = []
    student_results = [x.strip().split('\n') for x in student_stdout.split('***')]
    
    if solution_stdout == None:
        solution_results = [None for x in student_results]        
    else:
        solution_results = [x.strip().split('\n') for x in solution_stdout.split('***')]                
    
    queries     = []    
    i           = 0
    query_lines = Path(f"testset/stdin/{testname}.stdin").read_text().splitlines()    
    while i < len(query_lines):
        if query_lines[i] in ['*', 'quit']:
            i += 1
            continue
        queries.append({'query_type': query_lines[i], 'source': query_lines[i+1], 'dest': query_lines[i+2]})
        i += 3
        if queries[-1]['query_type'] == 'not':
            queries[-1]["nots"] = []        
            while query_lines[i] != "*":
                queries[-1]["nots"].append(query_lines[i])                
                i += 1
   
    for i, (student, solution, query_data) in enumerate(zip(student_results, solution_results, queries)):
        ccized_results.append(validate_result(student, solution, query_data, graph, i))
    
    #print("\n-------\n".join(ccized_results))

    return "\n-------\n".join(ccized_results)

def validate_result(student, solution, query_data, graph, ith_query):
    """
    student: list of strings, one per line of the student's solution
    solution: list of strings, one per line of the solution
    query_type: string, one of 'bfs', 'dfs', or 'not'
    graph: dict of dicts of sets, {artista:{artistb: (song1, song2, ...), artistc: (song1, song2, ...), ...}}
    """    

    # case of length 1 might be not found or no path cases - return in these instances.
    # however, might also be a dfs case where solution and student disagree but student is correct. 
    if len(student) == 1 and ((solution != None and ("A path does not exist between"  in solution or \
                                                    "was not found in the dataset :(" in solution)) \
                              or solution == None and ("A path does not exist between" in student or \
                                                       "was not found in the dataset :(" in student)):
        return student

    # running reference implementation; assume correct
    if solution == None:        
        return f"provided {query_data['query_type']} between {query_data['source']} and {query_data['dest']} is a correct path\nlength of path provided is: {len(student)}"
    
    # Format is: ""source" collaborated with "dest" in "song"". 
    # after split, we have source and dest
    stud_source, stud_dest = get_source(student[0]), get_dest(student[-1])   

    if stud_source != query_data['source'] or stud_dest != query_data['dest']:
        return f"INCORRECT_PATH -- STUDENT SOURCE: {stud_source} -> STUDENT DESTINATION: {stud_dest}\n" + \
               f"                  SOLUTION SOURCE: {query_data['source']} -> SOLUTION DESTINATION: {query_data['dest']}"
    
    curr_artist = stud_source
    artists_seen = set(curr_artist)
    for query_line in student:
        source, dest = get_source(query_line), get_dest(query_line)
        
        if dest in artists_seen:
            return f"INVALID_PATH: encountered {dest} twice in path"
        if source not in graph or dest not in graph:
            return f"INVALID_PATH: {source} -> {dest} - {source if source not in graph else dest} not in graph"
        if dest not in graph[curr_artist]:
            return f"INVALID_PATH: {curr_artist} -> {dest} - {dest} did not collaborate with {curr_artist}"
        if query_data['query_type'] == 'not' and dest in query_data['nots']:
            return f"INVALID_PATH: {curr_artist} -> {dest} - {dest} is in the NOT list"
        
        artists_seen.add(dest)
        curr_artist = dest
        
    if query_data['query_type'] == 'bfs':        
        if len(student) > len(solution):
            return f"query for bfs failed: {len(student)} is not the optimal path length of {len(solution)}"            
        else:
            return f"provided {query_data['query_type']} between {stud_source} and {stud_dest} is a correct and optimal shortest path"

    return f"provided {query_data['query_type']} between {stud_source} and {stud_dest} is a correct path"


# Format is: ""source" collaborated with "dest" in "song"". 
# after split, we have ["", "source", " collaborated with ", "dest", " in ", "song", "."]   
def get_source(query_line):
    return query_line.split('\"')[1]

def get_dest(query_line):
    return query_line.split('\"')[3]


def initGraph(artists_file):    
    # assumes no duplicate artists
    artist_songs = {}
    graph        = {}
        
    data = [x.strip().split('\n') for x in Path(artists_file).read_text().split('*')]
    
    if data[-1] == ['']: data = data[:-1] 

    for artist, *songs in data:
        artist_songs[artist] = songs
        graph[artist]        = {}
        
    for artist1 in list(graph.keys())[:len(list(graph.keys()))]:       
        for artist2 in graph:
            if artist1 == artist2:
                continue
    
            for song1 in artist_songs[artist1]:
                for song2 in artist_songs[artist2]:
                    if song1 == song2:
                        if artist2 not in graph[artist1]: 
                            graph[artist1][artist2] = set()
                            graph[artist2][artist1] = set()

                        graph[artist1][artist2].add(song1)
                        graph[artist2][artist1].add(song1)                    

    return graph    
        
if __name__ == "__main__":
    initGraph()
    