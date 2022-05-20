/* CS15 
*  Homework 1- CharArrayList & CharLinkedList
*
*  Test 40- Copy Constructor CharArrayList Test
*  Tests the copy constructor and ensures deep copy
*  
*  Spencer Ha(sha01)
*  9/25/21
*/

#include <iostream>
#include "CharArrayList.h"

int main(){
    //Create first list consisting of a
    CharArrayList *list1 = new CharArrayList('a');

    //Envokes the copy constuctor to *hopefully* make a deep copy
    CharArrayList list2 = *list1;

    delete list1;
    //If student's copy constructor does a shallow copy, code will seg fault
    //when attempting to print. 
    std::cout << list2.toString() << std::endl;

    return 0;
}