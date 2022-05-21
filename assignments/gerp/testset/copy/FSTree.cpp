/*
 * Created by Vivek on 10/30/16.
 *
 * Changelog:
 *     2016-11-27 MAS 
 *         - Changed constructor to put full pathname back in root
 *           Issue:  The name passed to the constructor may be an
 *                   arbitrary path name, e. g., "/comp/15/files/dirname",
 *                   but buildTree() puts only the basename ("dirname")
 *                   there.
 *           Yes, students could create local soft links, but this 
 *           confuses them, and is inconsistent with what we asked
 *           them to do.
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <dirent.h>
#include <stdlib.h>
#include <vector>
#include <iostream>
#include <exception>

#include "FSTree.h"

//Public Definitions
FSTree::FSTree(std::string rootName) {
    //TODO: Remove trailing "/" in rootname if it exists
    root = buildTree(rootName);
    root->setName(rootName);   // MAS:  put full path back in root node
}

FSTree::~FSTree() {
    burnTree(root);
}

DirNode *FSTree::getRoot() const {
    return root;
}

//Destroy the tree
void FSTree::burnTree() {
    burnTree(root);
    root = nullptr;
}

// checks if file @ path is a a file
// Throws an exception if a file is invalid or if stat has an error
bool FSTree::is_file(const char *path) {
    struct stat s;
    if (stat(path,&s) == 0) {
        if (s.st_mode & S_IFDIR) {
            return false;
        } else if (s.st_mode & S_IFREG) {
            return true;
        } else {
            throw std::runtime_error("Invalid file found: could not build tree");
        }
    } else {
        throw std::runtime_error("stat error: could not build tree");
    }
}

//if its not a file its a directory
bool FSTree::is_dir(const char *path) {
    return !is_file(path);
}

//returns the basename of a path
//e.g. /root/la/a/b/c/hello.c -> hello.c
std::string FSTree::baseName(std::string const &path) {
    return path.substr(path.find_last_of("/\\") + 1);
}

//builds the tree and returns the root.
//throws an exception if the root directory could not be found
DirNode *FSTree::buildTree(std::string rootName) {
    struct dirent *entry;
    DIR *dp;

    dp = opendir(rootName.c_str());
    if (dp == NULL) {
        throw std::runtime_error("Directory not found: could not build tree");
    }

    /* /root/la/a/b/c/hello.c -> hello.c */
    DirNode *current_dir = new DirNode(baseName(rootName));
    std::vector<std::string> todo;

    while ((entry = readdir(dp))) {
        std::string entryString = std::string(entry->d_name);
        /* Ignore hidden files */
        if (entryString[0] != '.') {
            todo.push_back(entryString);
        }
    }

    closedir(dp);

    for (std::string childName : todo) {
        std::string fullPath = rootName + "/" + childName;
        if (is_file(fullPath.c_str())) {
            current_dir->addFile(childName);
        }
        else {
            /* NOTE: does not handle links, etc */
            DirNode *newChild = buildTree(fullPath);
            newChild->setParent(current_dir);
            current_dir->addSubDirectory(newChild);
        }
    }

    return current_dir;
}

//destroys the tree
void FSTree::burnTree(DirNode *root) { /* muahaha */
    if (root == nullptr){
        return;
    }
    for (int i = 0; i < root->numSubDirs(); i++) {
        burnTree(root->getSubDir(i));
    }

    delete root;
}

bool FSTree::isEmpty() {
    return root == nullptr;
}

FSTree::FSTree() {
    root = nullptr;
}

FSTree::FSTree(const FSTree &other) {
    this->root = preOrderCopy(other.root, nullptr);
}

FSTree &FSTree::operator=(const FSTree &other) {

    if(this != &other){

        this->burnTree();
        this->root = preOrderCopy(other.root, nullptr);

    }
    return *this;
}

