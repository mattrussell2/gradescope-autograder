/**
 * CS15 HW1 TEST 42 (The answer to Life, the Universe and Everything!)
 * 
 * Assignment Operator - Non-Empty LHS
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passed[] = {'p', 'a', 's', 's', 'e', 'd'};
    char failed[] = {'f', 'a', 'i', 'l', 'e', 'd'};
    CharArrayList *list1 = new CharArrayList(passed, 6);
    CharArrayList list2(failed, 6);

    // Envoke the Assignment Operator
    list2 = *list1;

    // If the assignment operator made a deep copy, deleting list1 should not 
    // affect list2
    delete list1;

    /* Should print - [CharArrayList of size 6 <<passed>>] */
    std::cout << list2.toString() << std::endl;
    
    return 0;
}