/**
 ** SixDegrees.cpp
 **
 ** Project Two: Six Degrees of Collaboration
 **
 ** Purpose:
 **   Find 'paths of collaboration' between different artists
 **   using various algorithms, with the option to exlcude
 **   particular artists from the path
 **
 ** ChangeLog:
 **   17 Nov 2020: zgolds01
 **       SixDegrees class created
 **
 */


#include <vector>
#include <queue>
#include <stack>
#include <iostream>
#include <ostream>
#include <istream>
#include <fstream>
#include <string>
#include <exception>

#include "Artist.h"
#include "CollabGraph.h"
#include "SixDegrees.h"


/* this exception is no longer used by the reference */
class artist_error : public std::runtime_error
{
public:
    artist_error(char const* const message) throw()
        : std::runtime_error(message) {}

    char const *what() const throw()
        { return std::runtime_error::what(); }
};


SixDegrees::SixDegrees()
{
    inputp  = &std::cin;
    outputp = &std::cout;
}

SixDegrees::~SixDegrees()
{

}


void SixDegrees::run()
{
    std::string line;

    while (std::getline(*inputp, line) and line != "quit") {

        try {

            if (line == "bfs") {
                std::string a1 = "";
                std::string a2 = "";

                std::getline(*inputp, a1);
                std::getline(*inputp, a2);

                // std::cout << "BFS\n\n" << std::endl;

                bfs(a1, a2);
            } else if (line == "dfs") {
                std::string a1 = "";
                std::string a2 = "";

                std::getline(*inputp, a1);
                std::getline(*inputp, a2);

                dfs(a1, a2);
            } else if (line == "not") {
                std::string a1 = "";
                std::string a2 = "";
                std::vector<Artist> excluded;

                std::getline(*inputp, a1);
                std::getline(*inputp, a2);

                while (std::getline(*inputp, line) and line != "*") {
                    excluded.push_back(line);
                }

                excl(a1, a2, excluded);
            } else if (line == "incl") {
                std::string a1 = "";
                std::string a2 = "";
                std::string a3 = "";

                std::getline(*inputp, a1);
                std::getline(*inputp, a2);
                std::getline(*inputp, a3);

                incl(a1, a2, a3);
            } else if (line == "print") {

                graph.print_graph(*outputp);

            } else {
                *outputp << line
                         << " is not a command. Please try again."
                         << std::endl;
            }

        /* this code now redundant, as artist_errors are no
         * longer thrown
         */
        } catch (artist_error e) {
            *outputp << "\"" << e.what() << "\""
                     << " was not found in the dataset :("
                     << std::endl;
        }
    }
}



void SixDegrees::set_input(std::istream &in)
{
    inputp = &in;
}

void SixDegrees::set_output(std::ostream &out)
{
    outputp = &out;
}


/* must be given a fresh copy of a graph */
void SixDegrees::bfs(Artist source, Artist dest)
{
    graph.clear_metadata();

    bool safeToRun = true;
    safeToRun = check_valid_artist(source) and safeToRun;
    safeToRun = check_valid_artist(dest)   and safeToRun;


    if (not safeToRun) return;

    run_bfs(source, dest);

    print_path(source, dest, graph.report_path(source, dest));
    
}

void SixDegrees::dfs(Artist source, Artist dest)
{
    graph.clear_metadata();

    bool safeToRun = true;
    safeToRun = check_valid_artist(source) and safeToRun;
    safeToRun = check_valid_artist(dest)   and safeToRun;

    if (not safeToRun) return;
    
    run_dfs(source, dest);

    print_path(source, dest, graph.report_path(source, dest));

}
    
void SixDegrees::excl(Artist source, Artist dest,
                      std::vector<Artist> &excluded)
{
    graph.clear_metadata();

    bool safeToRun = true;
    safeToRun = check_valid_artist(source) and safeToRun;
    safeToRun = check_valid_artist(dest)   and safeToRun;
    for (Artist &artist : excluded)
        safeToRun = check_valid_artist(artist) and safeToRun;

    if (not safeToRun) return;

    for (Artist &artist : excluded) graph.mark_vertex(artist);
    run_bfs(source, dest);

    print_path(source, dest, graph.report_path(source, dest));

}

void SixDegrees::incl(Artist source, Artist dest, Artist incl)
{
    graph.clear_metadata();

    bool safeToRun = true;
    safeToRun = check_valid_artist(source) and safeToRun;
    safeToRun = check_valid_artist(dest) and safeToRun;
    safeToRun = check_valid_artist(incl) and safeToRun;

    *outputp << "incl command left as JFFE" << std::endl;

}


void SixDegrees::populate_graph(std::istream &datafile)
{
    std::string line = "";
    std::vector<Artist> artists;
    
    while (std::getline(datafile, line)) {
        Artist artist(line);

        while (std::getline(datafile, line) and line != "*") {
            artist.add_song(line);
        }

        artists.push_back(artist);
        graph.insert_vertex(artist);

    }

    // connect-edges subroutine, uses get_collaboration
    for (Artist a1 : artists) {
        for (Artist a2 : artists) {
            if (a1 != a2) {
                std::string song = a1.get_collaboration(a2);
                if (song != "")
                    graph.insert_edge(a1, a2, song);
            }
        }
    }
}

void SixDegrees::print_path(Artist source, Artist dest,
                            std::stack<Artist> path)
{
    if (path.empty()) {
        *outputp << "A path does not exist between "
                 << "\"" << source << "\" and \""
                 << dest << "\"." << std::endl;
        return;
    }

    while (not path.empty()) {
        Artist to = path.top();
        path.pop();
        if (not path.empty()) {
            Artist from = path.top();
            *outputp << "\"" << to << "\" collaborated with ";
            *outputp << "\"" << from << "\" in ";
            *outputp << "\"" << graph.get_edge(to, from) << "\".\n";
        }
    }
    *outputp << "***" << std::endl;
}

void SixDegrees::run_bfs(Artist source, Artist dest)
{

    std::queue<Artist> processQueue;

    processQueue.push(source);
    while (not processQueue.empty()) {
        
        Artist nextArtist = processQueue.front();
        processQueue.pop();

        if (graph.is_marked(nextArtist)) continue;
        graph.mark_vertex(nextArtist);

        std::vector<Artist> neighbors = graph.get_vertex_neighbors(nextArtist);

        for (Artist neighbor : neighbors) {
            if (not graph.is_marked(neighbor)) {
                graph.set_predecessor(neighbor, nextArtist);
                processQueue.push(neighbor);
            }
        }

        if (nextArtist == dest) break;

    }

}

bool SixDegrees::run_dfs(Artist curr, Artist dest)
{

    if (curr == dest) return true;

    if (graph.is_marked(curr)) return false;
    graph.mark_vertex(curr);

    std::vector<Artist> neighbors = graph.get_vertex_neighbors(curr);

    for (Artist neighbor : neighbors) {
        
        if (run_dfs(neighbor, dest)) {
            graph.set_predecessor(neighbor, curr);
            return true;
        }
    }

    return false;

}

bool SixDegrees::check_valid_artist(Artist artist)
{
    if (not graph.is_vertex(artist)) {
        *outputp << "\"" << artist.get_name() << "\""
                    << " was not found in the dataset :("
                    << std::endl;
        return false;
    }
    return true;

        //throw artist_error(artist.get_name().c_str());
}