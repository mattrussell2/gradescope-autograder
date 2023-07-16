#include <fstream>
#include <iostream>

int main(int argc, char **argv) {
    std::string   fname = argv[1];
    std::ofstream of(fname);
    for (int i = 100; i >= 0; i--) {
        of << i << std::endl;
    }
    return 0;
}