/**
 ** test14.cpp
 ** report_path: no path (vertex to a disconnected vertex)
 **
 ** use artist.txt
 ** prints nothing
 **
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
    (void)argv;
    CollabGraph graph;

    std::ifstream data;
    data.open(argv[1]);
    populate_graph(graph, data);

    // create 20 Artists and set predecessors for them manually
    Artist camila("Camila Cabello");
    Artist ellie("Ellie Goulding");
    Artist jay("Jay-Z");
    Artist christina("Christina Aguilera");

    Artist rick("Rick Astley");

    // set up for manually setting predecessors
    // from >> to
    // graph.set_predecessor(to, from);

    // camila >> ellie
    graph.set_predecessor(ellie, camila);
    // ellie >> jay
    graph.set_predecessor(jay, ellie);
    // jay >> christina
    graph.set_predecessor(christina, jay);


    stack <Artist>s = graph.report_path(camila, rick);

    while(not s.empty()) {
        Artist a = s.top();
        cout << a.get_name() << endl;
        s.pop();
    }

    data.close();


    return 0;
}


