/**
 * CS15 HW1 TEST 49
 * 
 * first() - while sequentially removing elements
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char numbs[] = {'9', '8', '7', '6', '5', '4', '3', '2', '1', '0'};
    CharArrayList list1(numbs, 10);
    CharArrayList list2(numbs, 10);

    try
    {   
        int i = 0;
        while (! list1.isEmpty()) {
            if (list1.first() != numbs[i]) {
                throw std::runtime_error("First element of Student's list1 was incorrect!");
            }
            list1.popFromFront();
            i++;
        }


        while (! list2.isEmpty()) {
            if (list2.first() != numbs[0]) {
                throw std::runtime_error("First element of Student's list2 was incorrect!");
            }
            list2.popFromBack();
        }

    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    std::cout << "Student correctly kept track of first() while inserting new "
                "elements."
            << std::endl;

    return 0;

}