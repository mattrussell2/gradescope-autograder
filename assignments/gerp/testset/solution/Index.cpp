/**
 * Index.cpp
 *
 *      Implementation for the Index class, a class that builds an queryable
 *      index of all text files below provided directory
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 * Changelog:
 *     2022-03-25 [Milod Kazerounian]
 *         - When reporting query results, maintain a set of (fileno, lineno)
 *         pairs that have already been reported. This is to fix a bug
 *         caught by Roger Burtonpatel, where the same line could be
 *         reported multiple times for case insensitive queries. 
 *         - Replaced buggy version of cleanString with 2017f solution
 *         version.
 *         - Fix to input file stream optimization: close filestreams when
 *          done with them.
 */
#include "Index.h"
#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <set>
#include <utility>
#include "DirNode.h"
#include "FSTree.h"

using namespace std;

Index::Index(string rootDir) {
        init(rootDir);
}
void Index::init(string rootDir) {
        buildIndex(FSTree(rootDir).getRoot(), rootDir);
}

/**
 * @brief         Performs either a sensitive or insensitive query on the index
 *
 * @param toQuery string   The string to query
 * @param out     ostream& The output stream to use to print out matches
 * @param mode    Enum     Either insensitive or sensitive
 *                         i.e  either (mode == Insensitive)
 *                              or     (mode == Sensitive)
 *                              will be true
 */
void Index::query(const string &toQuery, ostream &out, QueryMode mode) const {
        string key = toQuery, cleanQuery = toQuery;
        cleanString(cleanQuery);
        lower(cleanString(key));
        try {
                if (not reportMatch(entries.at(key), out, cleanQuery, mode))
                        throw std::runtime_error("");
        } catch (const std::runtime_error &e) {
                // For compatibility with testing script of previous semesters
                out << cleanQuery << " Not Found.";
                if (mode == Index::Sensitive)
                        out << " Try with @insensitive or @i.";
                out << "\n";
        }
        out << std::flush;
}

/**
 * @brief Returns the word starting at the first alnum char and ending
 *        at the last alnum char before the next whitespace char
 *
 * @details Advances the start pointer to the first whitespace after last alnum
 *          in returned word
 * @param  start start of char * to scan
 * @param  end   end of char *
 * @param  word outputParameter, "cleaned" word
 *
 * @return bool whether a string was read
 */
bool getNextWord(const char *&start, const char *&end, string &word) {
        // Find first alpha numeric char
        for (; start != end && not(::isalnum(*start)); start++)
                ;
        const char *lastAlnum = start;
        const char *curr;
        // Finds next whitespace character
        for (curr = start; curr != end && not(::isspace(*curr)); curr++)
                if (::isalnum(*curr))
                        lastAlnum = curr + 1;

        word.assign(start, lastAlnum);
        start = curr;
        return not word.empty();
}

/**
 * @brief Inserts all words from file and inserts into Index
 *
 * @param filename
 */
void Index::parseFile(const string &filename) {
        ifstream  infile(filename);
        string    line, word;
        streampos position;    // This a way of remembering positions in a file
        unsigned  lineno = 0;  // Current line number
        size_t    fileno = files.size();  // Current file index in files array

        if (!infile)
                throw runtime_error("Could not open " + filename);

        // Save position of infile (to remember where current line starts),
        // then gets the line
        // Uses comma operator : https://en.wikipedia.org/wiki/Comma_operator
        while (position = infile.tellg(), getline(infile, line)) {
                lineno++;

                // Get each word in line
#ifdef USE_STRINGSTREAM
                stringstream ss(line);
                while (ss >> word) {
                        cleanString(word);
#else
                const char *end   = line.data() + line.size();
                const char *start = line.data();
                while (getNextWord(start, end, word)) {
#endif
                        // Store cleaned word in the entry
                        Entry toAdd{word, lineno, position, fileno};

                        // Get the vector of entries from hashtable
                        // A new one is created if one didn't already exist
                        vector<Entry> &entryList = entries[lower(word)];

                        if (shouldAdd(entryList, toAdd))
                                entryList.push_back(toAdd);
                }
        }

        files.push_back(filename);
}

/**
 * @brief Checks whether another identical word on the same line was already
 *        added to the Index
 *
 * @param e      Vector of Entrys for a given key
 * @param toAdd  Potential entry to add to e
 * @return       Returns true if toAdd is not an empty string and hasn't
 *                            already been added to index
 *                       false otherwise
 */
bool Index::shouldAdd(const vector<Entry> &e, const Entry &toAdd) const {
        if (toAdd.word == "")
                return false;

        // Start from end of list of Entrys
        for (int i = (int)e.size() - 1; i >= 0; i--)
                // stop if current entry is not on same line or in same file
                if (toAdd.lineno != e[i].lineno or toAdd.fileno != e[i].fileno)
                        break;
                else if (e[i].word == toAdd.word)
                        return false;

        return true;
}

/**
 * @brief Converts a string to lowercase
 *
 * @param s        String to lower
 * @return string  Lowercase version of string
 */
string &Index::lower(string &s) const {
        // <algorithm> std::transform
        // Iterates through string and transforms string to lowercase
        std::transform(s.begin(), s.end(), s.begin(), ::tolower);
        return s;
}

/**
 * @brief Removes leading and trailing non-alphanumeric characters from string
 *
 * @param word       String to clean
 * @return string Cleaned version of string
 */
string &Index::cleanString(string &word) const{
        if (word == "") return word;

        size_t lowerbound = 0;
        size_t upperbound = 0;

        //find first alphanum
        for (lowerbound = 0; lowerbound < word.size(); lowerbound++) {
            if (isalnum(word[lowerbound])) {
                break;
            }
        }

        //find last alphanum
        for (upperbound = word.size() - 1; upperbound >= lowerbound; upperbound--) {
            if (isalnum(word[upperbound])) {
                break;
            }
        }

        word.replace(0, word.size(), word.substr(lowerbound, (upperbound - lowerbound + 1)));

        return word;
}

/**
 * @brief Iterates through directory tree, and parses any files found
 *
 * @param node Root of FSTree to search
 * @param dir  String representation of path prefix
 */
void Index::buildIndex(DirNode *node, string dir) {
        dir += "/";

        for (int i = 0; i < node->numSubDirs(); i++) {
                DirNode *subdir = node->getSubDir(i);
                buildIndex(subdir, dir + subdir->getName());
        }

        for (int i = 0; i < node->numFiles(); i++)
                parseFile(dir + node->getFile(i));
}

/**
 * @brief Prints out formatted output to request ostream
 *
 * @param e   Entry to print
 * @param out Stream to print to
 */
bool Index::reportMatch(const vector<Entry> &wordEntries, ostream &out,
                        string query, QueryMode mode) const {
        bool     reportedMatch = false;
        size_t   openFile;
        ifstream infile;
        set<pair<int, int>> reported;
        // At throws std::runtime_error if key not found
        for (const Entry &e : wordEntries)
                if (mode == Insensitive or e.word == query) {
                        // Check if current fileno, lineno pair was already reported,
                        // if so continue to next iteration. Necessary for @i queries.
                        pair<int, int> fileno_lineno = make_pair(e.fileno, e.lineno);
                        if (reported.find(fileno_lineno) != reported.end()) {
                                continue;
                        }
                        // Reopening and closing the file for each word causes
                        // a slowdown of several orders of Magnitude
                        // Caught by zgolds01 - Zachary Goldstein
                        if (openFile != e.fileno) {
                                openFile = e.fileno;
                                ifstream newFile(files[e.fileno]);
                                if (infile.is_open()) {
                                        infile.close();
                                }
                                std::swap(infile, newFile);
                                if (!infile)
                                        throw runtime_error("Could not open " +
                                                            files[e.fileno]);
                        }
                        string line;
                        // Read sentence from file
                        infile.seekg(e.sentence);
                        getline(infile, line);

                        out << files[e.fileno] << ":" << e.lineno << ": "
                            << line << "\n";
                        reported.insert(fileno_lineno);
                        reportedMatch = true;
                }
        if (infile.is_open()) {
                infile.close();
        }
        return reportedMatch;
}
