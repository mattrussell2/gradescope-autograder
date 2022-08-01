/**
 ** CollabGraph.h
 **
 ** Project Two: Six Degrees of Collaboration
 **
 ** Purpose:
 **   Represent a collaboration graph of artists, where each artist is
 **   a vertex and an edge between two artists is a song in which those
 **   artists have collaborated. Accessor and mutator functions are provided,
 **   allowing for convenient traversal of the graph.
 **
 ** Notes:
 **   1) Loops (edges from a vertex to itself) are forbidden
 **   2) Non-existent edges are represented by the empty string
 **   3) Artists with the empty string as their name are forbidden 
 **
 ** ChangeLog:
 **   17 Nov 2020: zgolds01
 **       CollabGraph class created
 **
 **/

#ifndef __COLLAB_GRAPH__
#define __COLLAB_GRAPH__

#include <iostream>
#include <stack>
#include <vector>
#include <unordered_map>

#include "Artist.h"

class CollabGraph {

public:

    /* Nullary Constructor */
    CollabGraph();

    /* The 'Big Three' */
    ~CollabGraph();
    CollabGraph(const CollabGraph &source);
    CollabGraph &operator=(const CollabGraph &rhs);

    /* Mutators */
    void insert_vertex(const Artist &artist);
    void insert_edge(const Artist &a1, const Artist &a2,
                     const std::string &song);
    void mark_vertex(const Artist &artist);
    void unmark_vertex(const Artist &artist);
    void set_predecessor(const Artist &to, const Artist &from);
    void clear_metadata();    

    /* Accessors */
    bool                is_vertex(const Artist &artist) const;
    bool                is_marked(const Artist &artist) const;
    Artist              get_predecessor(const Artist &artist) const;
    std::string         get_edge(const Artist &a1, const Artist &a2) const;
    std::vector<Artist> get_vertex_neighbors(const Artist &artist) const;
    std::stack<Artist>  report_path(const Artist &source,
                                    const Artist &dest) const;
    void                print_graph(std::ostream &out);

private:

    struct Vertex {
        Vertex() {};
        Vertex(Artist a) { artist = a; };

        Artist artist;
        std::vector<std::string> edgeNames;
        std::vector<Artist> neighbors;

        Vertex *predecessor = nullptr;
        bool visited = false;
    };

    void self_destruct();
    void enforce_valid_vertex(const Artist &artist) const;

    std::unordered_map<std::string, Vertex *> graph;

    /* used to efficiently iterate over each vertex to reset values */
    std::vector<Vertex *> vertices;

};

#endif /* __COLLAB_GRAPH__ */
