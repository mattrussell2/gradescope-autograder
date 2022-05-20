/* 
 * Homework 1 - CS15 - CharArrayList
 *
 * Test 20 - pushAtFront() - 1 element
 *
 * Author: Nickolas Gravel
 *   Date: 9.23.2021
 *
 */ 

#include <iostream>
#include "CharArrayList.h"

int main() {

    CharArrayList list;                         /* Create list */
    list.pushAtFront('n');                      /* Push 1 element to back */
    std::cout << list.toString() << std::endl;  /* Print list */

    return 0;
}
