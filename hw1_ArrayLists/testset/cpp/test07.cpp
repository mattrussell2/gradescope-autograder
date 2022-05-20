/**
 * CS15 HW1 TEST 07
 * 
 * Tests Clear - non-empty ArrayList
 * 
 * abui02
 * 9/23/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1('m');
    /* should print: [CharArrayList of size 1 <<m>>]*/
    std::cout << list1.toString() << " --> ";

    list1.clear();

    /* should print: [CharArrayList of size 0 <<>>] */
    std::cout << list1.toString() << std::endl;


    if (list1.isEmpty()) {
        std::cout << "PASS: Student correctly called clear() on a non-empty ArrayList.\n" << std::endl;
    } else {
        std::cout << "FAIL: Student incorrectly called clear() on a non-empty ArrayList.\n" << std::endl;
    }



    /*****************************************************/
    char comp[7] = {'C', 'o', 'm', 'p', ' ', '1', '5'};
    CharArrayList list2(comp, 7);
    /* should print: [CharArrayList of size 7 <<Comp 15>>]*/
    std::cout << list2.toString() << " --> ";

    list2.clear();

    /* should print: [CharArrayList of size 0 <<>>] */
    std::cout << list2.toString() << std::endl;

    if (list1.isEmpty()) {
        std::cout << "PASS: Student correctly called clear() on a non-empty ArrayList." << std::endl;
    } else {
        std::cout << "FAIL: Student incorrectly called clear() on a non-empty ArrayList." << std::endl;
    }

}