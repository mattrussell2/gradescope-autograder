#include <iostream>
#include "CharArrayList.h"

int main() {

    char comp[13] = {'C', 'O', 'M', 'P', '1', '5',
                     'f', 'i', 'f', 't', 'e', 'e', 'n'};

    CharArrayList sequenceComp(comp, 13);
    CharArrayList sequenceEmpty;
    //before
    //Should print - [CharArrayList of size 0 <<>>]
    sequenceEmpty.print();
    //Should print - [CharArrayList of size 13 <<COMP15fifteen>>]
    sequenceComp.print();

    //test slice()
    std::cout << "Testing slice\n";

    //slice 0-1 on empty
    //Should print - index_out_of_range
    try {
        CharArrayList *sequenceSliceEmpty = nullptr;
        sequenceSliceEmpty = sequenceEmpty.slice(0, 1);
        delete sequenceSliceEmpty;
    } catch (std::range_error) {
        std::cout << "index_out_of_range\n";
    } catch (...) {
        std::cout << "Incorrect Exception Thrown\n";
    }

    //slice 1-5 on nonempty
    CharArrayList *sequenceSliceOne = sequenceComp.slice(1, 7);
    //Should print - [CharArrayList of size 6 <<OMP15f>>]
    sequenceSliceOne->print();
    delete sequenceSliceOne;

    //slice 5-1 on nonempty
    CharArrayList *sequenceSliceTwo = sequenceComp.slice(5, 1);
    //Should print - [CharArrayList of size 0 <<>>]
    sequenceSliceTwo->print();
    delete sequenceSliceTwo;

    return 0;
}
