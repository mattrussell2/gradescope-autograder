//
// Created by Vivek on 10/30/16.
//
// Changelog:
//      2016-11-13 [MAS] 
//           - Changed throws to use out_of_range exception
//             rather than throw strings.
//           - Used "not" rather than "!"
//           - using namespace std:  this is C++ source not to be included
//

#include <exception>
#include <stdexcept>

#include "DirNode.h"

using namespace std;

DirNode::DirNode(string newName) {
    this->name = newName;
    this->parent = nullptr;
}

void DirNode::addFile(string newName) {
    fileNames.push_back(newName);
}

void DirNode::addSubDirectory(DirNode *newDir) {
    directories.push_back(newDir);
}

bool DirNode::hasSubDir() {
    return directories.size() != 0;
}

bool DirNode::hasFiles() {
    return fileNames.size() != 0;
}

bool DirNode::isEmpty() {
    return not hasFiles() and not hasSubDir();
}

int DirNode::numSubDirs() {
    return (int)directories.size();
}

int DirNode::numFiles() {
    return (int)fileNames.size();
}

void DirNode::setName(string newName) {
    name = newName;
}

string DirNode::getName() {
    return name;
}

DirNode *DirNode::getSubDir(int n) {
    if (n >= (int)directories.size()) {
        throw out_of_range("No sub dir at index:  " + to_string(n));
    }
    return directories[n];
}

string DirNode::getFile(int n) {
    if (n >= (int)fileNames.size()) {
        throw out_of_range("No file at index:  " + to_string(n));
    }
    return fileNames[n];
}

DirNode *DirNode::getParent() {
    return parent;
}

void DirNode::setParent(DirNode *newParent) {
    parent = newParent;
}

DirNode::DirNode(const DirNode &other) {
    this->parent = other.parent;
    this->name = other.name;
    this->fileNames = other.fileNames;
    this->directories = other.directories;
}

DirNode &DirNode::operator=(const DirNode &other) {

    if(this != &other){

        this->parent = other.parent;
        this->name = other.name;
        this->fileNames = other.fileNames;
        this->directories = other.directories;

    }
    return *this;
}

DirNode::DirNode() {
    this->parent = nullptr;
    this->name = "";
    this->directories.clear();
    this->fileNames.clear();
}
