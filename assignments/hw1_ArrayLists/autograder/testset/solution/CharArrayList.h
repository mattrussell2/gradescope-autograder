//
// Created by Vivek on 12/25/16.
//

// Modified 1/31/2020 by lchan05 for different exception message

#ifndef HW1_REF_CHARSEQUENCE_H
#define HW1_REF_CHARSEQUENCE_H

#define INITAL_CAPACITY 10

#include <iostream>
#include <string>

class CharArrayList {

public:
    //constructors
   CharArrayList();
   CharArrayList(char a);
   CharArrayList(char arr[], int size);
   // copy constructor 
   CharArrayList(const CharArrayList &other);
    //destructor
   ~CharArrayList();
    //Assignment operator overload
   CharArrayList &operator =(const CharArrayList &rhs);
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
    void concatenate(CharArrayList *other);
    void shrink();

    // JFFEs
    void sort();
   CharArrayList *slice(int left, int right);

private:
    // State Variables/Data Members
    char *data;
    int   arrCapacity;
    int   arrSize;

    //private methods
    void ensureCapacity(int newSize);
    void checkBoundsWithThrow(int index);
    void checkEmptyWithThrow(std::string message);
};


#endif //HW1_REF_CHARSEQUENCE_H
