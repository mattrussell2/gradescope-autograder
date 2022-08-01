/**
 ** main.cpp
 **
 ** Project Two: Six Degrees of Collaboration
 **
 ** Purpose:
 **   Interpret command line arguments and
 **   initialize a SixDegrees instance
 **
 ** ChangeLog:
 **   17 Nov 2020: zgolds01
 **       main.cpp driver created
 **
 **/

#include <fstream>
#include <iostream>
#include <ios>
#include <string>

#include "SixDegrees.h"

void usage(std::string progname)
{
	std::cerr << "Usage: "
			  << progname
			  << " dataFile"
			  << " [commandFile]"
			  << " [outputFile]"
			  << std::endl;
}

void assert_file(std::ios &file, std::string filename)
{
	if (not file.good()) {
		std::cerr << filename << " cannot be opened." << std::endl;
		exit(EXIT_FAILURE);
	}
}

int main(int argc, char *argv[])
{

	SixDegrees sd;
	std::ofstream output;
	std::ifstream commands;
	std::ifstream data;

    switch (argc) {
    	case 4: /* 3rd positional arg is output file */
    		output.open(argv[3]);
    		assert_file(output, argv[3]);
    		sd.set_output(output);


    	case 3: /* 2nd positional arg is commands file */
    		commands.open(argv[2]);
    		assert_file(commands, argv[2]);
    		sd.set_input(commands);


    	case 2: /* 1st positional arg is artists file */
    		data.open(argv[1]);
    		assert_file(data, argv[1]);
    		sd.populate_graph(data);
    		data.close();

    		break;

    	default:
    		usage(argv[0]);
    		exit(EXIT_FAILURE);
    		break;
    }

    sd.run();

    /* It is not necessary to close these file streams because there
     * is no need to free up resources immediately before program
     * termination (streams are closed automatically when they pass
     * out of scope).
     */
    output.close();
    commands.close();

    return 0;
}


