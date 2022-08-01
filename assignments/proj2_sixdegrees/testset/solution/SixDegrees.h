/**
 ** SixDegrees.h
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
 **/

#ifndef __SIX_DEGREES__
#define __SIX_DEGREES__

#include <vector>
#include <iostream>
#include <ostream>
#include <istream>

#include "Artist.h"
#include "CollabGraph.h"

class SixDegrees {

public:
	SixDegrees();
	~SixDegrees();

	void run();

	void set_input (std::istream &in);
	void set_output(std::ostream &out);

	void populate_graph(std::istream &datafile);
	
	void bfs (Artist source, Artist dest);
	void dfs (Artist source, Artist dest);
	void excl(Artist source, Artist dest,
		      std::vector<Artist> &excluded);
	void incl(Artist source, Artist dest, Artist incl);

private:

	CollabGraph graph;
	std::ostream* outputp;
	std::istream* inputp;

	void print_path(Artist source, Artist dest, std::stack<Artist> path);

	void run_bfs(Artist curr, Artist dest);
	bool run_dfs(Artist curr, Artist dest);

	bool check_valid_artist(Artist artist);

};

#endif /* __SIX_DEGREES */