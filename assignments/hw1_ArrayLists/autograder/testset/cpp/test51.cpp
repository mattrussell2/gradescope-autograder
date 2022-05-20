/**
 * CS15 HW1 TEST 51
 * 
 * elementAt - while adding elements
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"
#include "assert.h"


int main() {

    char followX[] = {'_', '_', '_', '_', 'X', '_', '_', '_', '_', '_'};
    CharArrayList list1(followX, 10);

    try
    {
        // Test first when inserting at front and back
        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                list1.pushAtFront('_');
                if (list1.elementAt(list1.size() / 2) != 'X') {
                    throw std::runtime_error("elementAt() was incorrect!");
                }
            } else {
                list1.pushAtBack('_');
                if (list1.elementAt((list1.size() / 2) - 1) != 'X') {
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
    

    std::cout << "Student correctly kept track of elementAt() while inserting new "
                 "elements."
              << std::endl;

    return 0;
}