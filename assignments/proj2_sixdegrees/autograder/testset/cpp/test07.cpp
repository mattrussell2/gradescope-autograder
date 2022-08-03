/**
 ** test09.cpp
 ** Get the neighbors of an artist with no collabs. 
 **/

#include <fstream>
#include <iostream>
#include <ios>
#include <string>

#include "CollabGraph.h"
#include "Artist.h"
#include <stack>

using namespace std;


void populate_graph(CollabGraph &graph, istream &datafile)
{
    string line = "";
    vector<Artist> artists;
    
    while (getline(datafile, line)) {
        Artist artist(line);

        while (getline(datafile, line) and line != "*") {
            artist.add_song(line);
        }

        artists.push_back(artist);
        graph.insert_vertex(artist);

    }

    // connect-edges subroutine, uses get_collaboration
    for (size_t i = 0; i < artists.size(); i++) {
        for (size_t j = i + 1; j < artists.size(); j++) {
            string song = artists[i].get_collaboration(artists[j]);
            if (song != "") {
                graph.insert_edge(artists[i], artists[j], song);
            }
        }
    }
}

int main(int argc, char *argv[])
{
    (void)argc;
    CollabGraph graph;

    // For both report_path and get_vertex_neighbors use lines 52-55
    std::ifstream data;
    data.open(argv[1]);
    populate_graph(graph, data);

    /* Empty vector because Rick Astley has no neighbors. */
    Artist rick("Rick Astley");
    vector<Artist> v = graph.get_vertex_neighbors(rick);

    for (auto &x : v) {
        cout << x.get_name() << endl;
    }

    data.close();

    return 0;
}


