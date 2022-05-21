/**
 * main.cpp
 *
 *      Driver for Gerp
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 */
#include "DirNode.h"
#include "FSTree.h"
#include "Index.h"
#include <fstream>
#include <iostream>

#define DIE(x)                    \
    do {                          \
        std::cout << (x) << "\n"; \
        return 1;                 \
    } while (0)

#ifdef TESTING_WITH_2018f
#include <sys/types.h>
#include <unistd.h>
#endif

int run(Index& ind, std::ofstream& output);

int main(int argc, char* argv[]) {
    // std::cout << sizeof(Entry) << std::endl;
    // std::cout << sizeof(std::streampos) << std::endl;
    // std::cout << sizeof(std::string) << std::endl;
    // std::cout << sizeof(unsigned) << std::endl;
    // std::cout << sizeof(size_t) << std::endl;
    // return 0;
    Index ind;

#ifdef TESTING_WITH_2018f
    // For compatibility with testing script of  previous versions of
    // assignment
    // Increment 2 to 3
    argc++;
#endif
    if (argc != 3) {
        // DIE("Usage: " + std::string(argv[0]) + " inputDirectory outputFile");
        std::cerr << "Usage: ./gerp inputDirectory outputFile\n";
        return 1;
    }

#ifdef TESTING_WITH_2018f
    // For compatibility with testing script of  previous versions of
    // assignment

    // Open dummy file so program thinks that file is open
    std::ofstream output("/dev/null");
    // Redirect output file to cout
    output.basic_ios<char>::rdbuf(std::cout.rdbuf());
#else
    // Spring 2019 Soluton
    std::ofstream output(argv[2]);
#endif
    if (!output.is_open()) DIE("Could not open output file");

    // Try to build index
    try {
        ind.init(argv[1]);
    } catch (...) { DIE("Could not build index, exiting."); }
    return run(ind, output);
}

int run(Index& ind, std::ofstream& output) {
    std::string input;
    // While loop condition prints query, then reads from cin and evaluates
    // cin as the loop condition
    // Uses comma-operator
    while ((std::cout << "Query? "), std::cin >> input) {
        if (input == "@q" or input == "@quit") {
            //            std::cout << "\n";
            break;
        }
        if (input == "@f") {
            if (!(std::cin >> input)) DIE("Unexpected EOF");

            output.close();
            output.open(input);
            if (not output.is_open()) DIE("Could not open " + input);
        } else if (input == "@i" or input == "@insensitive") {
            if (!(std::cin >> input)) DIE("Unexpected EOF");
            ind.query(input, output, Index::Insensitive);
        } else
            ind.query(input, output, Index::Sensitive);
        // std::cout << "\n";
    }

    std::cout << "Goodbye! Thank you and have a nice day.\n";
    return 0;
}
