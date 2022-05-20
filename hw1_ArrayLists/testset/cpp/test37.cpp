/*
  test77.cpp - concatenate a non empty char array list with an empty one
  Written by: Mateo Hernandez Idrovo
  Sept. 25, 2021
*/

#include <iostream>

#include "CharArrayList.h"

int main() {
    char newList[7] = {'g', 'o','o', 'd', 'b', 'y', 'e'}; 
    CharArrayList list1(newList, 7);
    CharArrayList list2;

    list1.concatenate(&list2);

    std::cout << list1.toString() << std::endl;
    std::cout << list2.toString() << std::endl;

}