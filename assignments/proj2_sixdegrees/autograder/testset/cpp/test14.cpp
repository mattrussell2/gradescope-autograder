/**
 ** test16.cpp
 ** report_path stress test: 20 predecessors
 **
 ** use artist.txt
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
    Artist adam("Adam Levine");
    Artist bebe("Bebe Rexha");
    Artist sean("Big Sean");
    Artist charlie("Charlie Puth");
    Artist fergie("Fergie");
    Artist keith("Keith Urban");
    Artist nicki("Nicki Minaj");
    Artist will("will.i.am");
    Artist wiz("Wiz Khalifa");
    Artist fifty("50Cent");
    Artist alessia("Alessia Cara");
    Artist ari("Ariana Grande");
    Artist dababy("DaBaby");
    Artist david("David Guetta");
    Artist demi("Demi Lovato");
    Artist diplo("Diplo");
    Artist gwen("Gwen Stefani");
    Artist halsey("Halsey");
    Artist icona("Icona Pop");
    Artist jenny("Jennifer Lopez");

    // set up for manually setting predecessors
    // from >> to
    // graph.set_predecessor(to, from);

    // adam >> bebe
    graph.set_predecessor(bebe, adam);
    // bebe >> sean
    graph.set_predecessor(sean, bebe);
    // sean >> charlie
    graph.set_predecessor(charlie, sean);
    // charlie >> fergie
    graph.set_predecessor(fergie, charlie);
    // fergie >> keith
    graph.set_predecessor(keith, fergie);
    // keith >> nicki
    graph.set_predecessor(nicki, keith);
    // nicki >> will
    graph.set_predecessor(will, nicki);
    // will >> wiz
    graph.set_predecessor(wiz, will);
    // wiz >> fifty
    graph.set_predecessor(fifty, wiz);
    // fifty >> alessia
    graph.set_predecessor(alessia, fifty);
    // alessia >> ari
    graph.set_predecessor(ari, alessia);
    // ari >> dababy
    graph.set_predecessor(dababy, ari);
    // dababy >> david
    graph.set_predecessor(david, dababy);
    // david >> demi
    graph.set_predecessor(demi, david);
    // demi >> diplo
    graph.set_predecessor(diplo, demi);
    // diplo >> gwen
    graph.set_predecessor(gwen, diplo);
    // gwen >> halsey
    graph.set_predecessor(halsey, gwen);
    // halsey >> icona
    graph.set_predecessor(icona, halsey);
    // icona >> jenny
    graph.set_predecessor(jenny, icona);



    stack <Artist>s = graph.report_path(adam, jenny);

    while(not s.empty()) {
        Artist a = s.top();
        cout << a.get_name() << endl;
        s.pop();
    }

    data.close();


    return 0;
}


