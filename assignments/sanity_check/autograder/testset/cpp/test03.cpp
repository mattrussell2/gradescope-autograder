#include <cassert>
#include <iostream>

int main() {
    int *x = new int[10];
    for (int i = 0; i < 10; i++) {
        x[i] = i;
    }
    delete[] x;
    return 0;
}