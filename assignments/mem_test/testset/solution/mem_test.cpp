#include <fstream>
#include <iostream>
#include <stdlib.h>


void myfunc(int *x, int len) {
    for (int i = 0; i < len; i++) {
        if (rand() * 10 > 5) { x[i] = rand() * 10000; }
    }
}

int main(int argc, char **argv) {
    int num_ints;
    std::cin >> num_ints;
    std::cout << "Allocing " << num_ints << " integers" << std::endl;
    int *x = new int[num_ints];
    // do something random and print the values so the compiler can't optimize
    // out the alloc
    std::cout << "inserting random values into the array" << std::endl;
    for (int i = 0; i < num_ints; i++) {
        x[i] = rand() * 100000;
        if (argc > 1) {
            std::cout << "blah blah blahdyy blah " << x[i] << std::endl;
        }
    }
    myfunc(x, num_ints);
    delete[] x;
    return 0;
}