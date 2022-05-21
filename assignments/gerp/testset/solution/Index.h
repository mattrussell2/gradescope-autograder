#ifndef INDEX_H
#define INDEX_H

#include <algorithm>
#include <cctype>
/**
 * Index.h
 *
 *      Interface for the Index class, a class that builds an queryable index
 *      of all text files below provided directory
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 */
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <vector>
#include "DirNode.h"
#include "Entry.h"
#include "FSTree.h"
#include "Hashtable.h"

class Index {
public:
        enum QueryMode { Sensitive, Insensitive };

private:
        // A unordered_map (hash table) that uses strings as keys that "map" to
        // vectors of Entries

        // std::unordered_map<std::string, std::vector<Entry>> entries;
        Hashtable<std::vector<Entry>> entries;
        std::vector<std::string>      files;

        std::string &lower(std::string &s) const;
        std::string &cleanString(std::string &s) const;
        void         buildIndex(DirNode *node, std::string dir);
        bool shouldAdd(const std::vector<Entry> &e, const Entry &toAdd) const;
        bool reportMatch(const std::vector<Entry> &e, std::ostream &out,
                         std::string key, QueryMode mode) const;
        void parseFile(const std::string &filename);

public:
        void query(const std::string &toQuery, std::ostream &out,
                   QueryMode mode) const;
        void init(std::string rootDir);
        Index(std::string rootDir);
        Index() {}
};

#endif