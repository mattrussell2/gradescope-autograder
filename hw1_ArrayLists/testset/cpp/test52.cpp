/**
 * CS15 HW1 TEST 52
 * 
 * elementAt - while removing elements
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"
#include "assert.h"


int main() {

    char followX[] = {'_', '_', '_', '_', 'X', '_', '_', '_', '_'};
    CharArrayList list1(followX, 9);

    try
    {
        // test elementAt() while removing elements from front and back of 
        // list. We keep track of the 'X' in the middle as we make each pass in
        // the for loop.
        for (int i = 0; i < 8; i++) {
            if (i % 2 == 0) {
                list1.popFromBack();
                if (list1.elementAt(list1.size() / 2) != 'X') {
                    throw std::runtime_error("elementAt() was incorrect!");
                }
            } else {
                list1.popFromFront();
                if (list1.elementAt((list1.size() / 2)) != 'X') {
                    throw std::runtime_error("elementAt() was incorrect!");
                }
            }
        }
    }
    catch(const std::runtime_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    

    std::cout << "Student correctly kept track of elementAt() while removing "
                 "elements."
              << std::endl;

    return 0;
}