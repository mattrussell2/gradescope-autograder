//
// Created by vbilol01 on 12/26/16.
//

#include "CharSequence.h"

CharSequence::CharSequence() {
    arrCapacity = INITAL_CAPACITY;
    arrSize = 0;
    seqArr = new char[arrCapacity];
}

CharSequence::CharSequence(char a) {
    arrCapacity = INITAL_CAPACITY;
    arrSize = 1;
    seqArr = new char[arrCapacity];
    seqArr[0] = a;
}

CharSequence::CharSequence(char *arr, int size) {
    //initialize array size
    arrCapacity = (size + 1)*2;
    arrSize = size;
    seqArr = new char[arrCapacity];

    //copy chars in
    for (int i = 0; i < size; ++i) {
        seqArr[i] = arr[i];
    }
}

CharSequence::~CharSequence() {
    delete [] seqArr;
}

bool CharSequence::isEmpty() {
    return size() == 0;
}

int CharSequence::size() {
    return arrSize;
}

char CharSequence::first() {
    checkEmptyWithThrow();
    return elementAt(0);
}

char CharSequence::last() {
    checkEmptyWithThrow();
    return elementAt(size()-1);
}

void CharSequence::print() {
    std::cout << "[CharSequence of size " << size() <<  " <<";

    for (int i = 0; i < size(); ++i) {
        std::cout << seqArr[i];
    }

    std::cout << ">>]" << std::endl;
}

char CharSequence::elementAt(int index) {
    checkBoundsWithThrow(index);
    return seqArr[index];
}

void CharSequence::pushAtFront(char a) {
    insertAt(a, 0);
}

void CharSequence::clear() {
    arrSize = 0;
}

void CharSequence::pushAtBack(char a) {
    insertAt(a, size());
}

void CharSequence::insertAt(char a, int index) {
    //check bounds and throw if index is out of bounds.
    if(!(index >= 0 && index <= size())){
        throw std::range_error("index_out_of_bounds");
    }

    ensureCapacity(size() + 1);

    //shift everything to the right to make space in the sequence
    for (int i = size(); i >= index ; --i) {
        seqArr[i+1] = seqArr[i];
    }

    seqArr[index] = a;
    ++arrSize;
}

void CharSequence::insertInOrder(char a) {
    if(isEmpty()){
        pushAtFront(a);
    }else {
        int pos = 0;
        for (pos = 0; pos < size(); ++pos) {
            if (a < seqArr[pos]) {
                break;
            }
        }
        insertAt(a, pos);
    }
}

void CharSequence::popFromFront() {
    checkEmptyWithThrow();
    removeAt(0);
}

void CharSequence::popFromBack() {
    checkEmptyWithThrow();
    removeAt(size()-1);
}

void CharSequence::removeAt(int index) {
    checkBoundsWithThrow(index);

    for (int i = index; i <size() ; ++i) {
        seqArr[i] = seqArr[i+1];
    }
    --arrSize;
}

void CharSequence::replaceAt(char a, int index) {
    checkBoundsWithThrow(index);
    seqArr[index] = a;
}

void CharSequence::concatenate(CharSequence *other) {
    int otherSize = other->size();
    for (int i = 0; i < otherSize; ++i) {
        pushAtBack(other->elementAt(i));
    }
}

void CharSequence::shrink() {
    char* oldArr = seqArr;
    int oldSize = size();

    seqArr = new char[oldSize];
    arrCapacity = oldSize;

    for (int i = 0; i < oldSize; ++i) {
        seqArr[i] = oldArr[i];
    }

    delete [] oldArr;
}

void CharSequence::sort() {
    //std::cerr << "sorting\n";
    //old info
    char* oldArr = seqArr;
    int oldSize = size();

    //new array
    arrSize = 0;
    seqArr = new char[arrCapacity];

    for (int i = 0; i < oldSize; ++i) {
        //std::cerr << oldArr[i] << std::endl;
        insertInOrder(oldArr[i]);
        //print();
    }
    delete [] oldArr;
    //print();
}

CharSequence *CharSequence::slice(int left, int right) {
    //if left or right are not valid.
    if((!(left >= 0 && left <= size()))
       ||!(right >= 0 && right <= size())){
        throw std::range_error("index_out_of_bounds");
    }
    CharSequence* newSeq = new CharSequence();
    for (int i = left; i < right ; ++i) {
        newSeq->pushAtBack(elementAt(i));
    }
    return newSeq;
}

void CharSequence::ensureCapacity(int newSize) {
    if (arrCapacity >= newSize) {
        return;
    } else {
        //expand the array
        newSize = newSize * 2 + 1;
        char *newArr = new char[newSize];
        for (int i = 0; i < arrSize; ++i) {
            newArr[i] = seqArr[i];
        }
        //delete old array
        delete[] seqArr;
        //set data members
        seqArr = newArr;
        arrCapacity = newSize;
    }
}

void CharSequence::checkBoundsWithThrow(int index) {
    if(!(index >= 0 && index < size())){
        throw std::range_error("index_out_of_range");
    }
}

void CharSequence::checkEmptyWithThrow() {
    if (isEmpty()){
        throw std::runtime_error("sequence_is_empty");
    }
}
