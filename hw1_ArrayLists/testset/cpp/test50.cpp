/**
 * CS15 HW1 TEST 50
 * 
 * first() - while sequentially adding elements
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"
#include "assert.h"


int main() {

    char numbs[] = {'9', '8', '7', '6', '5', '4', '3', '2', '1', '0'};
    CharArrayList list1;
    CharArrayList list2;
    try
    {
        // Test first when inserting at front
        for (int i = 0; i < 10; i++) {
            list1.pushAtFront(numbs[i]);
            if (list1.first() != numbs[i]) {
                throw std::runtime_error("First element of Student's list1 was incorrect!");
            }
        }

        // test first when insterting at back
        for (int i = 0; i < 10; i++) {
            list2.pushAtBack(numbs[i]);
            if (list2.first() != numbs[0]) {
                throw std::runtime_error("First element of Student's list2 was incorrect!");
            }
        }
    }
    catch(const std::runtime_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    

    std::cout << "Student correctly kept track of first() while inserting new "
                 "elements."
              << std::endl;

    return 0;
}