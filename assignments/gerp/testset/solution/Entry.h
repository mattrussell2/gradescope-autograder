/**
 * Entry.h
 *
 *      A data model for Index entries
 *        Note: This was seperated from Index class to allow the seperation of
 *              Hashtable template implementation from the interface
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 */
#ifndef ENTRY_H
#define ENTRY_H
/**
 * @brief An Index Entry. Stores the word verbatim, the lineno, the
 * file number (index into files array), and the position of its
 * sentence in the file.
 *
 */

struct Entry {
        std::streampos sentence;
        std::string    word;
        size_t         fileno;
        unsigned       lineno;

        Entry(std::string newWord, unsigned newLineno, std::streampos position,
              size_t new_fileno)
            : sentence(position),
              word(newWord),
              fileno(new_fileno),
              lineno(newLineno) {}
};
#endif