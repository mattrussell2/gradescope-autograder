/*
  test77.cpp - concatenates a non empty char array list with itself
  Written by: Mateo Hernandez Idrovo
  Sept. 25, 2021
*/

#include <iostream>

#include "CharArrayList.h"

int main() {
    char array1[17] = {'V', 'e', 'r', 'y', ' ', 'L', 'o', 'n', 'g', ' ', 
                      'S', 't', 'r', 'i', 'n', 'g', ' '}; 

    CharArrayList list1(array1, 17);

    list1.concatenate(&list1);
    std::cout << list1.toString() << std::endl;

}