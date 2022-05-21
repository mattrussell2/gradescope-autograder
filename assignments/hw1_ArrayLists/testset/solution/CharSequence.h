//
// Created by Vivek on 12/25/16.
//

#ifndef HW1_REF_CHARSEQUENCE_H
#define HW1_REF_CHARSEQUENCE_H

#define INITAL_CAPACITY 10

#include <iostream>

class CharSequence {

public:
    //constructors
    CharSequence();
    CharSequence(char a);
    CharSequence(char arr[], int size);

    //destructor
    ~CharSequence();

    //getters
    bool isEmpty();
    int size();
    char first();
    char last();
    char elementAt(int index);
    void print();

    // setters
    void clear();
    void pushAtFront (char a);
    void pushAtBack(char a);
    void insertAt(char a, int index);
    void insertInOrder(char a);
    void popFromFront();
    void popFromBack();
    void removeAt(int index);
    void replaceAt(char a, int index);
    void concatenate(CharSequence* other);
    void shrink();

    // JFFEs
    void sort();
    CharSequence* slice(int left, int right);

private:
    // State Variables/Data Members
    char* seqArr;
    int arrCapacity;
    int arrSize;

    //private methods
    void ensureCapacity(int newSize);
    void checkBoundsWithThrow(int index);
    void checkEmptyWithThrow();



};


#endif //HW1_REF_CHARSEQUENCE_H
