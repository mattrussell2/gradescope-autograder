//
// Created by vbilol01 on 12/26/16.
//
// Modified 2020-01-27 by MAS
//      made more consistent with assignment
//
// Modified 2020-01-31 by lchan05
//      made more consistent with assignment (exception messages)
//
#include "CharArrayList.h"
#include <sstream>

CharArrayList::CharArrayList() {
    arrCapacity = arrSize = 0;
    data                  = nullptr;
}

CharArrayList::CharArrayList(char a) {
    arrCapacity = arrSize = 1;
    data                  = new char[arrCapacity];
    data[0]               = a;
}

CharArrayList::CharArrayList(char *arr, int size) {
    // initialize array size
    arrCapacity = arrSize = size;
    data                  = new char[arrCapacity];

    // copy chars in
    for (int i = 0; i < size; ++i) {
        data[i] = arr[i];
    }
}
// CopyConstructor
CharArrayList::CharArrayList(const CharArrayList &other) {
    arrCapacity = other.arrCapacity;
    arrSize     = other.arrSize;
    data        = new char[arrCapacity];

    // copy chars in
    for (int i = 0; i < arrSize; ++i) {
        data[i] = other.data[i];
    }
}
// Assignemnt overload
CharArrayList &CharArrayList::operator=(const CharArrayList &rhs) {
    if (this != &rhs) {
        delete[] this->data; // free memory from LHS

        this->data        = new char[rhs.arrCapacity];
        this->arrCapacity = rhs.arrCapacity;
        this->arrSize     = rhs.arrSize;

        for (int i = 0; i < this->arrSize; ++i) {
            this->data[i] = rhs.data[i];
        }
    }
    return *this;
}

CharArrayList::~CharArrayList() {
    arrCapacity = arrSize = -1;
    delete[] data;
}

bool CharArrayList::isEmpty() const {
    return size() == 0;
}

int CharArrayList::size() const {
    return arrSize;
}

char CharArrayList::first() const {
    checkEmptyWithThrow("cannot get first of empty ArrayList");
    return elementAt(0);
}

char CharArrayList::last() const {
    checkEmptyWithThrow("cannot get last of empty ArrayList");
    return elementAt(size() - 1);
}

std::string CharArrayList::toString() const {
    std::stringstream ss;
    ss << "[CharArrayList of size " << size() << " <<";

    for (int i = 0; i < size(); ++i) {
        ss << data[i];
    }

    ss << ">>]";
    return ss.str();
}

std::string CharArrayList::toReverseString() const {
    std::stringstream ss;
    ss << "[CharArrayList of size " << size() << " <<";

    for (int i = size() - 1; i >= 0; i--) {
        ss << data[i];
    }

    ss << ">>]";
    return ss.str();
}

char CharArrayList::elementAt(int index) const {
    checkBoundsWithThrow(index);
    return data[index];
}

void CharArrayList::pushAtFront(char a) {
    insertAt(a, 0);
}

void CharArrayList::clear() {
    arrSize = 0;
}

void CharArrayList::pushAtBack(char a) {
    insertAt(a, size());
}

void CharArrayList::insertAt(char a, int index) {
    // check bounds and throw if index is out of bounds.
    if (not(index >= 0 and index <= size())) {
        throw std::range_error("index (" + std::to_string(index) +
                               ") not in range [0.." + std::to_string(size()) +
                               "]");
    }

    ensureCapacity(size() + 1);

    // shift everything to the right to make space in the sequence
    for (int i = size() - 1; i >= index; i--) {
        data[i + 1] = data[i];
    }

    data[index] = a;
    ++arrSize;
}

void CharArrayList::insertInOrder(char a) {
    if (isEmpty()) {
        pushAtFront(a);
    } else {
        int pos = 0;
        for (pos = 0; pos < size(); pos++) {
            if (a < data[pos]) { break; }
        }
        insertAt(a, pos);
    }
}

void CharArrayList::popFromFront() {
    checkEmptyWithThrow("cannot pop from empty ArrayList");
    removeAt(0);
}

void CharArrayList::popFromBack() {
    checkEmptyWithThrow("cannot pop from empty ArrayList");
    removeAt(size() - 1);
}

void CharArrayList::removeAt(int index) {
    checkBoundsWithThrow(index);

    for (int i = index; i < size() - 1; i++) {
        data[i] = data[i + 1];
    }
    arrSize--;
}

void CharArrayList::replaceAt(char a, int index) {
    checkBoundsWithThrow(index);
    data[index] = a;
}

void CharArrayList::concatenate(CharArrayList *other) {
    int otherSize = other->size();
    for (int i = 0; i < otherSize; ++i) {
        pushAtBack(other->elementAt(i));
    }
}

void CharArrayList::shrink() {
    char *oldArr  = data;
    int   oldSize = size();

    data        = new char[oldSize];
    arrCapacity = oldSize;

    for (int i = 0; i < oldSize; ++i) {
        data[i] = oldArr[i];
    }

    delete[] oldArr;
}

void CharArrayList::sort() {
    // old info
    char *oldArr  = data;
    int   oldSize = size();

    // new array
    arrSize = 0;
    data    = new char[arrCapacity];

    for (int i = 0; i < oldSize; ++i) {
        insertInOrder(oldArr[i]);
    }

    delete[] oldArr;
}

CharArrayList *CharArrayList::slice(int left, int right) {
    // if left or right are not valid.
    if ((not(left >= 0 && left <= size())) or
        not(right >= 0 && right <= size())) {
        throw std::range_error("index_out_of_bounds");
    }
    CharArrayList *newSeq = new CharArrayList();
    for (int i = left; i < right; ++i) {
        newSeq->pushAtBack(elementAt(i));
    }
    return newSeq;
}

void CharArrayList::ensureCapacity(int newSize) {
    if (arrCapacity >= newSize) {
        return;
    } else {
        // expand the array
        newSize      = newSize * 2 + 2;
        char *newArr = new char[newSize];
        for (int i = 0; i < arrSize; ++i) {
            newArr[i] = data[i];
        }
        // delete old array
        delete[] data;
        // set data members
        data        = newArr;
        arrCapacity = newSize;
    }
}

void CharArrayList::checkBoundsWithThrow(int index) const {
    if (!(index >= 0 && index < size())) {
        throw std::range_error("index (" + std::to_string(index) +
                               ") not in range [0.." + std::to_string(size()) +
                               ")");
    }
}

void CharArrayList::checkEmptyWithThrow(std::string message) const {
    if (isEmpty()) { throw std::runtime_error(message); }
}
