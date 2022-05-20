/* 
 * Homework 1 - CS15 - CharArrayList
 *
 * Test 22 - pushAtFront() - 3,000 element - a "stress test"
 *      
 * Author: Nickolas Gravel
 *   Date: 9.23.2021
 *
 */

#include <iostream>
#include "CharArrayList.h"

int main() {
    char cs[15] = {'I','N','F','R','A','S','T','R','U','C','T','U','R','E',' '};

    CharArrayList list;

    for (int i = 0; i < 200; i++) {
        for (int j = 0; j < 15; j++) {
            list.pushAtFront(cs[j]);   /* Push back contents of cs[i] (miami) */
        }
    }
    std::cout << list.toString() << std::endl;
    return 0;
}
