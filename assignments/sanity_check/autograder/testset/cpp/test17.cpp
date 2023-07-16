#include <iostream>

int main() {
    int *x = new int[1000000000];
    delete[] x;
    return 0;
}