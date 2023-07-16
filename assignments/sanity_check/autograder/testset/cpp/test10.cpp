#include <fstream>
#include <iostream>

int main(int argc, char **argv) {
    std::string   fname = argv[1];
    std::ofstream of(fname);
    of << "hello world!" << std::endl;
    return 0;
}