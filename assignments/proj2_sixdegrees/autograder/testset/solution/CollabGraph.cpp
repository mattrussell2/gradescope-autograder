/**
 ** CollabGraph.cpp
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

#include <iostream>
#include <stack>
#include <vector>
#include <unordered_map>
#include <functional>
#include <exception>

#include "Artist.h"
#include "CollabGraph.h"

/*********************************************************************
 ******************** public function definitions ********************
 *********************************************************************/


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: nullary constructor
 * @purpose: initialize a CollabGraph instance
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: none
 */
CollabGraph::CollabGraph()
{
    
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: destructor
 * @purpose: deallocate all memory associated with this CollabGraph
 *           instance
 *
 * @preconditions: none
 * @postconditions: all heap-allocated memory associated with this CollabGraph
 *                  instace is freed
 */
CollabGraph::~CollabGraph()
{
    self_destruct();
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: copy constructor
 * @purpose: deeply copy another CollabGraph instance
 *
 * @preconditions: none
 * @postconditions: this instance is a deep copy of the provided
 *                  CollabGraph reference
 *
 * @parameters: a const CollabGraph reference, to be deeply copied
 */
CollabGraph::CollabGraph(const CollabGraph &source)
{
   
    *this = source;

}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: assignment operator operload
 * @purpose: deeply copy another CollabGraph instance
 *
 * @preconditions: none
 * @postconditions: this instance is a deep copy of the provided
 *                  CollabGraph reference
 *
 * @parameters: a const CollabGraph reference, to be deeply copied
 * @returns: a CollabGraph reference
 */
CollabGraph &CollabGraph::operator=(const CollabGraph &rhs)
{
    if (this == &rhs) return *this;

    self_destruct();

    for (Vertex *vertex : rhs.vertices) {

        Vertex *vertexCopy = new Vertex;
        vertexCopy->artist      = vertex->artist;
        vertexCopy->edgeNames   = vertex->edgeNames;
        vertexCopy->neighbors   = vertex->neighbors;
        vertexCopy->predecessor = vertex->predecessor;
        vertexCopy->visited     = vertex->visited;

        vertices.push_back(vertexCopy);
        graph.insert({vertexCopy->artist.get_name(), vertexCopy});
    }

    return *this;

}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: insert_vertex
 * @purpose: insert a vertex in the collaboration graph
 * @throws: a runtime_error, iff the provided Artist has the empty string as
 *          its name, since an Artist instance with the empty string as its
 *          name is improperly initialized
 *
 * @preconditions: the name of the provided 'artist' is not the empty string
 * @postconditions: the provided 'artist' inserted into the graph
 *
 * @parameters: a const Artist reference, a vertex in the graph
 * @returns: none
 */
void CollabGraph::insert_vertex(const Artist &artist)
{
    if (artist.get_name() == "") {
        std::string message = "cannot insert an improperly initialized "
                              "Artist instance (name must be non-empty)";
        throw std::runtime_error(message.c_str());
    }

    /* Do not insert a vertex into the graph if that
     * vertex already exists in the graph
     */
    if (not is_vertex(artist)) {
        Vertex *vertex = new Vertex(artist);
        graph.insert({artist.get_name(), vertex});
        vertices.push_back(vertex);
    }
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: insert_edge
 * @purpose: insert an edge between two vertices in the collaboration graph
 * @throws: a runtime_error, iff:
 *            1) an empty string is provided as the 'edgeName', since this
 *               would violate the representation invariant that empty strings
 *               represent non-existent edges
 *        OR, 2) 'a1' and 'a2' are the same vertex, because creating an edge
 *               between a vertex and itself would product a loop (which would
 *               very likely result in an infinite loop during traversal)
 *
 * @preconditions: 1) both 'a1' and 'a2' are vertices in the graph
 *                 2) 'edgeName' is not the empty string
 * @postconditions: an edge with name 'edgeName' is inserted between 'a1' and
 *                  'a2' iff there was not already an edge connecting those
 *                  vertices
 *
 * @parameters: 1) a const Artist reference, a vertex in the graph
 *              2) a const Artist reference, another vertex in the graph
 *              3) a const std::string reference, the name of an edge that
 *                 connects the two provided vertices
 * @returns: none
 */
void CollabGraph::insert_edge(const Artist &a1, const Artist &a2,
                              const std::string &edgeName)
{
    enforce_valid_vertex(a1);
    enforce_valid_vertex(a2);

    if (edgeName == "") {
        std::string message = "the empty string is not a valid edge name";
        throw std::runtime_error(message.c_str());
    }

    if (a1 == a2) {
        std::string message = "cannot insert an edge between a "
                              "vertex and itself";
        throw std::runtime_error(message.c_str());
    }

    /* Do not insert an edge between a1 and a2 if there
     * is already an edge that connects them.
     */
    if (get_edge(a1, a2) != "") return;

    graph.at(a1.get_name())->neighbors.push_back(a2);
    graph.at(a1.get_name())->edgeNames.push_back(edgeName);

    graph.at(a2.get_name())->neighbors.push_back(a1);
    graph.at(a2.get_name())->edgeNames.push_back(edgeName);
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: mark_vertex
 * @purpose: set the visited field of the provided vertex to 'true'
 *
 * @preconditions: 'artist' is a vertex in the graph
 * @postconditions: the visited field of the provided vertex is set to true
 *
 * @parameters: an Artist instance, a vertex in the graph
 * @returns: none
 */
void CollabGraph::mark_vertex(const Artist &artist)
{
    enforce_valid_vertex(artist);
    graph.at(artist.get_name())->visited = true;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: unmark_vertex
 * @purpose: set the visited field of the provided vertex to 'false'
 *
 * @preconditions: 'artist' is a vertex in the graph
 * @postconditions: the visited field of the provided vertex is set to false
 *
 * @parameters: an Artist instance, a vertex in the graph
 * @returns: none
 */
void CollabGraph::unmark_vertex(const Artist &artist)
{
    enforce_valid_vertex(artist);
    graph.at(artist.get_name())->visited = false;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: set_predecessor
 * @purpose: update the predecessor field of the 'to' vertex for
 *           path generation
 *
 * @preconditions: both 'to' and 'from' are vertices in the graph
 * @postconditions: The predecessor of the 'to' vertex will only be set
 *                  as the 'from' vertex iff 'to' does not already
 *                  have a predecessor
 *
 * @parameters: 1) a const Artist reference, the vertex those predecessor
 *                 will be set
 *              2) a const Artist reference, the predecessor vertex                 
 * @returns: none
 * @note: when the path is generated, the path will move from the
 *        'from' (predecessor) vertex to the 'to' vertex
 */
void CollabGraph::set_predecessor(const Artist &to, const Artist &from)
{

    enforce_valid_vertex(to);
    enforce_valid_vertex(from);

    Vertex *vertex      = graph.at(to.get_name());
    Vertex *pred_vertex = graph.at(from.get_name());
    

    /* It is a mistake to set the predecessor of a vertex if it
     * already has one.
     */
    if (vertex->predecessor == nullptr) {
        vertex->predecessor = pred_vertex;
    }
    
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: clear_metadata
 * @purpose: clears the metadata in the graph, preparing the graph for
 *           another traversal
 *
 * @preconditions: none
 * @postconditions: 1) all vertices in the graph are marked as unvisited
 *                  2) the predecessor of each vertex is set to 'nullptr'
 *
 * @parameters: none
 * @returns: none
 * @warning: this function MUST be called before each traversal, and failure
 *           to heed this warning will result in undefined behavior
 */
void CollabGraph::clear_metadata()
{
    for (Vertex *vertex : vertices) {
        vertex->visited = false;
        vertex->predecessor = nullptr;
    }

}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: is_vertex
 * @purpose: determine whether an artist maps to a vertex in the
 *           collaboration graph
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: a const Artist referece
 * @returns: a bool, true iff the provided vertex is in the graph
 */
bool CollabGraph::is_vertex(const Artist &artist) const
{
    return graph.find(artist.get_name()) != graph.end();
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: is_marked
 * @purpose: determine whether the provided vertex has been visited
 *
 * @preconditions: 'artist' is in the graph
 * @postconditions: none
 *
 * @parameters: a const Artist reference
 * @returns: a bool, true iff the provided vertex has been visited
 */
bool CollabGraph::is_marked(const Artist &artist) const
{
    enforce_valid_vertex(artist);
    return graph.at(artist.get_name())->visited;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: get_predecessor
 * @purpose: retrieve predecessor of a vertex in the collaboration graph
 *
 * @preconditions: 'artist' is a vertex in the graph
 * @postconditions: none
 *
 * @parameters: a const Artist reference, a vertex in the graph
 * @returns: an Artist, which is the predecessor of the provided 'artist'
 *           in the collaboration graph
 * @note: if the provided 'artist' does not have a predecessor in the
 *        collaboration graph, then an artist with the empty string as
 *        its name is returned
 */
Artist CollabGraph::get_predecessor(const Artist &artist) const
{
    enforce_valid_vertex(artist);

    /* An artist with the empty string as its name represents a
     * non-existent artist */
    Artist pred_artist;
    
    
    Vertex *pred_vertex = graph.at(artist.get_name())->predecessor;

    if (pred_vertex != nullptr)
        pred_artist = pred_vertex->artist;

    return pred_artist;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: get_edge
 * @purpose: retrieve the edge between two vertices in the collaboration graph
 *
 * @preconditions: both 'a1' and 'a2' are vertices in the graph
 * @postconditions: none
 *
 * @parameters: 1) a const Artist reference, a vertex in the graph
 *              2) a const Artist reference, another vertex in the graph
 * @returns: a std::string, which is the name of the edge connecting 'a1' and
 *           'a2' (the empty string represents a non-existent edge)
 */
std::string CollabGraph::get_edge(const Artist &a1, const Artist &a2) const
{
    enforce_valid_vertex(a1);
    enforce_valid_vertex(a2);

    /* The empty string represents a non-existent edge */
    std::string edge = "";

    /* The 'neighbors' and 'edgeNames' vectors are parallel arrays.
     *
     * The 'index' is increased until the end of the adjacency list
     * is reached OR a2 is found in the adjacency list.
     */
    std::vector<Artist> adj = graph.at(a1.get_name())->neighbors;
    std::size_t index = 0;
    for (; index < adj.size() and adj.at(index) != a2; index++) {
         /* no loop body is necessary */
    }

    /* If a1 and a2 are neighbors, extract the name of the edge that
     * connects them
     */
    if (index < adj.size())
        edge = graph.at(a1.get_name())->edgeNames.at(index);

    return edge;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: get_vertex_neighbors
 * @purpose: retrieve the neighbors of a vertex in the collaboration graph
 *
 * @preconditions: 'artist' is a vertex in the graph
 * @postconditions: none
 *
 * @parameters: a const Artist reference, a vertex in the graph
 * @returns: a std::vector of Artist instances, which contains all neighbors
 *           of the provided vertex
 */
std::vector<Artist> CollabGraph::get_vertex_neighbors(const Artist &artist) const
{
    enforce_valid_vertex(artist);
    return graph.at(artist.get_name())->neighbors;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: report_path
 * @purpose: accumualate the path from the provided 'source' vertex to the
 *           provided 'dest' vertex
 *
 * @preconditions: 1) both 'source' and 'dest' are vertices in the graph
 *                 2) the graph has been traversed, and the predecessor field
 *                    of all vertices between 'source' and 'dest' has been
 *                    properly set
 * @postconditions: none
 *
 * @parameters: 1) a const Artist reference, the source vertex
 *              2) a const Artist reference, the destination vertex
 * @returns: a std::stack of Artist instances, where the top-most element
 *           is the source vertex, and the bottom-most element is the
 *           destination vertex
 * @note: when the path is generated, the path will move from the
 *        'from' (predecessor) vertex to the 'to' vertex
 */
std::stack<Artist> CollabGraph::report_path(const Artist &source,
                                            const Artist &dest) const
{
    enforce_valid_vertex(source);
    enforce_valid_vertex(dest);


    std::stack<Artist> path;

    Vertex *curr = graph.at(dest.get_name());

    /* There is no stored path from source to dest
     * iff predecessor of the 'dest' vertex is 'nullptr'
     */
    if (curr->predecessor == nullptr) return path;
    
    while (curr != nullptr and curr->artist != source) {
        path.push(curr->artist);
        curr = curr->predecessor;
    }

    path.push(graph.at(source.get_name())->artist);

    return path;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: print_graph
 * @purpose: print a representation of the informtation stored in the
 *           collaboration graph
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: a std::ostream reference, where output is sent
 * @returns: none
 */
void CollabGraph::print_graph(std::ostream &out)
{

    for (Vertex *vertex : vertices) {

        /* It is always the case that the edges and neighbors
         * vectors have the same number of elements
         */
        std::vector<std::string> edges = vertex->edgeNames;
        std::vector<Artist> neighbors = vertex->neighbors;

        for (std::size_t i = 0; i < edges.size(); i++) {
            out << "\"" << vertex->artist.get_name() << "\" "
                << "collaborated with "
                << "\"" << neighbors.at(i) << "\" in "
                << "\"" << edges.at(i) << "\"."
                << std::endl;
        }

        out << "***" << std::endl;
    }

}





/**********************************************************************
 ******************** private function definitions ********************
 **********************************************************************/



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: self_destruct
 * @purpose: deallocate all memory associated with this CollabGraph
 *           instance
 *
 * @preconditions: none
 * @postconditions: all heap-allocated memory associated with this CollabGraph
 *                  instace is freed
 *
 * @parameters: none
 * @returns: none
 */
void CollabGraph::self_destruct()
{
    for (Vertex *vertex : vertices) {
        delete vertex;
    }
    vertices.clear();

    graph.clear();
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: enforce_valid_vertex
 * @purpose: ensure that 
 * @throws: a runtime_error, iff the provied artist does not map to a vertex
 *          in the collaboration graph. 
 *
 * @preconditions: none
 * @postconditions: if an exception is not thrown, then the provided Artist
 *                  instance maps to a vertex in the collaboration graph
 *
 * @parameters: a const Artist reference, which must map to a vertex in
 *              the collaboration graph
 * @returns: none
 */
void CollabGraph::enforce_valid_vertex(const Artist &artist) const
{
    if (not is_vertex(artist)) {
        std::string message = "artist \"" + artist.get_name() + \
                              "\" does not exist in the collaboration graph";
        throw std::runtime_error(message.c_str());
    }
}

